import { describe, expect, it } from 'vitest';
import { defaultCommand, defaultValues, type Values } from '../src/engine/command';
import { LANGS } from '../src/engine/schema';
import { interpolate } from '../src/engine/text';
import { lesson, lessons, runCmd, runValues } from './helpers';

/**
 * System design · Fundamentos (F1 · Como sistemas grandes funcionam), simulated mode:
 * the default command runs without raising the break flag, the hint-3 cheat raises it,
 * the guess each lesson calls right is what the sim shows, every tryNext command runs and
 * its texts have no unfilled {placeholders}, every option combination only shows scene
 * texts that exist, and the mission starts broken, each single missing fix keeps it
 * failing and the full fix passes.
 */

type Lang = (typeof LANGS)[number];
const track = lessons.filter((l) => l.topic === 'system-design' && l.track === 'fundamentos');
const steps = track.filter((l) => l.def.kind === 'step');
const dflt = (id: string, lang: Lang) => runCmd(id, lang, defaultCommand(lesson(id).def.command, lang));

/** Every combination of the lesson's options (ints at min, default and max). */
function combos(id: string, lang: Lang): Values[] {
  const def = lesson(id).def.command;
  let out: Values[] = [defaultValues(def, lang)];
  for (const f of def.flags) {
    const vals: Values[string][] =
      f.type === 'enum' ? f.options!.map((o) => o.id) : f.type === 'bool' ? [true, false] : f.type === 'int' ? [f.min!, f.default as number, f.max!] : [];
    if (!vals.length) continue;
    out = out.flatMap((v) => vals.map((x) => ({ ...v, [f.name]: x })));
  }
  return out;
}

/** "@key" strings left in resolved widgets (they must exist in the lesson's scene texts). */
function sceneKeys(v: unknown, out = new Set<string>()): Set<string> {
  if (typeof v === 'string' && /^@[\w.]+$/.test(v)) out.add(v.slice(1));
  else if (Array.isArray(v)) v.forEach((x) => sceneKeys(x, out));
  else if (v && typeof v === 'object') Object.values(v).forEach((x) => sceneKeys(x, out));
  return out;
}

/** Every scene text a run shows, filled with the run's values, has no "{name}" left. */
function expectFilled(id: string, lang: Lang, r: { vars?: Record<string, unknown>; widgets?: unknown }) {
  const l = lesson(id);
  const vars = (r.vars ?? {}) as Record<string, string | number>;
  const loc = l.locale[lang];
  const texts = [...sceneKeys(r.widgets)].map((k) => String(loc.scene[k]));
  if (loc.break) texts.push(loc.break.success, loc.break.calm);
  if (loc.success) texts.push(loc.success);
  for (const t of texts) expect(interpolate(t, vars), `${id}: ${t}`).not.toMatch(/\{\w+\}/);
}

