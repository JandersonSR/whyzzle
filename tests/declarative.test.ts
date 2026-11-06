import { describe, expect, it } from 'vitest';
import { check } from '../src/engine/expr';
import { makeRng } from '../src/engine/text';
import { DeclData, declarative, declIssues, expressionsIn, WIDGET_KINDS } from '../src/models/declarative';
import gallery from '../src/scenes/gallery.json';
import { WIDGET_TYPES } from '../src/scenes/Widgets';

const run = (incidente: boolean) =>
  declarative.run({ incidente }, { lang: 'pt', layer: 'dev', data: { sim: gallery.sim }, text: {}, rng: makeRng(1) });

/** Every "@key" used anywhere in a resolved widget list. */
function keysIn(v: unknown, out: string[] = []): string[] {
  if (typeof v === 'string' && v.startsWith('@')) out.push(v.slice(1));
  else if (Array.isArray(v)) v.forEach((x) => keysIn(x, out));
  else if (v && typeof v === 'object') Object.values(v).forEach((x) => keysIn(x, out));
  return out;
}

describe('declarative model + widgets (gallery)', () => {
  it('model and scene agree on the widget types', () => {
    expect([...WIDGET_KINDS].sort()).toEqual([...WIDGET_TYPES].sort());
  });

  it('declIssues: the gallery is clean, a broken lesson is explained', () => {
    expect(declIssues(gallery.sim, gallery.scene.pt)).toEqual([]);
    const broken = {
      compute: { x: '1 +' },
      cases: [{ when: 'x > 1' }],
      widgets: [{ type: 'sparkle' }, { type: 'note', text: '@nope' }],
    };
    const issues = declIssues(broken, {});
    expect(issues.join('\n')).toMatch(/unknown type "sparkle"/);
    expect(issues.join('\n')).toMatch(/scene text "nope" is missing/);
    expect(issues.join('\n')).toMatch(/unexpected/);
    expect(declIssues({ widgets: [] }, {})[0]).toMatch(/^data\.sim/);
  });

  it('validates and every expression parses', () => {
    const d = DeclData.parse(gallery.sim);
    for (const w of d.widgets) {
      expect(WIDGET_TYPES, String(w.type)).toContain(w.type);
      for (const e of expressionsIn(w)) expect(() => check(e), e).not.toThrow();
    }
  });

  it('applies cases, flags and vars', () => {
    const ok = run(false);
    const bad = run(true);
    expect(ok.flags).toEqual(['healthy']);
    expect(bad.flags).toEqual(['incident']);
    expect(bad.vars?.culpado).toBe('api-7d9f');
    expect(bad.env.p95).toBe(2400);
  });

  it('resolves every expression and hides widgets whose "when" is false', () => {
    const ok = run(false);
    const bad = run(true);
    expect(JSON.stringify(bad.widgets)).not.toMatch(/"=/);
    expect(bad.widgets.some((w) => w.type === 'note')).toBe(true);
    expect(ok.widgets.some((w) => w.type === 'note')).toBe(false);
    const term = bad.widgets.find((w) => w.type === 'terminal') as { lines: string[] };
    expect(term.lines[2]).toMatch(/^!api-7d9f\s+0\/1\s+CrashLoopBackOff/);
  });

  it('uses only scene texts that exist in pt and en', () => {
    const keys = new Set([...keysIn(run(false).widgets), ...keysIn(run(true).widgets)]);
    for (const k of keys) {
      expect(gallery.scene.pt, `pt ${k}`).toHaveProperty(k);
      expect(gallery.scene.en, `en ${k}`).toHaveProperty(k);
    }
    expect(Object.keys(gallery.scene.pt).sort()).toEqual(Object.keys(gallery.scene.en).sort());
  });
});
