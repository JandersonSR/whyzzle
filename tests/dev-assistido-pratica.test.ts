import { describe, expect, it } from 'vitest';
import { defaultCommand, parseCommand } from '../src/engine/command';
import { LANGS, type Lang } from '../src/engine/schema';
import { interpolate, makeRng } from '../src/engine/text';
import { ADAPTERS, type RealDeps } from '../src/runtime/adapters';
import { lesson, lessons, runCmd, topics } from './helpers';

/**
 * Dev assistido por IA · Prática · P1 (fluxo com agentes de código). For pt and en: the default command runs without
 * error and never raises the break flag, hint 3 raises it, the guess marked right is what the simulator shows, every
 * tryNext command runs with every text it triggers filled, recipes are multi-line and table cells stay short.
 * Lesson 1's real executor runs with fake deps.
 */

const P1 = [
  'dai-p-especificacao-antes-do-codigo',
  'dai-p-arquivos-de-regras',
  'dai-p-tarefas-pequenas',
  'dai-p-testes-como-contrato',
  'dai-p-refatoracao-assistida',
  'dai-p-legado-e-codigo-desconhecido',
  'dai-p-agentes-em-paralelo',
];

type Run = ReturnType<typeof runCmd> & { widgets?: Record<string, unknown>[] };
const vars = (r: { vars?: Record<string, unknown> }) => (r.vars ?? {}) as Record<string, string | number>;
const filled = (t: string) => !/\{\w+\}/.test(t) && !/undefined|NaN|\[object/.test(t);

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

const expectFilled = (id: string, lang: Lang, r: Run, what: string) => {
  for (const t of shownTexts(id, lang, r)) expect(filled(t), `${id} ${what}: ${t}`).toBe(true);
};

describe('P1 structure', () => {
  it('ships seven steps in order 1..7 on the pratica track, the first requiring the Fundamentos mission', () => {
    const got = lessons.filter((l) => P1.includes(l.def.id)).sort((a, b) => a.def.order - b.def.order);
    expect(got.map((l) => l.def.id)).toEqual(P1);
    expect(got.map((l) => l.def.order)).toEqual([1, 2, 3, 4, 5, 6, 7]);
    for (const l of got) {
      expect(l.topic).toBe('dev-assistido-por-ia');
      expect(l.track).toBe('pratica');
      expect(l.def.kind).toBe('step');
      expect(l.def.executors[0]).toBe('simulado');
    }
    expect(got[0].def.requires).toEqual(['dai-missao-bug-com-teste']);
    for (let i = 1; i < got.length; i++) expect(got[i].def.requires).toEqual([P1[i - 1]]);
    const tr = topics.find((t) => t.def.id === 'dev-assistido-por-ia')!.def.tracks.find((t) => t.id === 'pratica')!;
    expect(tr.status).toBe('ready');
  });

  it('no computed value shadows a result flag or a command option', () => {
    for (const id of P1) {
      const l = lesson(id);
      const sim = l.def.data.sim as { compute: Record<string, string>; cases: { flags?: string[] }[] };
      const flags = new Set(sim.cases.flatMap((c) => c.flags ?? []));
      const options = l.def.command.flags.map((f) => f.name);
      for (const name of Object.keys(sim.compute)) {
        expect(flags.has(name), `${id}: compute "${name}" is a flag`).toBe(false);
        expect(options.includes(name), `${id}: compute "${name}" is an option`).toBe(false);
      }
    }
  });

  it('recipes are real multi-line code, and table cells stay short in every run we know', () => {
    for (const id of P1) {
      for (const lang of LANGS) {
        const l = lesson(id);
        const loc = l.locale[lang];
        expect(loc.recipe.steps.some((s) => s.split('\n').length >= 3), `${id} recipe has a multi-line step`).toBe(true);
        expect(loc.recipe.ok.length).toBeGreaterThan(20);
        const cmds = [defaultCommand(l.def.command, lang), loc.hints!.cmd[2], tryNextCommand(id, lang)];
        for (const c of cmds) {
          const r = runCmd(id, lang, c) as Run;
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
    }
  });

  it('uses the current Claude Code file and flag names, not stale ones', () => {
    for (const id of P1) {
      for (const lang of LANGS) {
        const all = JSON.stringify(lesson(id).locale[lang]);
        expect(all).not.toMatch(/\.cursorrules|claude-3|claude-2|--dangerously/);
      }
    }
    // Claude Code reads CLAUDE.md, not AGENTS.md: the rules lesson must say it imports it
    expect(JSON.stringify(lesson('dai-p-arquivos-de-regras').locale.pt.recipe)).toContain('@AGENTS.md');
  });
});

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = (a: string, b: string) => (pt ? a : b);

  describe(`[${lang}] P1 journeys`, () => {
    for (const id of P1) {
      it(`${id}: default runs clean, cheat breaks it, texts are filled`, () => {
        const l = lesson(id);
        const def = runCmd(id, lang, defaultCommand(l.def.command, lang)) as Run;
        expect(def.error, 'default must not error').toBeUndefined();
        expect(def.flags, 'default must not raise the break flag').not.toContain(l.def.break.flag);
        expectFilled(id, lang, def, 'default');
        const cheat = l.locale[lang].hints!.cmd[2];
        expect(l.locale[lang].break!.mission.cmd).toContain(cheat);
        const r = runCmd(id, lang, cheat) as Run;
        expect(r.error).toBeUndefined();
        expect(r.flags, cheat).toContain(l.def.break.flag);
        expectFilled(id, lang, r, 'cheat');
      });

      it(`${id}: the tryNext command runs and every text it triggers is filled`, () => {
        const r = runCmd(id, lang, tryNextCommand(id, lang)) as Run;
        expect(r.error, `${id} tryNext errors`).toBeUndefined();
        expectFilled(id, lang, r, 'tryNext');
      });
    }

    it('every example argument runs in simulated mode with filled texts', () => {
      for (const id of P1) {
        const l = lesson(id);
        for (const ex of l.def.command.arg.examples) {
          const r = runCmd(id, lang, `${l.def.command.verb[lang]} "${ex[lang]}"`) as Run;
          expect(r.error, `${id} ${ex[lang]}`).toBeUndefined();
          expectFilled(id, lang, r, ex[lang]);
        }
      }
    });

    it('01: the full spec gives the smaller diff; only the vague request without a plan breaks; free text is classified', () => {
      const id = 'dai-p-especificacao-antes-do-codigo';
      expect(lesson(id).def.predict!.answer).toBe('smaller');
      const [full, partial, vague] = lesson(id).def.command.arg.examples.map((e) => e[lang]);
      const v = q('especificar', 'specify');
      const d = runCmd(id, lang, `${v} "${full}"`);
      expect(d.vars).toMatchObject({ lines: 180, files: 5, extras: 0, rounds: 1 });
      expect(d.flags).toContain('lean');
      const bad = runCmd(id, lang, `${v} "${vague}" ${q('--plano nao', '--plan no')}`);
      expect(bad.vars).toMatchObject({ lines: 640, extras: 3, rounds: 4, reworkS: q('6,0', '6.0') });
      expect(bad.flags).toEqual(expect.arrayContaining(['rework', 'creep']));
      const saved = runCmd(id, lang, `${v} "${vague}" ${q('--plano sim', '--plan yes')}`);
      expect(saved.flags).not.toContain('rework');
      expect(saved.vars).toMatchObject({ lines: 260, rounds: 2 });
      // every non-vague spec, with or without plan, stays below the rework line
      for (const s of [full, partial]) for (const p of q('sim nao', 'yes no').split(' ')) {
        expect(runCmd(id, lang, `${v} "${s}" ${q('--plano', '--plan')} ${p}`).flags).not.toContain('rework');
      }
      const own = runCmd(id, lang, `${v} "${q('Critérios de aceite: X. Fora do escopo: Y.', 'Acceptance criteria: X. Out of scope: Y.')}" ${q('--plano nao', '--plan no')}`);
      expect(own.vars).toMatchObject({ lines: 180, crit: 4 });
      expect(runCmd(id, lang, `${v} "${q('faz aí', 'just do it')}" ${q('--plano nao', '--plan no')}`).flags).toContain('rework');
    });

    it('02: Claude Code only sees the rules through CLAUDE.md; AGENTS.md alone leaves it blind', () => {
      const id = 'dai-p-arquivos-de-regras';
      expect(lesson(id).def.predict!.answer).toBe('import');
      const d = runCmd(id, lang, q('regras', 'rules')) as Run;
      expect(d.vars).toMatchObject({ nSee: 3, copies: 1, adh: 95 });
      const t = d.widgets!.find((w) => w.type === 'table')! as { rows: unknown[][] };
      expect(t.rows[0][1]).toBe('@viaImport');
      const alone = runCmd(id, lang, q('regras --arquivos agents-md', 'rules --files agents-md'));
      expect(alone.flags).toContain('blind');
      expect(alone.vars).toMatchObject({ nSee: 2, blindNames: 'Claude Code' });
      const dangling = runCmd(id, lang, q('regras --arquivos claude-md', 'rules --files claude-md'));
      expect(dangling.vars).toMatchObject({ nSee: 0, blindNames: 'Claude Code, Copilot, Cursor' });
      const all = runCmd(id, lang, q('regras --arquivos agents-md,claude-md,copilot-instructions,cursor-rules', 'rules --files agents-md,claude-md,copilot-instructions,cursor-rules'));
      expect(all.flags).toEqual(expect.arrayContaining(['allSee', 'drift']));
      expect(all.vars?.copies).toBe(3);
      expect(runCmd(id, lang, q('regras --linhas 600', 'rules --lines 600')).flags).toContain('long');
      expect(parseCommand(q('regras --linhas 2000', 'rules --lines 2000'), lesson(id).def.command, lang).ok).toBe(false);
    });

    it('03: one slice without verification lets 6 of 8 bugs through; 6 verified slices let none; 8 costs more review', () => {
      const id = 'dai-p-tarefas-pequenas';
      expect(lesson(id).def.predict!.answer).toBe('most');
      const d = runCmd(id, lang, q('fatiar', 'slice')) as Run;
      expect(d.vars).toMatchObject({ slices: 6, lines: 200, escaped: 0, totalMin: 102 });
      const chart = d.widgets!.find((w) => w.type === 'chart') as { series: { values: number[] }[] };
      expect(chart.series[1].values[0]).toBe(6);
      const one = runCmd(id, lang, q('fatiar --fatias 1 --verificar nao', 'slice --slices 1 --verify no'));
      expect(one.vars).toMatchObject({ lines: 1200, found: 2, escaped: 6 });
      expect(runCmd(id, lang, q('fatiar --fatias 2 --verificar nao', 'slice --slices 2 --verify no')).flags).toContain('leak');
      expect(runCmd(id, lang, q('fatiar --fatias 1', 'slice --slices 1')).flags).not.toContain('leak');
      const eight = runCmd(id, lang, q('fatiar --fatias 8', 'slice --slices 8'));
      expect(eight.flags).toContain('overSliced');
      expect(Number(eight.vars?.totalMin)).toBeGreaterThan(102);
    });

    it('04: with the contract locked the agent fixes the code; a rule or no lock fakes a green suite', () => {
      const id = 'dai-p-testes-como-contrato';
      expect(lesson(id).def.predict!.answer).toBe('fixcode');
      const d = runCmd(id, lang, q('contrato', 'contract'));
      expect(d.flags).toContain('honestGreen');
      expect(d.vars).toMatchObject({ passed: 12, total: 12, bugs: 0, denied: 2 });
      const rule = runCmd(id, lang, q('contrato --protecao regra', 'contract --protection rule'));
      expect(rule.flags).toEqual(expect.arrayContaining(['fakeGreen', 'testsEdited']));
      expect(rule.vars).toMatchObject({ passed: 12, bugs: 1, changed: 1 });
      const later = runCmd(id, lang, q('contrato --teste-primeiro nao', 'contract --test-first no')) as Run;
      expect(later.flags).toContain('fakeGreen');
      expect(later.vars).toMatchObject({ passed: 6, total: 6, bugs: 2 });
      expectFilled(id, lang, later, 'test-first no');
    });

    it('05: green tests hide 3 changed orders; the recording catches them unless the fix is mixed in', () => {
      const id = 'dai-p-refatoracao-assistida';
      expect(lesson(id).def.predict!.answer).toBe('three');
      const d = runCmd(id, lang, q('refatorar', 'refactor'));
      expect(d.flags).toContain('preserved');
      expect(d.vars).toMatchObject({ caught: 3, silent: 0, shown: 3, perStep: 225, badStep: 2 });
      const blind = runCmd(id, lang, q('refatorar --gravar nao', 'refactor --record no'));
      expect(blind.vars).toMatchObject({ silent: 3, searchLines: 900 });
      const mixed = runCmd(id, lang, q('refatorar --misturar sim', 'refactor --mix yes')) as Run;
      expect(mixed.flags).toEqual(expect.arrayContaining(['silentChange', 'tangled']));
      expect(mixed.vars).toMatchObject({ shown: 17, silent: 3 });
      expectFilled(id, lang, mixed, 'mix');
      expect(runCmd(id, lang, q('refatorar --passos 1', 'refactor --steps 1')).flags).toContain('bigBang');
    });

    it('06: 2 of 10 statements are wrong; search and file:line each catch one', () => {
      const id = 'dai-p-legado-e-codigo-desconhecido';
      expect(lesson(id).def.predict!.answer).toBe('two');
      const v = q('explorar', 'explore');
      const d = runCmd(id, lang, v);
      expect(d.flags).toContain('understood');
      expect(d.vars).toMatchObject({ caught: 2, believed: 0, edited: 0 });
      for (const f of [q('--buscar nao', '--search no'), q('--citar nao', '--cite no')]) {
        const r = runCmd(id, lang, `${v} ${f}`) as Run;
        expect(r.flags, f).toContain('brokeLegacy');
        expect(r.vars?.believed).toBe(1);
        expectFilled(id, lang, r, f);
      }
      const both = runCmd(id, lang, `${v} ${q('--buscar nao --citar nao --so-leitura nao', '--search no --cite no --read-only no')}`) as Run;
      expect(both.vars).toMatchObject({ believed: 2, edited: 7 });
      expect(both.flags).toContain('editedBlind');
      expectFilled(id, lang, both, 'all off');
    });

    it('07: review is the bottleneck; coupon + delivery conflict in a worktree; the same folder clobbers', () => {
      const id = 'dai-p-agentes-em-paralelo';
      expect(lesson(id).def.predict!.answer).toBe('review');
      const v = q('paralelo', 'parallel');
      const d = runCmd(id, lang, v) as Run;
      expect(d.flags).toContain('reviewBound');
      expect(d.vars).toMatchObject({ n: 3, wall: 80, seq: 145, agentMax: 35, reviewSum: 55, conflicts: 0 });
      const conf = runCmd(id, lang, `${v} ${q('--tarefas cupom,frete', '--tasks coupon,delivery')}`);
      expect(conf.flags).toContain('conflict');
      expect(conf.vars).toMatchObject({ conflicts: 1, wall: 70, conflictFile: 'src/preco.ts' });
      const shared = runCmd(id, lang, `${v} ${q('--isolamento mesma-pasta', '--isolation same-folder')}`);
      expect(shared.vars).toMatchObject({ n: 3, red: 6 });
      const solo = runCmd(id, lang, `${v} ${q('--tarefas agenda --isolamento mesma-pasta', '--tasks booking --isolation same-folder')}`);
      expect(solo.flags).not.toContain('clobbered');
      const fast = runCmd(id, lang, `${v} ${q('--revisar nao', '--review no')}`) as Run;
      expect(fast.flags).toContain('unreviewed');
      expect(fast.vars?.wall).toBe(35);
      expectFilled(id, lang, fast, 'no review');
      const four = runCmd(id, lang, `${v} ${q('--tarefas cupom,agenda,relatorio,frete', '--tasks coupon,booking,report,delivery')}`) as Run;
      expect(four.error).toBeUndefined();
      expectFilled(id, lang, four, 'all four');
    });
  });
}

describe('real executor with fake deps (lesson 1, your own key)', () => {
  const id = 'dai-p-especificacao-antes-do-codigo';
  async function runReal(lang: Lang, input: string, reply: string) {
    const l = lesson(id);
    const p = parseCommand(input, l.def.command, lang);
    if (!p.ok) throw new Error(JSON.stringify(p.error));
    const cfg = l.def.real!['sua-chave']!;
    let system = '';
    const deps: RealDeps = {
      tokenizer: async () => ({ encode: () => [], decode: () => '' }),
      chat: async (m) => {
        system = m[0].content;
        return reply;
      },
    };
    const r = await ADAPTERS[cfg.adapter].run(p.values, { lang, layer: 'dev', data: l.def.data, text: l.locale[lang].data, rng: makeRng(1) }, deps, { executor: 'sua-chave', model: 'claude-haiku-5-5' }, cfg);
    return { r: r as unknown as Run, system };
  }

  it('only offers simulated and your-key executors', () => {
    expect(lesson(id).def.executors).toEqual(['simulado', 'sua-chave']);
    for (const other of P1.slice(1)) expect(lesson(other).def.real).toBeUndefined();
  });

  for (const lang of LANGS) {
    const v = lang === 'pt' ? 'especificar' : 'specify';
    it(`[${lang}] the model's criteria count decides the spec level, for any text`, async () => {
      const good = await runReal(lang, `${v} "qualquer texto" ${lang === 'pt' ? '--plano nao' : '--plan no'}`, 'Ok: {"criteria": 4, "out_of_scope": true, "question": "Quem cancela?"}');
      expect(good.system).toContain('JSON');
      expect(good.r.flags).toContain('lean');
      expect(good.r.vars).toMatchObject({ lines: 180, crit: 4, realQ: 'Quem cancela?' });
      expectFilled(id, lang, good.r, 'real good');
      const vague = await runReal(lang, `${v} "x" ${lang === 'pt' ? '--plano nao' : '--plan no'}`, '{"criteria": 0, "out_of_scope": false, "question": "O que é pronto?"}');
      expect(vague.r.flags).toContain('rework');
      expectFilled(id, lang, vague.r, 'real vague');
      const broken = await runReal(lang, `${v} "x"`, 'acho que está boa');
      expect(broken.r.flags).toContain('gradeBroken');
      expectFilled(id, lang, broken.r, 'real broken');
    });
  }
});
