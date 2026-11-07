import { describe, expect, it } from 'vitest';
import { defaultCommand } from '../src/engine/command';
import { LANGS, type Lang } from '../src/engine/schema';
import { interpolate } from '../src/engine/text';
import { lesson, lessons, runCmd } from './helpers';

/**
 * C# e ASP.NET Core · Fundamentos (F1 · C# do zero), simulated mode:
 * the default command runs without raising the break flag, the hint-3 cheat raises it,
 * the guess each lesson calls right is what the sim shows, every tryNext command runs
 * (and any success text it triggers is fully filled), and the mission starts broken,
 * fails with any single fix missing and passes when everything is fixed.
 */

const track = lessons.filter((l) => l.topic === 'csharp-e-aspnet' && l.track === 'fundamentos');
const steps = track.filter((l) => l.def.kind === 'step');
const dflt = (id: string, lang: Lang) => runCmd(id, lang, defaultCommand(lesson(id).def.command, lang));
const unfilled = (s: string) => s.match(/\{\w+\}/g) ?? [];

/** The command each lesson's tryNext.cmd tells the learner to run. */
const TRY_NEXT: Record<string, Record<Lang, string>> = {
  'cs-tipos-e-variaveis': { pt: 'somar --tipo double --qtd 10', en: 'add --type double --qty 10' },
  'cs-controle-de-fluxo': { pt: 'conferir --descarte nao', en: 'check --discard no' },
  'cs-colecoes-e-linq': { pt: 'consultar --pipoca sim', en: 'query --popcorn yes' },
  'cs-classes-e-records': { pt: 'copiar --tipo classe', en: 'copy --kind class' },
  'cs-nulabilidade': { pt: 'cumprimentar --acesso ponto --tem-apelido sim', en: 'greet --access dot --has-nickname yes' },
  'cs-excecoes': { pt: 'pedir "99999999999" --estrategia sem-catch', en: 'order "99999999999" --strategy no-catch' },
  'cs-async-await': { pt: 'preparar --modo um-por-vez', en: 'prepare --mode one-by-one' },
};

