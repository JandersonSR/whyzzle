import { interpolate } from '../engine/text';
import type { TokenizerResult } from '../models/tokenizer';
import { str, type SceneProps } from './types';



export function TokensScene({ s, preview, last, layer }: SceneProps) {
  const r = (preview ?? last) as TokenizerResult | null;
  if (!r) return <p className="wz-muted">{str(s, 'empty')}</p>;
  const legend = s.legend as Record<string, string>;
  return (
    <>
      <div className="wz-row wz-wrap wz-between">
        <span className="wz-strong">{interpolate(str(s, 'count'), { count: r.count, chars: r.chars })}</span>
        <span className="wz-mono wz-small">{interpolate(str(s, 'window'), { window: r.window })}</span>
      </div>
      <div className="wz-tokens" aria-live="polite">
        {r.tokens.map((t, i) => {
          const lost = i < r.overflow;
          return (
            <span key={i} className={`wz-token wz-token--${t.kind}${lost ? ' wz-token--lost' : ''}`} data-hue={lost ? undefined : i % 6}>
              <span className="wz-token__text">
                {t.space && <span className="wz-token__space" aria-hidden="true">·</span>}
                {t.text}
              </span>
              {layer !== 'simples' && <span className="wz-token__id">{t.id}</span>}
            </span>
          );
        })}
      </div>
      {r.overflow > 0 && (
        <p className="wz-note wz-note--warn">
          <span className="wz-token wz-token--lost wz-token--mini">abc</span> {str(s, 'forgotten')}
        </p>
      )}
      <div className="wz-window" aria-hidden="true">
        <span className="wz-window__lost" style={{ width: `${(r.overflow / Math.max(r.count, 1)) * 100}%` }} />
        <span className="wz-window__in" style={{ width: `${(Math.min(r.count, r.window) / Math.max(r.count, r.window)) * 100}%` }} />
      </div>
      <ul className="wz-legend">
        {(['word', 'piece', 'num', 'punct'] as const).map((k) => (
          <li key={k}>
            <span className={`wz-token wz-token--mini wz-token--${k}`}>a</span> {legend[k]}
          </li>
        ))}
      </ul>
      {layer !== 'simples' && <p className="wz-muted wz-small">{str(s, 'ids')}. {interpolate(str(s, 'cost'), { count: r.count })}</p>}
    </>
  );
}
