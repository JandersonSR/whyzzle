/**
 * Every learner action becomes an event. Today events only feed local
 * progress; later the same stream feeds class mode (teacher dashboard) and
 * per-student recommendations, without touching lessons.
 */

export type LearnEvent =
  | { type: 'opened'; stepId: string }
  | { type: 'predicted'; stepId: string; option: string; correct: boolean }
  | { type: 'ran'; stepId: string; ok: boolean; errorCode?: string; flags?: string[]; mode: 'ui' | 'cmd' }
  | { type: 'hint'; stepId: string; level: number }
  | { type: 'layer'; stepId: string; layer: string }
  | { type: 'phase'; stepId: string; phase: number }
  | { type: 'completed'; stepId: string };

export type StampedEvent = LearnEvent & { at: number };
type Listener = (e: StampedEvent) => void;

const listeners = new Set<Listener>();

export function emit(e: LearnEvent): void {
  const stamped = { ...e, at: Date.now() } as StampedEvent;
  for (const l of listeners) {
    try {
      l(stamped);
    } catch {
      // A failing listener must never break the lesson.
    }
  }
}

export function subscribe(l: Listener): () => void {
  listeners.add(l);
  return () => listeners.delete(l);
}
