import { fmtNum, interpolate } from '../engine/text';
import type { SamplerResult } from '../models/sampler';
import { softmax } from '../models/sampler';
import { str, type SceneProps } from './types';

const MOOD_COLORS = ['var(--blue)', 'var(--blue)', 'var(--ink-2)', 'var(--orange-ink)', 'var(--red)'];
const SHAKES = ['', 'wz-shake-1', 'wz-shake-2', 'wz-shake-3', 'wz-shake-4'];

function moodIndex(T: number): number {
  if (T === 0) return 0;
  if (T < 0.5) return 1;
  if (T <= 1.2) return 2;
  if (T <= 2) return 3;
  return 4;
}

/** Fixed pseudo-random value per marble, so the bag doesn't reshuffle on every render. */
const jitter = (j: number) => Math.abs(Math.sin((j + 1) * 12.9898) * 43758.5453) % 1;

export function SamplerScene({ lesson, loc, s, lang, layer, values, preview, last, runs }: SceneProps) {
  const logits = lesson.def.data.logits as number[];
  const colors = lesson.def.data.colors as string[];
  const words = loc.data.words as string[];
  const weirdFrom = Number(lesson.def.data.weirdFrom);
  const p = preview as SamplerResult | null;
  const T = p?.T ?? (values ? Number(values.temp) : 0) ?? 0;
  const probs = p?.probs ?? softmax(logits, T);
  const lastR = last as SamplerResult | null;
  const lastIdx = lastR ? lastR.idxs[lastR.idxs.length - 1] : -1;
  const m = moodIndex(T);
  const moods = s.moods as string[];

  return (
    <>
      <p className="wz-sentence" aria-live="polite">
        {String(loc.data.prefix)}{' '}
        {lastR ? (
          <span key={runs.length} className="wz-tok-new wz-pop">
            {words[lastIdx]}
          </span>
        ) : (
          <span className="wz-blank"> </span>
        )}
        .
      </p>

      <div className="wz-stack">
        <div className="wz-row wz-wrap wz-between">
          <span className="wz-strong">
            {str(s, 'thermo')}: <span className="wz-mono">{fmtNum(T, lang)}</span>
          </span>
          <span className="wz-strong" style={{ color: MOOD_COLORS[m] }}>
            {moods[m]}
          </span>
        </div>
        <div className="wz-thermo">
          <span className="wz-thermo__thumb" style={{ left: `${Math.min(T / 2, 1) * 100}%` }} />
        </div>
        <div className="wz-thermo__ticks" aria-hidden="true">
          <span>0</span>
          <span>1</span>
          <span>2+</span>
        </div>
      </div>

      {layer === 'simples' ? <Bag T={T} logits={logits} colors={colors} words={words} s={s} shake={SHAKES[m]} /> : (
        <div className="wz-stack">
          <span className="wz-strong">{str(s, 'bars')}</span>
          {probs.map((pr, i) => {
            const chosen = i === lastIdx;
            let pct = pr >= 0.9995 ? '100%' : pr < 0.001 ? '<0.1%' : `${(pr * 100).toFixed(pr < 0.1 ? 1 : 0)}%`;
            if (lang === 'pt') pct = pct.replace('.', ',');
            return (
              <div key={i} className="wz-barrow">
                <span className="wz-barrow__label" style={{ fontWeight: chosen ? 700 : 500 }}>
                  <span className="wz-dot" style={{ background: colors[i] }} />
                  {words[i]}
                </span>
                <span className="wz-barrow__track">
                  <span className="wz-bar" style={{ width: `${Math.max(pr * 100, 0.8)}%`, background: chosen ? 'var(--orange-2)' : 'var(--blue)' }} />
                </span>
                <span className="wz-mono wz-small wz-barrow__pct">{pct}</span>
              </div>
            );
          })}
          <span className="wz-muted wz-small">{str(s, 'barsNote')}</span>
        </div>
      )}

      {p?.otherPrompt && <p className="wz-note">{str(s, 'otherPrompt')}</p>}

      <History runs={runs} words={words} colors={colors} weirdFrom={weirdFrom} s={s} lang={lang} />
    </>
  );
}

function Bag({ T, logits, colors, words, s, shake }: { T: number; logits: number[]; colors: string[]; words: string[]; s: Record<string, unknown>; shake: string }) {
  // Marble counts are fixed (from T = 1); temperature only changes how mixed they are.
  const base = softmax(logits, 1);
  const counts = base.map((b) => Math.max(1, Math.round(b * 40)));
  const pool: { color: string; key: number; r: number }[] = [];
  counts.forEach((c, i) => {
    for (let j = 0; j < c; j++) pool.push({ color: colors[i], key: 0, r: 0 });
  });
  const mix = Math.min(T / 2.5, 1);
  const N = pool.length;
  const marbles = pool.map((m, j) => ({ ...m, r: jitter(j), key: (1 - mix) * j + mix * jitter(j) * N })).sort((a, b) => a.key - b.key);
  const jig = T >= 2 ? 'wz-jig wz-jig-fast' : T >= 1 ? 'wz-jig' : '';
  return (
    <div className="wz-bagwrap">
      <div className={`wz-bag ${shake}`}>
        <div className="wz-bag__tie" aria-hidden="true" />
        <div className="wz-bag__neck" aria-hidden="true" />
        <div className="wz-bag__body" role="img" aria-label={str(s, 'bagAria')}>
          {marbles.map((m, i) => (
            <span key={i} className={`wz-marble ${jig}`} style={{ background: m.color, animationDelay: `${(m.r * 0.4).toFixed(2)}s` }} />
          ))}
        </div>
      </div>
      <p className="wz-bag__caption">{str(s, 'bagCaption')}</p>
      <ul className="wz-legend wz-legend--center">
        {words.map((w, i) => (
          <li key={w}>
            <span className="wz-dot" style={{ background: colors[i] }} />
            {w} <span className="wz-mono wz-muted">×{counts[i]}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function History({ runs, words, colors, weirdFrom, s, lang }: { runs: SceneProps['runs']; words: string[]; colors: string[]; weirdFrom: number; s: Record<string, unknown>; lang: 'pt' | 'en' }) {
  if (!runs.length) return null;
  return (
    <div className="wz-stack">
      {runs.slice(0, 4).map((run, k) => {
        const r = run.result as SamplerResult;
        const d = new Set(r.idxs).size;
        const weird = r.idxs.some((i) => i >= weirdFrom);
        return (
          <div key={runs.length - k} className={`wz-batch${weird ? ' wz-batch--weird' : ''}`}>
            <span className="wz-small">
              <span className="wz-mono wz-strong">
                T={fmtNum(r.T, lang)} · {r.n}×
              </span>{' '}
              · {d === 1 ? str(s, 'oneWord') : interpolate(str(s, 'manyWords'), { d })}
            </span>
            <div className="wz-chips">
              {r.idxs.map((i, j) => (
                <span key={j} className={`wz-pill${i >= weirdFrom ? ' wz-pill--weird' : ''}`}>
                  <span className="wz-dot wz-dot--sm" style={{ background: colors[i] }} />
                  {words[i]}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
