import type { SimModel, ModelResult } from '../engine/registry';
import { normalize } from '../engine/text';

/**
 * Step 2 — a toy subword tokenizer. Common words are one token; rare words are
 * cut into pieces, like real BPE tokenizers do. Not a real vocabulary.
 */

export interface Tok {
  text: string;
  id: number;
  space: boolean;
  kind: 'word' | 'piece' | 'num' | 'punct';
}

export interface TokenizerResult extends ModelResult {
  tokens: Tok[];
  count: number;
  window: number;
  overflow: number;
  chars: number;
}

function hashId(s: string): number {
  let h = 2166136261;
  for (const c of s) h = Math.imul(h ^ c.charCodeAt(0), 16777619);
  return (h >>> 0) % 50000;
}

export function tokenizeText(text: string, vocab: Set<string>): Tok[] {
  const out: Tok[] = [];
  const re = /(\s*)([\p{L}]+|\d+|[^\s\p{L}\d])/gu;
  let m: RegExpExecArray | null;
  while ((m = re.exec(text))) {
    const space = m[1].length > 0 && out.length > 0;
    const w = m[2];
    if (/^\d+$/.test(w)) {
      for (let i = 0; i < w.length; i += 3) out.push(mk(w.slice(i, i + 3), i === 0 && space, 'num'));
    } else if (/^\p{L}+$/u.test(w)) {
      if (w.length <= 4 || vocab.has(normalize(w))) {
        out.push(mk(w, space, 'word'));
      } else {
        const pieces: string[] = [];
        let rest = w;
        while (rest.length > 5) {
          pieces.push(rest.slice(0, 4));
          rest = rest.slice(4);
        }
        pieces.push(rest);
        pieces.forEach((p, i) => out.push(mk(p, i === 0 && space, 'piece')));
      }
    } else {
      out.push(mk(w, space, 'punct'));
    }
  }
  return out;
}

function mk(text: string, space: boolean, kind: Tok['kind']): Tok {
  return { text, space, kind, id: hashId((space ? ' ' : '') + text) };
}

export const tokenizer: SimModel<TokenizerResult> = {
  id: 'tokenizer',
  run(values, ctx) {
    const vocab = new Set((ctx.text.vocab as string[]).map(normalize));
    const text = String(values.text);
    const tokens = tokenizeText(text, vocab);
    const window = Number(values.window);
    const overflow = Math.max(0, tokens.length - window);
    const flags: string[] = [];
    if (overflow > 0) flags.push('overflow');
    if (tokens.some((t) => t.kind === 'piece')) flags.push('split');
    const lost = tokens
      .slice(0, overflow)
      .map((t) => (t.space ? ' ' : '') + t.text)
      .join('')
      .trim();
    return {
      flags,
      vars: { count: tokens.length, window, lost: overflow, lostText: lost.length > 40 ? lost.slice(0, 40) + '…' : lost },
      tokens,
      count: tokens.length,
      window,
      overflow,
      chars: text.length,
    };
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
