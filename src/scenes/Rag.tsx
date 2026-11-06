import { interpolate } from '../engine/text';
import type { Doc, RagResult } from '../models/rag';
import { THRESHOLD } from '../models/rag';
import { str, type SceneProps } from './types';

export function RagScene({ loc, s, last, runs }: SceneProps) {
  const r = last as RagResult | null;
  const docs = loc.data.docs as Doc[];
  if (!r) {
    return (
      <>
        <span className="wz-strong">{str(s, 'docsLabel')}</span>
        <ul className="wz-docs">
          {docs.map((d) => (
            <li key={d.id} className="wz-doc">
              <strong>{d.title}</strong>
              <span className="wz-small wz-muted">{d.text}</span>
            </li>
          ))}
        </ul>
        <p className="wz-muted">{str(s, 'empty')}</p>
      </>
    );
  }
  const used = new Set(r.used.map((d) => d.id));
  const status = r.status;
  return (
    <div key={runs.length} className="wz-pipe">
      <div className="wz-pipe__step">
        <span className="wz-eyebrow">{str(s, 'question')}</span>
        <p className="wz-pipe__q">{r.question}</p>
      </div>
      <div className="wz-pipe__step">
        <span className="wz-eyebrow">{str(s, 'search')}</span>
        {!r.search ? (
          <p className="wz-note wz-note--warn">{str(s, 'searchOff')}</p>
        ) : (
          <ul className="wz-docs">
            {r.ranked.map(({ doc, score }) => (
              <li key={doc.id} className={`wz-doc${used.has(doc.id) ? ' wz-doc--used' : ''}`}>
                <div className="wz-row wz-between">
                  <strong>{doc.title}</strong>
                  {used.has(doc.id) && <span className="wz-badge wz-badge--green">{str(s, 'used')}</span>}
                </div>
                <div className="wz-barrow wz-barrow--compact">
                  <span className="wz-barrow__track">
                    <span className="wz-bar" style={{ width: `${Math.max(score * 100, 1)}%`, background: score >= THRESHOLD ? 'var(--green)' : 'var(--line-2)' }} />
                  </span>
                  <span className="wz-mono wz-small">{Math.round(score * 100)}%</span>
                </div>
                {score < THRESHOLD && <span className="wz-small wz-muted">{interpolate(str(s, 'threshold'), { pct: THRESHOLD * 100 })}</span>}
              </li>
            ))}
          </ul>
        )}
      </div>
      <div className="wz-pipe__step">
        <span className="wz-eyebrow">{str(s, 'answer')}</span>
        <div className={`wz-answer wz-pop wz-answer--${status}`} aria-live="polite">
          <span className={`wz-badge wz-badge--${status === 'grounded' ? 'green' : status === 'notFound' ? 'blue' : 'red'}`}>{str(s, status)}</span>
          <p>{r.answer}</p>
          {r.cites.map((c) => (
            <span key={c} className="wz-small wz-mono">
              {interpolate(str(s, 'source'), { doc: c })}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
