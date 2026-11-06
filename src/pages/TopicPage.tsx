import { useEffect } from 'react';
import { Link } from '../app/router';
import { useApp } from '../app/state';
import type { Topic } from '../content';
import { interpolate } from '../engine/text';

export function TopicPage({ topic }: { topic: Topic }) {
  const { ui, lang, store, version } = useApp();
  const all = store.all();
  void version;
  useEffect(() => {
    document.title = `${topic.def.title[lang]} · Whyzzle`;
  }, [topic, lang]);
  return (
    <main id="main" className="wz-main">
      <div className="wz-stack wz-stack--tight">
        <span className="wz-crumb">
          <Link href="/">{ui.catalog.backHome}</Link> · {ui.areas[topic.def.area]}
        </span>
        <h1 className="wz-h1">{topic.def.title[lang]}</h1>
        <span className="wz-sub">{topic.def.tagline[lang]}</span>
      </div>
      <div className="wz-tracks">
        {topic.def.tracks.map((tr) => {
          const lessons = topic.lessons.filter((l) => l.track === tr.id);
          const done = lessons.filter((l) => all[l.def.id]?.completed).length;
          const started = lessons.some((l) => all[l.def.id]?.ran);
          const nextL = lessons.find((l) => !all[l.def.id]?.completed) ?? lessons[0];
          const ready = tr.status === 'ready' && lessons.length > 0;
          return (
            <article key={tr.id} className={`wz-card wz-track${ready ? '' : ' wz-track--soon'}`}>
              <span className="wz-eyebrow">{tr.audience[lang]}</span>
              <h2 className="wz-h3">{tr.title[lang]}</h2>
              <p>{tr.description[lang]}</p>
              {ready ? (
                <>
                  <div className="wz-meter" aria-hidden="true">
                    <span className="wz-bar" style={{ width: `${(done / lessons.length) * 100}%`, background: 'var(--green)' }} />
                  </div>
                  <span className="wz-small wz-muted">{interpolate(ui.home.progress, { done, total: lessons.length })}</span>
                  <div className="wz-row wz-wrap">
                    <Link className="wz-btn wz-cta" href={`/${topic.def.id}/${tr.id}/${nextL.slug}`}>
                      {started ? ui.home.continue : ui.home.start} →
                    </Link>
                    <Link className="wz-btn wz-ghost" href={`/${topic.def.id}/${tr.id}`}>
                      {interpolate(ui.home.steps, { n: lessons.length })}
                    </Link>
                  </div>
                </>
              ) : (
                <span className="wz-badge">{ui.home.soon}</span>
              )}
            </article>
          );
        })}
      </div>
    </main>
  );
}
