import type { CommandDef, FlagDef, Lang } from './schema';
import { levenshtein, normalize } from './text';

/**
 * The command language every step shares:
 *   <verb> "<text>" --flag value --other=value
 * Both Portuguese and English verbs/flags are accepted, so a dev can type in
 * either language. Errors are structured so each step can explain them.
 */

export type FlagValue = number | string | boolean | string[];
export type Values = Record<string, FlagValue>;

export type ErrorCode =
  | 'empty'
  | 'unknownCommand'
  | 'missingArg'
  | 'unknownFlag'
  | 'oneDash'
  | 'missingValue'
  | 'missingFlag'
  | 'notNumber'
  | 'notInteger'
  | 'belowMin'
  | 'aboveMax'
  | 'notInEnum'
  | 'notBool'
  /** Raised by a model after parsing (e.g. a word the toy map doesn't know). */
  | 'model';

export interface CommandError {
  code: ErrorCode;
  /** Internal flag name (for "<code>.<flag>" error keys). */
  flag?: string;
  /** What the person typed for that flag, in the current language. */
  alias?: string;
  value?: string;
  min?: number;
  max?: number;
  suggestion?: string;
  options?: string;
  /** For code "model": the model's own error code, looked up as "model.<modelCode>". */
  modelCode?: string;
}

export type ParseResult = { ok: true; values: Values } | { ok: false; error: CommandError };

interface Token {
  text: string;
  quoted: boolean;
}

