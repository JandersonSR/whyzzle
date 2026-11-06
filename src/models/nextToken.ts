import type { SimModel, ModelResult } from '../engine/registry';
import { normalize } from '../engine/text';

/** Step 1 — a tiny "language model": a table of which word tends to follow which. */

type Table = Record<string, [string, number][]>;

export interface Position {
  word: string;
  cands: { word: string; p: number }[];
  unknown: boolean;
  from: string;
}

export interface NextTokenResult extends ModelResult {
  prefix: string;
  positions: Position[];
}

function generate(text: string, steps: number, table: Table, fallback: [string, number][]): NextTokenResult {
  const positions: Position[] = [];
  const typed = text.trim().split(/\s+/).filter(Boolean);
  let last = typed.length ? typed[typed.length - 1] : '';
  let unknownWord: string | undefined;
  for (let i = 0; i < steps; i++) {
    const key = normalize(last).replace(/[^a-z0-9-]/g, '');
    const row = table[key];
    const unknown = !row;
    if (unknown && unknownWord === undefined) unknownWord = last;
    const cands = (row ?? fallback).map(([word, p]) => ({ word, p })).sort((a, b) => b.p - a.p);
    const pick = cands[0];
    positions.push({ word: pick.word, cands: cands.slice(0, 3), unknown, from: last });
    if (pick.word === '.') break;
    last = pick.word;
  }
  const flags = unknownWord !== undefined ? ['unknown'] : [];
  return { flags, vars: { word: unknownWord ?? '' }, prefix: text.trim(), positions };
}

export const nextToken: SimModel<NextTokenResult> = {
  id: 'next-token',
  run(values, ctx) {
    const table = ctx.text.table as Table;
    const fallback = ctx.text.fallback as [string, number][];
    return generate(String(values.text), Number(values.steps), table, fallback);
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
