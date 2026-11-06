import { StepDef, StepLocale, TeacherGuide, TopicDef, stepLocaleIssues, type Lang, type TrackId } from './engine/schema';

/**
 * Loads every lesson from /content at build time. Adding a lesson = adding a
 * folder with step.json, pt.json, en.json and teacher.json. No code changes.
 */

/** Track-level pages live next to lessons in the URL, so lessons can't use these names. */
export const RESERVED_SLUGS = ['receitas', 'professor'];

export interface Lesson {
  topic: string;
  track: TrackId;
  /** URL slug, from the folder name without its numeric prefix. */
  slug: string;
  def: StepDef;
  locale: Record<Lang, StepLocale>;
  teacher: TeacherGuide;
}

export interface Topic {
  def: TopicDef;
  lessons: Lesson[];
}

const stepFiles = import.meta.glob('../content/*/*/*/step.json', { eager: true, import: 'default' });
const ptFiles = import.meta.glob('../content/*/*/*/pt.json', { eager: true, import: 'default' });
const enFiles = import.meta.glob('../content/*/*/*/en.json', { eager: true, import: 'default' });
const teacherFiles = import.meta.glob('../content/*/*/*/teacher.json', { eager: true, import: 'default' });
const topicFiles = import.meta.glob('../content/*/topic.json', { eager: true, import: 'default' });

function parse<T>(schema: { parse(v: unknown): T }, value: unknown, where: string): T {
  try {
    return schema.parse(value);
  } catch (e) {
    throw new Error(`Whyzzle content error in ${where}: ${(e as Error).message}`);
  }
}

export function loadTopics(): Topic[] {
  const topics: Topic[] = [];
  for (const [path, raw] of Object.entries(topicFiles)) {
    const def = parse(TopicDef, raw, path);
    topics.push({ def, lessons: [] });
  }
  for (const [path, raw] of Object.entries(stepFiles)) {
    const dir = path.slice(0, -'step.json'.length);
    const [, , topicId, track, folder] = path.split('/');
    const topic = topics.find((t) => t.def.id === topicId);
    if (!topic) throw new Error(`Whyzzle: ${path} has no topic.json for "${topicId}"`);
    const def = parse(StepDef, raw, path);
    if (def.track !== track) throw new Error(`Whyzzle: ${path} says track "${def.track}" but lives in "${track}"`);
    const locale = {
      pt: parse(StepLocale, ptFiles[`${dir}pt.json`], `${dir}pt.json`),
      en: parse(StepLocale, enFiles[`${dir}en.json`], `${dir}en.json`),
    };
    for (const lang of ['pt', 'en'] as const) {
      const issues = stepLocaleIssues(def, locale[lang]);
      if (issues.length) throw new Error(`Whyzzle content error in ${dir}${lang}.json: ${issues.join('; ')}`);
    }
    const slug = folder.replace(/^\d+-/, '');
    if (RESERVED_SLUGS.includes(slug)) throw new Error(`Whyzzle: ${path} uses the reserved slug "${slug}"`);
    topic.lessons.push({
      topic: topicId,
      track: track as TrackId,
      slug,
      def,
      locale,
      teacher: parse(TeacherGuide, teacherFiles[`${dir}teacher.json`], `${dir}teacher.json`),
    });
  }
  topics.sort((a, b) => a.def.order - b.def.order);
  for (const t of topics) t.lessons.sort((a, b) => (a.track === b.track ? a.def.order - b.def.order : a.track.localeCompare(b.track)));
  return topics;
}

/** Raw file maps, exposed for the content validation test. */
export const rawContent = { stepFiles, ptFiles, enFiles, teacherFiles, topicFiles };