describe('system-design / fundamentos', () => {
  it('ships 6 steps and the final mission, in order, all declarative and simulated', () => {
    expect(track.map((l) => l.def.order)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    expect(steps.length).toBe(6);
    expect(track[6].def.kind).toBe('mission');
    for (const l of track) {
      expect(l.def.id.startsWith('sd-'), l.def.id).toBe(true);
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

  for (const lang of LANGS) {
    it(`[${lang}] every option combination runs and only uses scene texts that exist`, () => {
      for (const l of track) {
        const scene = l.locale[lang].scene;
        for (const v of combos(l.def.id, lang)) {
          const r = runValues(l.def.id, lang, v) as unknown as { error?: unknown; widgets: unknown[]; vars: Record<string, unknown> };
          expect(r.error, `${l.def.id} ${JSON.stringify(v)}`).toBeUndefined();
          expect(JSON.stringify(r.widgets)).not.toMatch(/"=(?!>)/);
          expect(JSON.stringify(r.widgets)).not.toMatch(/NaN|Infinity|null/);
          for (const k of sceneKeys(r.widgets)) expect(typeof scene[k], `${l.def.id}: scene.${k}`).toBe('string');
          expectFilled(l.def.id, lang, r);
        }
      }
    });
  }
});

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = (p: string, e: string) => (pt ? p : e);
  const tryNext = (id: string, cmd: string) => {
    const r = runCmd(id, lang, cmd);
    expect(r.error, cmd).toBeUndefined();
    expectFilled(id, lang, r as never);
    return r;
  };

  describe(`[${lang}] System design · Fundamentos`, () => {
    for (const l of steps) {
      it(`${l.def.id}: default runs calm, cheat breaks it`, () => {
        const d = runCmd(l.def.id, lang, defaultCommand(l.def.command, lang));
        expect(d.error, 'default command must not error').toBeUndefined();
        expect(d.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        const cheat = l.locale[lang].hints!.cmd[2];
        const c = runCmd(l.def.id, lang, cheat);
        expect(c.error).toBeUndefined();
        expect(c.flags, cheat).toContain(l.def.break.flag);
        expectFilled(l.def.id, lang, c as never);
      });
    }

    it('1 · three round trips of 170 ms = 510 ms; in-memory sessions die on restart', () => {
      const id = 'sd-cliente-servidor';
      expect(lesson(id).def.predict!.answer).toBe('threeTrips');
      const d = dflt(id, lang);
      expect(d.vars?.pageMs).toBe(510);
      expect(d.vars?.lost).toBe(0);
      expect(runCmd(id, lang, q('pedir --sessao memoria', 'request --session memory')).vars?.lost).toBe(120);
      expect(runCmd(id, lang, q('pedir --sessao memoria --reinicio nao', 'request --session memory --restart no')).flags).not.toContain('sessionsLost');
      // tryNext
      expect(tryNext(id, q('pedir /cardapio --distancia perto', 'request /menu --distance near')).vars?.pageMs).toBe(120);
      const ten = tryNext(id, q('pedir /cardapio --idas 10', 'request /menu --trips 10'));
      expect(ten.vars?.pageMs).toBe(1700);
      expect(ten.flags).toContain('slowPage');
      expect(ten.flags).not.toContain('sessionsLost');
    });

    it('2 · four m machines survive a failure; one xl machine is a single point of failure; the database caps scaling out', () => {
      const id = 'sd-escalar-vertical-horizontal';
      expect(lesson(id).def.predict!.answer).toBe('four');
      const d = dflt(id, lang);
      expect(d.vars?.cost).toBe(800);
      expect(d.vars?.capAfter).toBe(2400);
      expect(d.vars?.errPct).toBe(0);
      const giant = runCmd(id, lang, q('escalar --maquinas 1 --tamanho gg', 'scale --machines 1 --size xl'));
      expect(giant.vars?.cost).toBe(800);
      expect(giant.vars?.errPct).toBe(100);
      // outage fires for a single machine of any size (the break text says "a single machine")
      expect(runCmd(id, lang, q('escalar --maquinas 1 --tamanho p', 'scale --machines 1 --size s')).flags).toContain('outage');
      // tryNext: the database becomes the bottleneck, not an outage
      const big = tryNext(id, q('escalar --maquinas 10 --tamanho gg --pico 8000', 'scale --machines 10 --size xl --peak 8000'));
      expect(big.flags).toContain('dbBound');
      expect(big.flags).not.toContain('outage');
      expect(big.vars?.served).toBe(3000);
    });

    it('3 · the HTTP check pulls the dead server in 10 s (1,000 errors); no check, a TCP check on 500s, ip-hash at a school', () => {
      const id = 'sd-balanceador';
      expect(lesson(id).def.predict!.answer).toBe('few');
      const d = dflt(id, lang);
      expect(d.vars?.failed).toBe(1000);
      expect(d.vars?.errPct).toBeCloseTo(0.56, 2);
      expect(d.flags).toContain('detected');
      expect(runCmd(id, lang, q('balancear --checagem nenhuma', 'balance --check none')).vars?.errPct).toBeCloseTo(33.33, 1);
      // tryNext: a TCP check can't see 500s (same break, other cause); ip-hash sends the whole school to app-1
      const tcp = tryNext(id, q('balancear --problema erro500 --checagem tcp', 'balance --problem error500 --check tcp'));
      expect(tcp.flags).toContain('blackhole');
      const hash = tryNext(id, q('balancear --algoritmo ip-hash', 'balance --algorithm ip-hash'));
      expect(hash.flags).toContain('hotspot');
      expect(hash.flags).not.toContain('blackhole');
      // least-connections pulls more traffic to a fast-failing server
      expect(runCmd(id, lang, q('balancear --algoritmo menos-conexoes --checagem nenhuma', 'balance --algorithm least-conn --check none')).vars?.share2).toBe(50);
      expect(runCmd(id, lang, q('balancear --problema erro500 --checagem http', 'balance --problem error500 --check http')).flags).not.toContain('blackhole');
    });

    it('4 · a 30 s cache sends less than 1% to the database; no cache melts it; no lock stampedes', () => {
      const id = 'sd-cache';
      expect(lesson(id).def.predict!.answer).toBe('lessThanOne');
      const d = dflt(id, lang);
      expect(Number(d.vars?.missPct)).toBeLessThan(1);
      expect(d.vars?.staleS).toBe(0);
      expect(runCmd(id, lang, q('cachear --ttl 3600 --invalidar nao', 'cache --ttl 3600 --invalidate no')).vars?.staleMin).toBe(60);
      const melt = tryNext(id, q('cachear --ttl 0', 'cache --ttl 0'));
      expect(melt.flags).toContain('dbMelt');
      expect(melt.flags).not.toContain('stale');
      expect(melt.vars?.errPct).toBe(75);
      const herd = tryNext(id, q('cachear --trava nao', 'cache --lock no'));
      expect(herd.flags).toContain('stampede');
      expect(herd.flags).not.toContain('stale');
      expect(herd.vars?.worstMs).toBe(810);
      expect(runCmd(id, lang, q('cachear --invalidar nao', 'cache --invalidate no')).flags).toContain('staleShort');
    });

    it('5 · two replicas are the minimum; reading your write from a lagging replica shows old data', () => {
      const id = 'sd-banco-replica';
      expect(lesson(id).def.predict!.answer).toBe('two');
      const d = dflt(id, lang);
      expect(d.flags).not.toContain('overload');
      expect(d.vars?.perReplica).toBe(700);
      expect(d.vars?.p95Read).toBe(50);
      const one = tryNext(id, q('replicar --replicas 1', 'replicate --replicas 1'));
      expect(one.flags).toContain('overload');
      expect(one.flags).not.toContain('staleRead');
      expect(runCmd(id, lang, q('replicar --replicas 0', 'replicate --replicas 0')).flags).toContain('overload');
      const fast = tryNext(id, q('replicar --ler-apos-escrita replica --atraso 100', 'replicate --read-after-write replica --lag 100'));
      expect(fast.flags).toContain('fragile');
      expect(fast.flags).not.toContain('staleRead');
    });

    it('6 · with a queue the counter answers in 20 ms and the queue grows; sync jams; more cooks or a limit help', () => {
      const id = 'sd-fila';
      expect(lesson(id).def.predict!.answer).toBe('ticket');
      const d = dflt(id, lang);
      expect(d.vars?.counterMs).toBe(20);
      expect(d.vars?.errPct).toBe(0);
      expect(d.vars?.backlog).toBe(1800);
      expect(d.vars?.waitMin).toBe(5);
      expect(runCmd(id, lang, q('atender --modo sincrono', 'serve --mode sync')).vars?.errPct).toBeCloseTo(33.3, 1);
      const five = tryNext(id, q('atender --cozinheiros 5', 'serve --cooks 5'));
      expect(five.vars?.backlog).toBe(0);
      expect(five.flags).not.toContain('counterJam');
      const lim = tryNext(id, q('atender --limite-fila 300', 'serve --queue-limit 300'));
      expect(lim.flags).toContain('shedLoad');
      expect(lim.vars?.rejected).toBe(1500);
      expect(lim.flags).not.toContain('counterJam');
      expect(runCmd(id, lang, q('atender --idempotente nao', 'serve --idempotent no')).vars?.dups).toBe(4);
      // sync with enough cooks works, just slowly
      expect(runCmd(id, lang, q('atender --modo sincrono --cozinheiros 5', 'serve --mode sync --cooks 5')).flags).not.toContain('counterJam');
    });

    it('mission: starts broken, each single missing fix keeps it failing, the full fix passes', () => {
      const id = 'sd-missao-encurtador';
      const flag = lesson(id).def.break.flag;
      const d = dflt(id, lang);
      expect(d.flags).not.toContain(flag);
      // only the budget is green: the cheapest design is the most broken
      expect(d.vars?.ok).toBe(1);
      const fix = {
        servers: q('--servidores 6', '--servers 6'),
        cache: '--cache ' + q('sim', 'yes'),
        replica: '--replica ' + q('sim', 'yes'),
        ids: '--ids ' + q('aleatorio', 'random'),
        limit: q('--limite 1200', '--limit 1200'),
        clicks: q('--cliques fila', '--clicks queue'),
      };
      const verb = q('desenhar', 'design');
      const full = `${verb} ${Object.values(fix).join(' ')}`;
      const ok = runCmd(id, lang, full);
      expect(ok.error).toBeUndefined();
      expect(ok.flags, full).toContain(flag);
      expect(Number(ok.vars?.p95)).toBeLessThanOrEqual(300);
      expect(Number(ok.vars?.cost)).toBeLessThanOrEqual(3500);
      expectFilled(id, lang, ok as never);
      for (const k of Object.keys(fix) as (keyof typeof fix)[]) {
        const partial = `${verb} ${Object.entries(fix).filter(([j]) => j !== k).map(([, v]) => v).join(' ')}`;
        const r = runCmd(id, lang, partial);
        expect(r.error).toBeUndefined();
        expect(r.flags, `without ${k}: ${partial}`).not.toContain(flag);
      }
      // 7 servers also pass; 5 miss the p95; 8 blow the budget; a limit that blocks the school fails
      expect(runCmd(id, lang, full.replace(/ 6\b/, ' 7')).flags).toContain(flag);
      expect(runCmd(id, lang, full.replace(/ 6\b/, ' 5')).flags).not.toContain(flag);
      expect(runCmd(id, lang, full.replace(/ 6\b/, ' 8')).flags).not.toContain(flag);
      expect(runCmd(id, lang, full.replace('1200', '300')).flags).not.toContain(flag);
    });
  });
}
