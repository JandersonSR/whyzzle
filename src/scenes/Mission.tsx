import { interpolate } from '../engine/text';
import type { MissionResult } from '../models/mission';
import { CRITERIA } from '../models/mission';
import { Check } from '../ui/Art';
import { str, type SceneProps } from './types';

export function MissionScene({ s, values, last, runs }: SceneProps) {
  const r = last as MissionResult | null;
  const vars = { role: String(values?.text ?? ''), invented: r?.vars?.invented, score: r?.vars?.score };
  return (
    <>
      <div className="wz-stack">
        <span className="wz-strong">{interpolate(str(s, 'criteriaLabel'), { done: r?.vars?.done ?? 0, total: CRITERIA.length })}</span>
        <ul className="wz-criteria">
          {CRITERIA.map((id) => {
            const c = r?.criteria.find((x) => x.id === id);
            const state = !c ? 'pending' : c.ok ? 'ok' : 'fail';
            return (
              <li key={id} data-state={state}>
                {state === 'pending' ? <span className="wz-criteria__pending" aria-hidden="true" /> : <Check ok={state === 'ok'} />}
                <span>
                  {str(s, `criteria.${id}`)}
                  {state === 'fail' && <span className="wz-criteria__why">{interpolate(str(s, `why.${id}`), vars)}</span>}
                </span>
              </li>
            );
          })}
        </ul>
      </div>
      {!r ? (
        <p className="wz-muted">{str(s, 'pending')}</p>
      ) : (
        <div key={runs.length} className="wz-stack">
          <span className="wz-strong">{str(s, 'answers')}</span>
          <div className="wz-table" role="table" aria-label={str(s, 'answers')}>
            {r.answers.map((a) => (
              <div key={a.q} role="row" className={`wz-table__row${a.invented ? ' wz-table__row--fail' : ''}`}>
                <span role="cell" className="wz-table__q">
                  {a.q}
                </span>
                <span role="cell" className="wz-table__a">
                  {a.text}
                  {a.invented && <span className="wz-badge wz-badge--red">{str(s, a.embellished ? 'embellished' : 'invented')}</span>}
                  {a.abstains && <span className="wz-badge wz-badge--blue">{str(s, 'abstained')}</span>}
                </span>
                <span role="cell" className="wz-table__v">
                  {r.tests.map((rule) => (
                    <span key={rule} className={`wz-verdict${a.verdicts[rule] ? '' : ' wz-verdict--no'}`}>
                      <Check ok={!!a.verdicts[rule]} size={14} /> {str(s, `rules.${rule}`)}
                    </span>
                  ))}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </>
  );
}
