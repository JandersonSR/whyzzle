import { useApp } from '../app/state';
import { buildCommand, defaultValue, defaultValues, optionLabel, type FlagValue, type Values } from '../engine/command';
import type { CommandDef, FlagDef, Lang } from '../engine/schema';
import { fmtNum } from '../engine/text';
import { Segmented } from '../ui/Chrome';
import type { StepApi } from './useStep';

/** "--temp N  [--vezes Q]" style help line, generated from the command definition. */
export function syntaxLine(def: CommandDef, lang: Lang, textWord: string): string {
  const parts = [`${def.verb[lang]} "${textWord}"`];
  for (const f of def.flags) {
    if (f.ui === 'hidden') continue;
    let v: string;
    switch (f.type) {
      case 'number':
      case 'int':
        v = `${f.min ?? ''}–${f.max ?? ''}`;
        break;
      case 'bool':
        v = lang === 'pt' ? 'sim|nao' : 'yes|no';
        break;
      case 'enum':
        v = (f.options ?? []).map((o) => o[lang]).join('|');
        break;
      case 'list':
        v = (f.options ?? []).map((o) => o[lang]).join(',');
        break;
      default:
        v = '"…"';
    }
    const p = `--${f.alias[lang]} ${v}`;
    parts.push(f.required ? p : `[${p}]`);
  }
  return parts.join('  ');
}

export function ModeSwitch({ step, dark }: { step: StepApi; dark?: boolean }) {
  const { ui, setMode } = useApp();
  const pick = (m: 'ui' | 'cmd') => {
    // Buttons mode needs a valid command to start from.
    if (m === 'ui' && !step.live.ok) step.setInput(buildCommand(step.def.command, step.lang, defaultValues(step.def.command, step.lang)));
    setMode(m);
  };
  return (
    <Segmented
      small
      dark={dark}
      label={ui.modeAria}
      value={step.mode}
      onChange={pick}
      options={[
        { id: 'ui', label: ui.modes.ui },
        { id: 'cmd', label: ui.modes.cmd },
      ]}
    />
  );
}

function runLabel(values: Values, ui: { run: string; runTimes: string }, t: (s: string, v: Record<string, number>) => string) {
  const n = Number(values.times ?? 1);
  return n > 1 ? t(ui.runTimes, { n }) : ui.run;
}

export function ControlsPanel({ step }: { step: StepApi }) {
  const { ui, t } = useApp();
  const { def, lang, loc } = step;
  const cmd = def.command;
  const values: Values = step.live.ok ? step.live.values : defaultValues(cmd, lang);
  const set = (name: string, v: FlagValue | undefined) => {
    const next = { ...values };
    if (v === undefined) delete next[name];
    else next[name] = v;
    step.setInput(buildCommand(cmd, lang, next));
  };
  const arg = String(values[cmd.arg.name] ?? '');
  const argId = `wz-arg-${def.id}`;

  return (
    <div className="wz-card wz-panel">
      <div className="wz-panel__head">
        <span className="wz-eyebrow wz-eyebrow--blue">{ui.panelLabel}</span>
        <ModeSwitch step={step} />
      </div>

      <div className="wz-field">
        <label htmlFor={argId} className="wz-field__label">
          {loc.controls.arg}
        </label>
        {cmd.arg.examples.length > 1 && (
          <div className="wz-chips" role="group" aria-label={ui.examplesLabel}>
            {cmd.arg.examples.map((ex) => (
              <button
                key={ex[lang]}
                type="button"
                className="wz-btn wz-chip"
                aria-pressed={arg === ex[lang]}
                onClick={() => set(cmd.arg.name, ex[lang])}
              >
                {ex[lang]}
              </button>
            ))}
          </div>
        )}
        {cmd.arg.ui === 'textarea' || arg.length > 60 ? (
          <textarea id={argId} className="wz-input wz-input--area" rows={3} value={arg} onChange={(e) => set(cmd.arg.name, e.target.value)} />
        ) : (
          <input id={argId} className="wz-input" type="text" value={arg} onChange={(e) => set(cmd.arg.name, e.target.value)} />
        )}
      </div>

      {cmd.flags.map((f) => (
        <FlagControl key={f.name} f={f} lang={lang} label={loc.controls[f.name] ?? f.name} value={values[f.name]} onChange={(v) => set(f.name, v)} noneLabel={ui.none} />
      ))}

      <button type="button" className="wz-btn wz-run wz-run--big" onClick={step.run}>
        {runLabel(values, ui, t)}
      </button>

      {step.state.error && (
        <div role="alert" className="wz-alert">
          <strong>{ui.errTitle}</strong>
          <span>{step.errorText}</span>
        </div>
      )}

      <div className="wz-equiv">
        <span className="wz-equiv__label">{ui.equivLabel}</span>
        <code className="wz-equiv__code">
          <span aria-hidden="true">› </span>
          {step.state.input}
        </code>
      </div>
    </div>
  );
}

