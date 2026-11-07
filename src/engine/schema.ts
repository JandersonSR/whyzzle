import { z } from 'zod';

/**
 * Schemas for everything a lesson ships as data.
 * A topic has tracks; a track has steps; each step is a folder with:
 *   step.json    — language-neutral definition (command, model, scene, checks)
 *   pt.json/en.json — every human-readable text, same keys in both
 *   teacher.json — teacher guide (both languages)
 */

export const LANGS = ['pt', 'en'] as const;
export type Lang = (typeof LANGS)[number];

export const TRACKS = ['fundamentos', 'pratica', 'producao'] as const;
export type TrackId = (typeof TRACKS)[number];

export const LAYERS = ['simples', 'dev', 'especialista'] as const;
export type Layer = (typeof LAYERS)[number];

export const EXECUTORS = ['simulado', 'no-navegador', 'sua-chave'] as const;
export type ExecutorId = (typeof EXECUTORS)[number];

export const Loc = z.object({ pt: z.string().min(1), en: z.string().min(1) });
export type Loc = z.infer<typeof Loc>;

const Option = z.object({ id: z.string().min(1), pt: z.string().min(1), en: z.string().min(1) });

const FlagValue = z.union([z.number(), z.string(), z.boolean(), z.array(z.string())]);

export const FlagDef = z
  .object({
    /** Internal name, used by models and in error keys (e.g. "belowMin.temp"). */
    name: z.string().min(1),
    /** What the person types after "--", per language. Both are always accepted. */
    alias: Loc,
    type: z.enum(['number', 'int', 'string', 'enum', 'list', 'bool']),
    min: z.number().optional(),
    max: z.number().optional(),
    step: z.number().optional(),
    /** Range shown by the beginner slider (may be narrower than min/max). */
    uiMin: z.number().optional(),
    uiMax: z.number().optional(),
    default: FlagValue.optional(),
    defaultLoc: Loc.optional(),
    required: z.boolean().default(false),
    options: z.array(Option).optional(),
    /** How Buttons mode renders the flag. */
    ui: z.enum(['slider', 'toggle10', 'text', 'select', 'checkboxes', 'switch', 'hidden']).optional(),
  })
  .superRefine((f, ctx) => {
    if ((f.type === 'enum' || f.type === 'list') && !f.options?.length) {
      ctx.addIssue({ code: 'custom', message: `flag ${f.name}: enum/list needs options` });
    }
  });
export type FlagDef = z.infer<typeof FlagDef>;

export const CommandDef = z.object({
  verb: Loc,
  arg: z.object({
    name: z.string().min(1),
    required: z.boolean().default(true),
    default: Loc,
    /** Ready-made examples offered in Buttons mode. */
    examples: z.array(Loc).default([]),
    ui: z.enum(['text', 'textarea', 'examples']).default('text'),
  }),
  flags: z.array(FlagDef).default([]),
});
export type CommandDef = z.infer<typeof CommandDef>;

export const StepDef = z.object({
  id: z.string().regex(/^[a-z0-9-]+$/),
  order: z.number().int().positive(),
  track: z.enum(TRACKS),
  kind: z.enum(['step', 'mission']).default('step'),
  minutes: z.number().positive(),
  tags: z.array(z.string()).default([]),
  /** Step ids that should come first (used for recommendations later). */
  requires: z.array(z.string()).default([]),
  /** Which executors can run this step, in order of preference. */
  executors: z.array(z.enum(EXECUTORS)).min(1),
  model: z.string().min(1),
  scene: z.string().min(1),
  command: CommandDef,
  /** Steps only: the guess offered before the first run. */
  predict: z.object({ options: z.array(z.string()).min(2), answer: z.string() }).optional(),
  /**
   * Steps: complete when a run in the "break" phase raises this flag.
   * Missions: complete when any run raises it (all criteria met).
   */
  break: z.object({ flag: z.string().min(1) }),
  /** Language-neutral model data (numbers, coordinates, logits...). */
  data: z.record(z.string(), z.unknown()).default({}),
  /** Real executors this step supports: which adapter, and for the browser which model. */
  real: z
    .object({
      'no-navegador': z.object({ adapter: z.string().min(1), model: z.string().min(1) }).optional(),
      'sua-chave': z.object({ adapter: z.string().min(1) }).optional(),
    })
    .optional(),
})
  .superRefine((s, ctx) => {
    if (s.kind === 'step' && !s.predict) ctx.addIssue({ code: 'custom', message: `step ${s.id}: needs "predict"` });
    if (s.predict && !s.predict.options.includes(s.predict.answer)) {
      ctx.addIssue({ code: 'custom', message: `step ${s.id}: predict.answer must be one of predict.options` });
    }
  });
