import { useMemo, useState } from 'react';
import { Link } from '../app/router';
import { useApp } from '../app/state';
import type { Topic } from '../content';
import { AREAS, type Area } from '../engine/schema';
import { interpolate, normalize } from '../engine/text';
import { Whyz } from '../ui/Art';

export function Home() {
  const { ui, lang, topics, store, version } = useApp();
  const [q, setQ] = useState('');
  const [area, setArea] = useState<Area | 'all'>('all');
  const [confirm, setConfirm] = useState(false);
  void version;

  const shown = useMemo(() => {
    const nq = normalize(q);
    return topics.filter((t) => {
      if (area !== 'all' && t.def.area !== area) return false;
      if (!nq) return true;
      const hay = normalize([t.def.title.pt, t.def.title.en, t.def.tagline[lang], ...t.def.tracks.map((tr) => tr.description[lang])].join(' '));
      return nq.split(/\s+/).every((w) => hay.includes(w));
    });
  }, [topics, area, q, lang]);

  const usedAreas = AREAS.filter((a) => topics.some((t) => t.def.area === a));

  return (
    <main id="main" className="wz-main">
      <section className="wz-hero">
        <Whyz className="wz-hero__mascot" />
        <div className="wz-stack">
          <h1 className="wz-display">{ui.home.heroTitle}</h1>
          <p className="wz-lead">{ui.home.heroSub}</p>
        </div>
      </section>

      <section className="wz-stack" aria-labelledby="wz-catalog">
        <div className="wz-stack wz-stack--tight">
          <h2 className="wz-h2" id="wz-catalog">
            {ui.catalog.title}
          </h2>
          <p className="wz-muted">{interpolate(ui.catalog.sub, { n: topics.length })}</p>
        </div>
        <div className="wz-filters">
          <label className="wz-search">
            <span className="wz-sr">{ui.catalog.search}</span>
            <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="11" cy="11" r="7" fill="none" stroke="currentColor" strokeWidth="2" />
              <path d="M20 20l-4-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
            </svg>
            <input type="search" value={q} placeholder={ui.catalog.searchPh} onChange={(e) => setQ(e.target.value)} />
          </label>
          <div className="wz-chips" role="group" aria-label={ui.catalog.areas}>
            {(['all', ...usedAreas] as const).map((a) => (
              <button key={a} type="button" className="wz-btn wz-chip" aria-pressed={area === a} onClick={() => setArea(a)}>
                {ui.areas[a]}
              </button>
            ))}
          </div>
        </div>
        {shown.length === 0 ? (
          <p className="wz-muted">{ui.catalog.empty}</p>
        ) : (
          <ul className="wz-topics">
            {shown.map((t) => (
              <li key={t.def.id}>
                <TopicCard topic={t} done={t.lessons.filter((l) => store.get(l.def.id).completed).length} />
              </li>
            ))}
          </ul>
        )}
      </section>

      <section className="wz-card wz-how">
        <h2 className="wz-h3">{ui.home.how}</h2>
        <ol className="wz-how__list">
          {ui.home.howItems.map((h) => (
            <li key={h}>{h}</li>
          ))}
        </ol>
      </section>

      <div className="wz-row">
        <button
          type="button"
          className="wz-btn wz-ghost wz-small"
          onClick={() => {
            if (!confirm) return setConfirm(true);
            store.reset();
            setConfirm(false);
          }}
        >
          {confirm ? ui.home.resetConfirm : ui.home.resetAll}
        </button>
      </div>
    </main>
  );
}

function TopicCard({ topic, done }: { topic: Topic; done: number }) {
  const { ui, lang } = useApp();
  const ready = topic.def.tracks.filter((tr) => tr.status === 'ready' && topic.lessons.some((l) => l.track === tr.id));
  return (
    <Link href={`/${topic.def.id}`} className={`wz-card wz-topic${ready.length ? '' : ' wz-topic--soon'}`}>
      <div className="wz-row wz-between wz-wrap">
        <span className="wz-eyebrow">{ui.areas[topic.def.area]}</span>
        {ready.length ? (
          <span className="wz-badge wz-badge--green">{interpolate(ui.catalog.ready, { n: ready.length })}</span>
        ) : (
          <span className="wz-badge">{ui.catalog.soon}</span>
        )}
      </div>
      <h3 className="wz-h3">{topic.def.title[lang]}</h3>
      <p className="wz-topic__tag">{topic.def.tagline[lang]}</p>
      <div className="wz-topic__tracks" aria-label={ui.catalog.tracksLabel}>
        {topic.def.tracks.map((tr) => (
          <span key={tr.id} data-ready={ready.includes(tr) ? 'yes' : 'no'}>
            {tr.title[lang]}
          </span>
        ))}
      </div>
      {topic.lessons.length > 0 && (
        <div className="wz-meter" aria-hidden="true">
          <span className="wz-bar" style={{ width: `${(done / topic.lessons.length) * 100}%`, background: 'var(--green)' }} />
        </div>
      )}
    </Link>
  );
}
