import { describe, expect, it } from 'vitest';
import { defaultCommand } from '../src/engine/command';
import { LANGS } from '../src/engine/schema';
import { lesson, lessons, runCmd } from './helpers';

/**
 * Mensageria e streaming · Fundamentos (F1 · Por que filas existem), simulated mode:
 * the default command runs without raising the break flag, the hint-3 cheat raises it,
 * the guess each lesson calls right is what the sim shows, and the mission starts
 * broken and can be fixed.
 */

const track = lessons.filter((l) => l.topic === 'mensageria-e-streaming' && l.track === 'fundamentos');
const steps = track.filter((l) => l.def.kind === 'step');
const dflt = (id: string, lang: (typeof LANGS)[number]) => defaultCommand(lesson(id).def.command, lang);

describe('mensageria-e-streaming / fundamentos', () => {
  it('ships 7 steps and the final mission, all declarative', () => {
    expect(steps.length).toBe(7);
    expect(track.filter((l) => l.def.kind === 'mission').length).toBe(1);
    for (const l of track) {
      expect(l.def.id.startsWith('msg-'), l.def.id).toBe(true);
      expect(l.def.model).toBe('declarative');
      expect(l.def.scene).toBe('widgets');
    }
  });

  it('no computed value shadows a result flag or a command option', () => {
    for (const l of track) {
      const sim = l.def.data.sim as { compute: Record<string, string>; cases: { flags?: string[] }[] };
      const flags = new Set(sim.cases.flatMap((c) => c.flags ?? []));
      const options = l.def.command.flags.map((f) => f.name);
      for (const name of Object.keys(sim.compute)) {
        expect(flags.has(name), `${l.def.id}: compute "${name}" is also a result flag`).toBe(false);
        expect(options.includes(name), `${l.def.id}: compute "${name}" overwrites a command option`).toBe(false);
      }
    }
  });
});

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = (p: string, e: string) => (pt ? p : e);

  describe(`[${lang}] Mensageria · Fundamentos`, () => {
    for (const l of steps) {
      it(`${l.def.id}: default runs calm, cheat breaks it`, () => {
        const def = runCmd(l.def.id, lang, dflt(l.def.id, lang));
        expect(def.error, 'default command must not error').toBeUndefined();
        expect(def.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        const cheat = l.locale[lang].hints!.cmd[2];
        expect(runCmd(l.def.id, lang, cheat).flags, cheat).toContain(l.def.break.flag);
      });
    }

    it('guesses match what the simulator shows', () => {
      // 1: with a queue, the rush waits in line and nothing is lost
      const s1 = runCmd('msg-sincrono-assincrono', lang, dflt('msg-sincrono-assincrono', lang));
      expect(s1.vars?.lost).toBe(0);
      expect(Number(s1.vars?.maxq)).toBeGreaterThan(0);
      expect(runCmd('msg-sincrono-assincrono', lang, q('atender --modo sincrono', 'serve --mode sync')).vars?.lost).toBe(24);
      // 2: events need zero cashier changes when loyalty joins
      const s2 = runCmd('msg-comando-evento', lang, q('anunciar --servicos cozinha,nota,fidelidade', 'announce --services kitchen,invoice,loyalty'));
      expect(s2.vars?.change).toBe(0);
      expect(s2.flags).not.toContain('coupled');
      // 3: manual ack → unacked tickets go back, one is made twice, none lost
      const s3 = runCmd('msg-ack-e-garantias', lang, dflt('msg-ack-e-garantias', lang));
      expect(s3.vars?.lost).toBe(0);
      expect(s3.vars?.back).toBe(7);
      expect(s3.vars?.dup).toBe(1);
      expect(runCmd('msg-ack-e-garantias', lang, q('cozinhar --ack auto', 'cook --ack auto')).vars?.lost).toBe(6);
      // 4: dedup by message id still lets the resend (new id) through: one extra
      expect(runCmd('msg-consumidor-idempotente', lang, q('consumir --chave mensagem', 'consume --key message')).vars?.extra).toBe(1);
      expect(runCmd('msg-consumidor-idempotente', lang, dflt('msg-consumidor-idempotente', lang)).vars?.extra).toBe(0);
      expect(runCmd('msg-consumidor-idempotente', lang, q('consumir --transacao nao', 'consume --transaction no')).vars?.extra).toBe(1);
      // 5: prefetch 10 is slower than prefetch 1 with a slow and a fast cook; single consumer keeps order
      const p1 = Number(runCmd('msg-ordem-dlq-prefetch', lang, q('distribuir --prefetch 1', 'dispatch --prefetch 1')).vars?.finish);
      const p10 = Number(runCmd('msg-ordem-dlq-prefetch', lang, q('distribuir --prefetch 10', 'dispatch --prefetch 10')).vars?.finish);
      expect(p10).toBeGreaterThan(p1);
      expect(runCmd('msg-ordem-dlq-prefetch', lang, q('distribuir --unico sim', 'dispatch --single yes')).vars?.ooo).toBe(0);
      // 6: on a shared queue each service gets about a third of the events
      const s6 = runCmd('msg-pub-sub', lang, q('publicar --filas compartilhada', 'publish --queues shared'));
      expect(s6.vars?.kitchen).toBe(3);
      expect(runCmd('msg-pub-sub', lang, q('publicar --log sim', 'publish --log yes')).vars?.analytics).toBe(9);
      // 7: a queue in front of a price lookup is the wrong tool; direct is right
      expect(runCmd('msg-quando-nao-usar-fila', lang, q('decidir --caso preco --modo fila', 'decide --case price --mode queue')).flags).toContain('wrongTool');
      expect(runCmd('msg-quando-nao-usar-fila', lang, q('decidir --caso preco --modo direto', 'decide --case price --mode direct')).flags).toContain('rightTool');
    });

    it('mission: starts broken, partial fixes fail, the full fix passes', () => {
      const id = 'msg-missao-black-friday';
      const flag = lesson(id).def.break.flag;
      expect(runCmd(id, lang, dflt(id, lang)).flags).not.toContain(flag);
      // confirms + manual ack without a business key: redeliveries and resends double-charge
      const partial = runCmd(id, lang, q(
        'configurar --ack manual --chave mensagem --dlq sim --prefetch 20 --confirmacao sim',
        'configure --ack manual --key message --dlq yes --prefetch 20 --confirms yes'));
      expect(partial.flags).not.toContain(flag);
      expect(partial.flags).toContain('doubleCharge');
      // unlimited prefetch fails even when everything else is right
      expect(runCmd(id, lang, q(
        'configurar --ack manual --chave pedido --dlq sim --prefetch 0 --confirmacao sim',
        'configure --ack manual --key order --dlq yes --prefetch 0 --confirms yes')).flags).not.toContain(flag);
      const fixed = runCmd(id, lang, q(
        'configurar --ack manual --chave pedido --dlq sim --prefetch 20 --confirmacao sim',
        'configure --ack manual --key order --dlq yes --prefetch 20 --confirms yes'));
      expect(fixed.error).toBeUndefined();
      expect(fixed.flags).toContain(flag);
      expect(fixed.vars?.lost).toBe(0);
      expect(fixed.vars?.dups).toBe(0);
    });
  });
}
