import type { SimModel, ModelResult } from '../engine/registry';
import { interpolate, normalize } from '../engine/text';
import { verdict, RULES, type Rule } from './evals';
import { rank, THRESHOLD, type Doc } from './rag';

/**
 * Final mission of Fundamentos — build the school front-office assistant.
 * It combines what the track taught: role (step 4), temperature (3), retrieval
 * with sources (6) and an evaluation that can catch invention (8).
 * Defaults are deliberately bad, so the learner has to fix each one.
 */

interface MissionQuestion {
  q: string;
  /** What a model without grounding says (sounds right, is wrong). */
  invent: string;
}

export const CRITERIA = ['role', 'grounded', 'noInvent', 'cites', 'stable', 'testCatches', 'score'] as const;
export type Criterion = (typeof CRITERIA)[number];

export interface MissionAnswer {
  q: string;
  text: string;
  correct: boolean;
  cites: boolean;
  abstains: boolean;
  invented: boolean;
  embellished: boolean;
  doc: string | null;
  verdicts: Partial<Record<Rule, boolean>>;
  pass: boolean;
}

export interface MissionResult extends ModelResult {
  answers: MissionAnswer[];
  criteria: { id: Criterion; ok: boolean }[];
  score: number;
  tests: Rule[];
  passed: boolean;
}

export const STABLE_MAX_T = 0.5;
export const EMBELLISH_FROM_T = 0.8;
export const PASS_SCORE = 0.8;

export const mission: SimModel<MissionResult> = {
  id: 'mission',
  run(values, ctx) {
    const docs = ctx.text.docs as Doc[];
    const stop = new Set(ctx.text.stopwords as string[]);
    const qs = ctx.text.questions as MissionQuestion[];
    const roleWords = (ctx.text.roleWords as string[]).map(normalize);
    const role = String(values.text);
    const T = Number(values.temp);
    const search = values.search === true;
    const cite = values.cite === true;
    const tests = ((values.tests as string[]) ?? []).filter((r): r is Rule => (RULES as readonly string[]).includes(r));

    const answers: MissionAnswer[] = qs.map((mq, i) => {
      let text: string;
      let correct = false;
      let cites = false;
      let abstains = false;
      let doc: string | null = null;
      const best = search ? rank(mq.q, docs, stop)[0] : undefined;
      if (best && best.score >= THRESHOLD) {
        doc = best.doc.title;
        correct = true;
        text = best.doc.answer;
        if (cite) {
          cites = true;
          text += ' ' + interpolate(String(ctx.text.citeFmt), { doc: best.doc.title });
        }
      } else if (search && cite) {
        abstains = true;
        text = String(ctx.text.notFound);
      } else {
        text = mq.invent;
      }
      // Hot sampling adds a confident extra "fact" to one grounded answer.
      let embellished = false;
      if (T >= EMBELLISH_FROM_T && correct && i === Number(ctx.data.embellishIndex)) {
        embellished = true;
        correct = false;
        text = text.replace(/\s*\[[^\]]*\]$/, '') + ' ' + String(ctx.text.embellish) + (cites ? ' ' + interpolate(String(ctx.text.citeFmt), { doc: doc ?? '' }) : '');
      }
      const ans = { text, correct, cites, abstains };
      const verdicts: Partial<Record<Rule, boolean>> = {};
      for (const r of tests) verdicts[r] = verdict(r, ans);
      return {
        q: mq.q,
        ...ans,
        invented: !correct && !abstains,
        embellished,
        doc,
        verdicts,
        pass: tests.length > 0 && tests.every((r) => verdicts[r]),
      };
    });

    const score = Math.round((answers.filter((a) => a.pass).length / answers.length) * 100) / 100;
    const invented = answers.filter((a) => a.invented).length;
    const ok: Record<Criterion, boolean> = {
      role: roleWords.some((w) => normalize(role).includes(w)),
      grounded: search,
      noInvent: invented === 0,
      cites: answers.every((a) => a.abstains || a.cites),
      stable: T <= STABLE_MAX_T,
      testCatches: tests.includes('honest') || tests.includes('source'),
      score: score >= PASS_SCORE,
    };
    const criteria = CRITERIA.map((id) => ({ id, ok: ok[id] }));
    const passed = criteria.every((c) => c.ok);
    const flags = passed ? ['passed'] : [];
    if (invented) flags.push('invented');
    return {
      flags,
      vars: { score: Math.round(score * 100), invented, done: criteria.filter((c) => c.ok).length, total: criteria.length },
      answers,
      criteria,
      score,
      tests,
      passed,
    };
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
