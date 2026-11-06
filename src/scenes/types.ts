import type { ComponentType } from 'react';
import type { Lesson } from '../content';
import type { Values } from '../engine/command';
import type { ModelResult } from '../engine/registry';
import type { Lang, Layer, StepLocale } from '../engine/schema';
import type { Run } from '../engine/stepMachine';

/** What every scene receives. Scenes only draw; they never change the step. */
export interface SceneProps {
  lesson: Lesson;
  loc: StepLocale;
  /** Strings from the step's pt.json/en.json → scene. */
  s: Record<string, unknown>;
  lang: Lang;
  layer: Layer;
  /** Values parsed from what is typed right now (null while the command is invalid). */
  values: Values | null;
  /** Deterministic preview of the current values, updated as the person types. */
  preview: ModelResult | null;
  /** Result of the last real run. */
  last: ModelResult | null;
  runs: Run[];
}

export type Scene = ComponentType<SceneProps>;

/** Reads a scene string; nested keys with dots ("kinds.think"). */
export function str(s: Record<string, unknown>, key: string): string {
  const v = key.split('.').reduce<unknown>((o, k) => (o && typeof o === 'object' ? (o as Record<string, unknown>)[k] : undefined), s);
  return typeof v === 'string' ? v : key;
}
