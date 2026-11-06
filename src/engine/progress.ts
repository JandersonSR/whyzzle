import { subscribe, type StampedEvent } from './events';
import type { Lang, Layer } from './schema';

/**
 * Progress lives behind this interface. Today: the browser (localStorage).
 * Class mode later swaps in a store that also syncs to a backend.
 */

export interface StepProgress {
  predicted?: string;
  ran?: boolean;
  completed?: boolean;
  hints?: number;
  layersSeen?: string[];
}

export interface Prefs {
  lang?: Lang;
  layer?: Layer;
  mode?: 'ui' | 'cmd';
  /** Explicit choice; absent = follow the system setting. */
  theme?: 'light' | 'dark';
}

export interface ProgressStore {
  get(stepId: string): StepProgress;
  all(): Record<string, StepProgress>;
  update(stepId: string, patch: Partial<StepProgress>): void;
  prefs(): Prefs;
  setPrefs(patch: Partial<Prefs>): void;
  events(): StampedEvent[];
  log(e: StampedEvent): void;
  reset(): void;
  onChange(fn: () => void): () => void;
}

const KEY = 'whyzzle:v1';
const MAX_EVENTS = 500;

interface Saved {
  steps: Record<string, StepProgress>;
  prefs: Prefs;
  events: StampedEvent[];
}

function safeStorage(): Storage | null {
  try {
    const s = window.localStorage;
    s.setItem('__wz', '1');
    s.removeItem('__wz');
    return s;
  } catch {
    return null;
  }
}

export function createLocalStore(): ProgressStore {
  const storage = typeof window === 'undefined' ? null : safeStorage();
  let state: Saved = { steps: {}, prefs: {}, events: [] };
  try {
    const raw = storage?.getItem(KEY);
    if (raw) state = { ...state, ...JSON.parse(raw) };
  } catch {
    // Corrupt or unreadable data: start fresh rather than crash.
  }
  const fns = new Set<() => void>();
  const save = () => {
    try {
      storage?.setItem(KEY, JSON.stringify(state));
    } catch {
      // Storage full or blocked: keep working in memory.
    }
    fns.forEach((f) => f());
  };

  return {
    get: (id) => state.steps[id] ?? {},
    all: () => state.steps,
    update: (id, patch) => {
      state.steps = { ...state.steps, [id]: { ...state.steps[id], ...patch } };
      save();
    },
    prefs: () => state.prefs,
    setPrefs: (patch) => {
      state.prefs = { ...state.prefs, ...patch };
      save();
    },
    events: () => state.events,
    reset: () => {
      state = { steps: {}, prefs: state.prefs, events: [] };
      save();
    },
    log: (e) => {
      state.events = [...state.events, e].slice(-MAX_EVENTS);
      try {
        storage?.setItem(KEY, JSON.stringify(state));
      } catch {
        // Ignore: events are best-effort.
      }
    },
    onChange: (fn) => {
      fns.add(fn);
      return () => {
        fns.delete(fn);
      };
    },
  };
}

/** Wires the event stream into a store: progress is derived from events. */
export function connectEvents(store: ProgressStore): () => void {
  return subscribe((e) => {
    store.log(e);
    const p = store.get(e.stepId);
    switch (e.type) {
      case 'predicted':
        store.update(e.stepId, { predicted: e.option });
        break;
      case 'ran':
        if (e.ok) store.update(e.stepId, { ran: true });
        break;
      case 'hint':
        store.update(e.stepId, { hints: Math.max(p.hints ?? 0, e.level) });
        break;
      case 'layer':
        store.update(e.stepId, { layersSeen: Array.from(new Set([...(p.layersSeen ?? []), e.layer])) });
        break;
      case 'completed':
        store.update(e.stepId, { completed: true });
        break;
      default:
        break;
    }
  });
}
