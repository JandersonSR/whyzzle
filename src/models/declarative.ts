import { z } from 'zod';
import type { ModelResult, SimModel } from '../engine/registry';
import { check, evaluate, type Env, type Value } from '../engine/expr';

/**
 * The declarative model: a lesson describes its simulation in step.json → data,
 * so most new lessons need no code.
 *
 *   consts   literal values (also step.json data and pt/en.json data are visible)
 *   compute  name → expression, evaluated in order after the command values
 *   cases    { when, flags?, set?, vars?, error? } — every matching case applies, in order
 *   widgets  what the "widgets" scene draws; any string starting with "=" is an expression
 *
 * See ARCHITECTURE.md → "Lições só com dados".
 */

const Expr = z.string().min(1);
export const DeclCase = z.object({
  when: Expr,
  flags: z.array(z.string()).default([]),
  /** Extra names computed only when the case matches (e.g. terminal lines). */
  set: z.record(z.string(), Expr).default({}),
  /** Values exposed to the step texts as {name}. */
  vars: z.record(z.string(), Expr).default({}),
  /** A model error code, explained in errors["model.<code>"]. */
  error: z.string().optional(),
});

export const DeclData = z.object({
  consts: z.record(z.string(), z.unknown()).default({}),
  compute: z.record(z.string(), Expr).default({}),
  cases: z.array(DeclCase).default([]),
  widgets: z.array(z.record(z.string(), z.unknown())).min(1),
});
export type DeclData = z.infer<typeof DeclData>;

/** Widget types the "widgets" scene can draw (kept in sync with scenes/Widgets.tsx by a test). */
export const WIDGET_KINDS = ['metrics', 'terminal', 'queue', 'cluster', 'table', 'flow', 'chart', 'note', 'checks'] as const;

/**
 * Problems in a declarative lesson, in plain words, so a broken lesson fails
 * the build with a useful message: bad data, expressions that don't parse,
 * unknown widgets, and "@key" texts missing from the lesson's scene strings.
 */
export function declIssues(sim: unknown, sceneTexts: Record<string, unknown>): string[] {
  const parsed = DeclData.safeParse(sim);
  if (!parsed.success) return [`data.sim: ${parsed.error.issues.map((i) => `${i.path.join('.')} ${i.message}`).join('; ')}`];
  const d = parsed.data;
  const issues: string[] = [];
  const exprs = [...Object.values(d.compute), ...d.cases.flatMap((c) => [c.when, ...Object.values(c.set), ...Object.values(c.vars)])];
  d.widgets.forEach((w, i) => {
    if (!(WIDGET_KINDS as readonly string[]).includes(String(w.type))) issues.push(`widgets[${i}]: unknown type "${String(w.type)}"`);
    exprs.push(...expressionsIn(w));
    for (const m of JSON.stringify(w).match(/"@[\w.]+"/g) ?? []) {
      const key = m.slice(2, -1);
      const v = key.split('.').reduce<unknown>((o, k) => (o && typeof o === 'object' ? (o as Record<string, unknown>)[k] : undefined), sceneTexts);
      if (typeof v !== 'string') issues.push(`widgets[${i}]: scene text "${key}" is missing`);
    }
  });
  for (const e of exprs) {
    try {
      check(e);
    } catch (err) {
      issues.push((err as Error).message);
    }
  }
  return issues;
}

export interface DeclResult extends ModelResult {
  /** Widgets with every "=expression" resolved. */
  widgets: Record<string, unknown>[];
  /** Primitive values visible to texts and widget labels. */
  env: Record<string, string | number | boolean>;
}

/** Resolves "=expr" strings anywhere inside a widget config. */
export function resolve(v: unknown, env: Env, rng: () => number): unknown {
  if (typeof v === 'string') return v.startsWith('=') ? evaluate(v.slice(1), env, rng) : v;
  if (Array.isArray(v)) return v.map((x) => resolve(x, env, rng));
  if (v && typeof v === 'object') {
    const out: Record<string, unknown> = {};
    for (const [k, x] of Object.entries(v)) out[k] = resolve(x, env, rng);
    return out;
  }
  return v;
}

/** Walks a widget config and yields every expression, for validation. */
export function* expressionsIn(v: unknown): Generator<string> {
  if (typeof v === 'string' && v.startsWith('=')) yield v.slice(1);
  else if (Array.isArray(v)) for (const x of v) yield* expressionsIn(x);
  else if (v && typeof v === 'object') for (const x of Object.values(v)) yield* expressionsIn(x);
}

const primitive = (v: unknown): v is string | number | boolean => ['string', 'number', 'boolean'].includes(typeof v);

export const declarative: SimModel<DeclResult> = {
  id: 'declarative',
  run(values, ctx) {
    const d = DeclData.parse(ctx.data.sim ?? {});
    const env: Env = { ...ctx.data, ...ctx.text, ...d.consts, ...values, lang: ctx.lang, layer: ctx.layer };
    delete env.sim;
    for (const [name, src] of Object.entries(d.compute)) env[name] = evaluate(src, env, ctx.rng);
    const flags: string[] = [];
    const vars: Record<string, string | number | undefined> = {};
    let error: { code: string; value?: string } | undefined;
    for (const c of d.cases) {
      if (!evaluate(c.when, env, ctx.rng)) continue;
      for (const [name, src] of Object.entries(c.set)) env[name] = evaluate(src, env, ctx.rng);
      for (const f of c.flags) if (!flags.includes(f)) flags.push(f);
      for (const [name, src] of Object.entries(c.vars)) {
        const v = evaluate(src, env, ctx.rng) as Value;
        vars[name] = primitive(v) ? (v as string | number) : String(v);
      }
      if (c.error && !error) error = { code: c.error, value: String(values.text ?? '') };
    }
    const flat: Record<string, string | number | boolean> = {};
    for (const [k, v] of Object.entries(env)) if (primitive(v)) flat[k] = v;
    for (const [k, v] of Object.entries(vars)) if (v !== undefined) flat[k] = v;
    const widgets = d.widgets
      .filter((w) => w.when === undefined || Boolean(resolve(w.when, env, ctx.rng)))
      .map((w) => resolve(w, env, ctx.rng) as Record<string, unknown>);
    return { flags, vars: { ...flat, ...vars } as Record<string, string | number>, widgets, env: flat, ...(error ? { error } : {}) };
  },
  preview(values, ctx) {
    return this.run(values, ctx);
  },
};
