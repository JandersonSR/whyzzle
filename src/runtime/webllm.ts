import type { Progress } from './transformers';

/** WebLLM: an open LLM running on the person's GPU (WebGPU). Loaded on demand. */

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}
export interface ChatOptions {
  temperature?: number;
  top_p?: number;
  max_tokens?: number;
}
interface Engine {
  chat: { completions: { create(req: { messages: ChatMessage[] } & ChatOptions): Promise<{ choices: { message: { content: string | null } }[]; usage?: { prompt_tokens: number; completion_tokens: number } }> } };
}

const engines = new Map<string, Promise<Engine>>();

export function loadChat(modelId: string, onProgress?: (p: Progress) => void): Promise<Engine> {
  let e = engines.get(modelId);
  if (!e) {
    e = import('@mlc-ai/web-llm').then(
      (m) =>
        m.CreateMLCEngine(modelId, {
          initProgressCallback: (r: { progress: number; text: string }) => onProgress?.({ ratio: r.progress, text: r.text }),
        }) as unknown as Promise<Engine>,
    );
    e.catch(() => engines.delete(modelId));
    engines.set(modelId, e);
  }
  return e;
}

export async function chatLocal(modelId: string, messages: ChatMessage[], opts: ChatOptions = {}) {
  const engine = await loadChat(modelId);
  const r = await engine.chat.completions.create({ messages, ...opts });
  return { text: r.choices[0]?.message.content ?? '', usage: r.usage };
}

export function isChatLoaded(modelId: string): boolean {
  return engines.has(modelId);
}
