/**
 * A tiny, safe expression language for data-driven lessons (no eval).
 *
 *   numbers 1.5 · strings 'a' "b" · lists [1, 2] · identifiers a.b · x[0]
 *   + - * / % **  == != < <= > >=  && || !  cond ? a : b
 *   functions: see FUNCS below
 *
 * Lessons use it in step.json → data (compute, cases, widgets).
 */

export type Value = number | string | boolean | null | undefined | Value[] | { [k: string]: Value };
export type Env = Record<string, unknown>;

type Node =
  | { t: 'num'; v: number }
  | { t: 'str'; v: string }
  | { t: 'list'; items: Node[] }
  | { t: 'id'; name: string }
  | { t: 'member'; obj: Node; key: string }
  | { t: 'index'; obj: Node; index: Node }
  | { t: 'call'; name: string; args: Node[] }
  | { t: 'unary'; op: string; arg: Node }
  | { t: 'bin'; op: string; l: Node; r: Node }
  | { t: 'cond'; c: Node; a: Node; b: Node };

export class ExprError extends Error {}

interface Tok {
  k: 'num' | 'str' | 'id' | 'op' | 'end';
  v: string;
}

const OPS = ['**', '==', '!=', '<=', '>=', '&&', '||', '+', '-', '*', '/', '%', '<', '>', '!', '?', ':', '(', ')', '[', ']', ',', '.'];

function lex(src: string): Tok[] {
  const out: Tok[] = [];
  let i = 0;
  while (i < src.length) {
    const c = src[i];
    if (/\s/.test(c)) {
      i++;
      continue;
    }
    if (/[0-9]/.test(c) || (c === '.' && /[0-9]/.test(src[i + 1] ?? ''))) {
      let j = i;
      while (j < src.length && /[0-9._]/.test(src[j])) j++;
      out.push({ k: 'num', v: src.slice(i, j).replace(/_/g, '') });
      i = j;
      continue;
    }
    if (c === "'" || c === '"') {
      let j = i + 1;
      let s = '';
      while (j < src.length && src[j] !== c) s += src[j++];
      if (j >= src.length) throw new ExprError(`unterminated string in: ${src}`);
      out.push({ k: 'str', v: s });
      i = j + 1;
      continue;
    }
    if (/[A-Za-z_$]/.test(c)) {
      let j = i;
      while (j < src.length && /[A-Za-z0-9_$]/.test(src[j])) j++;
      out.push({ k: 'id', v: src.slice(i, j) });
      i = j;
      continue;
    }
    const op = OPS.find((o) => src.startsWith(o, i));
    if (!op) throw new ExprError(`unexpected "${c}" in: ${src}`);
    out.push({ k: 'op', v: op });
    i += op.length;
  }
  out.push({ k: 'end', v: '' });
  return out;
}

const BIN: Record<string, number> = { '||': 1, '&&': 2, '==': 3, '!=': 3, '<': 4, '<=': 4, '>': 4, '>=': 4, '+': 5, '-': 5, '*': 6, '/': 6, '%': 6, '**': 8 };

function parse(src: string): Node {
  const toks = lex(src);
  let p = 0;
  const peek = () => toks[p];
  const eat = (v?: string) => {
    const t = toks[p];
    if (v !== undefined && t.v !== v) throw new ExprError(`expected "${v}" but got "${t.v || 'end'}" in: ${src}`);
    p++;
    return t;
  };

  function primary(): Node {
    const t = eat();
    if (t.k === 'num') return { t: 'num', v: Number(t.v) };
    if (t.k === 'str') return { t: 'str', v: t.v };
    if (t.k === 'op' && t.v === '(') {
      const e = expr();
      eat(')');
      return e;
    }
    if (t.k === 'op' && t.v === '[') {
      const items: Node[] = [];
      if (peek().v !== ']') {
        do items.push(expr());
        while (peek().v === ',' && eat());
      }
      eat(']');
      return { t: 'list', items };
    }
    if (t.k === 'id') {
      if (peek().v === '(') {
        eat('(');
        const args: Node[] = [];
        if (peek().v !== ')') {
          do args.push(expr());
          while (peek().v === ',' && eat());
        }
        eat(')');
        return { t: 'call', name: t.v, args };
      }
      return { t: 'id', name: t.v };
    }
    throw new ExprError(`unexpected "${t.v || 'end'}" in: ${src}`);
  }

  function postfix(): Node {
    let n = primary();
    for (;;) {
      if (peek().v === '.') {
        eat('.');
        const k = eat();
        if (k.k !== 'id' && k.k !== 'num') throw new ExprError(`bad member access in: ${src}`);
        n = { t: 'member', obj: n, key: k.v };
      } else if (peek().v === '[') {
        eat('[');
        const index = expr();
        eat(']');
        n = { t: 'index', obj: n, index };
      } else return n;
    }
  }

  function unary(): Node {
    if (peek().k === 'op' && (peek().v === '!' || peek().v === '-')) {
      const op = eat().v;
      return { t: 'unary', op, arg: unary() };
    }
    return postfix();
  }

  function binary(min: number): Node {
    let l = unary();
    for (;;) {
      const t = peek();
      const prec = t.k === 'op' ? BIN[t.v] : undefined;
      if (prec === undefined || prec < min) return l;
      eat();
      // ** is right-associative
      const r = binary(t.v === '**' ? prec : prec + 1);
      l = { t: 'bin', op: t.v, l, r };
    }
  }

  function expr(): Node {
    const c = binary(1);
    if (peek().v === '?') {
      eat('?');
      const a = expr();
      eat(':');
      const b = expr();
      return { t: 'cond', c, a, b };
    }
    return c;
  }

  const n = expr();
  if (peek().k !== 'end') throw new ExprError(`unexpected "${peek().v}" in: ${src}`);
  return n;
}

