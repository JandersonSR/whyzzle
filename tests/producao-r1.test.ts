import { describe, expect, it } from 'vitest';
import { defaultCommand, parseCommand } from '../src/engine/command';
import { LANGS, type Lang } from '../src/engine/schema';
import { interpolate, makeRng } from '../src/engine/text';
import { ADAPTERS, type RealDeps } from '../src/runtime/adapters';
import { lesson, lessons, runCmd, topics } from './helpers';

/**
 * IA aplicada · Produção · R1 (avaliação e qualidade). For pt and en: the default command runs without error and
 * never raises the break flag, hint 3 raises it, the guess marked right is what the simulator shows, and every
 * tryNext command runs with every text it triggers fully filled. Real ops run with fake deps.
 */

const R1 = [
  'r-conjunto-de-avaliacao-versionado',
  'r-metricas-de-rag',
  'r-llm-como-juiz',
  'r-testes-de-regressao-no-ci',
  'r-testes-ab-de-prompt',
  'r-casos-dificeis-e-perguntas-sem-resposta',
  'r-ciclo-de-feedback-de-usuarios',
];

type Run = ReturnType<typeof runCmd> & { widgets?: Record<string, unknown>[] };
const vars = (r: { vars?: Record<string, unknown> }) => (r.vars ?? {}) as Record<string, string | number>;
const filled = (t: string) => !/\{\w+\}/.test(t) && !/undefined|NaN/.test(t);