export type StepDef = z.infer<typeof StepDef>;

const ModeText = z.object({ ui: z.string().min(1), cmd: z.string().min(1) });

export const StepLocale = z.object({
  title: z.string().min(1),
  subtitle: z.string().min(1),
  mission: z.string().min(1),
  // Steps have the full predict → run → see → why → break cycle; missions skip
  // predict, feedback, tryNext, break and hints (checked by stepLocaleIssues).
  predict: z.object({ question: z.string().min(1), options: z.record(z.string(), z.string().min(1)) }).optional(),
  feedback: z.object({ right: z.string().min(1), wrong: z.string().min(1), skipped: z.string().min(1) }).optional(),
  coach: ModeText,
  tryNext: ModeText.optional(),
  why: z.object({ simples: z.string().min(1), dev: z.string().min(1), especialista: z.string().min(1) }),
  formula: z.string().optional(),
  break: z.object({ mission: ModeText, success: z.string().min(1), calm: z.string().min(1) }).optional(),
  hints: z.object({ ui: z.array(z.string().min(1)).length(3), cmd: z.array(z.string().min(1)).length(3) }).optional(),
  /** Missions: what success looks like, shown after all criteria pass. */
  success: z.string().min(1).optional(),
  /** Explanations for common mistakes. Keys: "<code>" or "<code>.<flag>". */
  errors: z.record(z.string(), z.string().min(1)).default({}),
  /** Labels for Buttons-mode controls, keyed by flag name (and "arg"). */
  controls: z.record(z.string(), z.string().min(1)).default({}),
  /** Strings used by the scene. */
  scene: z.record(z.string(), z.unknown()).default({}),
  /** Language-specific model data (documents, vocabulary, word maps...). */
  data: z.record(z.string(), z.unknown()).default({}),
  recipe: z.object({ steps: z.array(z.string().min(1)).min(1), ok: z.string().min(1) }),
});
export type StepLocale = z.infer<typeof StepLocale>;

/** Cross-checks a locale against its step: what each kind must ship. */
export function stepLocaleIssues(def: StepDef, loc: StepLocale): string[] {
  const issues: string[] = [];
  if (def.kind === 'step') {
    for (const k of ['predict', 'feedback', 'tryNext', 'break', 'hints'] as const) {
      if (!loc[k]) issues.push(`missing "${k}"`);
    }
    for (const o of def.predict?.options ?? []) {
      if (!loc.predict?.options[o]) issues.push(`predict.options.${o} has no text`);
    }
  } else if (!loc.success) {
    issues.push('missions need "success"');
  }
  for (const f of def.command.flags) {
    if (f.ui !== 'hidden' && !loc.controls[f.name]) issues.push(`controls.${f.name} has no label`);
  }
  if (!loc.controls.arg) issues.push('controls.arg has no label');
  return issues;
}

const TeacherLoc = z.object({
  objectives: z.array(z.string().min(1)).min(1),
  minutes: z.number().positive(),
  activity: z.string().min(1),
  discussion: z.array(z.string().min(1)).min(1),
  misconceptions: z.array(z.string().min(1)).min(1),
});
export const TeacherGuide = z.object({ pt: TeacherLoc, en: TeacherLoc });
export type TeacherGuide = z.infer<typeof TeacherGuide>;

/** Catalog areas, used to group and filter topics. */
export const AREAS = ['ia', 'arquitetura', 'backend', 'frontend', 'dados', 'infra', 'seguranca', 'carreira', 'base', 'negocios'] as const;
export type Area = (typeof AREAS)[number];

export const TopicDef = z.object({
  id: z.string().regex(/^[a-z0-9-]+$/),
  /** Priority in the roadmap (1 = first). */
  order: z.number().int().positive(),
  area: z.enum(AREAS),
  title: Loc,
  tagline: Loc,
  tracks: z
    .array(
      z.object({
        id: z.enum(TRACKS),
        status: z.enum(['ready', 'soon']),
        title: Loc,
        audience: Loc,
        description: Loc,
      }),
    )
    .length(3),
});
export type TopicDef = z.infer<typeof TopicDef>;
