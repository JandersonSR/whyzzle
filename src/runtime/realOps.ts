import type { Values } from '../engine/command';
import { evaluate } from '../engine/expr';
import { interpolate } from '../engine/text';
import type { RealDeps } from './adapters';
import type { ChatMessage } from './webllm';

/**
 * Real operations for data-driven lessons. Each op runs a real model and returns
 * names ("real…") that the lesson's declarative sim reads instead of its toy values:
 *
 *   "real": { "no-navegador": { "adapter": "declarative", "model": "…", "op": "tokens", "args": { … } } }
 *
 * The sim declares defaults in consts (real: false, realTokens: 0, …) and picks
 * with "real ? realTokens : estimate". Ops never see anything outside the lesson.
 */

export type Env = Record<string, unknown>;
export type RealOp = (env: Env, args: Record<string, unknown>, deps: RealDeps, values: Values) => Promise<Record<string, unknown>>;

const fill = (tpl: unknown, env: Env) => interpolate(String(tpl ?? ''), env as Record<string, string | number>);
const listFrom = (env: Env, name: unknown): unknown[] => (Array.isArray(env[String(name)]) ? (env[String(name)] as unknown[]) : []);

function messages(env: Env, args: Record<string, unknown>): ChatMessage[] {
  const m: ChatMessage[] = [];
  // systemFrom + systemBy: pick the system prompt by the value of a command option.
  const sys = args.systemFrom ? ((env[String(args.systemFrom)] as Record<string, string>) ?? {})[String(env[String(args.systemBy)])] : args.system;
  if (sys) m.push({ role: 'system', content: fill(sys, env) });
  m.push({ role: 'user', content: fill(args.user ?? '{text}', env) });
  return m;
}

const cosine = (a: number[], b: number[]) => {
  let d = 0;
  for (let i = 0; i < a.length; i++) d += a[i] * b[i];
  return d; // vectors come normalized
};

/** First {...} block of a reply, parsed; null when there is none or it doesn't parse. */
export function extractJson(text: string): Record<string, unknown> | null {
  const start = text.indexOf('{');
  const end = text.lastIndexOf('}');
  if (start < 0 || end <= start) return null;
  try {
    const v = JSON.parse(text.slice(start, end + 1));
    return v && typeof v === 'object' && !Array.isArray(v) ? (v as Record<string, unknown>) : null;
  } catch {
    return null;
  }
}

/** Minimal schema check: { field: "string" | "number" | "boolean" | "array" | "enum:a|b" }, all required. */
export function validate(obj: Record<string, unknown> | null, schema: Record<string, string>): string[] {
  if (!obj) return ['json'];
  const problems: string[] = [];
  for (const [field, type] of Object.entries(schema)) {
    const v = obj[field];
    if (v === undefined || v === null || v === '') problems.push(`missing:${field}`);
    else if (type.startsWith('enum:')) {
      if (!type.slice(5).split('|').includes(String(v))) problems.push(`enum:${field}`);
    } else if (type === 'array' ? !Array.isArray(v) : typeof v !== type) problems.push(`type:${field}`);
  }
  for (const k of Object.keys(obj)) if (!(k in schema)) problems.push(`extra:${k}`);
  return problems;
}

/** Deterministic tools the agent lesson can call. */
export function runTool(name: string, args: Record<string, unknown>, env: Env): string {
  if (name === 'calculadora' || name === 'calculator') {
    const expr = String(args.expressao ?? args.expression ?? '');
    if (!/^[\d\s+\-*/().,%]+$/.test(expr)) return 'erro: só números e + - * / ( )';
    try {
      return String(evaluate(expr.replace(/,/g, '.'), {}));
    } catch {
      return 'erro: expressão inválida';
    }
  }
  if (name === 'consultar' || name === 'lookup') {
    const table = (env.registros ?? env.records) as Record<string, string> | undefined;
    const key = String(args.chave ?? args.key ?? '').toLowerCase();
    const hit = table && Object.entries(table).find(([k]) => k.toLowerCase() === key);
    return hit ? hit[1] : 'não encontrado';
  }
  return `erro: ferramenta "${name}" não existe`;
}

