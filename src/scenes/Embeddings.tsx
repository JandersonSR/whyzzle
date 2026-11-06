import { fmtNum } from '../engine/text';
import type { EmbeddingResult, Point } from '../models/embeddings';
import { str, type SceneProps } from './types';

const GROUP_COLORS = ['#2F5BEA', '#15803D', '#C2410C', '#7C3AED', '#0E7490', '#B45309', '#BE185D'];

export function EmbeddingsScene({ loc, s, lang, layer, preview, last }: SceneProps) {
  const r = (preview ?? last) as EmbeddingResult | null;
  const points = loc.data.points as Point[];
  const groups = s.groups as Record<string, string>;
  const groupIds = Object.keys(groups);
  const color = (g: string) => GROUP_COLORS[groupIds.indexOf(g) % GROUP_COLORS.length];
  const near = new Set(r?.neighbors.map((n) => n.point.w));
  return (
    <>
      <div className="wz-map" role="img" aria-label={str(s, 'mapAria')}>
        <svg className="wz-map__lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
          {r?.query &&
            r.neighbors.map((n) => (
              <line key={n.point.w} x1={r.query!.x} y1={r.query!.y} x2={n.point.x} y2={n.point.y} stroke="var(--orange-2)" strokeWidth="2" vectorEffect="non-scaling-stroke" strokeDasharray="4 3" />
            ))}
        </svg>
        {points.map((p) => {
          const isQ = r?.query?.w === p.w;
          const isN = near.has(p.w);
          return (
            <span
              key={p.w}
              className={`wz-pt${isQ ? ' wz-pt--q' : ''}${isN ? ' wz-pt--n' : ''}${r?.query && !isQ && !isN ? ' wz-pt--dim' : ''}`}
              style={{ left: `${p.x}%`, top: `${p.y}%`, ['--c' as string]: color(p.group) }}
            >
              <span className="wz-pt__dot" />
              <span className="wz-pt__label">{p.w}</span>
            </span>
          );
        })}
      </div>
      <ul className="wz-legend">
        {groupIds.map((g) => (
          <li key={g}>
            <span className="wz-dot" style={{ background: color(g) }} /> {groups[g]}
          </li>
        ))}
        <li className="wz-muted">{str(s, 'dims')}</li>
      </ul>
      {r?.query ? (
        <div className="wz-stack">
          <span className="wz-strong">{str(s, 'nearest')}</span>
          {r.neighbors.map((n) => (
            <div key={n.point.w} className="wz-barrow">
              <span className="wz-barrow__label">
                <span className="wz-dot" style={{ background: color(n.point.group) }} />
                {n.point.w}
              </span>
              <span className="wz-barrow__track">
                <span className="wz-bar" style={{ width: `${n.sim * 100}%`, background: color(n.point.group) }} />
              </span>
              <span className="wz-mono wz-small wz-barrow__pct">{layer === 'simples' ? `${Math.round(n.sim * 100)}%` : fmtNum(n.sim, lang, 2)}</span>
            </div>
          ))}
          <span className="wz-muted wz-small">{str(s, 'sim')}</span>
        </div>
      ) : (
        <p className="wz-muted">{str(s, 'empty')}</p>
      )}
    </>
  );
}