describe('csharp-e-aspnet / fundamentos', () => {
  it('ships 7 steps and the final mission, in order, all declarative', () => {
    expect(track.map((l) => l.def.order).sort((a, b) => a - b)).toEqual([1, 2, 3, 4, 5, 6, 7, 8]);
    expect(steps.length).toBe(7);
    expect(lesson('cs-missao-emprestimo').def.kind).toBe('mission');
    for (const l of track) {
      expect(l.def.id.startsWith('cs-'), l.def.id).toBe(true);
      expect(l.def.model).toBe('declarative');
      expect(l.def.scene).toBe('widgets');
      expect(l.def.executors).toEqual(['simulado']);
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

  describe(`[${lang}] C# · Fundamentos`, () => {
    for (const l of steps) {
      it(`${l.def.id}: default runs calm, cheat breaks it, tryNext runs`, () => {
        const loc = l.locale[lang];
        const d = dflt(l.def.id, lang);
        expect(d.error, 'default command must not error').toBeUndefined();
        expect(d.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        expect(unfilled(interpolate(loc.break!.calm, d.vars)), 'calm text filled').toEqual([]);
        const cheat = loc.hints!.cmd[2];
        const c = runCmd(l.def.id, lang, cheat);
        expect(c.error).toBeUndefined();
        expect(c.flags, cheat).toContain(l.def.break.flag);
        expect(unfilled(interpolate(loc.break!.success, c.vars)), 'success text filled').toEqual([]);
        const next = TRY_NEXT[l.def.id][lang];
        expect(loc.tryNext!.cmd, 'tryNext text names the command').toContain(next);
        const t = runCmd(l.def.id, lang, next);
        expect(t.error, next).toBeUndefined();
        if (t.flags.includes(l.def.break.flag)) expect(unfilled(interpolate(loc.break!.success, t.vars)), next).toEqual([]);
      });
    }

    it('1 · double drifts on 3 candies; decimal and int-in-cents are exact', () => {
      const r = runCmd('cs-tipos-e-variaveis', lang, q('somar --tipo double', 'add --type double'));
      expect(r.vars?.printed).toBe(q('0,30000000000000004', '0.30000000000000004'));
      expect(dflt('cs-tipos-e-variaveis', lang).vars?.printed).toBe(q('0,30', '0.30'));
      const i = runCmd('cs-tipos-e-variaveis', lang, q('somar --tipo int', 'add --type int'));
      expect(i.vars?.cents).toBe(30);
      expect(i.vars?.intDiv).toBe(0);
      expect(runCmd('cs-tipos-e-variaveis', lang, q('somar --tipo double --qtd 1', 'add --type double --qty 1')).flags).not.toContain('moneyDrift');
    });

    it('2 · for with <= serves everyone and then crashes', () => {
      const r = runCmd('cs-controle-de-fluxo', lang, q('conferir --laco for-menor-igual', 'check --loop for-le'));
      expect(r.vars?.shown).toBe(5);
      expect(r.vars?.loops).toBe(6);
      expect(r.flags).toContain('outOfRange');
      expect(runCmd('cs-controle-de-fluxo', lang, q('conferir --descarte nao', 'check --discard no')).flags).toContain('switchCrash');
    });

    it('3 · deferred LINQ interleaves where, select and mostra; Count() runs it twice', () => {
      const r = dflt('cs-colecoes-e-linq', lang) as unknown as { widgets: { type: string; lines?: string[] }[] };
      const out = r.widgets.filter((w) => w.type === 'terminal')[1].lines!;
      expect(out.slice(1, 5)).toEqual(['  where  Coxinha', '  where  Suco', '  select Suco', 'mostra Suco']);
      const twice = runCmd('cs-colecoes-e-linq', lang, q('consultar --contar sim', 'query --count yes'));
      expect(twice.vars?.runs).toBe(2);
      expect(twice.vars?.whereN).toBe(8);
      expect(runCmd('cs-colecoes-e-linq', lang, q('consultar --contar sim --modo tolist', 'query --count yes --mode tolist')).vars?.runs).toBe(1);
    });

    it('4 · records compare by value; class + assign aliases', () => {
      expect(dflt('cs-classes-e-records', lang).vars?.equal).toBe('True');
      const a = runCmd('cs-classes-e-records', lang, q('copiar --tipo classe --copia igual', 'copy --kind class --copy assign'));
      expect(a.vars?.aText).toBe('Bolo');
      expect(a.vars?.equal).toBe('False');
    });

    it('5 · the dot on string? compiles with CS8602; ! silences it and still crashes', () => {
      const w = runCmd('cs-nulabilidade', lang, q('cumprimentar --acesso ponto', 'greet --access dot'));
      expect(w.flags).toContain('compilerWarned');
      expect(w.error).toBeUndefined();
      const b = runCmd('cs-nulabilidade', lang, q('cumprimentar --acesso exclamacao', 'greet --access bang'));
      expect(b.flags).toContain('nullCrash');
      expect(b.flags).not.toContain('compilerWarned');
    });

    it('6 · an empty catch turns "abc" into a silent R$ 0.00; TryParse explains', () => {
      const s = runCmd('cs-excecoes', lang, q('pedir "abc" --estrategia engolir', 'order "abc" --strategy swallow'));
      expect(s.vars?.total).toBe(q('0,00', '0.00'));
      expect(s.vars?.exc).toBe('FormatException');
      expect(runCmd('cs-excecoes', lang, q('pedir "abc"', 'order "abc"')).flags).toContain('handled');
      expect(runCmd('cs-excecoes', lang, q('pedir "99999999999" --estrategia sem-catch', 'order "99999999999" --strategy no-catch')).vars?.exc).toBe('OverflowException');
      expect(dflt('cs-excecoes', lang).vars?.total).toBe(q('13,50', '13.50'));
    });

    it('7 · WhenAll takes the slowest (3 s); one by one adds up (6 s)', () => {
      expect(dflt('cs-async-await', lang).vars?.total).toBe(q('3,0 s', '3.0 s'));
      expect(runCmd('cs-async-await', lang, q('preparar --modo um-por-vez', 'prepare --mode one-by-one')).vars?.total).toBe(q('6,0 s', '6.0 s'));
    });

    it('8 · mission: starts broken, each single missing fix fails, the full fix passes', () => {
      const id = 'cs-missao-emprestimo';
      const flag = lesson(id).def.break.flag;
      const start = dflt(id, lang);
      expect(start.error).toBeUndefined();
      expect(start.flags).not.toContain(flag);
      expect(start.vars?.done).toBe(0);
      const fix: Record<string, string> = pt
        ? { dinheiro: 'decimal', taxa: 'decimal', 'taxa-zero': 'sim', centavos: 'sim', validar: 'sim', erros: 'lancar', testes: 'basico,taxa-zero,centavos,invalido' }
        : { money: 'decimal', rate: 'decimal', 'zero-rate': 'yes', cents: 'yes', validate: 'yes', errors: 'throw', tests: 'basic,zero-rate,cents,invalid' };
      const bad: Record<string, string> = pt
        ? { dinheiro: 'double', taxa: 'inteira', 'taxa-zero': 'nao', centavos: 'nao', validar: 'nao', erros: 'engolir', testes: 'basico,taxa-zero,centavos' }
        : { money: 'double', rate: 'int', 'zero-rate': 'no', cents: 'no', validate: 'no', errors: 'swallow', tests: 'basic,zero-rate,cents' };
      const verb = q('calcular', 'calculate');
      const build = (v: Record<string, string>) => `${verb} ${Object.entries(v).map(([k, x]) => `--${k} ${x}`).join(' ')}`;
      const good = runCmd(id, lang, build(fix));
      expect(good.error).toBeUndefined();
      expect(good.flags).toContain(flag);
      expect(good.vars?.done).toBe(6);
      expect(unfilled(interpolate(lesson(id).locale[lang].success!, good.vars))).toEqual([]);
      for (const k of Object.keys(fix)) {
        const r = runCmd(id, lang, build({ ...fix, [k]: bad[k] }));
        expect(r.error, k).toBeUndefined();
        expect(r.flags, `missing fix: ${k}`).not.toContain(flag);
      }
    });
  });
}
