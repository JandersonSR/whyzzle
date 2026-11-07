import type { Values } from './command';
import { getModel, type ModelCtx, type ModelResult } from './registry';
import type { ExecutorId, Loc, StepDef } from './schema';
import { ADAPTERS, type RealDeps } from '../runtime/adapters';
import { chatByok, getKeyConfig } from '../runtime/byok';
import { REAL_MODELS, type RealModel } from '../runtime/catalog';
import type { Progress } from '../runtime/transformers';

/**
 * Executors are "who produces the answer":
 *  - simulado: the toy models, always available.
 *  - no-navegador: a real model downloaded into the browser (Transformers.js / WebLLM).
 *  - sua-chave: the person's own API key, called straight from the browser.
 * A step offers a real executor only if step.json → real names an adapter for it.
 */

export type ExecStatus =
  | { state: 'ready'; model?: RealModel; label?: string }
  | { state: 'needsDownload'; model: RealModel }
  | { state: 'needsKey' }
  | { state: 'unsupported'; reason: Loc };

export interface Executor {
  id: ExecutorId;
  label: Loc;
  supports(step: StepDef): boolean;
  status(step: StepDef): ExecStatus;
  prepare?(step: StepDef, onProgress: (p: Progress) => void): Promise<void>;
  run(step: StepDef, values: Values, ctx: ModelCtx): Promise<ModelResult>;
}

const simulated: Executor = {
  id: 'simulado',
  label: { pt: 'Simulado', en: 'Simulated' },
  supports: () => true,
  status: () => ({ state: 'ready' }),
  run: async (step, values, ctx) => getModel(step.model).run(values, ctx),
};

const loaded = new Set<string>();
const hasGpuApi = () => typeof navigator !== 'undefined' && 'gpu' in navigator;

async function loadReal(m: RealModel, onProgress?: (p: Progress) => void): Promise<void> {
  if (m.lib === 'webllm') {
    const { hasWebGPU } = await import('../runtime/transformers');
    if (!(await hasWebGPU())) throw new Error('webgpu');
    const { loadChat } = await import('../runtime/webllm');
    await loadChat(m.id, onProgress);
  } else if (m.kind === 'tokenizer') {
    const { loadTokenizer } = await import('../runtime/transformers');
    await loadTokenizer(m.id, onProgress);
  } else {
    const { loadEmbedder } = await import('../runtime/transformers');
    await loadEmbedder(m.id, onProgress);
  }
  loaded.add(m.id);
}

const realDepsLocal = (model: string): RealDeps => ({
  tokenizer: async (id) => (await import('../runtime/transformers')).loadTokenizer(id),
  chat: async (messages, opts) => (await (await import('../runtime/webllm')).chatLocal(model, messages, opts)).text,
});

const inBrowser: Executor = {
  id: 'no-navegador',
  label: { pt: 'No navegador', en: 'In the browser' },
  supports: (step) => Boolean(step.real?.['no-navegador']),
  status(step) {
    const m = REAL_MODELS[step.real?.['no-navegador']?.model ?? ''];
    if (!m) return { state: 'unsupported', reason: { pt: 'Este passo não tem modelo real.', en: 'This step has no real model.' } };
    if (m.needsWebGPU && !hasGpuApi()) {
      return {
        state: 'unsupported',
        reason: {
          pt: 'Este navegador não tem WebGPU. Use Chrome, Edge ou Safari recentes, ou a opção "Sua chave".',
          en: 'This browser has no WebGPU. Use a recent Chrome, Edge or Safari, or the "Your key" option.',
        },
      };
    }
    return loaded.has(m.id) ? { state: 'ready', model: m, label: m.label } : { state: 'needsDownload', model: m };
  },
  async prepare(step, onProgress) {
    const m = REAL_MODELS[step.real!['no-navegador']!.model!];
    await loadReal(m, onProgress);
  },
  async run(step, values, ctx) {
    const cfg = step.real!['no-navegador']!;
    const m = REAL_MODELS[cfg.model!];
    if (!loaded.has(m.id)) await loadReal(m);
    return ADAPTERS[cfg.adapter].run(values, ctx, realDepsLocal(m.id), { executor: 'no-navegador', model: m.label });
  },
};

const ownKey: Executor = {
  id: 'sua-chave',
  label: { pt: 'Sua chave', en: 'Your key' },
  supports: (step) => Boolean(step.real?.['sua-chave']),
  status() {
    const k = getKeyConfig();
    return k && k.model ? { state: 'ready', label: k.model } : { state: 'needsKey' };
  },
  async run(step, values, ctx) {
    const k = getKeyConfig();
    if (!k) throw new Error('needsKey');
    const deps: RealDeps = {
      tokenizer: () => Promise.reject(new Error('no tokenizer through an API')),
      chat: (messages, opts) => chatByok(k, messages, opts),
    };
    return ADAPTERS[step.real!['sua-chave']!.adapter].run(values, ctx, deps, { executor: 'sua-chave', model: k.model });
  },
};

export const executors: Record<ExecutorId, Executor> = {
  simulado: simulated,
  'no-navegador': inBrowser,
  'sua-chave': ownKey,
};

/** Executors this step offers, in the order the lesson prefers. */
export function offeredExecutors(step: StepDef): Executor[] {
  const ids: ExecutorId[] = ['simulado', ...step.executors.filter((id) => id !== 'simulado')];
  return ids.map((id) => executors[id]).filter((e) => e.supports(step));
}
