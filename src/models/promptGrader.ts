import type { SimModel, ModelResult } from '../engine/registry';
import { interpolate, normalize, words } from '../engine/text';

/**
 * Step 4 — a toy model that answers one topic. What changes the answer is how
 * the prompt is written: audience, format, tone and role. It also obeys any
 * "ignore everything" text pasted into the task (a preview of prompt injection).
 */

interface Pools {
  technical: string[];
  simple: string[];
  fun: string[];
  injected: string[];
  opener: string;
  injectWords: string[];
  topicWords: string[];
}

export interface PromptResult extends ModelResult {
  opener: string | null;
  sentences: string[];
  bullets: boolean;
  checklist: { audience: boolean; format: boolean; tone: boolean; role: boolean };
  score: number;
  injected: boolean;
  offTopic: boolean;
}

export const promptGrader: SimModel<PromptResult> = {
  id: 'prompt-grader',
  run(values, ctx) {
    const p = ctx.text as unknown as Pools;
    const task = String(values.text);
    const audience = typeof values.audience === 'string' && values.audience.trim() ? values.audience : '';
    const format = typeof values.format === 'string' && values.format.trim() ? values.format : '';
    const tone = typeof values.tone === 'string' ? values.tone : '';
    const role = typeof values.role === 'string' && values.role.trim() ? values.role : '';
    const checklist = { audience: !!audience, format: !!format, tone: !!tone, role: !!role };
    const score = Object.values(checklist).filter(Boolean).length / 4;

    const taskWords = words(task);
    const injected = p.injectWords.some((w) => taskWords.includes(normalize(w)));
    const offTopic = !injected && !p.topicWords.some((w) => normalize(task).includes(normalize(w)));

    if (injected) {
      return {
        flags: ['injected'],
        opener: null,
        sentences: p.injected,
        bullets: false,
        checklist,
        score,
        injected,
        offTopic: false,
      };
    }

    const numMatch = format.match(/\d+/);
    let n = format ? 3 : 5;
    if (numMatch) n = Math.min(5, Math.max(1, Number(numMatch[0])));
    const bullets = /t[oó]pico|lista|bullet|list|item/i.test(format);
    const pool = audience ? p.simple : p.technical;
    const sentences = pool.slice(0, n).map((s, i) => (tone === 'divertido' && i % 2 === 1 ? p.fun[i % p.fun.length] : s));
    const flags: string[] = [];
    if (score >= 0.75) flags.push('good');
    if (offTopic) flags.push('offTopic');
    return {
      flags,
      vars: { score: Math.round(score * 100) },
      opener: role ? interpolate(p.opener, { role }) : null,
      sentences,
      bullets,
      checklist,
      score,
      injected,
      offTopic,
    };
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
