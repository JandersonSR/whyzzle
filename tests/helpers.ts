import { loadTopics, type Lesson } from '../src/content';
import { parseCommand, type Values } from '../src/engine/command';
import { getModel, type ModelResult } from '../src/engine/registry';
import type { Lang } from '../src/engine/schema';
import { makeRng } from '../src/engine/text';
import { registerAllModels } from '../src/models';

registerAllModels();
export const topics = loadTopics();
export const lessons = topics.flatMap((t) => t.lessons);

export function lesson(id: string): Lesson {
  const l = lessons.find((x) => x.def.id === id);
  if (!l) throw new Error(`no lesson ${id}`);
  return l;
}

/** Parses a command in the lesson's grammar and runs its simulated model. */
export function runCmd(id: string, lang: Lang, input: string, seed = 1): ModelResult & Record<string, unknown> {
  const l = lesson(id);
  const r = parseCommand(input, l.def.command, lang);
  if (!r.ok) throw new Error(`parse failed for ${input}: ${JSON.stringify(r.error)}`);
  return runValues(id, lang, r.values, seed);
}

export function runValues(id: string, lang: Lang, values: Values, seed = 1): ModelResult & Record<string, unknown> {
  const l = lesson(id);
  return getModel(l.def.model).run(values, {
    lang,
    layer: 'dev',
    data: l.def.data,
    text: l.locale[lang].data,
    rng: makeRng(seed),
  }) as ModelResult & Record<string, unknown>;
}
