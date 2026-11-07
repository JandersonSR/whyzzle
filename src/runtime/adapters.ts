import type { Values } from '../engine/command';
import { getModel, type ModelCtx, type ModelResult } from '../engine/registry';
import type { Lang } from '../engine/schema';
import type { PromptResult } from '../models/promptGrader';
import type { Tok, TokenizerResult } from '../models/tokenizer';
import { computeEnv } from '../models/declarative';
import { OPS } from './realOps';
import type { ChatMessage, ChatOptions } from './webllm';

/**
 * Adapters turn a real model's output into the same result shape the step's
 * scene already draws, so scenes don't care which executor ran.
 * Dependencies are injected so tests can run without the network.
 */

export interface RealDeps {
  embed?(texts: string[]): Promise<number[][]>;
  tokenizer(model: string): Promise<{ encode(text: string, o?: { add_special_tokens?: boolean }): number[]; decode(ids: number[]): string }>;
  chat(messages: ChatMessage[], opts?: ChatOptions): Promise<string>;
}

export interface RealInfo {
  executor: 'no-navegador' | 'sua-chave';
  model: string;
}

export interface RealConfig {
  op?: string;
  args?: Record<string, unknown>;
}

export interface RealAdapter {
  id: string;
  run(values: Values, ctx: ModelCtx, deps: RealDeps, info: RealInfo, cfg?: RealConfig): Promise<ModelResult & { real: RealInfo }>;
}

const isLetter = (s: string) => /\p{L}/u.test(s);

/** Labels each real token the way the toy tokenizer scene expects. */
export function classifyTokens(ids: number[], pieces: string[]): Tok[] {
  return pieces.map((p, i) => {
    const core = p.replace(/^\s+/, '');
    const space = i > 0 && /^\s/.test(p);
    let kind: Tok['kind'] = 'word';
    if (/^\d+$/.test(core)) kind = 'num';
    else if (!isLetter(core)) kind = 'punct';
    else {
      const prev = pieces[i - 1];
      const next = pieces[i + 1];
      const joinsPrev = i > 0 && !/^\s/.test(p) && prev !== undefined && isLetter(prev.slice(-1));
      const joinsNext = next !== undefined && !/^\s/.test(next) && isLetter(next[0] ?? '');
      if (joinsPrev || joinsNext) kind = 'piece';
    }
    return { text: core || p, space, kind, id: ids[i] };
  });
}

const tokenize: RealAdapter = {
  id: 'tokenize',
  async run(values, _ctx, deps, info) {
    const tok = await deps.tokenizer(info.model);
    const text = String(values.text);
    const ids = tok.encode(text, { add_special_tokens: false });
    const tokens = classifyTokens(
      ids,
      ids.map((id) => tok.decode([id])),
    );
    const window = Number(values.window);
    const overflow = Math.max(0, tokens.length - window);
    const flags: string[] = [];
    if (overflow > 0) flags.push('overflow');
    if (tokens.some((t) => t.kind === 'piece')) flags.push('split');
    const lost = tokens
      .slice(0, overflow)
      .map((t) => (t.space ? ' ' : '') + t.text)
      .join('')
      .trim();
    const r: TokenizerResult & { real: RealInfo } = {
      flags,
      vars: { count: tokens.length, window, lost: overflow, lostText: lost.length > 40 ? lost.slice(0, 40) + '…' : lost, model: info.model },
      tokens,
      count: tokens.length,
      window,
      overflow,
      chars: text.length,
      real: info,
    };
    return r;
  },
};

const ANSWER_IN: Record<Lang, string> = { pt: 'Responda em português do Brasil.', en: 'Answer in English.' };
const ROLE: Record<Lang, string> = { pt: 'Você é {role}.', en: 'You are {role}.' };
const LINES: Record<Lang, { audience: string; format: string; tone: string }> = {
  pt: { audience: 'Público: {v}.', format: 'Formato: {v}.', tone: 'Tom: {v}.' },
  en: { audience: 'Audience: {v}.', format: 'Format: {v}.', tone: 'Tone: {v}.' },
};

/** Builds the real prompt from the same fields the Buttons mode edits. */
export function buildPrompt(values: Values, lang: Lang, toneLabel?: string): ChatMessage[] {
  const system = [values.role ? ROLE[lang].replace('{role}', String(values.role)) : '', ANSWER_IN[lang]].filter(Boolean).join(' ');
  const parts = [String(values.text)];
  if (values.audience) parts.push(LINES[lang].audience.replace('{v}', String(values.audience)));
  if (values.format) parts.push(LINES[lang].format.replace('{v}', String(values.format)));
  if (values.tone) parts.push(LINES[lang].tone.replace('{v}', toneLabel ?? String(values.tone)));
  return [
    { role: 'system', content: system },
    { role: 'user', content: parts.join('\n') },
  ];
}

const chatPrompt: RealAdapter = {
  id: 'chat-prompt',
  async run(values, ctx, deps, info) {
    // The toy grader still scores how clear the request is; the answer is real.
    const sim = getModel('prompt-grader').run(values, ctx) as PromptResult;
    const text = (await deps.chat(buildPrompt(values, ctx.lang), { temperature: 0.7, max_tokens: 350 })).trim();
    const lines = text.split(/\n+/).map((l) => l.trim()).filter(Boolean);
    const bullets = lines.length > 1 && lines.every((l) => /^([-*•]|\d+[.)])\s/.test(l));
    const sentences = bullets ? lines.map((l) => l.replace(/^([-*•]|\d+[.)])\s+/, '')) : [lines.join(' ')];
    // Did the pasted instruction win? The real model either stayed on topic or not.
    const topic = (ctx.text.topicWords as string[]).map((w) => w.toLowerCase());
    const stayed = topic.some((w) => text.toLowerCase().includes(w));
    const injected = sim.injected && !stayed;
    const flags = sim.flags.filter((f) => f !== 'injected' && f !== 'offTopic');
    if (injected) flags.push('injected');
    if (sim.injected && stayed) flags.push('resisted');
    return { ...sim, flags, opener: null, sentences, bullets, injected, offTopic: false, vars: { ...sim.vars, model: info.model }, real: info };
  },
};

/** Runs a real op, then the lesson's declarative sim with the real values injected. */
const declarativeReal: RealAdapter = {
  id: 'declarative',
  async run(values, ctx, deps, info, cfg) {
    const op = OPS[cfg?.op ?? ''];
    if (!op) throw new Error(`unknown real op "${cfg?.op}"`);
    // The op sees what the lesson computes before cases (e.g. chunks), in simulated terms.
    const env = computeEnv(values, ctx);
    const injected = await op(env, { model: info.model, ...(cfg?.args ?? {}) }, deps, values);
    const r = getModel('declarative').run({ ...values, ...injected, real: true } as Values, ctx);
    return { ...r, real: info };
  },
};

export const ADAPTERS: Record<string, RealAdapter> = { tokenize, 'chat-prompt': chatPrompt, declarative: declarativeReal };
