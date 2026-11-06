import { interpolate, fmtNum } from '../engine/text';
import type { NextTokenResult } from '../models/nextToken';
import { str, type SceneProps } from './types';

export function NextTokenScene({ s, preview, last, lang, layer }: SceneProps) {
  const r = (preview ?? last) as NextTokenResult | null;
  if (!r) return <p className="wz-muted">{str(s, 'empty')}</p>;
  return (
    <>
      <p className="wz-sentence" aria-live="polite">
        {r.prefix}{' '}
        {r.positions.map((p, i) => (
          <span key={`${i}-${p.word}`} className={`wz-tok-new wz-pop${p.unknown ? ' wz-tok-new--guess' : ''}`} style={{ animationDelay: `${i * 70}ms` }}>
            {p.word}
          </span>
        ))}
      </p>
      <div className="wz-stack">
        <span className="wz-strong">{str(s, 'candidates')}</span>
        <div className="wz-cands">
          {r.positions.map((p, i) => (
            <div key={i} className={`wz-cand${p.unknown ? ' wz-cand--guess' : ''}`}>
              <span className="wz-cand__from">{interpolate(str(s, p.unknown ? 'guess' : 'after'), { from: p.from })}</span>
              {p.cands.map((c, j) => (
                <div key={c.word} className="wz-cand__row">
                  <span className={`wz-cand__word${j === 0 ? ' wz-cand__word--chosen' : ''}`}>{c.word}</span>
                  <span className="wz-cand__track">
                    <span className="wz-bar" style={{ width: `${Math.max(c.p * 100, 2)}%`, background: j === 0 ? 'var(--orange-2)' : 'var(--blue)' }} />
                  </span>
                  <span className="wz-mono wz-small">{layer === 'simples' ? `${Math.round(c.p * 100)}%` : fmtNum(c.p, lang, 2)}</span>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </>
  );
}
