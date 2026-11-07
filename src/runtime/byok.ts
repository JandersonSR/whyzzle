import type { ChatMessage, ChatOptions } from './webllm';

/**
 * "Sua chave": the person's own API key, used straight from the browser.
 * The key never goes to a Whyzzle server (there is none). By default it lives
 * only in memory for this tab; "remember on this device" stores it in localStorage.
 *
 * Browser access per provider (checked nov/2026):
 *  - Anthropic: needs the "anthropic-dangerous-direct-browser-access: true" header.
 *  - OpenAI: recent reports show /chat/completions refusing browser calls while
 *    /responses and /models still work, so we use the Responses API.
 *  - Google Gemini: generateContent with the x-goog-api-key header.
 *  - OpenAI-compatible (e.g. OpenRouter): /chat/completions at a base URL the person sets.
 */

export type ProviderId = 'anthropic' | 'openai' | 'gemini' | 'compatible';
export const PROVIDERS: { id: ProviderId; label: string; keyHint: string; defaultBase?: string }[] = [
  { id: 'anthropic', label: 'Anthropic (Claude)', keyHint: 'sk-ant-…' },
  { id: 'openai', label: 'OpenAI', keyHint: 'sk-…' },
  { id: 'gemini', label: 'Google Gemini', keyHint: 'AIza…' },
  { id: 'compatible', label: 'OpenAI-compatible (OpenRouter…)', keyHint: 'sk-or-…', defaultBase: 'https://openrouter.ai/api/v1' },
];

export interface KeyConfig {
  provider: ProviderId;
  key: string;
  model: string;
  baseUrl?: string;
  remember: boolean;
}

export interface HttpRequest {
  url: string;
  init: RequestInit & { headers: Record<string, string> };
}

const STORE = 'whyzzle:apikey';
let memory: KeyConfig | null = null;

export function getKeyConfig(): KeyConfig | null {
  if (memory) return memory;
  try {
    const raw = localStorage.getItem(STORE);
    if (raw) memory = JSON.parse(raw) as KeyConfig;
  } catch {
    // Unreadable storage: behave as if no key is saved.
  }
  return memory;
}

export function saveKeyConfig(cfg: KeyConfig): void {
  memory = cfg;
  try {
    if (cfg.remember) localStorage.setItem(STORE, JSON.stringify(cfg));
    else localStorage.removeItem(STORE);
  } catch {
    // Storage blocked: the key stays in memory for this tab only.
  }
}

export function forgetKey(): void {
  memory = null;
  try {
    localStorage.removeItem(STORE);
  } catch {
    // nothing to do
  }
}

const trimBase = (u: string) => u.replace(/\/+$/, '');

export function listModelsRequest(c: Pick<KeyConfig, 'provider' | 'key' | 'baseUrl'>): HttpRequest {
  switch (c.provider) {
    case 'anthropic':
      return { url: 'https://api.anthropic.com/v1/models?limit=100', init: { method: 'GET', headers: anthropicHeaders(c.key) } };
    case 'openai':
      return { url: 'https://api.openai.com/v1/models', init: { method: 'GET', headers: { authorization: `Bearer ${c.key}` } } };
    case 'gemini':
      return { url: 'https://generativelanguage.googleapis.com/v1beta/models?pageSize=200', init: { method: 'GET', headers: { 'x-goog-api-key': c.key } } };
    case 'compatible':
      return { url: `${trimBase(c.baseUrl || '')}/models`, init: { method: 'GET', headers: { authorization: `Bearer ${c.key}` } } };
  }
}

function anthropicHeaders(key: string): Record<string, string> {
  return {
    'x-api-key': key,
    'anthropic-version': '2023-06-01',
    'anthropic-dangerous-direct-browser-access': 'true',
    'content-type': 'application/json',
  };
}