/** The command inside a tryNext.cmd sentence: the longest prefix from the verb that parses, minus trailing prose. */
function tryNextCommand(id: string, lang: Lang): string {
  const l = lesson(id);
  const t = l.locale[lang].tryNext!.cmd;
  const rest = t.slice(t.indexOf(`${l.def.command.verb[lang]} `));
  const cuts = [...rest.matchAll(/ /g)].map((m) => m.index!).concat([rest.length]).reverse();
  for (const i of cuts) {
    let c = rest.slice(0, i).replace(/[.,]$/, '');
    if ((c.match(/"/g) ?? []).length % 2) continue;
    if (!parseCommand(c, l.def.command, lang).ok) continue;
    const q = c.lastIndexOf('"');
    if (q >= 0 && !c.slice(q).includes('--')) c = c.slice(0, q + 1);
    return c;
  }
  throw new Error(`no command in tryNext of ${id}`);
}

/** Every "@key" text the resolved widgets show, interpolated with the run's vars (what the scene renders). */
function sceneTexts(id: string, lang: Lang, r: Run): string[] {
  const scene = lesson(id).locale[lang].scene as Record<string, unknown>;
  const out: string[] = [];
  const walk = (v: unknown) => {
    if (typeof v === 'string' && v.startsWith('@')) {
      const s = scene[v.slice(1)];
      expect(typeof s, `${id}: scene.${v.slice(1)}`).toBe('string');
      out.push(interpolate(String(s), vars(r)));
    } else if (Array.isArray(v)) v.forEach(walk);
    else if (v && typeof v === 'object') Object.values(v).forEach(walk);
  };
  walk(r.widgets ?? []);
  return out;
}

/** The texts the app shows after a run: success when the break flag is up, calm otherwise, plus the scene texts. */
function shownTexts(id: string, lang: Lang, r: Run): string[] {
  const l = lesson(id);
  const b = l.locale[lang].break!;
  const main = r.flags.includes(l.def.break.flag) ? b.success : b.calm;
  return [interpolate(main, vars(r)), ...sceneTexts(id, lang, r)];
}

describe('R1 structure', () => {
  it('ships the seven lessons in order 1..7 on the producao track, the first requiring the Prática mission', () => {
    const got = lessons.filter((l) => R1.includes(l.def.id)).sort((a, b) => a.def.order - b.def.order);
    expect(got.map((l) => l.def.id)).toEqual(R1);
    expect(got.map((l) => l.def.order)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    for (const l of got) {
      expect(l.track).toBe('producao');
      expect(l.def.executors[0]).toBe('simulado');
    }
    expect(got[0].def.requires).toEqual(['p-missao-assistente-de-rh']);
    const tr = topics.find((t) => t.def.id === 'ia-aplicada')!.def.tracks.find((t) => t.id === 'producao')!;
    expect(tr.status).toBe('ready');
  });

  it('no computed value shadows a result flag or a command option', () => {
    for (const id of R1) {
      const l = lesson(id);
      const sim = l.def.data.sim as { compute: Record<string, string>; cases: { flags: string[] }[] };
      const flags = new Set(sim.cases.flatMap((c) => c.flags));
      const options = l.def.command.flags.map((f) => f.name);
      for (const name of Object.keys(sim.compute)) {
        expect(flags.has(name), `${id}: compute "${name}" is a flag`).toBe(false);
        expect(options.includes(name), `${id}: compute "${name}" is an option`).toBe(false);
      }
    }
  });

  it('recipes are real multi-line code, and table cells stay short', () => {
    for (const id of R1) {
      for (const lang of LANGS) {
        const loc = lesson(id).locale[lang];
        expect(loc.recipe.steps.some((s) => s.split('\n').length >= 3), `${id} recipe has a multi-line step`).toBe(true);
        const r = runCmd(id, lang, defaultCommand(lesson(id).def.command, lang)) as Run;
        for (const w of r.widgets ?? []) {
          if (w.type !== 'table') continue;
          for (const row of w.rows as unknown[][]) {
            for (const cell of row) {
              const t = typeof cell === 'string' && cell.startsWith('@') ? String((loc.scene as Record<string, unknown>)[cell.slice(1)]) : String(cell);
              expect(t.length, `${id} cell "${t}"`).toBeLessThanOrEqual(36);
            }
          }
        }
      }
    }
  });
});

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = (a: string, b: string) => (pt ? a : b);

  describe(`[${lang}] R1 journeys`, () => {
    for (const id of R1) {
      it(`${id}: default runs clean, cheat breaks it, texts are filled`, () => {
        const l = lesson(id);
        const def = runCmd(id, lang, defaultCommand(l.def.command, lang)) as Run;
        expect(def.error, 'default must not error').toBeUndefined();
        expect(def.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        for (const t of shownTexts(id, lang, def)) expect(filled(t), `${id} default: ${t}`).toBe(true);
        const cheat = l.locale[lang].hints!.cmd[2];
        expect(l.locale[lang].break!.mission.cmd).toContain(cheat);
        const r = runCmd(id, lang, cheat) as Run;
        expect(r.error).toBeUndefined();
        expect(r.flags, cheat).toContain(l.def.break.flag);
        for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} cheat: ${t}`).toBe(true);
      });

      it(`${id}: the tryNext command runs and every text it triggers is filled`, () => {
        const r = runCmd(id, lang, tryNextCommand(id, lang)) as Run;
        expect(r.error, `${id} tryNext errors`).toBeUndefined();
        for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} tryNext: ${t}`).toBe(true);
      });
    }

    it('every example argument runs in simulated mode with filled texts', () => {
      for (const id of R1) {
        const l = lesson(id);
        for (const ex of l.def.command.arg.examples) {
          const r = runCmd(id, lang, `${l.def.command.verb[lang]} "${ex[lang]}"`) as Run;
          expect(r.error, `${id} ${ex[lang]}`).toBeUndefined();
          for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} ${ex[lang]}: ${t}`).toBe(true);
        }
      }
    });

    it('01: v3 beats v2 on the same set; mixing set versions or leaking breaks the comparison', () => {
      const id = 'r-conjunto-de-avaliacao-versionado';
      expect(lesson(id).def.predict!.answer).toBe('v3');
      const fair = runCmd(id, lang, q('comparar "v3"', 'compare "v3"'));
      expect(fair.flags).toContain('better');
      expect(fair.vars).toMatchObject({ candPct: 85, basePct: 75 });
      const mixed = runCmd(id, lang, q('comparar "v3" --conjunto-base 2026-06', 'compare "v3" --base-set 2026-06'));
      expect(mixed.vars).toMatchObject({ candPct: 85, basePct: 92, shownS: '-7', cleanPct: 85, baseOnCandPct: 75 });
      const leak = runCmd(id, lang, q('comparar "v3" --vazar sim', 'compare "v3" --leak yes'));
      expect(leak.flags).toContain('leaked');
      expect(leak.flags).not.toContain('mismatch');
      expect(leak.vars).toMatchObject({ candPct: 98, holdCPct: 85 });
      expect((runCmd(id, lang, q('comparar "v9"', 'compare "v9"')).error as { code?: string } | undefined)?.code).toBe('unknownPrompt');
    });

    it('02: the made-up answer has high relevance; only faithfulness catches it, only relevance catches the dodge', () => {
      const id = 'r-metricas-de-rag';
      expect(lesson(id).def.predict!.answer).toBe('high');
      const [, invent, dodge] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const both = runCmd(id, lang, `${q('medir', 'measure')} "${invent}"`);
      expect(Number(both.vars?.relPct)).toBeGreaterThanOrEqual(85);
      expect(both.vars?.faithPct).toBe(33);
      expect(both.flags).toContain('caught');
      expect(runCmd(id, lang, `${q('medir', 'measure')} "${dodge}"`).flags).toContain('caught');
      expect(runCmd(id, lang, `${q('medir', 'measure')} "${dodge}" ${q('--metricas fidelidade', '--metrics faithfulness')}`).flags).toContain('fooled');
    });

    it('03: vague + examples agrees 88% but kappa 0.44 (not trusted); criteria + examples is trusted', () => {
      const id = 'r-llm-como-juiz';
      expect(lesson(id).def.predict!.answer).toBe('no');
      const v1 = runCmd(id, lang, q('julgar --rubrica vaga --exemplos sim', 'judge --rubric vague --examples yes'));
      expect(v1.vars).toMatchObject({ agreePct: 88, kappaS: q('0,44', '0.44') });
      expect(v1.flags).toContain('untrusted');
      expect(v1.flags).not.toContain('fooled');
      const best = runCmd(id, lang, q('julgar --exemplos sim', 'judge --examples yes'));
      expect(best.flags).toContain('trusted');
      expect(best.vars?.kappaS).toBe(q('0,76', '0.76'));
      // the recommended judge agrees with HR on every example answer
      for (const ex of lesson(id).def.command.arg.examples) {
        expect(runCmd(id, lang, `${q('julgar', 'judge')} "${ex[lang]}" ${q('--exemplos sim', '--examples yes')}`).flags, ex[lang]).toContain('agrees');
      }
    });

    it('04: the short prompt passes the average but critical cases block it; the cheaper model ships with a loose gate', () => {
      const id = 'r-testes-de-regressao-no-ci';
      expect(lesson(id).def.predict!.answer).toBe('block');
      const [shortPr, cheap, chunk] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const r = runCmd(id, lang, `ci "${shortPr}"`);
      expect(r.flags).toEqual(expect.arrayContaining(['red', 'blocked']));
      expect(r.vars).toMatchObject({ scorePct: 83, crit: 18 });
      const loose = runCmd(id, lang, `ci "${cheap}" ${q('--limite 0.75 --queda 10', '--threshold 0.75 --max-drop 10')}`) as Run;
      expect(loose.flags).toContain('shipped');
      for (const t of shownTexts(id, lang, loose)) expect(filled(t), t).toBe(true);
      expect(runCmd(id, lang, `ci "${chunk}"`).flags).toContain('green');
      expect(runCmd(id, lang, `ci "${chunk}" ${q('--limite 0.9', '--threshold 0.9')}`).flags).toContain('needless');
    });

    it('05: the 14-day test shows a 4-point lift; peeking stops on day 2 with 9; 5 days is inconclusive', () => {
      const id = 'r-testes-ab-de-prompt';
      expect(lesson(id).def.predict!.answer).toBe('shrinks');
      const full = runCmd(id, lang, q('ab --dias 14', 'ab --days 14'));
      expect(full.flags).toContain('significant');
      expect(full.vars).toMatchObject({ liftS: q('+4,0', '+4.0'), rateA: 62, rateB: 66, pS: q('0,002', '0.002') });
      const peek = runCmd(id, lang, q('ab --espiar sim', 'ab --peek yes'));
      expect(peek.vars).toMatchObject({ stopDay: 2, liftS: q('+9,0', '+9.0'), trueLiftS: q('+4,0', '+4.0') });
      const small = runCmd(id, lang, q('ab --dias 5', 'ab --days 5'));
      expect(small.flags).toEqual(expect.arrayContaining(['inconclusive', 'underpowered']));
      // peeking with a 1-day test can't stop early on a significant day, so it isn't the "peeked" case
      expect(runCmd(id, lang, q('ab --dias 1 --espiar sim', 'ab --days 1 --peek yes')).flags).not.toContain('peeked');
    });

    it('06: v3 gets few false-premise questions right; the old composition hides it', () => {
      const id = 'r-casos-dificeis-e-perguntas-sem-resposta';
      expect(lesson(id).def.predict!.answer).toBe('few');
      const all = runCmd(id, lang, q('testar', 'test')) as Run;
      expect(all.vars).toMatchObject({ setPct: 74, prodPct: 72, covered: 100, blindCount: 0 });
      const table = all.widgets!.find((w) => w.type === 'table')!;
      expect((table.rows as unknown[][])[3]).toEqual([q('premissa falsa', 'false premise'), 10, '30%', '11%']);
      const old = runCmd(id, lang, q('testar --categorias respondiveis,fora,delicadas', 'test --categories answerable,outside,sensitive'));
      expect(old.vars).toMatchObject({ setPct: 85, covered: 78, blindCount: 2 });
      const oneMissing = runCmd(id, lang, q('testar --categorias respondiveis,fora,delicadas,ambiguas,injecao', 'test --categories answerable,outside,sensitive,ambiguous,injection'));
      expect(oneMissing.flags).toContain('blindSpot');
      expect(String(oneMissing.vars?.blindNames)).toContain(q('premissa falsa', 'false-premise'));
      expect((runCmd(id, lang, q('testar --categorias nenhuma', 'test --categories none')).error as { code?: string } | undefined)?.code).toBe('emptySet');
    });

    it('07: optimizing for thumbs raises approval and lowers accuracy; no random review finds nothing silent', () => {
      const id = 'r-ciclo-de-feedback-de-usuarios';
      expect(lesson(id).def.predict!.answer).toBe('down');
      const good = runCmd(id, lang, q('ciclo', 'loop'));
      expect(good.vars).toMatchObject({ acc0: 74, accEnd: 78, found: 24, added: 36 });
      expect(good.flags).toContain('improving');
      const bad = runCmd(id, lang, q('ciclo --otimizar polegar', 'loop --optimize thumbs'));
      expect(bad.vars).toMatchObject({ thumbsEnd: 82, accEnd: 67 });
      const blind = runCmd(id, lang, q('ciclo --revisao 0', 'loop --review 0'));
      expect(blind.flags).toContain('blind');
      expect(blind.vars).toMatchObject({ found: 0, likedWrongS: '?' });
    });
  });
}

describe('real executors with fake deps', () => {
  function runReal(id: string, lang: Lang, input: string, deps: Partial<RealDeps>, executor: 'no-navegador' | 'sua-chave' = 'sua-chave') {
    const l = lesson(id);
    const p = parseCommand(input, l.def.command, lang);
    if (!p.ok) throw new Error(JSON.stringify(p.error));
    const cfg = l.def.real![executor]!;
    const full: RealDeps = { tokenizer: async () => ({ encode: () => [], decode: () => '' }), chat: async () => '', ...deps };
    return ADAPTERS[cfg.adapter].run(p.values, { lang, layer: 'dev', data: l.def.data, text: l.locale[lang].data, rng: makeRng(1) }, full, { executor, model: 'm' }, cfg);
  }

  it('lessons without a real model only offer the simulated executor', () => {
    for (const id of ['r-conjunto-de-avaliacao-versionado', 'r-testes-de-regressao-no-ci', 'r-testes-ab-de-prompt']) {
      expect(lesson(id).def.executors).toEqual(['simulado']);
      expect(lesson(id).def.real).toBeUndefined();
    }
  });

  for (const lang of LANGS) {
    it(`[${lang}] 02: real relevance comes from the embedder, for any text`, async () => {
      let seen: string[] = [];
      const embed = async (texts: string[]) => {
        seen = texts;
        return texts.map((_, i) => (i === 0 ? [1, 0] : [0.6, 0.8]));
      };
      const r = await runReal('r-metricas-de-rag', lang, `${lang === 'pt' ? 'medir' : 'measure'} "qualquer texto"`, { embed }, 'no-navegador');
      expect(r.error).toBeUndefined();
      expect(seen).toHaveLength(2);
      expect(seen[0].startsWith('query: ')).toBe(true);
      expect(seen[1]).toBe('query: qualquer texto');
      expect(r.vars?.relPct).toBe(60);
    });

    it(`[${lang}] 03: the real judge's verdict is compared with HR's label; broken JSON is flagged`, async () => {
      const id = 'r-llm-como-juiz';
      let system = '';
      const pass = await runReal(id, lang, lang === 'pt' ? 'julgar' : 'judge', {
        chat: async (m) => {
          system = m[0].content;
          return 'Aqui: {"verdict":"pass","reason":"ok"}';
        },
      });
      expect(system).toMatch(/1\)/);
      expect(pass.flags).toContain('disagrees'); // the default answer is the long wrong one: HR failed it
      const fail = await runReal(id, lang, lang === 'pt' ? 'julgar' : 'judge', { chat: async () => '{"verdict":"fail","reason":"inventou metade"}' });
      expect(fail.flags).toContain('agrees');
      const broken = await runReal(id, lang, lang === 'pt' ? 'julgar' : 'judge', { chat: async () => 'acho que passa' });
      expect(broken.flags).toContain('judgeBroken');
      expect(broken.flags).not.toContain('agrees');
      for (const t of shownTexts(id, lang, broken as Run)) expect(filled(t), t).toBe(true);
    });

    it(`[${lang}] 06: the real model's action is checked against the expected one`, async () => {
      const id = 'r-casos-dificeis-e-perguntas-sem-resposta';
      let system = '';
      const r = await runReal(id, lang, lang === 'pt' ? 'testar' : 'test', {
        chat: async (m) => {
          system = m[0].content;
          return '{"action":"refuse","text":"Esse auxílio não existe no manual."}';
        },
      }, 'no-navegador');
      expect(system).toContain('[12]');
      expect(r.flags).toContain('handled');
      const wrong = await runReal(id, lang, lang === 'pt' ? 'testar' : 'test', { chat: async () => '{"action":"answer","text":"Peça no portal."}' });
      expect(wrong.flags).toContain('mishandled');
    });

    it(`[${lang}] 07: the real triage reads category and add_to_eval`, async () => {
      const id = 'r-ciclo-de-feedback-de-usuarios';
      const r = await runReal(id, lang, lang === 'pt' ? 'ciclo' : 'loop', { chat: async () => '{"category":"wrong_answer","add_to_eval":true}' });
      expect(r.flags).toContain('triagedRight');
      const w = (r as unknown as Run).widgets!.filter((x) => x.type === 'flow')[1] as { steps: { sub: string }[] };
      expect(w.steps[2].sub).toBe('@subYes');
      const bad = await runReal(id, lang, lang === 'pt' ? 'ciclo' : 'loop', { chat: async () => '{"category":"bug"}' });
      expect(bad.flags).toEqual(expect.arrayContaining(['invalidJson', 'triagedWrong']));
    });
  }
});
