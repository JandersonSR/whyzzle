import type { Loc } from '../engine/schema';

/**
 * Real models the site can download into the browser. Sizes are approximate
 * download sizes, shown to the person before anything is fetched.
 * Checked against @huggingface/transformers 4.3.2 and @mlc-ai/web-llm 0.2.87 (nov/2026).
 */
export interface RealModel {
  id: string;
  lib: 'transformers' | 'webllm';
  kind: 'tokenizer' | 'embeddings' | 'chat';
  label: string;
  sizeMB: number;
  needsWebGPU: boolean;
  note: Loc;
}

export const REAL_MODELS: Record<string, RealModel> = {
  'Xenova/gpt-4o': {
    id: 'Xenova/gpt-4o',
    lib: 'transformers',
    kind: 'tokenizer',
    label: 'Tokenizador do GPT-4o (o200k)',
    sizeMB: 8,
    needsWebGPU: false,
    note: { pt: 'Só o tokenizador, sem o modelo. Roda em qualquer navegador.', en: 'Tokenizer only, no model. Runs in any browser.' },
  },
  'Xenova/multilingual-e5-small': {
    id: 'Xenova/multilingual-e5-small',
    lib: 'transformers',
    kind: 'embeddings',
    label: 'multilingual-e5-small (embeddings, ~100 idiomas)',
    sizeMB: 120,
    needsWebGPU: false,
    note: { pt: 'Usa WebGPU se houver; senão, roda mais devagar na CPU.', en: 'Uses WebGPU when available; otherwise runs slower on the CPU.' },
  },
  'Llama-3.2-1B-Instruct-q4f16_1-MLC': {
    id: 'Llama-3.2-1B-Instruct-q4f16_1-MLC',
    lib: 'webllm',
    kind: 'chat',
    label: 'Llama 3.2 1B Instruct (4 bits)',
    sizeMB: 880,
    needsWebGPU: true,
    note: {
      pt: 'Modelo aberto pequeno que fala português. Precisa de WebGPU (Chrome, Edge ou Safari recentes) e de cerca de 1 GB livre.',
      en: 'Small open model that speaks Portuguese. Needs WebGPU (recent Chrome, Edge or Safari) and about 1 GB free.',
    },
  },
};
