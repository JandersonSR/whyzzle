import { useCallback, useEffect, useMemo, useReducer, useRef } from 'react';
import { useApp, type Mode } from '../app/state';
import type { Lesson } from '../content';
import { defaultCommand, parseCommand, translateCommand, type CommandError, type ParseResult } from '../engine/command';
import { emit } from '../engine/events';
import { pickExecutor } from '../engine/executors';
import { getModel, type ModelCtx, type ModelResult } from '../engine/registry';
import { initialState, reduce, type Phase } from '../engine/stepMachine';
import { interpolate, makeRng } from '../engine/text';

/** All the behavior of one step page: parsing, preview, running, phases and events. */
export function useStep(lesson: Lesson) {
  const app = useApp();
  const { lang, layer, modePref, ui } = app;
  const def = lesson.def;
  const loc = lesson.locale[lang];
  const isMission = def.kind === 'mission';
  const mode: Mode = modePref ?? (layer === 'simples' ? 'ui' : 'cmd');

  const [state, dispatch] = useReducer(reduce, undefined, () => initialState(defaultCommand(def.command, lang)));
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    emit({ type: 'opened', stepId: def.id });
  }, [def.id]);

  // Switching language re-expresses the command, keeping the person's values.
  const prevLang = useRef(lang);
  useEffect(() => {
    if (prevLang.current === lang) return;
    dispatch({ type: 'input', value: translateCommand(stateRef.current.input, def.command, prevLang.current, lang) });
    prevLang.current = lang;
  }, [lang, def.command]);

  useEffect(() => {
    emit({ type: 'layer', stepId: def.id, layer });
  }, [layer, def.id]);

  const ctx = useCallback(
    (rng: () => number): ModelCtx => ({ lang, layer, data: def.data, text: loc.data, rng }),
    [lang, layer, def.data, loc.data],
  );

  const live: ParseResult = useMemo(() => parseCommand(state.input, def.command, lang), [state.input, def.command, lang]);

  const preview: ModelResult | null = useMemo(() => {
    if (!live.ok) return null;
    const m = getModel(def.model);
    if (!m.preview) return null;
    try {
      const r = m.preview(live.values, ctx(makeRng(7)));
      return r.error ? null : r;
    } catch {
      return null;
    }
  }, [live, def.model, ctx]);

  const executor = pickExecutor(def);
  const last: ModelResult | null = state.runs[0]?.result ?? null;

  const run = useCallback(async () => {
    const s = stateRef.current;
    const r = parseCommand(s.input, def.command, lang);
    if (!r.ok) {
      dispatch({ type: 'error', error: r.error });
      emit({ type: 'ran', stepId: def.id, ok: false, errorCode: r.error.code, mode });
      return;
    }
    const result = await executor.run(def, r.values, ctx(Math.random));
    const modelErr = result.error as { code: string; value?: string } | undefined;
    if (modelErr) {
      dispatch({ type: 'error', error: { code: 'model', modelCode: modelErr.code, value: modelErr.value } });
      emit({ type: 'ran', stepId: def.id, ok: false, errorCode: `model.${modelErr.code}`, mode });
      return;
    }
    dispatch({ type: 'ran', input: s.input, result, breakFlag: def.break.flag, anyPhase: isMission });
    emit({ type: 'ran', stepId: def.id, ok: true, flags: result.flags, mode });
    const breakable = isMission || s.phase === 4;
    if (!s.broke && breakable && result.flags.includes(def.break.flag)) emit({ type: 'completed', stepId: def.id });
  }, [def, lang, mode, executor, ctx, isMission]);

  const errorText = useMemo(() => {
    const e: CommandError | null = state.error;
    if (!e) return '';
    const keys = e.code === 'model' ? [`model.${e.modelCode}`] : [`${e.code}.${e.flag}`, e.code];
    const tpl = keys.map((k) => loc.errors[k]).find(Boolean) ?? (ui.errors as Record<string, string>)[e.code] ?? e.code;
    return interpolate(tpl, { ...e, min: e.min, max: e.max });
  }, [state.error, loc.errors, ui.errors]);

  return {
    lesson,
    def,
    loc,
    lang,
    layer,
    mode,
    isMission,
    state,
    live,
    preview,
    last,
    executor,
    errorText,
    run,
    setInput: (value: string) => dispatch({ type: 'input', value }),
    predict: (option: string) => {
      dispatch({ type: 'predict', option });
      emit({ type: 'predicted', stepId: def.id, option, correct: option === def.predict?.answer });
    },
    goto: (phase: Phase) => {
      dispatch({ type: 'goto', phase });
      emit({ type: 'phase', stepId: def.id, phase });
    },
    hint: () => {
      const level = Math.min(3, stateRef.current.hints + 1);
      dispatch({ type: 'hint' });
      emit({ type: 'hint', stepId: def.id, level });
    },
    reset: () => dispatch({ type: 'reset', input: defaultCommand(def.command, lang) }),
  };
}

export type StepApi = ReturnType<typeof useStep>;
