import type { Values } from './command';
import type { Lang, Layer } from './schema';

/**
 * Plug-in points. A lesson only names what it uses ("model": "sampler",
 * "scene": "sampler"); the code that implements each name registers itself here.
 */

export interface ModelCtx {
  lang: Lang;
  layer: Layer;
  /** step.json → data (language-neutral). */
  data: Record<string, unknown>;
  /** pt.json/en.json → data (language-specific). */
  text: Record<string, unknown>;
  rng: () => number;
}

export interface ModelResult {
  /** Named facts about the run, e.g. "weird", "overflow", "hallucinated". Checks read these. */
  flags: string[];
  /** Values the step texts can interpolate, e.g. {tok}. */
  vars?: Record<string, string | number | undefined>;
  [key: string]: unknown;
}

export interface SimModel<R extends ModelResult = ModelResult> {
  id: string;
  /** A real run (may be random). */
  run(values: Values, ctx: ModelCtx): R;
  /** A cheap, deterministic view used while the person is still typing. */
  preview?(values: Values, ctx: ModelCtx): R;
}

const models = new Map<string, SimModel>();

export function registerModel(m: SimModel): void {
  models.set(m.id, m as SimModel);
}

export function getModel(id: string): SimModel {
  const m = models.get(id);
  if (!m) throw new Error(`Whyzzle: no simulated model registered as "${id}"`);
  return m;
}

export function hasModel(id: string): boolean {
  return models.has(id);
}

/** Checks decide when something counts as done. Lessons reference them by name. */
export type Check = (result: ModelResult, params: Record<string, unknown>) => boolean;
const checks = new Map<string, Check>();

export function registerCheck(id: string, fn: Check): void {
  checks.set(id, fn);
}

export function runCheck(id: string, result: ModelResult, params: Record<string, unknown> = {}): boolean {
  const c = checks.get(id);
  if (!c) throw new Error(`Whyzzle: no check registered as "${id}"`);
  return c(result, params);
}

registerCheck('flag', (r, p) => r.flags.includes(String(p.flag)));
registerCheck('allFlags', (r, p) => (p.flags as string[]).every((f) => r.flags.includes(f)));