export function parseModelList(provider: ProviderId, body: unknown): string[] {
  const b = body as { data?: { id: string }[]; models?: { name: string; supportedGenerationMethods?: string[] }[] };
  if (provider === 'gemini') {
    return (b.models ?? []).filter((m) => !m.supportedGenerationMethods || m.supportedGenerationMethods.includes('generateContent')).map((m) => m.name.replace(/^models\//, ''));
  }
  return (b.data ?? []).map((m) => m.id);
}

/** A sensible default: the smallest fast model the account offers. */
export function suggestModel(provider: ProviderId, models: string[]): string {
  const prefs: Record<ProviderId, RegExp[]> = {
    anthropic: [/haiku/i, /sonnet/i],
    openai: [/^gpt-[\d.]+-mini$/i, /mini/i, /^gpt-/i],
    gemini: [/flash-lite/i, /flash/i],
    compatible: [/haiku|mini|flash/i],
  };
  for (const re of prefs[provider]) {
    const m = models.find((x) => re.test(x));
    if (m) return m;
  }
  return models[0] ?? '';
}

export function chatRequest(c: KeyConfig, messages: ChatMessage[], opts: ChatOptions = {}): HttpRequest {
  const system = messages.filter((m) => m.role === 'system').map((m) => m.content).join('\n');
  const turns = messages.filter((m) => m.role !== 'system');
  const max = opts.max_tokens ?? 512;
  switch (c.provider) {
    case 'anthropic':
      return {
        url: 'https://api.anthropic.com/v1/messages',
        init: {
          method: 'POST',
          headers: anthropicHeaders(c.key),
          body: JSON.stringify({ model: c.model, max_tokens: max, ...(system ? { system } : {}), messages: turns, ...(opts.temperature !== undefined ? { temperature: opts.temperature } : {}) }),
        },
      };
    case 'openai':
      return {
        url: 'https://api.openai.com/v1/responses',
        init: {
          method: 'POST',
          headers: { authorization: `Bearer ${c.key}`, 'content-type': 'application/json' },
          body: JSON.stringify({ model: c.model, ...(system ? { instructions: system } : {}), input: turns.map((m) => ({ role: m.role, content: m.content })), max_output_tokens: max }),
        },
      };
    case 'gemini':
      return {
        url: `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(c.model)}:generateContent`,
        init: {
          method: 'POST',
          headers: { 'x-goog-api-key': c.key, 'content-type': 'application/json' },
          body: JSON.stringify({
            ...(system ? { systemInstruction: { parts: [{ text: system }] } } : {}),
            contents: turns.map((m) => ({ role: m.role === 'assistant' ? 'model' : 'user', parts: [{ text: m.content }] })),
            generationConfig: { maxOutputTokens: max, ...(opts.temperature !== undefined ? { temperature: opts.temperature } : {}) },
          }),
        },
      };
    case 'compatible':
      return {
        url: `${trimBase(c.baseUrl || '')}/chat/completions`,
        init: {
          method: 'POST',
          headers: { authorization: `Bearer ${c.key}`, 'content-type': 'application/json' },
          body: JSON.stringify({ model: c.model, messages, max_tokens: max, ...(opts.temperature !== undefined ? { temperature: opts.temperature } : {}) }),
        },
      };
  }
}

export function parseChat(provider: ProviderId, body: unknown): string {
  const b = body as Record<string, unknown>;
  if (provider === 'anthropic') {
    return ((b.content as { type: string; text?: string }[]) ?? []).filter((p) => p.type === 'text').map((p) => p.text).join('');
  }
  if (provider === 'openai') {
    if (typeof b.output_text === 'string') return b.output_text;
    return ((b.output as { type: string; content?: { type: string; text?: string }[] }[]) ?? [])
      .filter((o) => o.type === 'message')
      .flatMap((o) => o.content ?? [])
      .filter((p) => p.type === 'output_text')
      .map((p) => p.text)
      .join('');
  }
  if (provider === 'gemini') {
    const parts = ((b.candidates as { content?: { parts?: { text?: string }[] } }[]) ?? [])[0]?.content?.parts ?? [];
    return parts.map((p) => p.text ?? '').join('');
  }
  return ((b.choices as { message?: { content?: string } }[]) ?? [])[0]?.message?.content ?? '';
}

export class ByokError extends Error {
  constructor(
    public kind: 'blocked' | 'auth' | 'quota' | 'model' | 'other',
    message: string,
  ) {
    super(message);
  }
}

async function send(req: HttpRequest): Promise<unknown> {
  let res: Response;
  try {
    res = await fetch(req.url, req.init);
  } catch (e) {
    // A network-level failure from a browser is almost always CORS: the provider refuses browser calls.
    throw new ByokError('blocked', (e as Error).message);
  }
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const msg = JSON.stringify(body).slice(0, 300);
    if (res.status === 401 || res.status === 403) throw new ByokError('auth', msg);
    if (res.status === 429) throw new ByokError('quota', msg);
    if (res.status === 404 || res.status === 400) throw new ByokError('model', msg);
    throw new ByokError('other', `${res.status} ${msg}`);
  }
  return body;
}

export async function listModels(c: Pick<KeyConfig, 'provider' | 'key' | 'baseUrl'>): Promise<string[]> {
  return parseModelList(c.provider, await send(listModelsRequest(c)));
}

export async function chatByok(c: KeyConfig, messages: ChatMessage[], opts?: ChatOptions): Promise<string> {
  return parseChat(c.provider, await send(chatRequest(c, messages, opts)));
}
