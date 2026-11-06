import type { SimModel, ModelResult } from '../engine/registry';
import { normalize } from '../engine/text';

/** Step 3 — temperature sampling over a fixed set of next-word scores (logits). */

export interface SamplerResult extends ModelResult {
  T: number;
  n: number;
  idxs: number[];
  probs: number[];
  otherPrompt: boolean;
}

export function softmax(logits: number[], T: number): number[] {
  const t = Math.max(T, 0.01);
  const z = logits.map((v) => v / t);
  const mx = Math.max(...z);
  const e = z.map((v) => Math.exp(v - mx));
  const sum = e.reduce((a, b) => a + b, 0);
  return e.map((v) => v / sum);
}

export function sample(probs: number[], T: number, rng: () => number): number {
  if (T === 0) return probs.indexOf(Math.max(...probs));
  const x = rng();
  let acc = 0;
  for (let i = 0; i < probs.length; i++) {
    acc += probs[i];
    if (x <= acc) return i;
  }
  return probs.length - 1;
}

function base(values: Record<string, unknown>, ctx: { data: Record<string, unknown>; text: Record<string, unknown> }) {
  const logits = ctx.data.logits as number[];
  const T = Number(values.temp);
  const n = Number(values.times ?? 1);
  const probs = softmax(logits, T);
  const otherPrompt = normalize(String(values.text)) !== normalize(String(ctx.text.prefix));
  return { logits, T, n, probs, otherPrompt };
}

export const sampler: SimModel<SamplerResult> = {
  id: 'sampler',
  run(values, ctx) {
    const { T, n, probs, otherPrompt } = base(values, ctx);
    const weirdFrom = Number(ctx.data.weirdFrom);
    const words = ctx.text.words as string[];
    const idxs = Array.from({ length: n }, () => sample(probs, T, ctx.rng));
    const weirdIdx = idxs.find((i) => i >= weirdFrom);
    const flags: string[] = [];
    if (weirdIdx !== undefined && T >= 1.5) flags.push('weird');
    if (new Set(idxs).size > 1) flags.push('varied');
    if (otherPrompt) flags.push('otherPrompt');
    return {
      flags,
      vars: { tok: weirdIdx !== undefined ? words[weirdIdx] : words[idxs[idxs.length - 1]], T, n, distinct: new Set(idxs).size },
      T,
      n,
      idxs,
      probs,
      otherPrompt,
    };
  },
  preview(values, ctx) {
    const { T, n, probs, otherPrompt } = base(values, ctx);
    return { flags: [], T, n, idxs: [], probs, otherPrompt };
  },
};
