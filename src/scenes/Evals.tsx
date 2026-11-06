import { interpolate } from '../engine/text';
import type { EvalResult } from '../models/evals';
import { Check } from '../ui/Art';
import { str, type SceneProps } from './types';

export function EvalsScene({ s, preview, last }: SceneProps) {
  const r = (preview ?? last) as EvalResult | null;
  if (!r) return <p className="wz-muted">{str(s, 'empty')}</p>;
  const m = r.model.toUpperCase();
  return (
    <>
      <div className="wz-stack">
        <span className="wz-strong">{str(s, 'board')}</span>
        <div className="wz-board">
          {(['a', 'b'] as const).map((k) => (
            <div key={k} className={`wz-board__card${r.model === k ? ' wz-board__card--on' : ''}`}>
              <span className="wz-strong">{interpolate(str(s, 'assistant'), { m: k.toUpperCase() })}</span>
              <span className="wz-board__score">{Math.round(r.scores[k] * 100)}%</span>
              <span className="wz-small wz-muted">{str(s, `${k}Desc`)}</span>
            </div>
          ))}
        </div>
        {!r.rules.length && <p className="wz-note wz-note--warn">{str(s, 'noRules')}</p>}
      </div>
      <div className="wz-table" role="table" aria-label={interpolate(str(s, 'answer'), { m })}>
        {r.rows.map((row) => (
          <div key={row.q} role="row" className={`wz-table__row${row.pass ? '' : ' wz-table__row--fail'}`}>
            <span role="cell" className="wz-table__q">
              {row.q}
            </span>
            <span role="cell" className="wz-table__a">
              {row.answer.text}
              {row.invented && <span className="wz-badge wz-badge--red">{str(s, 'invented')}</span>}
            </span>
            <span role="cell" className="wz-table__v">
              {r.rules.map((rule) => (
                <span key={rule} className={`wz-verdict${row.verdicts[rule] ? '' : ' wz-verdict--no'}`}>
                  <Check ok={!!row.verdicts[rule]} size={14} /> {str(s, `rules.${rule}`)}
                </span>
              ))}
            </span>
          </div>
        ))}
      </div>
    </>
  );
}
