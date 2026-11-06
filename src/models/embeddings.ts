import type { SimModel, ModelResult } from '../engine/registry';
import { normalize } from '../engine/text';

/**
 * Step 5 — a hand-made 2D "embedding" map. Real embeddings have hundreds of
 * dimensions; two are enough to see the idea: meaning becomes distance.
 */

export interface Point {
  w: string;
  x: number;
  y: number;
  group: string;
  ambiguous?: boolean;
}

export interface EmbeddingResult extends ModelResult {
  query: Point | null;
  neighbors: { point: Point; sim: number }[];
  points: Point[];
}

const MAX_D = Math.SQRT2 * 100;

export function similarity(a: Point, b: Point): number {
  return Math.round((1 - Math.hypot(a.x - b.x, a.y - b.y) / MAX_D) * 100) / 100;
}

export const embeddings: SimModel<EmbeddingResult> = {
  id: 'embeddings',
  run(values, ctx) {
    const points = ctx.text.points as Point[];
    const q = normalize(String(values.text));
    const query = points.find((p) => normalize(p.w) === q) ?? null;
    if (!query) {
      return { flags: [], error: { code: 'unknownWord', value: String(values.text) }, vars: { word: String(values.text) }, query, neighbors: [], points };
    }
    const neighbors = points
      .filter((p) => p !== query)
      .map((point) => ({ point, sim: similarity(query, point) }))
      .sort((a, b) => b.sim - a.sim)
      .slice(0, Number(values.top));
    const flags = query.ambiguous ? ['ambiguous'] : [];
    const groups = Array.from(new Set(neighbors.map((n) => n.point.group)));
    return { flags, vars: { word: query.w, nearest: neighbors[0]?.point.w ?? '', groups: groups.length }, query, neighbors, points };
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
