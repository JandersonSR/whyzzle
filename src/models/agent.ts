import type { SimModel, ModelResult } from '../engine/registry';
import { interpolate, normalize } from '../engine/text';

/**
 * Step 7 — a toy agent loop: think → call a tool → observe → repeat, until it
 * can answer or hits the step limit. Tools: calculator, clock (real time via
 * Intl), and a web search that is always "down" (to show retries and limits).
 */

export interface TraceItem {
  kind: 'think' | 'act' | 'observe' | 'answer' | 'stop';
  text: string;
  tool?: string;
  cycle: number;
}

export interface AgentResult extends ModelResult {
  trace: TraceItem[];
  cycles: number;
  max: number;
  final: string[];
}

interface City {
  names: string[];
  tz: string;
  label: { pt: string; en: string };
}

type P = Record<string, string>;

type Task =
  | { kind: 'calc'; a: number; op: string; b: number; expr: string }
  | { kind: 'time'; city: City }
  | { kind: 'weather'; city: City };

const OPS: Record<string, string> = { x: '×', '×': '×', '*': '×', vezes: '×', times: '×', '+': '+', mais: '+', plus: '+', '-': '−', menos: '−', minus: '−', '/': '÷', dividido: '÷', divided: '÷' };

export function findTasks(text: string, cities: City[]): Task[] {
  const tasks: Task[] = [];
  const n = normalize(text);
  const m = n.match(/(\d[\d.]*)\s*(x|×|\*|vezes|times|\+|mais|plus|-|menos|minus|\/|dividido|divided)\s*(?:por|by)?\s*(\d[\d.]*)/);
  if (m) {
    const a = Number(m[1].replace(/\./g, ''));
    const b = Number(m[3].replace(/\./g, ''));
    const op = OPS[m[2]];
    tasks.push({ kind: 'calc', a, op, b, expr: `${a} ${op} ${b}` });
  }
  const city = cities.find((c) => c.names.some((nm) => n.includes(normalize(nm))));
  const wantsWeather = /clima|previsao|chover|chuva|weather|forecast|rain/.test(n);
  const wantsTime = /hora|horas|horario|time|o'clock/.test(n);
  if (wantsTime) tasks.push({ kind: 'time', city: city ?? cities[0] });
  if (wantsWeather) tasks.push({ kind: 'weather', city: city ?? cities[0] });
  return tasks;
}

export function calc(a: number, op: string, b: number): number {
  switch (op) {
    case '+':
      return a + b;
    case '−':
      return a - b;
    case '÷':
      return b === 0 ? NaN : Math.round((a / b) * 1000) / 1000;
    default:
      return a * b;
  }
}

function timeIn(tz: string, lang: 'pt' | 'en'): string {
  try {
    return new Intl.DateTimeFormat(lang === 'pt' ? 'pt-BR' : 'en-US', { timeZone: tz, hour: '2-digit', minute: '2-digit' }).format(new Date());
  } catch {
    return '??:??';
  }
}

export const agent: SimModel<AgentResult> = {
  id: 'agent',
  run(values, ctx) {
    const t = ctx.text.phrases as P;
    const cities = ctx.data.cities as City[];
    const tools = values.tools as string[];
    const max = Number(values.maxSteps);
    const lang = ctx.lang;
    const fmt = (v: number) => v.toLocaleString(lang === 'pt' ? 'pt-BR' : 'en-US');
    const tasks = findTasks(String(values.text), cities);
    const trace: TraceItem[] = [];
    const final: string[] = [];
    const flags = new Set<string>();
    let cycle = 0;
    let stopped = false;

    const next = () => {
      if (cycle >= max) {
        stopped = true;
        return false;
      }
      cycle++;
      return true;
    };

    if (!tasks.length) {
      trace.push({ kind: 'think', text: t.noTask, cycle: 0 });
      return { flags: ['noTask'], vars: { max }, trace, cycles: 0, max, final: [t.noTask] };
    }

    for (const task of tasks) {
      if (stopped || !next()) break;
      if (task.kind === 'calc') {
        trace.push({ kind: 'think', text: interpolate(t.thinkCalc, { expr: task.expr }), cycle });
        const real = calc(task.a, task.op, task.b);
        if (tools.includes('calc')) {
          trace.push({ kind: 'act', tool: 'calc', text: interpolate(t.callCalc, { expr: task.expr }), cycle });
          trace.push({ kind: 'observe', text: fmt(real), cycle });
          final.push(interpolate(t.answerCalc, { expr: task.expr, value: fmt(real) }));
        } else {
          const guess = Math.round((real * 1.0137) / 100) * 100;
          flags.add('guessed');
          trace.push({ kind: 'think', text: interpolate(t.guessCalc, { guess: fmt(guess) }), cycle });
          final.push(interpolate(t.answerGuess, { expr: task.expr, value: fmt(guess) }));
        }
      } else if (task.kind === 'time') {
        const city = task.city.label[lang];
        trace.push({ kind: 'think', text: interpolate(t.thinkTime, { city }), cycle });
        if (tools.includes('clock')) {
          const time = timeIn(task.city.tz, lang);
          trace.push({ kind: 'act', tool: 'clock', text: interpolate(t.callClock, { city }), cycle });
          trace.push({ kind: 'observe', text: time, cycle });
          final.push(interpolate(t.answerTime, { city, time }));
        } else {
          trace.push({ kind: 'think', text: t.guessTime, cycle });
          final.push(interpolate(t.answerTimeGuess, { city }));
        }
      } else {
        const city = task.city.label[lang];
        trace.push({ kind: 'think', text: interpolate(t.thinkWeather, { city }), cycle });
        if (!tools.includes('search')) {
          trace.push({ kind: 'think', text: t.noSearch, cycle });
          final.push(interpolate(t.answerNoWeather, { city }));
          continue;
        }
        let attempt = 0;
        for (;;) {
          attempt++;
          trace.push({ kind: 'act', tool: 'search', text: interpolate(t.callSearch, { city }), cycle });
          trace.push({ kind: 'observe', text: t.searchDown, cycle });
          if (!next()) break;
          trace.push({ kind: 'think', text: interpolate(t.retry, { n: attempt + 1 }), cycle });
        }
      }
    }

    if (stopped) {
      flags.add('limit');
      trace.push({ kind: 'stop', text: interpolate(t.limit, { max }), cycle });
    } else {
      trace.push({ kind: 'answer', text: final.join(' '), cycle });
    }
    return { flags: Array.from(flags), vars: { max, cycles: cycle }, trace, cycles: cycle, max, final };
  },
};
