import type { SimModel, ModelResult } from '../engine/registry';
import { words } from '../engine/text';

/**
 * Step 6 — retrieval-augmented generation over a fictional school's documents.
 * Retrieval here is keyword overlap (real systems use embeddings, step 5).
 */

export interface Doc {
  id: string;
  title: string;
  text: string;
  answer: string;
  wrong: string;
}

export interface RagResult extends ModelResult {
  question: string;
  search: boolean;
  ranked: { doc: Doc; score: number }[];
  used: Doc[];
  answer: string;
  cites: string[];
  status: 'grounded' | 'notFound' | 'hallucinated';
}

export const THRESHOLD = 0.3;

const stem = (w: string) => w.slice(0, 4);

export function rank(question: string, docs: Doc[], stop: Set<string>) {
  const q = Array.from(new Set(words(question).filter((w) => !stop.has(w) && w.length > 2).map(stem)));
  return docs
    .map((doc) => {
      const terms = new Set(words(`${doc.title} ${doc.text}`).map(stem));
      const hit = q.filter((t) => terms.has(t)).length;
      return { doc, score: q.length ? Math.round((hit / q.length) * 100) / 100 : 0 };
    })
    .sort((a, b) => b.score - a.score);
}

export const rag: SimModel<RagResult> = {
  id: 'rag',
  run(values, ctx) {
    const docs = ctx.text.docs as Doc[];
    const stop = new Set(ctx.text.stopwords as string[]);
    const question = String(values.text);
    const search = values.search !== false;
    const top = Number(values.top);
    const ranked = rank(question, docs, stop);
    const best = ranked[0];
    const relevant = best && best.score >= THRESHOLD;
    if (!search) {
      const answer = relevant ? best.doc.wrong : String(ctx.text.genericWrong);
      return { flags: ['hallucinated'], vars: {}, question, search, ranked: [], used: [], answer, cites: [], status: 'hallucinated' };
    }
    const used = ranked.slice(0, top).filter((r) => r.score >= THRESHOLD).map((r) => r.doc);
    if (!relevant) {
      return { flags: ['notFound'], vars: {}, question, search, ranked, used: [], answer: String(ctx.text.notFound), cites: [], status: 'notFound' };
    }
    return {
      flags: ['grounded'],
      vars: { doc: best.doc.title },
      question,
      search,
      ranked,
      used,
      answer: best.doc.answer,
      cites: [best.doc.title],
      status: 'grounded',
    };
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
