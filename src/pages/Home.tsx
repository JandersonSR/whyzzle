import { useState } from 'react';
import { Link } from '../app/router';
import { useApp } from '../app/state';
import { interpolate } from '../engine/text';
import { Whyz } from '../ui/Art';

export function Home() {
  const { ui, lang, topics, store, version } = useApp();
  const [confirm, setConfirm] = useState(false);
  const all = store.all();
  void version;
  return (
    <main id="main" className="wz-main">
      <section className="wz-hero">
        <Whyz className="wz-hero__mascot" />
        <div className="wz-stack">
          <h1 className="wz-display">{ui.home.heroTitle}</h1>
          <p className="wz-lead">{ui.home.heroSub}</p>
        </div>
      </section>

      {topics.map((topic) => (
        <section key={topic.def.id} className="wz-stack">
          <div className="wz-stack wz-stack--tight">
            <h2 className="wz-h2">{topic.def.title[lang]}</h2>
            <p className="wz-muted">{topic.def.tagline[lang]}</p>
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
                  <h3 className="wz-h3">{tr.title[lang]}</h3>
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
        </section>
      ))}

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