const num = (v: unknown) => (typeof v === 'number' ? v : Number(v));
const arr = (v: unknown): Value[] => (Array.isArray(v) ? (v as Value[]) : []);

/** Whitelisted functions. `rng` comes from the evaluation context. */
const FUNCS: Record<string, (args: Value[], rng: () => number) => Value> = {
  min: (a) => Math.min(...a.map(num)),
  max: (a) => Math.max(...a.map(num)),
  pow: ([b, e]) => Math.pow(num(b), num(e)),
  sqrt: ([x]) => Math.sqrt(num(x)),
  abs: ([x]) => Math.abs(num(x)),
  round: ([x, d]) => {
    const f = Math.pow(10, num(d ?? 0));
    return Math.round(num(x) * f) / f;
  },
  floor: ([x]) => Math.floor(num(x)),
  ceil: ([x]) => Math.ceil(num(x)),
  clamp: ([x, lo, hi]) => Math.min(num(hi), Math.max(num(lo), num(x))),
  log10: ([x]) => Math.log10(num(x)),
  len: ([x]) => (typeof x === 'string' ? x.length : arr(x).length),
  includes: ([list, x]) => (typeof list === 'string' ? list.includes(String(x)) : arr(list).some((v) => v === x)),
  range: ([n, start]) => Array.from({ length: Math.max(0, Math.floor(num(n))) }, (_, i) => i + num(start ?? 0)),
  fill: ([n, v]) => Array.from({ length: Math.max(0, Math.floor(num(n))) }, () => v),
  sum: ([list]) => arr(list).reduce<number>((s, v) => s + num(v), 0),
  count: ([list, v]) => arr(list).filter((x) => x === v).length,
  join: ([list, sep]) => arr(list).join(String(sep ?? ', ')),
  lower: ([s]) => String(s ?? '').toLowerCase(),
  str: ([v]) => String(v ?? ''),
  number: ([v]) => num(v),
  concat: (a) => a.flatMap((x) => (Array.isArray(x) ? x : [x])),
  slice: ([list, a, b]) => arr(list).slice(num(a), b === undefined ? undefined : num(b)),
  /** Text helpers for data-driven lessons. */
  words: ([s]) => String(s ?? '').trim().split(/\s+/).filter(Boolean).length,
  nonascii: ([s]) => Array.from(String(s ?? '')).filter((c) => c.codePointAt(0)! > 127).length,
  /** Jaccard overlap of the words (accents and case ignored, short words skipped): 0–1. */
  overlap: ([a, b, stop]) => {
    const norm = (x: Value) =>
      String(x ?? '')
        .toLowerCase()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '');
    const skip = new Set(arr(stop).map(norm));
    const set = (x: Value) => new Set(norm(x).split(/[^a-z0-9]+/).filter((w) => w.length > 2 && !skip.has(w)));
    const A = set(a);
    const B = set(b);
    if (!A.size || !B.size) return 0;
    let inter = 0;
    for (const w of A) if (B.has(w)) inter++;
    return inter / (A.size + B.size - inter);
  },
  overlapall: ([s, list, stop], rng) => arr(list).map((x) => FUNCS.overlap([s, x, stop], rng) as number),
  argmax: ([list]) => {
    const l = arr(list).map(num);
    return l.length ? l.indexOf(Math.max(...l)) : -1;
  },
  /** Indices sorted by value, highest first. */
  order: ([list]) =>
    arr(list)
      .map((v, i) => [num(v), i] as const)
      .sort((a, b) => b[0] - a[0])
      .map((x) => x[1]),
  pickall: ([list, idxs]) => arr(idxs).map((i) => arr(list)[num(i)]),
  zip: (lists) => {
    const ls = lists.map(arr);
    const n = Math.min(...ls.map((l) => l.length));
    return Array.from({ length: n }, (_, i) => ls.map((l) => l[i]));
  },
  scale: ([list, k]) => arr(list).map((v) => num(v) * num(k)),
  clampall: ([list, lo, hi]) => arr(list).map((v) => Math.min(num(hi), Math.max(num(lo), num(v)))),
  affine: ([list, a, b]) => arr(list).map((v) => num(a) + num(b) * num(v)),
  roundall: ([list, d]) => arr(list).map((v) => Math.round(num(v) * 10 ** num(d ?? 0)) / 10 ** num(d ?? 0)),
  /** n items: `a` at index idx, `b` elsewhere (e.g. row tones). */
  mark: ([n, idx, a, b]) => Array.from({ length: Math.max(0, num(n)) }, (_, i) => (i === num(idx) ? a : b)),
  unique: ([list]) => Array.from(new Set(arr(list))),
  /** n picks (with replacement) among the first k items. */
  sample: ([list, n, k], rng) => {
    const l = arr(list).slice(0, Math.max(1, num(k)));
    return Array.from({ length: Math.max(0, num(n)) }, () => l[Math.floor(rng() * l.length)]);
  },
  /** Cuts each text to n words, adding "…" when cut. */
  truncwords: ([list, n]) =>
    arr(list).map((s) => {
      const w = String(s ?? '').split(/\s+/);
      return w.length > num(n) ? w.slice(0, Math.max(1, num(n))).join(' ') + '…' : String(s ?? '');
    }),
  /** Text → word chunks of `size` words with `overlap` words shared between neighbors. */
  chunks: ([text, size, overlap]) => {
    const w = String(text ?? '').split(/\s+/).filter(Boolean);
    const n = Math.max(1, Math.floor(num(size)));
    const o = Math.min(n - 1, Math.max(0, Math.floor(num(overlap ?? 0))));
    const out: string[] = [];
    for (let i = 0; i < w.length; i += n - o) {
      out.push(w.slice(i, i + n).join(' '));
      if (i + n >= w.length) break;
    }
    return out;
  },
  lines: ([text]) => String(text ?? '').split(/\n/),
  /** Drops items that contain any of the patterns (case-insensitive). */
  dropmatching: ([list, patterns]) => {
    const ps = arr(patterns).map((p) => String(p).toLowerCase());
    return arr(list).filter((x) => !ps.some((p) => String(x).toLowerCase().includes(p)));
  },
  trimall: ([list]) => arr(list).map((x) => String(x ?? '').trim()).filter((x) => x !== ''),
  /** Re-joins words broken across lines with a hyphen ("ante-\ncedência"). */
  unhyphen: ([text]) => String(text ?? '').replace(/(\p{L})-\n(\p{L})/gu, '$1$2'),
  /** BM25 keyword scores of a query against documents, scaled so the best is 1. */
  bm25: ([query, docs, stop]) => {
    const norm = (x: unknown) => String(x ?? '').toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '');
    const skip = new Set(arr(stop).map(norm));
    const toks = (x: unknown) => norm(x).split(/[^a-z0-9]+/).filter((t) => t.length > 1 && !skip.has(t));
    const D = arr(docs).map(toks);
    const N = D.length || 1;
    const avg = D.reduce((s, d) => s + d.length, 0) / N || 1;
    const q = Array.from(new Set(toks(query)));
    const k1 = 1.2;
    const b = 0.75;
    const scores = D.map((d) =>
      q.reduce((sum, term) => {
        const tf = d.filter((t) => t === term).length;
        if (!tf) return sum;
        const df = D.filter((x) => x.includes(term)).length;
        const idf = Math.log(1 + (N - df + 0.5) / (df + 0.5));
        return sum + (idf * tf * (k1 + 1)) / (tf + k1 * (1 - b + (b * d.length) / avg));
      }, 0),
    );
    const max = Math.max(...scores, 0);
    return scores.map((s) => (max ? Math.round((s / max) * 1000) / 1000 : 0));
  },
  /** Each value divided by the largest (0 when all are 0). */
  normalizeall: ([list]) => {
    const l = arr(list).map(num);
    const max = Math.max(...l, 0);
    return l.map((v) => (max ? v / max : 0));
  },
  /** Rescales to 0–1 by min and max (all 0 when flat). */
  minmax: ([list]) => {
    const l = arr(list).map(num);
    const lo = Math.min(...l);
    const hi = Math.max(...l);
    return l.map((v) => (hi > lo ? (v - lo) / (hi - lo) : 0));
  },
  minmaxall: ([m], rng) => arr(m).map((row) => FUNCS.minmax([row], rng)),
  bm25all: ([queries, docs, stop], rng) => arr(queries).map((q) => FUNCS.bm25([q, docs, stop], rng)),
  blendall: ([m1, m2, a], rng) => arr(m1).map((row, i) => FUNCS.blend([row, arr(m2)[i], a], rng)),
  /** Indices of the k best values; scores of 0 or less are never "found". */
  topk: ([list, k], rng) =>
    (FUNCS.order([list], rng) as Value[]).filter((i) => num(arr(list)[num(i)]) > 0).slice(0, Math.max(0, num(k))),
  /** a[i] × b[i], item by item. */
  mul: ([a, b]) => arr(a).map((v, i) => num(v) * num(arr(b)[i] ?? 0)),
  /** Running total: [1, 2, 3] → [1, 3, 6]. */
  cumsum: ([list]) => {
    let t = 0;
    return arr(list).map((v) => (t += num(v)));
  },
  /** map[key] for each key (default when missing). */
  lookupall: ([map, keys, dflt]) => {
    const m = map && typeof map === 'object' ? (map as Record<string, Value>) : {};
    return arr(keys).map((k) => (Object.prototype.hasOwnProperty.call(m, String(k)) ? m[String(k)] : (dflt ?? null)));
  },
  /** True when the text contains any of the keywords (case-insensitive). */
  containsany: ([text, keys]) => arr(keys).some((k) => String(text ?? '').toLowerCase().includes(String(k).toLowerCase())),
  /** Largest value of each row. */
  maxall: ([m]) => arr(m).map((row) => Math.max(...arr(row).map(num))),
  /** Item ≥ x / item < x, as booleans. */
  geall: ([list, x]) => arr(list).map((v) => num(v) >= num(x)),
  ltall: ([list, x]) => arr(list).map((v) => num(v) < num(x)),
  /** Rows of a matrix (or items of a list) at the given indices. */
  pickrows: ([m, idxs]) => arr(idxs).map((i) => arr(m)[num(i)]),
  /** Per item: a[i] where mask[i] is truthy, else b[i] (a or b may be a single value). */
  where: ([mask, a, b]) => arr(mask).map((m, i) => (m ? (Array.isArray(a) ? a[i] : a) : Array.isArray(b) ? b[i] : b) as Value),
  /** a[i] + b[i], item by item. */
  addall: ([a, b]) => arr(a).map((v, i) => num(v) + num(Array.isArray(b) ? b[i] : b)),
  /** Items whose mask is truthy. */
  maskfilter: ([list, mask]) => arr(list).filter((_, i) => Boolean(arr(mask)[i])),
  /** Number as text with fixed decimals and the language's separators: fmt(1234.5, 2, 'pt') → "1.234,50". */
  fmt: ([x, d, lang]) =>
    num(x).toLocaleString(String(lang ?? 'pt') === 'en' ? 'en-US' : 'pt-BR', { minimumFractionDigits: num(d ?? 0), maximumFractionDigits: num(d ?? 0) }),
  /** 1 for each item that is in the set, else 0. */
  memberall: ([list, set]) => arr(list).map((x) => (arr(set).includes(x) ? 1 : 0)),
  /** Prefixes each text: `yes` when it contains any pattern (case-insensitive), else `no`. */
  tagmatching: ([list, patterns, yes, no]) => {
    const ps = arr(patterns).map((p) => String(p).toLowerCase());
    return arr(list).map((x) => (ps.some((p) => String(x).toLowerCase().includes(p)) ? String(yes ?? '') : String(no ?? '')) + String(x));
  },
  /** recall@k of each row against its gold list. */
  recallall: ([m, golds, k], rng) => arr(m).map((row, i) => FUNCS.recall([FUNCS.topk([row, k], rng), arr(golds)[i]], rng) as number),
  split: ([text, sep]) => String(text ?? '').split(String(sep)).map((x) => x.trim()).filter(Boolean),
  anyincludes: ([list, s]) => arr(list).some((x) => String(x).includes(String(s))),
  /** a·x + b·y, item by item. */
  blend: ([x, y, a]) => arr(x).map((v, i) => num(a) * num(v) + (1 - num(a)) * num(arr(y)[i] ?? 0)),
  /** map[key] when present, else the default. */
  lookup: ([map, key, dflt]) => {
    const m = map && typeof map === 'object' ? (map as Record<string, Value>) : {};
    return Object.prototype.hasOwnProperty.call(m, String(key)) ? m[String(key)] : dflt;
  },
  /** Numbers cited as [n] in a text. */
  refs: ([text]) => Array.from(String(text ?? '').matchAll(/\[(\d+)\]/g)).map((m) => Number(m[1])),
  /** Fraction of the gold ids found in the top-k list (recall@k). */
  recall: ([top, gold]) => {
    const g = arr(gold);
    if (!g.length) return 1;
    return g.filter((x) => arr(top).includes(x)).length / g.length;
  },
  endsany: ([s, list]) => arr(list).some((x) => String(s ?? '').trimEnd().endsWith(String(x))),
  /** Seeded random in [0, 1): deterministic in previews and tests. */
  rand: (_a, rng) => rng(),
  pick: ([list], rng) => {
    const l = arr(list);
    return l[Math.floor(rng() * l.length)];
  },
};

