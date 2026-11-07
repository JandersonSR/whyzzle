import { describe, expect, it } from 'vitest';
import { defaultCommand, parseCommand } from '../src/engine/command';
import { LANGS, type Lang } from '../src/engine/schema';
import { interpolate, makeRng } from '../src/engine/text';
import { ADAPTERS, type RealDeps } from '../src/runtime/adapters';
import { lesson, runCmd } from './helpers';

/**
 * Prática · 23 · missão do assistente de RH da Aurora (simulado): começa quebrada, nenhuma correção
 * sozinha basta, o comando totalmente corrigido passa. O executor "no-navegador" é exercitado com
 * embeddings falsos, como em realops.test.ts.
 */

const ID = 'p-missao-assistente-de-rh';
const SUCCESS = 'passed';

const FIXED = {
  pt: 'montar "assistente-rh" --limpar sim --modo hibrida --k 3 --limite 0.78 --citar sim --recusar sim --triagem sim',
  en: 'build "hr-assistant" --clean yes --mode hybrid --k 3 --threshold 0.78 --cite yes --refuse yes --triage yes',
};

/** The fixed command with one option swapped (pt, en). */
function fixedWith(lang: Lang, pt: [string, string], en: [string, string]) {
  const [a, b] = lang === 'pt' ? pt : en;
  expect(FIXED[lang], `fixed command has ${a}`).toContain(a);
  return FIXED[lang].replace(a, b);
}

describe('structure', () => {
  it('is the last lesson of the track, a mission whose break flag is the success flag', () => {
    const l = lesson(ID);
    expect(l.def.kind).toBe('mission');
    expect(l.def.order).toBe(23);
    expect(l.def.break.flag).toBe(SUCCESS);
    expect(l.def.predict).toBeUndefined();
    expect(l.def.requires).toContain('p-avaliar-recuperacao');
    expect(l.def.requires).toContain('p-mcp-conectar-sistemas');
    expect(l.def.executors).toEqual(['simulado', 'no-navegador']);
    for (const lang of LANGS) {
      expect(l.locale[lang].success).toBeTruthy();
      expect(l.locale[lang].hints!.cmd[2]).toBe(FIXED[lang]);
    }
  });

  it('no computed value shadows a command option', () => {
    const l = lesson(ID);
    const sim = l.def.data.sim as { compute: Record<string, string> };
    const names = new Set(l.def.command.flags.map((f) => f.name));
    for (const n of Object.keys(sim.compute)) expect(names.has(n), n).toBe(false);
  });
});