export const OPS: Record<string, RealOp> = {
  async tokens(env, args, deps) {
    const tok = await deps.tokenizer(String(args.model ?? ''));
    const texts: Record<string, string> = {};
    for (const [name, src] of Object.entries((args.texts as Record<string, string>) ?? { realTokens: 'text' })) texts[name] = String(env[src] ?? '');
    const out: Record<string, unknown> = {};
    for (const [name, text] of Object.entries(texts)) {
      const ids = tok.encode(text, { add_special_tokens: false });
      out[name] = ids.length;
      out[`${name}Pieces`] = ids.slice(0, 60).map((id) => tok.decode([id]));
    }
    return out;
  },

  async embed(env, args, deps) {
    const items = listFrom(env, args.against).map((x) => (typeof x === 'string' ? x : String((x as Record<string, unknown>)[String(args.field ?? 'text')] ?? '')));
    const q = `${args.queryPrefix ?? ''}${String(env[String(args.query ?? 'text')] ?? '')}`;
    if (!deps.embed) throw new Error("embeddings need the in-browser executor");
    const vecs = await deps.embed([q, ...items.map((t) => `${args.passagePrefix ?? ''}${t}`)]);
    const sims = vecs.slice(1).map((v) => Math.round(cosine(vecs[0], v) * 1000) / 1000);
    const order = sims.map((s, i) => [s, i] as const).sort((a, b) => b[0] - a[0]);
    return { realSims: sims, realTop: order[0]?.[1] ?? -1, realTopSim: order[0]?.[0] ?? 0, realOrder: order.map((o) => o[1]) };
  },

  /** Similarity of every query against every document: realMatrix[q][d]. */
  async embedmatrix(env, args, deps) {
    if (!deps.embed) throw new Error('embeddings need the in-browser executor');
    const qs = listFrom(env, args.queries).map((x) => `${args.queryPrefix ?? ''}${String(x)}`);
    const ds = listFrom(env, args.against).map((x) => `${args.passagePrefix ?? ''}${String(x)}`);
    const vecs = await deps.embed([...qs, ...ds]);
    const Q = vecs.slice(0, qs.length);
    const D = vecs.slice(qs.length);
    return { realMatrix: Q.map((q) => D.map((d) => Math.round(cosine(q, d) * 1000) / 1000)) };
  },

  /** LLM as reranker: scores each candidate 0–10 for the question. */
  async rerank(env, args, deps) {
    const cands = listFrom(env, args.candidates).map(String);
    const q = String(env[String(args.query ?? 'text')] ?? '');
    const list = cands.map((c, i) => `[${i + 1}] ${c}`).join('\n');
    const reply = await deps.chat(
      [
        { role: 'system', content: fill(args.system, env) },
        { role: 'user', content: `${q}\n\n${list}` },
      ],
      { temperature: 0, max_tokens: 120 },
    );
    const obj = extractJson(reply);
    const raw = (obj?.scores as unknown[]) ?? [];
    const scores = cands.map((_, i) => Math.max(0, Math.min(10, Number(raw[i] ?? 0))) / 10);
    return { realRerank: scores, realRerankOk: Array.isArray(obj?.scores) };
  },

  async chat(env, args, deps, values) {
    const n = Math.max(1, Math.min(5, Number(values.samples ?? args.samples ?? 1)));
    const outs: string[] = [];
    for (let i = 0; i < n; i++) {
      outs.push(
        (
          await deps.chat(messages(env, args), {
            temperature: values.temp === undefined ? undefined : Number(values.temp),
            top_p: values.topP === undefined ? undefined : Number(values.topP),
            max_tokens: Number(values.maxTokens ?? args.maxTokens ?? 200),
          })
        ).trim(),
      );
    }
    return { realOutputs: outs, realOutput: outs[0] ?? '', realDistinct: new Set(outs).size };
  },

  async json(env, args, deps, values) {
    const text = (await deps.chat(messages(env, args), { temperature: Number(values.temp ?? 0), max_tokens: 300 })).trim();
    const obj = extractJson(text);
    const problems = validate(obj, (args.schema as Record<string, string>) ?? {});
    return { realOutput: text, realJson: obj ? JSON.stringify(obj, null, 1) : '', realValid: problems.length === 0, realProblems: problems };
  },

  async tools(env, args, deps, values) {
    const max = Math.max(1, Number(values.maxSteps ?? 4));
    const allowed = (values.tools as string[] | undefined) ?? (args.tools as string[]) ?? [];
    const history: ChatMessage[] = messages(env, args);
    const trace: string[] = [];
    let answer = '';
    let calls = 0;
    for (let step = 1; step <= max; step++) {
      const reply = (await deps.chat(history, { temperature: 0, max_tokens: 200 })).trim();
      const obj = extractJson(reply);
      if (obj && typeof obj.answer === 'string') {
        answer = obj.answer;
        trace.push(`+ ${answer}`);
        break;
      }
      if (obj && typeof obj.tool === 'string') {
        calls++;
        const name = obj.tool;
        const a = (obj.args as Record<string, unknown>) ?? {};
        trace.push(`$ ${name}(${JSON.stringify(a)})`);
        const result = allowed.includes(name) ? runTool(name, a, env) : `erro: ferramenta "${name}" não está liberada`;
        trace.push(result.startsWith('erro') ? `! ${result}` : `~ ${result}`);
        history.push({ role: 'assistant', content: reply }, { role: 'user', content: `Resultado de ${name}: ${result}` });
        continue;
      }
      trace.push(`? ${reply.slice(0, 160)}`);
      history.push({ role: 'assistant', content: reply }, { role: 'user', content: fill(args.nudge ?? 'Responda só com JSON: {"tool":…,"args":…} ou {"answer":…}.', env) });
    }
    return { realTrace: trace, realAnswer: answer, realCalls: calls, realLimit: !answer };
  },
};
