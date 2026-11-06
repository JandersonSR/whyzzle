import type { SimModel, ModelResult } from '../engine/registry';
import { normalize } from '../engine/text';

/**
 * Step 8 — evaluating two toy assistants on the same questions with rules the
 * person chooses. A weak test (only "short") gives a lying model a perfect score.
 */

interface Answer {
  text: string;
  correct: boolean;
  cites: boolean;
  abstains: boolean;
}

interface Question {
  q: string;
  inDocs: boolean;
  a: Answer;
  b: Answer;
}

export const RULES = ['source', 'honest', 'short'] as const;
export type Rule = (typeof RULES)[number];

export const SHORT_LIMIT = 90;

export function verdict(rule: Rule, ans: Answer): boolean {
  switch (rule) {
    case 'source':
      return ans.cites || ans.abstains;
    case 'honest':
      return ans.correct || ans.abstains;
    case 'short':
      return ans.text.length <= SHORT_LIMIT;
  }
}

export interface EvalRow {
  q: string;
  answer: Answer;
  verdicts: Partial<Record<Rule, boolean>>;
  pass: boolean;
  invented: boolean;
}

export interface EvalResult extends ModelResult {
  model: 'a' | 'b';
  rules: Rule[];
  rows: EvalRow[];
  score: number;
  scores: { a: number; b: number };
  invented: number;
}

function scoreFor(qs: Question[], model: 'a' | 'b', rules: Rule[]): { rows: EvalRow[]; score: number } {
  const rows = qs.map((q) => {
    const answer = q[model];
    const verdicts: Partial<Record<Rule, boolean>> = {};
    for (const r of rules) verdicts[r] = verdict(r, answer);
    const pass = rules.every((r) => verdicts[r]);
    return { q: q.q, answer, verdicts, pass, invented: !answer.correct && !answer.abstains };
  });
  const score = rules.length ? rows.filter((r) => r.pass).length / rows.length : 0;
  return { rows, score: Math.round(score * 100) / 100 };
}

export function parseModel(s: string): 'a' | 'b' | null {
  const n = normalize(s).replace(/modelo|model|\s/g, '');
  if (n === 'a') return 'a';
  if (n === 'b') return 'b';
  return null;
}

export const evals: SimModel<EvalResult> = {
  id: 'evals',
  run(values, ctx) {
    const qs = ctx.text.questions as Question[];
    const rules = (values.rules as string[]).filter((r): r is Rule => (RULES as readonly string[]).includes(r));
    const model = parseModel(String(values.text));
    if (!model) {
      return {
        flags: [],
        error: { code: 'unknownModel', value: String(values.text) },
        model: 'a',
        rules,
        rows: [],
        score: 0,
        scores: { a: 0, b: 0 },
        invented: 0,
      };
    }
    const mine = scoreFor(qs, model, rules);
    const scores = { a: scoreFor(qs, 'a', rules).score, b: scoreFor(qs, 'b', rules).score };
    const invented = mine.rows.filter((r) => r.invented).length;
    const flags: string[] = [];
    if (!rules.length) flags.push('noRules');
    if (invented > 0 && mine.score === 1) flags.push('goodhart');
    if (invented > 0 && mine.rows.some((r) => r.invented && !r.pass)) flags.push('caught');
    return {
      flags,
      vars: { score: Math.round(mine.score * 100), invented, model: model.toUpperCase() },
      model,
      rules,
      rows: mine.rows,
      score: mine.score,
      scores,
      invented,
    };
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
