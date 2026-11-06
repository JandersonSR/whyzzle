import { useEffect } from 'react';
import { Link } from '../app/router';
import { useApp } from '../app/state';
import type { Topic } from '../content';
import type { TrackId } from '../engine/schema';
import { interpolate } from '../engine/text';
import { RecipeCard } from '../step/Parts';
import { Check } from '../ui/Art';

export function TrackPage({ topic, track }: { topic: Topic; track: TrackId }) {
  const { ui, lang, store, version } = useApp();
  const tr = topic.def.tracks.find((t) => t.id === track)!;
  const lessons = topic.lessons.filter((l) => l.track === track);
  const all = store.all();
  void version;
  useEffect(() => {
    document.title = `${tr.title[lang]} · ${topic.def.title[lang]} · Whyzzle`;
  }, [tr, topic, lang]);
  return (
    <main id="main" className="wz-main">
      <div className="wz-stack wz-stack--tight">
        <span className="wz-crumb">
          <Link href="/">{ui.nav.home}</Link> · {topic.def.title[lang]}
        </span>
        <h1 className="wz-h1">{tr.title[lang]}</h1>
        <span className="wz-sub">{tr.description[lang]}</span>
      </div>
      {lessons.length === 0 ? (
        <p className="wz-badge">{ui.home.soon}</p>
      ) : (
        <ol className="wz-lessons">
          {lessons.map((l, i) => {
            const p = all[l.def.id] ?? {};
            return (
              <li key={l.def.id}>
                <Link className="wz-card wz-lesson" href={`/${l.topic}/${l.track}/${l.slug}`} data-state={p.completed ? 'done' : p.ran ? 'tried' : 'todo'}>
                  <span className="wz-lesson__n">{p.completed ? <Check ok /> : i + 1}</span>
                  <span className="wz-stack wz-stack--tight">
                    <strong>{l.locale[lang].title}</strong>
                    <span className="wz-small wz-muted">
                      {l.locale[lang].subtitle} · {interpolate(ui.minutes, { n: l.def.minutes })}
                      {l.def.kind === 'mission' && ` · ${ui.track.mission}`}
                      {p.completed ? ` · ${ui.track.done}` : p.ran ? ` · ${ui.track.tried}` : ''}
                    </span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
      )}
      <div className="wz-row wz-wrap">
        <Link className="wz-btn wz-ghost" href={`/${topic.def.id}/${track}/receitas`}>
          {ui.track.recipes}
        </Link>
        <Link className="wz-btn wz-ghost" href={`/${topic.def.id}/${track}/professor`}>
          {ui.track.teacher}
        </Link>
      </div>
    </main>
  );
}

export function RecipesPage({ topic, track }: { topic: Topic; track: TrackId }) {
  const { ui, lang } = useApp();
  const tr = topic.def.tracks.find((t) => t.id === track)!;
  const lessons = topic.lessons.filter((l) => l.track === track);
  useEffect(() => {
    document.title = `${ui.track.recipes} · ${tr.title[lang]} · Whyzzle`;
  }, [ui, tr, lang]);
  return (
    <main id="main" className="wz-main">
      <div className="wz-stack wz-stack--tight">
        <span className="wz-crumb">
          <Link href={`/${topic.def.id}/${track}`}>
            {topic.def.title[lang]} · {tr.title[lang]}
          </Link>
        </span>
        <h1 className="wz-h1">{ui.track.recipes}</h1>
        <span className="wz-sub">{ui.track.recipesSub}</span>
      </div>
      {lessons.map((l, i) => (
        <RecipeCard key={l.def.id} lesson={l} n={i + 1} />
      ))}
    </main>
  );
}

export function TeacherPage({ topic, track }: { topic: Topic; track: TrackId }) {
  const { ui, lang } = useApp();
  const tr = topic.def.tracks.find((t) => t.id === track)!;
  const lessons = topic.lessons.filter((l) => l.track === track);
  useEffect(() => {
    document.title = `${ui.teacher.title} · ${tr.title[lang]} · Whyzzle`;
  }, [ui, tr, lang]);
  return (
    <main id="main" className="wz-main wz-teacher">
      <div className="wz-row wz-between wz-wrap">
        <div className="wz-stack wz-stack--tight">
          <span className="wz-crumb">
            <Link href={`/${topic.def.id}/${track}`}>
              {topic.def.title[lang]} · {tr.title[lang]}
            </Link>
          </span>
          <h1 className="wz-h1">{ui.teacher.title}</h1>
          <span className="wz-sub">{ui.teacher.intro}</span>
        </div>
        <button type="button" className="wz-btn wz-ghost wz-noprint" onClick={() => window.print()}>
          {ui.teacher.print}
        </button>
      </div>
      {lessons.map((l, i) => {
        const g = l.teacher[lang];
        return (
          <article key={l.def.id} className="wz-card wz-guide">
            <h2 className="wz-h3">
              {i + 1}. {l.locale[lang].title} <span className="wz-muted wz-small">· {interpolate(ui.minutes, { n: g.minutes })}</span>
            </h2>
            <h3 className="wz-h4">{ui.teacher.objectives}</h3>
            <ul>
              {g.objectives.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
            <h3 className="wz-h4">{ui.teacher.activity}</h3>
            <p>{g.activity}</p>
            <h3 className="wz-h4">{ui.teacher.discussion}</h3>
            <ul>
              {g.discussion.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
            <h3 className="wz-h4">{ui.teacher.misconceptions}</h3>
            <ul>
              {g.misconceptions.map((x) => (
                <li key={x}>{x}</li>
              ))}
            </ul>
          </article>
        );
      })}
    </main>
  );
}