function lookup(env: Env, name: string): Value {
  if (name === 'true') return true;
  if (name === 'false') return false;
  if (name === 'null') return null;
  if (!Object.prototype.hasOwnProperty.call(env, name)) throw new ExprError(`unknown name "${name}"`);
  return env[name] as Value;
}

function ev(n: Node, env: Env, rng: () => number): Value {
  switch (n.t) {
    case 'num':
      return n.v;
    case 'str':
      return n.v;
    case 'list':
      return n.items.map((i) => ev(i, env, rng));
    case 'id':
      return lookup(env, n.name);
    case 'member': {
      const o = ev(n.obj, env, rng);
      if (o === null || o === undefined) return undefined;
      if (n.key === 'length' && (Array.isArray(o) || typeof o === 'string')) return o.length;
      return Object.prototype.hasOwnProperty.call(o, n.key) ? (o as Record<string, Value>)[n.key] : undefined;
    }
    case 'index': {
      const o = ev(n.obj, env, rng);
      const i = ev(n.index, env, rng);
      if (o === null || o === undefined) return undefined;
      return Object.prototype.hasOwnProperty.call(o, String(i)) ? (o as Record<string, Value>)[String(i)] : undefined;
    }
    case 'call': {
      const f = FUNCS[n.name];
      if (!f) throw new ExprError(`unknown function "${n.name}"`);
      return f(
        n.args.map((a) => ev(a, env, rng)),
        rng,
      );
    }
    case 'unary': {
      const v = ev(n.arg, env, rng);
      return n.op === '!' ? !v : -num(v);
    }
    case 'cond':
      return ev(n.c, env, rng) ? ev(n.a, env, rng) : ev(n.b, env, rng);
    case 'bin': {
      if (n.op === '&&') return ev(n.l, env, rng) ? ev(n.r, env, rng) : false;
      if (n.op === '||') {
        const l = ev(n.l, env, rng);
        return l ? l : ev(n.r, env, rng);
      }
      const l = ev(n.l, env, rng);
      const r = ev(n.r, env, rng);
      switch (n.op) {
        case '+':
          return typeof l === 'string' || typeof r === 'string' ? `${l ?? ''}${r ?? ''}` : num(l) + num(r);
        case '-':
          return num(l) - num(r);
        case '*':
          return num(l) * num(r);
        case '/':
          return num(l) / num(r);
        case '%':
          return num(l) % num(r);
        case '**':
          return Math.pow(num(l), num(r));
        case '==':
          return l === r;
        case '!=':
          return l !== r;
        case '<':
          return num(l) < num(r);
        case '<=':
          return num(l) <= num(r);
        case '>':
          return num(l) > num(r);
        case '>=':
          return num(l) >= num(r);
      }
    }
  }
  throw new ExprError('bad expression');
}

const cache = new Map<string, Node>();

/** Parses (once, cached) and evaluates an expression. */
export function evaluate(src: string, env: Env, rng: () => number = Math.random): Value {
  let n = cache.get(src);
  if (!n) {
    n = parse(src);
    cache.set(src, n);
  }
  return ev(n, env, rng);
}

/** Throws ExprError if the expression doesn't parse (used by content tests). */
export function check(src: string): void {
  parse(src);
}

export const FUNCTION_NAMES = Object.keys(FUNCS);