const QUOTES = /["“”«»]/;

export function tokenize(input: string): Token[] {
  const out: Token[] = [];
  let i = 0;
  const s = input.trim();
  while (i < s.length) {
    if (/\s/.test(s[i])) {
      i++;
      continue;
    }
    if (QUOTES.test(s[i])) {
      i++;
      let buf = '';
      while (i < s.length && !QUOTES.test(s[i])) buf += s[i++];
      i++; // closing quote (or end)
      out.push({ text: buf, quoted: true });
      continue;
    }
    let buf = '';
    while (i < s.length && !/\s/.test(s[i])) {
      if (QUOTES.test(s[i]) && buf.endsWith('=')) {
        // --flag="value with spaces"
        i++;
        while (i < s.length && !QUOTES.test(s[i])) buf += s[i++];
        i++;
        break;
      }
      buf += s[i++];
    }
    out.push({ text: buf, quoted: false });
  }
  return out;
}

const isFlagToken = (t: Token) => !t.quoted && /^-+[^\d.,-]/.test(t.text);

function findFlag(def: CommandDef, raw: string): FlagDef | undefined {
  const n = normalize(raw);
  return def.flags.find((f) => [f.name, f.alias.pt, f.alias.en].some((a) => normalize(a) === n));
}

function suggestFlag(def: CommandDef, raw: string, lang: Lang): string | undefined {
  const n = normalize(raw);
  if (!n) return def.flags[0] ? `--${def.flags[0].alias[lang]}` : undefined;
  let best: { alias: string; d: number } | undefined;
  for (const f of def.flags) {
    for (const a of [f.alias[lang], f.alias.pt, f.alias.en]) {
      const na = normalize(a);
      const d = na.startsWith(n) || n.startsWith(na) ? 0 : levenshtein(n, na);
      if (!best || d < best.d) best = { alias: f.alias[lang], d };
    }
  }
  return best && best.d <= 3 ? `--${best.alias}` : undefined;
}

const TRUE = ['sim', 's', 'yes', 'y', 'on', 'true', '1', 'ligado'];
const FALSE = ['nao', 'n', 'no', 'off', 'false', '0', 'desligado'];
const NONE = ['nenhuma', 'nenhum', 'none', 'nada', '-'];

function convert(f: FlagDef, raw: string, lang: Lang): { ok: true; v: FlagValue } | { ok: false; error: CommandError } {
  const base = { flag: f.name, alias: `--${f.alias[lang]}`, value: raw, min: f.min, max: f.max };
  const optionList = () => (f.options ?? []).map((o) => o[lang]).join(', ');
  const matchOption = (r: string) => {
    const n = normalize(r);
    return (f.options ?? []).find((o) => [o.id, o.pt, o.en].some((x) => normalize(x) === n));
  };
  switch (f.type) {
    case 'number':
    case 'int': {
      const v = Number(raw.replace(',', '.'));
      if (raw.trim() === '' || Number.isNaN(v)) return { ok: false, error: { code: 'notNumber', ...base } };
      if (f.type === 'int' && !Number.isInteger(v)) return { ok: false, error: { code: 'notInteger', ...base } };
      if (f.min !== undefined && v < f.min) return { ok: false, error: { code: 'belowMin', ...base } };
      if (f.max !== undefined && v > f.max) return { ok: false, error: { code: 'aboveMax', ...base } };
      return { ok: true, v };
    }
    case 'string':
      if (!raw.trim()) return { ok: false, error: { code: 'missingValue', ...base } };
      return { ok: true, v: raw.trim() };
    case 'enum': {
      const o = matchOption(raw);
      if (!o) return { ok: false, error: { code: 'notInEnum', ...base, options: optionList() } };
      return { ok: true, v: o.id };
    }
    case 'list': {
      if (NONE.includes(normalize(raw))) return { ok: true, v: [] };
      const ids: string[] = [];
      for (const part of raw.split(',').map((p) => p.trim()).filter(Boolean)) {
        const o = matchOption(part);
        if (!o) return { ok: false, error: { code: 'notInEnum', ...base, value: part, options: optionList() } };
        if (!ids.includes(o.id)) ids.push(o.id);
      }
      return { ok: true, v: ids };
    }
    case 'bool': {
      const n = normalize(raw);
      if (TRUE.includes(n)) return { ok: true, v: true };
      if (FALSE.includes(n)) return { ok: true, v: false };
      return { ok: false, error: { code: 'notBool', ...base } };
    }
  }
}

export function defaultValue(f: FlagDef, lang: Lang): FlagValue | undefined {
  if (f.defaultLoc) return f.defaultLoc[lang];
  return f.default;
}

export function parseCommand(input: string, def: CommandDef, lang: Lang): ParseResult {
  const tokens = tokenize(input);
  if (!tokens.length) return { ok: false, error: { code: 'empty', suggestion: def.verb[lang] } };

  const verb = normalize(tokens[0].text);
  if (tokens[0].quoted || (verb !== normalize(def.verb.pt) && verb !== normalize(def.verb.en))) {
    return { ok: false, error: { code: 'unknownCommand', value: tokens[0].text, suggestion: def.verb[lang] } };
  }

  let i = 1;
  const argParts: string[] = [];
  while (i < tokens.length && !isFlagToken(tokens[i])) argParts.push(tokens[i++].text);
  const values: Values = {};
  const arg = argParts.join(' ').trim();
  if (!arg && def.arg.required) {
    return { ok: false, error: { code: 'missingArg', suggestion: `${def.verb[lang]} "${def.arg.default[lang]}"` } };
  }
  values[def.arg.name] = arg || def.arg.default[lang];

  while (i < tokens.length) {
    const tok = tokens[i++];
    if (!isFlagToken(tok)) {
      // Stray word after flags: most often a missing "--" or an unquoted value.
      return { ok: false, error: { code: 'unknownFlag', value: tok.text, suggestion: suggestFlag(def, tok.text, lang) } };
    }
    const dashes = tok.text.match(/^-+/)![0].length;
    let name = tok.text.slice(dashes);
    let raw: string | undefined;
    const eq = name.indexOf('=');
    if (eq >= 0) {
      raw = name.slice(eq + 1);
      name = name.slice(0, eq);
    }
    const f = findFlag(def, name);
    if (!f) {
      return { ok: false, error: { code: 'unknownFlag', value: tok.text, suggestion: suggestFlag(def, name, lang) } };
    }
    if (dashes === 1) {
      return { ok: false, error: { code: 'oneDash', flag: f.name, value: tok.text, suggestion: `--${f.alias[lang]}` } };
    }
    if (raw === undefined) {
      const next = tokens[i];
      if (next && !isFlagToken(next)) {
        raw = next.text;
        i++;
      } else if (f.type === 'bool') {
        raw = 'sim';
      } else {
        return { ok: false, error: { code: 'missingValue', flag: f.name, alias: `--${f.alias[lang]}` } };
      }
    }
    const c = convert(f, raw, lang);
    if (!c.ok) return c;
    values[f.name] = c.v;
  }

  for (const f of def.flags) {
    if (values[f.name] !== undefined) continue;
    if (f.required) return { ok: false, error: { code: 'missingFlag', flag: f.name, alias: `--${f.alias[lang]}` } };
    const d = defaultValue(f, lang);
    if (d !== undefined) values[f.name] = d;
  }
  return { ok: true, values };
}

function fmtValue(f: FlagDef, v: FlagValue, lang: Lang): string {
  const q = (s: string) => (/\s/.test(s) || s === '' ? `"${s}"` : s);
  if (Array.isArray(v)) return v.length ? v.map((id) => optionLabel(f, id, lang)).join(',') : lang === 'pt' ? 'nenhuma' : 'none';
  if (typeof v === 'boolean') return v ? (lang === 'pt' ? 'sim' : 'yes') : lang === 'pt' ? 'nao' : 'no';
  if (typeof v === 'number') return String(Math.round(v * 100) / 100);
  if (f.type === 'enum') return q(optionLabel(f, v, lang));
  return q(v);
}

export function optionLabel(f: FlagDef, id: string, lang: Lang): string {
  return f.options?.find((o) => o.id === id)?.[lang] ?? id;
}

/** Builds the command line equivalent to a set of values (used by Buttons mode). */
export function buildCommand(def: CommandDef, lang: Lang, values: Values): string {
  const arg = String(values[def.arg.name] ?? def.arg.default[lang]);
  let out = `${def.verb[lang]} "${arg}"`;
  for (const f of def.flags) {
    const v = values[f.name];
    if (v === undefined) continue;
    const d = defaultValue(f, lang);
    const same = JSON.stringify(v) === JSON.stringify(d);
    if (!f.required && same) continue;
    out += ` --${f.alias[lang]} ${fmtValue(f, v, lang)}`;
  }
  return out;
}

/** Re-expresses a command in another language, keeping its values. */
export function translateCommand(input: string, def: CommandDef, from: Lang, to: Lang): string {
  const r = parseCommand(input, def, from);
  if (!r.ok) return defaultCommand(def, to);
  const values = { ...r.values };
  if (values[def.arg.name] === def.arg.default[from]) values[def.arg.name] = def.arg.default[to];
  for (const f of def.flags) {
    if (f.defaultLoc && values[f.name] === f.defaultLoc[from]) values[f.name] = f.defaultLoc[to];
  }
  return buildCommand(def, to, values);
}

export function defaultValues(def: CommandDef, lang: Lang): Values {
  const v: Values = { [def.arg.name]: def.arg.default[lang] };
  for (const f of def.flags) {
    const d = defaultValue(f, lang);
    if (d !== undefined) v[f.name] = d;
  }
  return v;
}

export function defaultCommand(def: CommandDef, lang: Lang): string {
  const v = defaultValues(def, lang);
  let out = `${def.verb[lang]} "${v[def.arg.name]}"`;
  for (const f of def.flags) {
    if (f.required && v[f.name] !== undefined) out += ` --${f.alias[lang]} ${fmtValue(f, v[f.name], lang)}`;
  }
  return out;
}