function FlagControl({
  f,
  lang,
  label,
  value,
  onChange,
  noneLabel,
}: {
  f: FlagDef;
  lang: Lang;
  label: string;
  value: FlagValue | undefined;
  onChange(v: FlagValue | undefined): void;
  noneLabel: string;
}) {
  const id = `wz-flag-${f.name}`;
  const ui = f.ui ?? (f.type === 'bool' ? 'switch' : f.type === 'list' ? 'checkboxes' : f.type === 'enum' ? 'select' : f.type === 'string' ? 'text' : 'slider');
  if (ui === 'hidden') return null;

  if (ui === 'slider') {
    const min = f.uiMin ?? f.min ?? 0;
    const max = f.uiMax ?? f.max ?? 10;
    const v = Number(value ?? defaultValue(f, lang) ?? min);
    return (
      <div className="wz-field">
        <label htmlFor={id} className="wz-field__row">
          <span className="wz-field__label">{label}</span>
          <span className="wz-mono wz-field__value">{fmtNum(v, lang)}</span>
        </label>
        <input id={id} className="wz-range" type="range" min={min} max={max} step={f.step ?? 1} value={v} onChange={(e) => onChange(Number(e.target.value))} />
        <div className="wz-range__ends" aria-hidden="true">
          <span>{fmtNum(min, lang)}</span>
          <span>{fmtNum(max, lang)}</span>
        </div>
      </div>
    );
  }

  if (ui === 'toggle10' || ui === 'switch') {
    const checked = ui === 'toggle10' ? Number(value ?? 1) > 1 : value === true;
    return (
      <label className="wz-check">
        <input type="checkbox" checked={checked} onChange={(e) => onChange(ui === 'toggle10' ? (e.target.checked ? 10 : 1) : e.target.checked)} />
        <span>{label}</span>
      </label>
    );
  }

  if (ui === 'text') {
    return (
      <div className="wz-field">
        <label htmlFor={id} className="wz-field__label">
          {label}
        </label>
        <input id={id} className="wz-input" type="text" value={typeof value === 'string' ? value : ''} onChange={(e) => onChange(e.target.value.trim() ? e.target.value : undefined)} />
      </div>
    );
  }

  if (ui === 'select') {
    const opts = f.options ?? [];
    return (
      <div className="wz-field">
        <span className="wz-field__label" id={id}>
          {label}
        </span>
        <div className="wz-chips" role="group" aria-labelledby={id}>
          <button type="button" className="wz-btn wz-chip" aria-pressed={value === undefined} onClick={() => onChange(undefined)}>
            {noneLabel}
          </button>
          {opts.map((o) => (
            <button key={o.id} type="button" className="wz-btn wz-chip" aria-pressed={value === o.id} onClick={() => onChange(o.id)}>
              {optionLabel(f, o.id, lang)}
            </button>
          ))}
        </div>
      </div>
    );
  }

  // checkboxes (list)
  const list = Array.isArray(value) ? value : [];
  return (
    <fieldset className="wz-field wz-fieldset">
      <legend className="wz-field__label">{label}</legend>
      <div className="wz-checks">
        {(f.options ?? []).map((o) => (
          <label key={o.id} className="wz-check">
            <input
              type="checkbox"
              checked={list.includes(o.id)}
              onChange={(e) => {
                const ids = (f.options ?? []).map((x) => x.id).filter((x) => (x === o.id ? e.target.checked : list.includes(x)));
                onChange(ids);
              }}
            />
            <span>{o[lang]}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export function Terminal({ step }: { step: StepApi }) {
  const { ui } = useApp();
  const id = `wz-cmd-${step.def.id}`;
  return (
    <div className="wz-card wz-term">
      <div className="wz-panel__head">
        <label htmlFor={id} className="wz-eyebrow wz-eyebrow--light">
          {ui.cmdLabel}
        </label>
        <ModeSwitch step={step} dark />
      </div>
      <div className="wz-term__box">
        <span aria-hidden="true" className="wz-term__prompt">
          ›
        </span>
        <input
          id={id}
          className="wz-term__input"
          type="text"
          spellCheck={false}
          autoComplete="off"
          autoCapitalize="off"
          autoCorrect="off"
          value={step.state.input}
          onChange={(e) => step.setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault();
              void step.run();
            }
          }}
        />
        <button type="button" className="wz-btn wz-run" onClick={step.run}>
          {ui.run}
        </button>
      </div>
      <p className="wz-term__help">
        <span>{ui.cmdHelpLabel} </span>
        <code>{syntaxLine(step.def.command, step.lang, ui.syntaxText)}</code>
      </p>
      {step.state.error && (
        <div role="alert" className="wz-term__err">
          <strong>{ui.errTitle}</strong>
          <span>{step.errorText}</span>
        </div>
      )}
    </div>
  );
}
