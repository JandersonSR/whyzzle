import type { CommandError } from './command';
import type { ModelResult } from './registry';

/**
 * The cycle every step follows:
 *   0 predict → 1 run → 2 see → 3 why → 4 break
 * Pure reducer so it can be tested and replayed (class mode, analytics).
 */

export const PHASES = ['predict', 'run', 'see', 'why', 'break'] as const;
export type Phase = 0 | 1 | 2 | 3 | 4;

export interface Run {
  input: string;
  result: ModelResult;
}

export interface StepState {
  phase: Phase;
  maxPhase: Phase;
  prediction: string | null;
  input: string;
  runs: Run[];
  error: CommandError | null;
  hints: number;
  broke: boolean;
  /** Result of the last run made during the "break" phase. */
  breakResult: ModelResult | null;
}

export type Action =
  | { type: 'predict'; option: string }
  | { type: 'input'; value: string }
  | { type: 'error'; error: CommandError }
  | { type: 'ran'; input: string; result: ModelResult; breakFlag: string; anyPhase?: boolean }
  | { type: 'goto'; phase: Phase }
  | { type: 'hint' }
  | { type: 'reset'; input: string };

export const MAX_RUNS = 5;

export function initialState(input: string): StepState {
  return { phase: 0, maxPhase: 0, prediction: null, input, runs: [], error: null, hints: 0, broke: false, breakResult: null };
}

const max = (a: Phase, b: Phase): Phase => (a > b ? a : b);

export function reduce(s: StepState, a: Action): StepState {
  switch (a.type) {
    case 'predict':
      return { ...s, prediction: a.option, phase: 1, maxPhase: max(s.maxPhase, 1) };
    case 'input':
      return { ...s, input: a.value };
    case 'error':
      return { ...s, error: a.error };
    case 'ran': {
      const phase: Phase = s.phase < 2 ? 2 : s.phase;
      const runs = [{ input: a.input, result: a.result }, ...s.runs].slice(0, MAX_RUNS);
      const next: StepState = { ...s, error: null, runs, phase, maxPhase: max(s.maxPhase, phase) };
      // Steps break in the last phase; missions complete on any run that meets the goal.
      if (phase === 4 || a.anyPhase) {
        next.breakResult = a.result;
        if (a.result.flags.includes(a.breakFlag)) next.broke = true;
      }
      return next;
    }
    case 'goto':
      return a.phase <= s.maxPhase || a.phase === s.maxPhase + 1
        ? { ...s, phase: a.phase, maxPhase: max(s.maxPhase, a.phase) }
        : s;
    case 'hint':
      return { ...s, hints: Math.min(3, s.hints + 1) };
    case 'reset':
      return initialState(a.input);
  }
}

export function feedbackKey(s: StepState, answer: string): 'right' | 'wrong' | 'skipped' {
  if (!s.prediction) return 'skipped';
  return s.prediction === answer ? 'right' : 'wrong';
}
