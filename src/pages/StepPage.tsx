import { useEffect, useRef } from 'react';
import { Link } from '../app/router';
import { useApp } from '../app/state';
import type { Lesson, Topic } from '../content';
import { interpolate } from '../engine/text';
import { scenes } from '../scenes';
import { str } from '../scenes/types';
import { ControlsPanel, Terminal } from '../step/Controls';
import { Coach, ExecutorBadge, Hints, RecipeCard, Stepper, Why } from '../step/Parts';
import { useStep, type StepApi } from '../step/useStep';
import { Check, Whyz } from '../ui/Art';

export function StepPage({ topic, lesson }: { topic: Topic; lesson: Lesson }) {
  const { ui, lang, store, version } = useApp();
  const step = useStep(lesson);
  const { loc, def } = step;
  const track = topic.lessons.filter((l) => l.track === lesson.track);
  const idx = track.indexOf(lesson);
  const next = track[idx + 1];
  const trackDef = topic.def.tracks.find((t) => t.id === lesson.track)!;
  const all = store.all();
  void version;

  useEffect(() => {
    document.title = `${loc.title} · Whyzzle`;
  }, [loc.title]);

  return (
    <main id="main" className="wz-main">
      <div className="wz-titlebar">
        <div className="wz-stack wz-stack--tight">
          <span className="wz-crumb">
            <Link href={`/${topic.def.id}/${lesson.track}`}>
              {topic.def.title[lang]} · {trackDef.title[lang]}
            </Link>{' '}
            · {def.kind === 'mission' ? ui.mission.label : interpolate(ui.stepOf, { n: idx + 1, total: track.filter((l) => l.def.kind === 'step').length })}
          </span>
          <h1 className="wz-h1">{loc.title}</h1>
          <span className="wz-sub">{loc.subtitle}</span>
        </div>
        <ol aria-label={ui.progressAria} className="wz-dots">
          {track.map((l, i) => {
            const p = all[l.def.id] ?? {};
            const st = l === lesson ? 'current' : p.completed ? 'done' : p.ran ? 'tried' : 'todo';
            return (
              <li key={l.def.id}>
                <Link href={`/${l.topic}/${l.track}/${l.slug}`} className="wz-dots__dot" data-state={st} data-mission={l.def.kind === 'mission' ? 'yes' : undefined} title={`${i + 1}. ${l.locale[lang].title}`}>
                  <span className="wz-sr">{`${i + 1}. ${l.locale[lang].title}`}</span>
                </Link>
              </li>
            );
          })}
        </ol>
      </div>

      {def.kind === 'mission' ? <MissionBody step={step} /> : <StepBody step={step} next={next} />}

      <RecipeCard lesson={lesson} />
    </main>
  );
}

function SceneCard({ step }: { step: StepApi }) {
  const S = scenes[step.def.scene];
  const ref = useRef<HTMLElement>(null);
  const runs = step.state.runs.length;
  // On phones the scene sits below the controls: after a run, bring it into view.
  useEffect(() => {
    const el = ref.current;
    if (!runs || !el) return;
    if (el.getBoundingClientRect().top > window.innerHeight * 0.75) {
      const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
      el.scrollIntoView({ behavior: reduce ? 'auto' : 'smooth', block: 'start' });
    }
  }, [runs]);
  const s = step.loc.scene;
  const label = step.layer === 'simples' && s.labelSimple ? str(s, 'labelSimple') : s.labelTech ? str(s, 'labelTech') : str(s, 'label');
  return (
    <section ref={ref} className="wz-card wz-scene" aria-label={label}>
      <div className="wz-row wz-between wz-wrap">
        <span className="wz-eyebrow">{label}</span>
      </div>
      {S ? (
        <S
          lesson={step.lesson}
          loc={step.loc}
          s={s}
          lang={step.lang}
          layer={step.layer}
          values={step.live.ok ? step.live.values : null}
          preview={step.preview}
          last={step.last}
          runs={step.state.runs}
        />
      ) : (
        <p className="wz-muted">scene “{step.def.scene}” missing</p>
      )}
      <ExecutorBadge step={step} />
    </section>
  );
}

function StepBody({ step, next }: { step: StepApi; next?: Lesson }) {
  return (
    <>
      <Stepper step={step} />
      <div className="wz-cols">
        <section className="wz-col">
          <div className="wz-card wz-mission">
            <MissionLabel />
            <p className="wz-mission__text">{step.loc.mission}</p>
          </div>
          <Coach step={step} next={next} />
          {step.mode === 'ui' ? <ControlsPanel step={step} /> : <Terminal step={step} />}
          <Hints step={step} />
        </section>
        <SceneCard step={step} />
      </div>
    </>
  );
}

function MissionLabel() {
  const { ui } = useApp();
  return <span className="wz-eyebrow wz-eyebrow--orange">{ui.missionLabel}</span>;
}

function MissionBody({ step }: { step: StepApi }) {
  const { ui, layer, lang, topics } = useApp();
  const passed = step.state.broke;
  const vars = step.state.breakResult?.vars;
  const topic = topics.find((t) => t.def.id === step.lesson.topic)!;
  return (
    <div className="wz-cols">
      <section className="wz-col">
        <div className="wz-card wz-mission wz-mission--final">
          <MissionLabel />
          <p className="wz-mission__text">{step.loc.mission}</p>
          <span className="wz-muted wz-small">{ui.mission.noHints}</span>
        </div>
        <div className="wz-card wz-coach" aria-live="polite">
          <Whyz mood={passed ? 'proud' : 'happy'} />
          <div className="wz-coach__body">
            {passed ? (
              <>
                <p className="wz-result wz-result--broke">{interpolate(step.loc.success ?? '', vars)}</p>
                <Why step={step} layerLabel={ui.layers[layer]} title={ui.mission.debrief} />
                <div className="wz-done">
                  <span className="wz-done__badge">
                    <Check ok /> {str(step.loc.scene, 'trackDone')}
                  </span>
                  <Link className="wz-btn wz-cta wz-cta--ink" href={`/${topic.def.id}/${step.lesson.track}/receitas`}>
                    {ui.mission.recipes}
                  </Link>
                </div>
              </>
            ) : (
              <p className="wz-coach__say">
                <strong>{ui.whyzName}</strong> {step.loc.coach[step.mode]}
              </p>
            )}
          </div>
        </div>
        {step.mode === 'ui' ? <ControlsPanel step={step} /> : <Terminal step={step} />}
        <span className="wz-sr">{lang}</span>
      </section>
      <SceneCard step={step} />
    </div>
  );
}
