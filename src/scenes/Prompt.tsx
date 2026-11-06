import { interpolate } from '../engine/text';
import type { PromptResult } from '../models/promptGrader';
import { Check } from '../ui/Art';
import { str, type SceneProps } from './types';

export function PromptScene({ s, preview, last, runs }: SceneProps) {
  const live = preview as PromptResult | null;
  const r = last as PromptResult | null;
  const prev = runs[1]?.result as PromptResult | undefined;
  const items = s.items as Record<string, string>;
  const checklist = live?.checklist ?? r?.checklist;
  const score = live?.score ?? r?.score ?? 0;
  return (
    <>
      <div className="wz-stack">
        <span className="wz-strong">{str(s, 'checklist')}</span>
        <ul className="wz-checklist">
          {(['audience', 'format', 'tone', 'role'] as const).map((k) => (
            <li key={k} data-ok={checklist?.[k] ? 'yes' : 'no'}>
              <Check ok={!!checklist?.[k]} /> {items[k]}
            </li>
          ))}
        </ul>
        <div className="wz-meter" aria-hidden="true">
          <span className="wz-bar" style={{ width: `${score * 100}%`, background: score >= 0.75 ? 'var(--green)' : 'var(--blue)' }} />
        </div>
        <span className="wz-small">
          {interpolate(str(s, 'score'), { score: Math.round(score * 100) })}
          {prev && !prev.injected && <span className="wz-muted"> · {interpolate(str(s, 'before'), { score: Math.round(prev.score * 100) })}</span>}
        </span>
      </div>

      {!r ? (
        <p className="wz-muted">{str(s, 'empty')}</p>
      ) : (
        <div key={runs.length} className={`wz-answer wz-pop${r.injected ? ' wz-answer--danger' : ''}`} aria-live="polite">
          {r.injected && <strong className="wz-answer__warn">{str(s, 'injected')}</strong>}
          {r.opener && <p className="wz-answer__opener">{r.opener}</p>}
          {r.bullets ? (
            <ul>
              {r.sentences.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          ) : (
            <p>{r.sentences.join(' ')}</p>
          )}
        </div>
      )}
      {r?.offTopic && <p className="wz-note">{str(s, 'offTopic')}</p>}
    </>
  );
}
