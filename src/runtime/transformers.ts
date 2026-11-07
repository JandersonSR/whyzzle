/**
 * Transformers.js, loaded only when a lesson asks for a real model.
 * The library and the model files come down on demand and are cached by the browser.
 */

export interface Progress {
  /** 0–1, or null when unknown. */
  ratio: number | null;
  text: string;
}
type OnProgress = (p: Progress) => void;

type Lib = typeof import('@huggingface/transformers');
let lib: Promise<Lib> | null = null;
const load = () => (lib ??= import('@huggingface/transformers'));

export async function hasWebGPU(): Promise<boolean> {
  try {
    const gpu = (navigator as Navigator & { gpu?: { requestAdapter(): Promise<unknown> } }).gpu;
    return Boolean(gpu && (await gpu.requestAdapter()));
  } catch {
    return false;
  }
}

/** Sums per-file download progress into one bar. */
function progressAdapter(onProgress?: OnProgress) {
  const files = new Map<string, { loaded: number; total: number }>();
  return (info: { status: string; file?: string; loaded?: number; total?: number }) => {
    if (!onProgress) return;
    if (info.status === 'progress' && info.file) {
      files.set(info.file, { loaded: info.loaded ?? 0, total: info.total ?? 0 });
      let loaded = 0;
      let total = 0;
      for (const f of files.values()) {
        loaded += f.loaded;
        total += f.total;
      }
      onProgress({ ratio: total ? loaded / total : null, text: info.file });
    } else if (info.status === 'ready') onProgress({ ratio: 1, text: 'ready' });
  };
}

interface Tokenizer {
  encode(text: string, opts?: { add_special_tokens?: boolean }): number[];
  decode(ids: number[]): string;
}
const tokenizers = new Map<string, Promise<Tokenizer>>();

export function loadTokenizer(id: string, onProgress?: OnProgress): Promise<Tokenizer> {
  let t = tokenizers.get(id);
  if (!t) {
    t = load().then((m) => m.AutoTokenizer.from_pretrained(id, { progress_callback: progressAdapter(onProgress) }) as unknown as Promise<Tokenizer>);
    t.catch(() => tokenizers.delete(id));
    tokenizers.set(id, t);
  }
  return t;
}

type Embedder = (texts: string[], opts: { pooling: 'mean'; normalize: boolean }) => Promise<{ tolist(): number[][] }>;
const embedders = new Map<string, Promise<Embedder>>();

export function loadEmbedder(id: string, onProgress?: OnProgress): Promise<Embedder> {
  let e = embedders.get(id);
  if (!e) {
    e = (async () => {
      const m = await load();
      const device = (await hasWebGPU()) ? 'webgpu' : 'wasm';
      return (await m.pipeline('feature-extraction', id, { device, dtype: 'q8', progress_callback: progressAdapter(onProgress) })) as unknown as Embedder;
    })();
    e.catch(() => embedders.delete(id));
    embedders.set(id, e);
  }
  return e;
}

export function isLoaded(id: string): boolean {
  return tokenizers.has(id) || embedders.has(id);
}
