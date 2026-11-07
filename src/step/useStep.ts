import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { useApp, type Mode } from '../app/state';
import type { Lesson } from '../content';
import { defaultCommand, parseCommand, translateCommand, type CommandError, type ParseResult } from '../engine/command';
import { emit } from '../engine/events';
import { executors, offeredExecutors, type ExecStatus } from '../engine/executors';
import type { ExecutorId } from '../engine/schema';
import { ByokError } from '../runtime/byok';
import type { Progress } from '../runtime/transformers';
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

  // Which executor answers, and the state of any download it needs.
  const offered = offeredExecutors(def);
  const [execId, setExecId] = useState<ExecutorId>('simulado');
  const [tick, setTick] = useState(0);
  const [prep, setPrep] = useState<{ loading: boolean; progress: Progress | null; error: string | null }>({ loading: false, progress: null, error: null });
  const executor = executors[execId];
  const status: ExecStatus = useMemo(() => executor.status(def), [executor, def, tick]); // eslint-disable-line react-hooks/exhaustive-deps

  const prepare = useCallback(async () => {
    if (!executor.prepare) return;
    setPrep({ loading: true, progress: { ratio: 0, text: '' }, error: null });
    try {
      await executor.prepare(def, (progress) => setPrep((p) => ({ ...p, progress })));
      setPrep({ loading: false, progress: null, error: null });
    } catch (e) {
      setPrep({ loading: false, progress: null, error: (e as Error).message === 'webgpu' ? 'webgpu' : 'download' });
    }
    setTick((t) => t + 1);
  }, [executor, def]);

  const preview: ModelResult | null = useMemo(() => {
    // Real executors answer only when asked: no preview while typing.
    if (!live.ok || execId !== 'simulado') return null;
    const m = getModel(def.model);
    if (!m.preview) return null;
    try {
      const r = m.preview(live.values, ctx(makeRng(7)));
      return r.error ? null : r;
    } catch {
      return null;
    }
  }, [live, def.model, ctx, execId]);
  const last: ModelResult | null = state.runs[0]?.result ?? null;

  const run = useCallback(async () => {
    const s = stateRef.current;
    const r = parseCommand(s.input, def.command, lang);
    if (!r.ok) {
      dispatch({ type: 'error', error: r.error });
      emit({ type: 'ran', stepId: def.id, ok: false, errorCode: r.error.code, mode });
      return;
    }
    if (status.state !== 'ready') {
      dispatch({ type: 'error', error: { code: 'model', modelCode: `real.${status.state}` } });
      return;
    }
    let result: ModelResult;
    try {
      result = await executor.run(def, r.values, ctx(Math.random));
    } catch (e) {
      const kind = e instanceof ByokError ? e.kind : 'other';
      dispatch({ type: 'error', error: { code: 'model', modelCode: `real.${kind}`, value: (e as Error).message.slice(0, 160) } });
      emit({ type: 'ran', stepId: def.id, ok: false, errorCode: `real.${kind}`, mode });
      return;
    }
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
  }, [def, lang, mode, executor, status, ctx, isMission]);

  const errorText = useMemo(() => {
    const e: CommandError | null = state.error;
    if (!e) return '';
    const keys = e.code === 'model' ? [`model.${e.modelCode}`] : [`${e.code}.${e.flag}`, e.code];
    const realKey = e.modelCode?.startsWith('real.') ? e.modelCode.slice(5) : null;
    const tpl =
      keys.map((k) => loc.errors[k]).find(Boolean) ??
      (realKey ? (ui.real.errors as Record<string, string>)[realKey] : undefined) ??
      (ui.errors as Record<string, string>)[e.code] ??
      e.code;
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
    offered,
    execId,
    setExecutor: (id: ExecutorId) => {
      setExecId(id);
      setPrep({ loading: false, progress: null, error: null });
      dispatch({ type: 'input', value: stateRef.current.input });
    },
    status,
    prep,
    prepare,
    refreshStatus: () => setTick((t) => t + 1),
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
