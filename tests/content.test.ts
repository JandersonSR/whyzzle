import { describe, expect, it } from 'vitest';
import { buildCommand, defaultCommand, defaultValues, parseCommand } from '../src/engine/command';
import { hasModel } from '../src/engine/registry';
import { scenes } from '../src/scenes';
import { ADAPTERS } from '../src/runtime/adapters';
import { REAL_MODELS } from '../src/runtime/catalog';
import { LANGS } from '../src/engine/schema';
import { lessons, topics } from './helpers';

/** Every key path in a JSON value, with array lengths, so pt and en must match in shape. */
function shape(v: unknown, path = ''): string[] {
  if (Array.isArray(v)) return [`${path}[${v.length}]`, ...v.flatMap((x, i) => shape(x, `${path}[${i}]`))];
  if (v && typeof v === 'object') return Object.entries(v).flatMap(([k, x]) => shape(x, path ? `${path}.${k}` : k));
  return [path];
}

/** {placeholders} used in every string, by key path. */
function placeholders(v: unknown, path = '', out: Record<string, string> = {}): Record<string, string> {
  if (typeof v === 'string') out[path] = (v.match(/\{\w+\}/g) ?? []).sort().join(',');
  else if (Array.isArray(v)) v.forEach((x, i) => placeholders(x, `${path}[${i}]`, out));
  else if (v && typeof v === 'object') for (const [k, x] of Object.entries(v)) placeholders(x, path ? `${path}.${k}` : k, out);
  return out;
}

describe('content', () => {
  it('loads every topic and lesson through the schemas', () => {
    expect(topics.length).toBeGreaterThan(0);
    const ia = topics.find((t) => t.def.id === 'ia-aplicada')!.lessons;
    expect(ia.filter((l) => l.track === 'fundamentos').length).toBe(9);
    expect(ia.filter((l) => l.track === 'pratica').length).toBeGreaterThanOrEqual(15);
  });

  it('catalog: unique topic ids and priorities, honest track status', () => {
    const ids = topics.map((t) => t.def.id);
    expect(new Set(ids).size).toBe(ids.length);
    const orders = topics.map((t) => t.def.order);
    expect(new Set(orders).size).toBe(orders.length);
    expect(orders).toEqual([...orders].sort((a, b) => a - b));
    for (const t of topics) {
      for (const tr of t.def.tracks) {
        const has = t.lessons.some((l) => l.track === tr.id);
        expect(tr.status === 'ready', `${t.def.id}/${tr.id}: "ready" iff it has lessons`).toBe(has);
      }
    }
  });

  it('has unique ids and orders per track', () => {
    const ids = lessons.map((l) => l.def.id);
    expect(new Set(ids).size).toBe(ids.length);
    const orders = lessons.map((l) => `${l.track}:${l.def.order}`);
    expect(new Set(orders).size).toBe(orders.length);
  });

  it('uses only registered models and known prerequisites', () => {
    const ids = new Set(lessons.map((l) => l.def.id));
    for (const l of lessons) {
      expect(hasModel(l.def.model), `${l.def.id} model`).toBe(true);
      for (const r of l.def.requires) expect(ids.has(r), `${l.def.id} requires ${r}`).toBe(true);
      expect(scenes[l.def.scene], `${l.def.id} scene "${l.def.scene}"`).toBeTruthy();
    }
  });

  it('real executors point at existing adapters and catalog models', () => {
    for (const l of lessons) {
      for (const [ex, cfg] of Object.entries(l.def.real ?? {})) {
        expect(l.def.executors, `${l.def.id} lists ${ex}`).toContain(ex);
        expect(ADAPTERS[cfg.adapter], `${l.def.id} adapter ${cfg.adapter}`).toBeTruthy();
        if ('model' in cfg) expect(REAL_MODELS[cfg.model], `${l.def.id} model ${cfg.model}`).toBeTruthy();
      }
    }
  });

  it('no topic id collides with an app route', () => {
    for (const t of topics) expect(['galeria', 'professor', 'receitas', 'sua-chave']).not.toContain(t.def.id);
  });

  for (const l of lessons) {
    describe(l.def.id, () => {
      it('ships pt and en with the same keys and placeholders', () => {
        const { pt, en } = l.locale;
        // Model data and the embedding map's group names are language-specific by design
        // (the ambiguous word is "manga" in pt and "bat" in en).
        const skip = (p: string) => p.startsWith('data.') || p.startsWith('scene.groups.');
        expect(shape(pt).filter((p) => !skip(p))).toEqual(shape(en).filter((p) => !skip(p)));
        const php = placeholders(pt);
        const phe = placeholders(en);
        for (const k of Object.keys(php)) if (!skip(k)) expect(phe[k], `placeholder ${k}`).toBe(php[k]);
        expect(shape(l.teacher.pt)).toEqual(shape(l.teacher.en));
      });

      for (const lang of LANGS) {
        it(`[${lang}] default command, examples and the last command hint all parse`, () => {
          const def = l.def.command;
          expect(parseCommand(defaultCommand(def, lang), def, lang).ok).toBe(true);
          for (const ex of def.arg.examples) {
            const line = buildCommand(def, lang, { ...defaultValues(def, lang), [def.arg.name]: ex[lang] });
            const r = parseCommand(line, def, lang);
            expect(r.ok, ex[lang]).toBe(true);
          }
          const cheat = l.locale[lang].hints?.cmd[2];
          if (cheat) expect(parseCommand(cheat, def, lang), cheat).toMatchObject({ ok: true });
        });

        it(`[${lang}] every map point has a group label`, () => {
          const points = l.locale[lang].data.points as { group: string }[] | undefined;
          const groups = (l.locale[lang].scene.groups ?? {}) as Record<string, string>;
          for (const p of points ?? []) expect(groups[p.group], p.group).toBeTruthy();
        });

        it(`[${lang}] error texts point at real flags`, () => {
          const names = new Set(['arg', ...l.def.command.flags.map((f) => f.name)]);
          for (const key of Object.keys(l.locale[lang].errors)) {
            const [code, flag] = key.split('.');
            if (code === 'model') continue;
            if (flag) expect(names.has(flag), `${key}`).toBe(true);
          }
        });
      }
    });
  }
});
