import type { ReactNode } from 'react';
import { fmtNum, interpolate } from '../engine/text';
import type { Lang } from '../engine/schema';
import type { DeclResult } from '../models/declarative';
import { Check } from '../ui/Art';
import { str, type SceneProps } from './types';

/**
 * The reusable scene. A lesson lists widgets in step.json → data.sim.widgets;
 * the declarative model resolves their expressions and this file draws them.
 *
 * Text fields: "@key" → the lesson's scene string (with {vars}); anything else is shown as is.
 * Tones: ok · warn · bad · info · dim · neutral.
 */

type Tone = 'ok' | 'warn' | 'bad' | 'info' | 'dim' | 'neutral';
type W = Record<string, unknown>;

interface Ctx {
  s: Record<string, unknown>;
  vars: Record<string, string | number | boolean>;
  lang: Lang;
}

function text(v: unknown, c: Ctx): string {
  if (v === undefined || v === null) return '';
  if (typeof v === 'string' && v.startsWith('@')) return interpolate(str(c.s, v.slice(1)), c.vars);
  if (typeof v === 'number') return fmtNum(v, c.lang);
  return String(v);
}

const asArr = <T,>(v: unknown): T[] => (Array.isArray(v) ? (v as T[]) : []);
const tone = (v: unknown): Tone => (['ok', 'warn', 'bad', 'info', 'dim', 'neutral'].includes(String(v)) ? (v as Tone) : 'neutral');

/** "+ ok", "! bad", "? warn", "~ dim", "$ command" prefixes for one-line items. */
function prefixed(line: string): { text: string; tone: Tone; cmd: boolean } {
  const m = line.match(/^([+!?~$])\s?(.*)$/s);
  if (!m) return { text: line, tone: 'neutral', cmd: false };
  const map: Record<string, Tone> = { '+': 'ok', '!': 'bad', '?': 'warn', '~': 'dim', $: 'neutral' };
  return { text: m[2], tone: map[m[1]], cmd: m[1] === '$' };
}

