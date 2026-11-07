import type { ReactNode } from 'react';
import { Link } from '../app/router';
import { useApp } from '../app/state';
import type { Lesson } from '../content';
import { feedbackKey, type Phase } from '../engine/stepMachine';
import { interpolate } from '../engine/text';
import { Check, RecipeIcon, Whyz } from '../ui/Art';
import { Segmented } from '../ui/Chrome';
import type { StepApi } from './useStep';

export function Stepper({ step }: { step: StepApi }) {
  const { ui } = useApp();
  const { phase, maxPhase } = step.state;
  return (
    <nav aria-label={ui.cycleAria} className="wz-cycle">
      {ui.cycle.map((label, i) => {
        const reached = i <= maxPhase;
        return (
          <button
            key={label}
            type="button"
            className="wz-btn wz-cycle__item"
            data-state={i === phase ? 'current' : reached ? 'reached' : 'locked'}
            disabled={!reached}
            aria-current={i === phase ? 'step' : undefined}
            onClick={() => step.goto(i as Phase)}
          >
            <span className="wz-cycle__n">{i + 1}</span>
            {label}
          </button>
        );
      })}
    </nav>
  );
}

export function Coach({ step, next }: { step: StepApi; next?: Lesson }) {
  const { ui, lang, layer } = useApp();
  const { loc, def, mode, state } = step;
  const say = (text: string) => (
    <p className="wz-coach__say">
      <strong>{ui.whyzName}</strong> {text}
    </p>
  );
  let body: ReactNode;
  switch (state.phase) {
    case 0:
      body = (
        <>
          {say(loc.predict!.question)}
          <div className="wz-options">
            {def.predict!.options.map((o) => (
              <button key={o} type="button" className="wz-btn wz-option" onClick={() => step.predict(o)}>
                {loc.predict!.options[o]}
              </button>
            ))}
          </div>
        </>
      );
      break;
    case 1:
      body = (
        <>
          {say(loc.coach[mode])}
          {state.prediction && (
            <span className="wz-muted">
              {ui.yourGuess} <strong>{loc.predict!.options[state.prediction]}</strong>
            </span>
          )}
        </>
      );
      break;
    case 2:
      body = (
        <>
          {say(loc.feedback![feedbackKey(state, def.predict!.answer)])}
          <p className="wz-muted">{loc.tryNext![mode]}</p>
          <button type="button" className="wz-btn wz-cta" onClick={() => step.goto(3)}>
            {ui.whyBtn}
          </button>
        </>
      );
      break;
    case 3:
      body = <Why step={step} layerLabel={ui.layers[layer]} onBreak={() => step.goto(4)} breakLabel={ui.breakBtn} />;
      break;
    default: {
      const br = state.breakResult;
      body = (
        <>
          {say(loc.break!.mission[mode])}
          {br && (
            <p className={`wz-result${state.broke ? ' wz-result--broke' : ''}`}>
              {interpolate(state.broke ? loc.break!.success : loc.break!.calm, br.vars)}
            </p>
          )}
          {state.broke && (
            <div className="wz-done">
              <span className="wz-done__badge">
                <Check ok /> {ui.done}
              </span>
              {next ? (
                <Link className="wz-btn wz-cta wz-cta--ink" href={`/${next.topic}/${next.track}/${next.slug}`}>
                  {interpolate(ui.nextStep, { title: next.locale[lang].title })} →
                </Link>
              ) : (
                <Link className="wz-btn wz-cta wz-cta--ink" href="/">
                  {ui.trackEnd}
                </Link>
              )}
            </div>
          )}
        </>
      );
    }
  }
  return (
    <div className="wz-card wz-coach" aria-live="polite">
      <Whyz mood={state.broke ? 'proud' : 'happy'} />
      <div className="wz-coach__body">{body}</div>
    </div>
  );
}

export function Why({ step, layerLabel, onBreak, breakLabel, title }: { step: StepApi; layerLabel: string; onBreak?: () => void; breakLabel?: string; title?: string }) {
  const { ui, layer } = useApp();
  const { loc } = step;
  return (
    <>
      <div className="wz-why__head">
        <h2 className="wz-h2">{title ?? ui.whyTitle}</h2>
        <span className="wz-badge">{layerLabel}</span>
      </div>
      <p className="wz-why__text">{loc.why[layer]}</p>
      {loc.formula && layer !== 'simples' && <code className="wz-formula">{loc.formula}</code>}
      <span className="wz-muted wz-small">{ui.layerTip}</span>
      {onBreak && (
        <button type="button" className="wz-btn wz-cta wz-cta--orange" onClick={onBreak}>
          {breakLabel}
        </button>
      )}
    </>
  );
}

