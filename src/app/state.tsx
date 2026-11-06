import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';
import type { Topic } from '../content';
import type { ProgressStore } from '../engine/progress';
import type { Lang, Layer } from '../engine/schema';
import { interpolate } from '../engine/text';
import en from '../i18n/en.json';
import pt from '../i18n/pt.json';

export type UiText = typeof pt;
const UI: Record<Lang, UiText> = { pt, en };

export type Mode = 'ui' | 'cmd';

interface AppState {
  lang: Lang;
  setLang(l: Lang): void;
  layer: Layer;
  setLayer(l: Layer): void;
  /** Explicit choice, or undefined to follow the layer (Simples → Buttons). */
  modePref: Mode | undefined;
  setMode(m: Mode): void;
  ui: UiText;
  /** UI string with {placeholders} filled in. */
  t(template: string, vars?: Record<string, string | number | undefined>): string;
  topics: Topic[];
  store: ProgressStore;
  /** Bumps whenever progress changes, so pages re-read the store. */
  version: number;
}

const Ctx = createContext<AppState | null>(null);

export function useApp(): AppState {
  const c = useContext(Ctx);
  if (!c) throw new Error('useApp outside AppProvider');
  return c;
}

function initialLang(store: ProgressStore): Lang {
  const saved = store.prefs().lang;
  if (saved) return saved;
  const nav = typeof navigator !== 'undefined' ? navigator.language : 'pt';
  return nav.toLowerCase().startsWith('pt') ? 'pt' : 'en';
}

export function AppProvider({ topics, store, children }: { topics: Topic[]; store: ProgressStore; children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => initialLang(store));
  const [layer, setLayerState] = useState<Layer>(() => store.prefs().layer ?? 'simples');
  const [modePref, setModeState] = useState<Mode | undefined>(() => store.prefs().mode);
  const [version, setVersion] = useState(0);

  useEffect(() => store.onChange(() => setVersion((v) => v + 1)), [store]);
  useEffect(() => {
    document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';
  }, [lang]);

  const value = useMemo<AppState>(
    () => ({
      lang,
      setLang: (l) => {
        setLangState(l);
        store.setPrefs({ lang: l });
      },
      layer,
      setLayer: (l) => {
        setLayerState(l);
        store.setPrefs({ layer: l });
      },
      modePref,
      setMode: (m) => {
        setModeState(m);
        store.setPrefs({ mode: m });
      },
      ui: UI[lang],
      t: (template, vars) => interpolate(template, vars),
      topics,
      store,
      version,
    }),
    [lang, layer, modePref, topics, store, version],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}