function fmtValue(v: unknown, format: unknown, c: Ctx): string {
  if (typeof v !== 'number') return text(v, c);
  switch (format) {
    case 'pct':
      return `${fmtNum(v, c.lang, v % 1 === 0 ? 0 : v < 10 ? 2 : 1)}%`;
    case 'int':
      return Math.round(v).toLocaleString(c.lang === 'pt' ? 'pt-BR' : 'en-US');
    case 'ms':
      return `${Math.round(v).toLocaleString(c.lang === 'pt' ? 'pt-BR' : 'en-US')} ms`;
    case 'min':
      return `${fmtNum(Math.round(v * 10) / 10, c.lang)} min`;
    case 'money':
      return (c.lang === 'pt' ? 'R$ ' : '$ ') + v.toLocaleString(c.lang === 'pt' ? 'pt-BR' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    default:
      return fmtNum(Math.round(v * 100) / 100, c.lang);
  }
}

function Heading({ w, c }: { w: W; c: Ctx }) {
  return w.label ? <span className="wz-strong">{text(w.label, c)}</span> : null;
}

function Metrics({ w, c }: { w: W; c: Ctx }) {
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <div className="wz-metrics">
        {asArr<W>(w.items).map((it, i) => (
          <div key={i} className="wz-metric" data-tone={tone(it.tone)}>
            {(() => {
              const v = fmtValue(it.value, it.format, c);
              return (
                <span className="wz-metric__value" data-long={v.length > 12 ? '' : undefined}>
                  {v}
                </span>
              );
            })()}
            <span className="wz-metric__label">{text(it.label, c)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function Terminal({ w, c }: { w: W; c: Ctx }) {
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <pre className="wz-wterm" aria-live="polite">
        {asArr<unknown>(w.lines).map((l, i) => {
          const p = prefixed(text(l, c));
          return (
            <span key={i} className="wz-wterm__line" data-tone={p.tone}>
              {p.cmd && <span className="wz-wterm__ps">$ </span>}
              {p.text}
              {'\n'}
            </span>
          );
        })}
      </pre>
    </div>
  );
}

function chipsFrom(v: unknown, c: Ctx, cap = 30): { text: string; tone: Tone }[] {
  if (typeof v === 'number') return Array.from({ length: Math.min(v, cap) }, (_, i) => ({ text: String(i + 1), tone: 'neutral' as Tone }));
  return asArr<unknown>(v)
    .slice(0, cap)
    .map((x) => (typeof x === 'object' && x ? { text: text((x as W).label, c), tone: tone((x as W).tone) } : prefixed(text(x, c))));
}

function Queue({ w, c }: { w: W; c: Ctx }) {
  const msgs = chipsFrom(w.messages, c);
  const total = typeof w.messages === 'number' ? w.messages : asArr(w.messages).length;
  const more = total - msgs.length;
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <div className="wz-queue">
        {w.producer !== undefined && (
          <div className="wz-queue__node" data-tone={tone(w.producerTone)}>
            {text(w.producer, c)}
          </div>
        )}
        <span className="wz-queue__arrow" aria-hidden="true">
          →
        </span>
        <div className="wz-queue__pipe" role="list" aria-label={text(w.queueLabel ?? w.label, c)}>
          {msgs.length === 0 && <span className="wz-muted wz-small">{text(w.empty ?? '∅', c)}</span>}
          {msgs.map((m, i) => (
            <span key={i} role="listitem" className="wz-msg" data-tone={m.tone}>
              {m.text}
            </span>
          ))}
          {more > 0 && <span className="wz-muted wz-small">+{more}</span>}
        </div>
        <span className="wz-queue__arrow" aria-hidden="true">
          →
        </span>
        <div className="wz-queue__consumers">
          {asArr<W>(w.consumers).map((cn, i) => (
            <div key={i} className="wz-queue__node" data-tone={tone(cn.tone)}>
              <span>{text(cn.label, c)}</span>
              {cn.note !== undefined && <span className="wz-small">{text(cn.note, c)}</span>}
            </div>
          ))}
        </div>
      </div>
      {w.dlq !== undefined && (
        <div className="wz-row wz-wrap">
          <span className="wz-badge wz-badge--red">{text(w.dlqLabel ?? 'DLQ', c)}</span>
          <div className="wz-chips">
            {chipsFrom(w.dlq, c).map((m, i) => (
              <span key={i} className="wz-msg" data-tone="bad">
                {m.text}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

const STATUS_TONE: Record<string, Tone> = {
  Running: 'ok',
  Ready: 'ok',
  Completed: 'dim',
  Succeeded: 'dim',
  Pending: 'warn',
  ContainerCreating: 'warn',
  Terminating: 'dim',
  NotReady: 'bad',
  CrashLoopBackOff: 'bad',
  Error: 'bad',
  OOMKilled: 'bad',
  ImagePullBackOff: 'bad',
  ErrImagePull: 'bad',
  Evicted: 'bad',
};

function Cluster({ w, c }: { w: W; c: Ctx }) {
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <div className="wz-cluster">
        {asArr<W>(w.nodes).map((n, i) => (
          <div key={i} className="wz-node" data-tone={tone(n.tone ?? STATUS_TONE[String(n.status)] ?? 'neutral')}>
            <div className="wz-row wz-between wz-wrap">
              <strong className="wz-mono wz-small">{text(n.name, c)}</strong>
              {n.status !== undefined && <span className="wz-small">{text(n.status, c)}</span>}
            </div>
            <div className="wz-pods">
              {asArr<W>(n.pods).map((p, j) => {
                const st = String(p.status ?? 'Running');
                return (
                  <span key={j} className="wz-pod" data-tone={tone(p.tone ?? STATUS_TONE[st] ?? 'neutral')} title={st}>
                    <span className="wz-mono">{text(p.name, c)}</span>
                    <span className="wz-pod__st">{st}</span>
                  </span>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Table({ w, c }: { w: W; c: Ctx }) {
  const cols = asArr<unknown>(w.columns);
  const rows = asArr<unknown[]>(w.rows);
  const tones = asArr<unknown>(w.tones);
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <div className="wz-dbtable-wrap">
        <table className="wz-dbtable">
          <thead>
            <tr>
              {cols.map((h, i) => (
                <th key={i} scope="col">
                  {text(h, c)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i} data-tone={tone(tones[i])}>
                {asArr<unknown>(r).map((cell, j) => (
                  <td key={j}>{text(cell, c)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {w.caption !== undefined && <span className="wz-muted wz-small">{text(w.caption, c)}</span>}
    </div>
  );
}

function Flow({ w, c }: { w: W; c: Ctx }) {
  const steps = asArr<W>(w.steps);
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <ol className="wz-flow">
        {steps.map((st, i) => (
          <li key={i} className="wz-flow__step" data-tone={tone(st.tone)}>
            <strong>{text(st.label, c)}</strong>
            {st.sub !== undefined && <span className="wz-small">{text(st.sub, c)}</span>}
          </li>
        ))}
      </ol>
    </div>
  );
}

const SERIES_COLORS = ['var(--blue)', 'var(--orange-2)', 'var(--green)', 'var(--red)'];

function Chart({ w, c }: { w: W; c: Ctx }) {
  const labels = asArr<unknown>(w.labels);
  const series = asArr<W>(w.series);
  const all = series.flatMap((s) => asArr<number>(s.values).map(Number));
  const thr = w.threshold as W | undefined;
  const max = Math.max(Number(w.max ?? 0), ...all, thr ? Number(thr.value) : 0, 1);
  const H = 120;
  const n = Math.max(labels.length, ...series.map((s) => asArr(s.values).length), 1);
  const Wd = 300;
  const x = (i: number) => (n === 1 ? Wd / 2 : (i / (n - 1)) * (Wd - 20) + 10);
  const y = (v: number) => H - (v / max) * (H - 10);
  const kind = w.kind === 'line' ? 'line' : 'bar';
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <svg className="wz-chart" viewBox={`0 0 ${Wd} ${H + 4}`} role="img" aria-label={text(w.label ?? '', c)} preserveAspectRatio="none">
        {thr && <line x1="0" x2={Wd} y1={y(Number(thr.value))} y2={y(Number(thr.value))} stroke="var(--red)" strokeDasharray="4 3" strokeWidth="1.5" vectorEffect="non-scaling-stroke" />}
        {kind === 'line'
          ? series.map((s, k) => (
              <polyline
                key={k}
                fill="none"
                stroke={SERIES_COLORS[k % SERIES_COLORS.length]}
                strokeWidth="2.5"
                vectorEffect="non-scaling-stroke"
                strokeLinejoin="round"
                points={asArr<number>(s.values)
                  .map((v, i) => `${x(i)},${y(Number(v))}`)
                  .join(' ')}
              />
            ))
          : series.map((s, k) =>
              asArr<number>(s.values).map((v, i) => {
                const bw = (Wd - 20) / n / series.length - 4;
                const bx = 10 + (i * (Wd - 20)) / n + k * (bw + 2);
                return <rect key={`${k}-${i}`} x={bx} y={y(Number(v))} width={Math.max(bw, 2)} height={H - y(Number(v))} rx="2" fill={SERIES_COLORS[k % SERIES_COLORS.length]} />;
              }),
            )}
      </svg>
      <div className="wz-row wz-between wz-small wz-muted wz-mono">
        <span>{text(labels[0], c)}</span>
        <span>{text(labels[labels.length - 1], c)}</span>
      </div>
      <ul className="wz-legend">
        {series.map((s, k) => (
          <li key={k}>
            <span className="wz-dot" style={{ background: SERIES_COLORS[k % SERIES_COLORS.length] }} />
            {text(s.label, c)}
          </li>
        ))}
        {thr && (
          <li>
            <span className="wz-dot" style={{ background: 'var(--red)' }} />
            {text(thr.label, c)}
          </li>
        )}
      </ul>
    </div>
  );
}

function Note({ w, c }: { w: W; c: Ctx }) {
  const t = tone(w.tone);
  return <p className={`wz-note${t === 'warn' || t === 'bad' ? ' wz-note--warn' : ''}`}>{text(w.text, c)}</p>;
}

function Checks({ w, c }: { w: W; c: Ctx }) {
  return (
    <div className="wz-stack">
      <Heading w={w} c={c} />
      <ul className="wz-criteria">
        {asArr<W>(w.items).map((it, i) => (
          <li key={i} data-state={it.ok ? 'ok' : 'fail'}>
            <Check ok={Boolean(it.ok)} />
            <span>
              {text(it.label, c)}
              {!it.ok && it.why !== undefined && <span className="wz-criteria__why">{text(it.why, c)}</span>}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

const RENDER: Record<string, (p: { w: W; c: Ctx }) => ReactNode> = {
  metrics: Metrics,
  terminal: Terminal,
  queue: Queue,
  cluster: Cluster,
  table: Table,
  flow: Flow,
  chart: Chart,
  note: Note,
  checks: Checks,
};
export const WIDGET_TYPES = Object.keys(RENDER);

export function WidgetsScene({ lesson, s, lang, preview, last }: SceneProps) {
  // "live": the scene follows what is typed (preview); otherwise it shows the last run.
  const live = Boolean((lesson.def.data.sim as { live?: boolean } | undefined)?.live);
  const r = (live ? (preview ?? last) : (last ?? preview)) as DeclResult | null;
  if (!r) return <p className="wz-muted">{str(s, 'empty')}</p>;
  const c: Ctx = { s, vars: r.env, lang };
  return (
    <div className="wz-widgets">
      {r.widgets.map((w, i) => {
        const R = RENDER[String(w.type)];
        return R ? <R key={i} w={w} c={c} /> : null;
      })}
    </div>
  );
}