export function Hints({ step }: { step: StepApi }) {
  const { ui, t } = useApp();
  const list = step.loc.hints?.[step.mode] ?? [];
  const shown = list.slice(0, step.state.hints);
  return (
    <div className="wz-card wz-hints">
      <div className="wz-hints__head">
        <span className="wz-strong">
          {ui.hintsLabel} <span className="wz-muted">({step.state.hints}/3)</span>
        </span>
        {step.state.hints < 3 && (
          <button type="button" className="wz-btn wz-ghost" onClick={step.hint}>
            {step.state.hints === 0 ? ui.hintFirst : ui.hintMore}
          </button>
        )}
      </div>
      {shown.map((h, i) => (
        <div key={i} className="wz-hint">
          <span className="wz-hint__n">{t(ui.hintN, { n: i + 1 })}</span>
          <span className={i === 2 && step.mode === 'cmd' ? 'wz-mono' : undefined}>{h}</span>
        </div>
      ))}
    </div>
  );
}

export function RecipeCard({ lesson, n }: { lesson: Lesson; n?: number }) {
  const { ui, lang } = useApp();
  const loc = lesson.locale[lang];
  return (
    <section className="wz-card wz-recipe" aria-label={ui.recipeLabel}>
      <div className="wz-recipe__head">
        <RecipeIcon />
        <h2 className="wz-h3">{n ? `${n}. ${loc.title}` : ui.recipeLabel}</h2>
        {!n && <span className="wz-muted wz-small">{ui.recipeSub}</span>}
      </div>
      <ol className="wz-recipe__steps">
        {loc.recipe.steps.map((s) => (
          <li key={s}>{s}</li>
        ))}
      </ol>
      <div className="wz-recipe__ok">
        <Check ok />
        <span>
          <strong>{ui.recipeOkLabel}</strong> {loc.recipe.ok}
        </span>
      </div>
    </section>
  );
}

function fmtSize(mb: number, lang: 'pt' | 'en'): string {
  return mb >= 1000 ? `${(mb / 1000).toFixed(1).replace('.', lang === 'pt' ? ',' : '.')} GB` : `${mb} MB`;
}

/** "Who answers": simulated, a real model in the browser, or the person's own key. */
export function ExecutorPanel({ step }: { step: StepApi }) {
  const { ui, lang, t } = useApp();
  const { status, prep } = step;
  const realInfo = (step.last as { real?: { model: string } } | null)?.real;
  if (step.offered.length < 2) {
    return (
      <div className="wz-exec">
        <span className="wz-exec__dot" aria-hidden="true" />
        <span>{ui.real.simNote}</span>
      </div>
    );
  }
  return (
    <div className="wz-exec wz-exec--panel">
      <div className="wz-row wz-wrap wz-between">
        <span className="wz-strong">{ui.real.label}</span>
        <Segmented small label={ui.real.label} value={step.execId} onChange={step.setExecutor} options={step.offered.map((e) => ({ id: e.id, label: e.label[lang] }))} />
      </div>
      {step.execId === 'simulado' && <span>{ui.real.simNote}</span>}
      {status.state === 'needsDownload' && !prep.loading && (
        <div className="wz-stack wz-stack--tight">
          <span>{t(ui.real.download, { model: status.model.label, size: fmtSize(status.model.sizeMB, lang) })}</span>
          <span className="wz-muted">{status.model.note[lang]}</span>
          <button type="button" className="wz-btn wz-cta" onClick={step.prepare}>
            {ui.real.downloadBtn}
          </button>
        </div>
      )}
      {prep.loading && (
        <div className="wz-stack wz-stack--tight" aria-live="polite">
          <span>{t(ui.real.downloading, { pct: prep.progress?.ratio != null ? `${Math.round(prep.progress.ratio * 100)}%` : '' })}</span>
          <div className="wz-meter">
            <span className="wz-bar" style={{ width: `${(prep.progress?.ratio ?? 0.05) * 100}%`, background: 'var(--blue)' }} />
          </div>
        </div>
      )}
      {prep.error && <span className="wz-red">{(ui.real.errors as Record<string, string>)[prep.error]}</span>}
      {status.state === 'unsupported' && <span className="wz-red">{status.reason[lang]}</span>}
      {status.state === 'needsKey' && (
        <span>
          {ui.real.needsKey}{' '}
          <Link href="/sua-chave">{ui.real.keyLink}</Link>
        </span>
      )}
      {status.state === 'ready' && step.execId === 'no-navegador' && (
        <span>
          {t(ui.real.ready, { model: status.label })} {ui.real.privacy}
        </span>
      )}
      {status.state === 'ready' && step.execId === 'sua-chave' && (
        <span>
          {t(ui.real.keyReady, { model: status.label })} · <Link href="/sua-chave">{ui.real.keyLink}</Link>
        </span>
      )}
      {realInfo && <span className="wz-badge wz-badge--green">{t(ui.real.realBadge, { model: realInfo.model })}</span>}
      {step.last?.flags.includes('resisted') && <span className="wz-note">{ui.real.resisted}</span>}
    </div>
  );
}