for (const lang of LANGS) {
  const pt = lang === 'pt';
  const q = (a: string, b: string) => (pt ? a : b);

  describe(`[${lang}] mission`, () => {
    const l = lesson(ID);
    const run = (cmd: string) => runCmd(ID, lang, cmd);

    it('default does not succeed and shows which criteria fail', () => {
      const r = run(defaultCommand(l.def.command, lang));
      expect(r.error).toBeUndefined();
      expect(r.flags).not.toContain(SUCCESS);
      expect(r.flags).toEqual(expect.arrayContaining(['dirtyIndex', 'wrongAnswers', 'noCitation', 'badRefusal', 'noTriage']));
      const checks = (r as unknown as { widgets: { type: string; items: { ok: boolean }[] }[] }).widgets.find((w) => w.type === 'checks')!;
      expect(checks.items).toHaveLength(6);
      expect(checks.items.filter((i) => i.ok).length).toBeLessThan(6);
    });

    it('the fully fixed command succeeds and every criterion is green', () => {
      const r = run(FIXED[lang]);
      expect(r.error).toBeUndefined();
      expect(r.flags).toContain(SUCCESS);
      expect(r.vars).toMatchObject({ nCorrect: 9, nAns: 9, nOutRef: 2, nOut: 2, nRouted: 2, nSens: 2, recPct: 100 });
      const checks = (r as unknown as { widgets: { type: string; items: { ok: boolean }[] }[] }).widgets.find((w) => w.type === 'checks')!;
      expect(checks.items.every((i) => i.ok)).toBe(true);
      // the success text renders with no placeholder left over
      const text = interpolate(l.locale[lang].success!, r.vars as Record<string, string | number>);
      expect(text).not.toMatch(/\{\w+\}/);
    });

    it('every command that succeeds shares the same essential fixes (success text holds for all of them)', () => {
      // k 3..6 and thresholds 75..80% all pass and render the success text
      for (const k of [3, 4, 5, 6]) {
        for (const limit of ['0.75', '0.78', '0.8']) {
          const cmd = fixedWith(lang, ['--k 3', `--k ${k}`], ['--k 3', `--k ${k}`]).replace('0.78', limit);
          const r = run(cmd);
          expect(r.flags, cmd).toContain(SUCCESS);
          expect(interpolate(l.locale[lang].success!, r.vars as Record<string, string | number>)).not.toMatch(/\{\w+\}/);
        }
      }
    });

    const single: [string, string, [string, string], [string, string], string][] = [
      ['dirty index', 'dirtyIndex', ['--limpar sim', '--limpar nao'], ['--clean yes', '--clean no'], 'clean off'],
      ['keyword search', 'wrongAnswers', ['--modo hibrida', '--modo palavra'], ['--mode hybrid', '--mode keyword'], 'keyword only'],
      ['vector-only search', 'noCitation', ['--modo hibrida', '--modo vetor'], ['--mode hybrid', '--mode vector'], 'vector only'],
      ['k too small', 'wrongAnswers', ['--k 3', '--k 1'], ['--k 3', '--k 1'], 'k = 1'],
      ['k = 2', 'wrongAnswers', ['--k 3', '--k 2'], ['--k 3', '--k 2'], 'k = 2'],
      ['no threshold', 'badRefusal', ['--limite 0.78', '--limite 0'], ['--threshold 0.78', '--threshold 0'], 'threshold 0'],
      ['threshold too low', 'badRefusal', ['--limite 0.78', '--limite 0.74'], ['--threshold 0.78', '--threshold 0.74'], 'threshold 0.74'],
      ['threshold too high', 'wrongAnswers', ['--limite 0.78', '--limite 0.85'], ['--threshold 0.78', '--threshold 0.85'], 'threshold 0.85'],
      ['no citation', 'noCitation', ['--citar sim', '--citar nao'], ['--cite yes', '--cite no'], 'cite off'],
      ['no refusal sentence', 'badRefusal', ['--recusar sim', '--recusar nao'], ['--refuse yes', '--refuse no'], 'refuse off'],
      ['no triage', 'noTriage', ['--triagem sim', '--triagem nao'], ['--triage yes', '--triage no'], 'triage off'],
    ];
    for (const [name, flag, ptSwap, enSwap] of single) {
      it(`one missing fix keeps it failing: ${name}`, () => {
        const r = run(fixedWith(lang, ptSwap, enSwap));
        expect(r.flags).not.toContain(SUCCESS);
        expect(r.flags).toContain(flag);
      });
    }

    it('guesses about the setup match the simulator', () => {
      // a threshold between the outside-the-handbook questions (74%) and the lowest handbook one (80%) works
      expect(run(q('montar --limite 0.75', 'build --threshold 0.75')).vars?.nOutRef).toBe(0); // refuse is still off
      const only = run(FIXED[lang]);
      expect(only.vars?.nFalseRef).toBe(0);
      // hybrid with a clean index recovers the acronym and synonym questions that single modes miss
      const kw = run(fixedWith(lang, ['--modo hibrida', '--modo palavra'], ['--mode hybrid', '--mode keyword']));
      const hy = run(FIXED[lang]);
      expect(Number(hy.vars?.nCorrect)).toBeGreaterThan(Number(kw.vars?.nCorrect));
    });
  });
}

describe('real executor (no-navegador) with fake embeddings', () => {
  const l = lesson(ID);
  const runReal = async (lang: Lang, input: string, embed: (t: string[]) => Promise<number[][]>) => {
    const p = parseCommand(input, l.def.command, lang);
    if (!p.ok) throw new Error(JSON.stringify(p.error));
    const cfg = l.def.real!['no-navegador']!;
    const deps: RealDeps = { tokenizer: async () => ({ encode: () => [], decode: () => '' }), chat: async () => '', embed };
    return ADAPTERS[cfg.adapter].run(p.values, { lang, layer: 'dev', data: l.def.data, text: l.locale[lang].data, rng: makeRng(1) }, deps, { executor: 'no-navegador', model: 'm' }, cfg);
  };

  for (const lang of LANGS) {
    it(`[${lang}] query × chunk similarities from the embedder drive retrieval`, async () => {
      const sim = l.def.data.sim as { consts: { golds: number[][]; semMatrix: number[][] } };
      const golds = sim.consts.golds;
      const nQ = golds.length;
      const nD = sim.consts.semMatrix[0].length;
      const unit = (ids: number[], bad = false) => {
        const v = Array.from({ length: nD }, (_, j) => (ids.includes(bad ? (j + 5) % nD : j) ? 1 : 0));
        const n = Math.hypot(...v) || 1;
        return v.map((x) => x / n);
      };
      let seen: string[] = [];
      const good = async (texts: string[]) => {
        seen = texts;
        return texts.map((_, i) => (i < nQ ? unit(golds[i]) : unit([i - nQ])));
      };
      const r = await runReal(lang, FIXED[lang], good);
      expect(seen).toHaveLength(nQ + nD);
      expect(seen[0].startsWith('query: ')).toBe(true);
      expect(seen[nQ].startsWith('passage: ')).toBe(true);
      expect(r.real.executor).toBe('no-navegador');
      expect(r.flags).toContain(SUCCESS);
      expect(r.vars?.recPct).toBe(100);

      // an embedder that points every question at the wrong chunks: retrieval fails, so the mission does too
      const bad = async (texts: string[]) => texts.map((_, i) => (i < nQ ? unit(golds[i], true) : unit([i - nQ])));
      const rb = await runReal(lang, FIXED[lang], bad);
      expect(rb.flags).not.toContain(SUCCESS);
      expect(rb.flags).toContain('wrongAnswers');
    });
  }
});
