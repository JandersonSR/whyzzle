import type { Values } from './command';
import { getModel, type ModelCtx, type ModelResult } from './registry';
import type { ExecutorId, Loc, StepDef } from './schema';

/**
 * Executors are "who produces the answer". Fundamentos uses only the simulated
 * toy models; the other two are declared now so Prática can plug in without
 * changing lessons:
 *  - no-navegador: Transformers.js / WebLLM, downloaded on demand (needs WebGPU for chat).
 *  - sua-chave: the person's own API key, kept only in their browser.
 */

export interface Availability {
  ok: boolean;
  reason?: Loc;
}

export interface Executor {
  id: ExecutorId;
  label: Loc;
  available(): Availability;
  run(step: StepDef, values: Values, ctx: ModelCtx): Promise<ModelResult>;
}

const simulated: Executor = {
  id: 'simulado',
  label: { pt: 'Simulado · modelo de brinquedo', en: 'Simulated · toy model' },
  available: () => ({ ok: true }),
  run: async (step, values, ctx) => getModel(step.model).run(values, ctx),
};

const inBrowser: Executor = {
  id: 'no-navegador',
  label: { pt: 'Modelo real no navegador', en: 'Real model in the browser' },
  available: () => {
    const hasGpu = typeof navigator !== 'undefined' && 'gpu' in navigator;
    return {
      ok: false,
      reason: hasGpu
        ? { pt: 'Chega com a trilha Prática.', en: 'Arrives with the Practice track.' }
        : {
            pt: 'Este aparelho não tem WebGPU. Na trilha Prática ele usa o modo simulado.',
            en: 'This device has no WebGPU. In the Practice track it falls back to simulated mode.',
          },
    };
  },
  run: async () => {
    throw new Error('no-navegador executor not implemented yet');
  },
};

const ownKey: Executor = {
  id: 'sua-chave',
  label: { pt: 'Sua chave de API', en: 'Your API key' },
  available: () => ({
    ok: false,
    reason: { pt: 'Chega com a trilha Prática.', en: 'Arrives with the Practice track.' },
  }),
  run: async () => {
    throw new Error('sua-chave executor not implemented yet');
  },
};

export const executors: Record<ExecutorId, Executor> = {
  simulado: simulated,
  'no-navegador': inBrowser,
  'sua-chave': ownKey,
};

/** First executor the step accepts that can run here; falls back to simulated. */
export function pickExecutor(step: StepDef, preferred?: ExecutorId): Executor {
  const order = preferred ? [preferred, ...step.executors] : step.executors;
  for (const id of order) {
    if (step.executors.includes(id) && executors[id].available().ok) return executors[id];
  }
  return simulated;
}
