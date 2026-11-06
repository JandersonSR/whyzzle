import { interpolate } from '../engine/text';
import type { AgentResult } from '../models/agent';
import { str, type SceneProps } from './types';

const TOOL_IDS = ['calc', 'clock', 'search'] as const;

export function AgentScene({ s, values, last, runs }: SceneProps) {
  const r = last as AgentResult | null;
  const tools = (values?.tools as string[] | undefined) ?? [];
  return (
    <>
      <div className="wz-stack">
        <span className="wz-strong">{str(s, 'toolbox')}</span>
        <div className="wz-chips">
          {TOOL_IDS.map((id) => {
            const on = tools.includes(id);
            return (
              <span key={id} className={`wz-tool${on ? '' : ' wz-tool--off'}`}>
                <strong>{str(s, `tools.${id}`)}</strong>
                {!on ? <span className="wz-small">{str(s, 'toolOff')}</span> : id === 'search' && <span className="wz-small wz-red">{str(s, 'toolDown')}</span>}
              </span>
            );
          })}
        </div>
      </div>
      {!r ? (
        <p className="wz-muted">{str(s, 'empty')}</p>
      ) : (
        <div key={runs.length} className="wz-stack">
          <div className="wz-row wz-between wz-wrap">
            <span className="wz-strong">{str(s, 'label')}</span>
            <span className={`wz-mono wz-small${r.flags.includes('limit') ? ' wz-red' : ''}`}>{interpolate(str(s, 'cycles'), { cycles: r.cycles, max: r.max })}</span>
          </div>
          <div className="wz-steps-meter" aria-hidden="true">
            {Array.from({ length: r.max }, (_, i) => (
              <span key={i} data-used={i < r.cycles ? 'yes' : 'no'} data-limit={r.flags.includes('limit') ? 'yes' : 'no'} />
            ))}
          </div>
          <ol className="wz-trace">
            {r.trace.map((it, i) => (
              <li key={i} className={`wz-trace__item wz-trace__item--${it.kind} wz-pop`} style={{ animationDelay: `${i * 90}ms` }}>
                <span className="wz-trace__kind">{str(s, `kinds.${it.kind}`)}</span>
                <span className={it.kind === 'act' ? 'wz-mono' : undefined}>{it.text}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </>
  );
}
