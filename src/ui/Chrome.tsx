import { Link } from '../app/router';
import { useApp } from '../app/state';
import { LANGS, LAYERS } from '../engine/schema';
import { LogoMark } from './Art';

export function Segmented<T extends string>({
  label,
  options,
  value,
  onChange,
  dark,
  small,
}: {
  label: string;
  options: { id: T; label: string }[];
  value: T;
  onChange(v: T): void;
  dark?: boolean;
  small?: boolean;
}) {
  return (
    <div role="group" aria-label={label} className={`wz-seg${dark ? ' wz-seg--dark' : ''}${small ? ' wz-seg--small' : ''}`}>
      {options.map((o) => (
        <button key={o.id} type="button" className="wz-btn" aria-pressed={o.id === value} onClick={() => onChange(o.id)}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Header() {
  const { ui, lang, setLang, layer, setLayer, theme, toggleTheme } = useApp();
  return (
    <header className="wz-topbar">
      <a className="wz-skip" href="#main">
        {ui.skip}
      </a>
      <div className="wz-topbar__inner">
        <Link href="/" className="wz-brand" aria-label="Whyzzle">
          <LogoMark />
          <span className="wz-brand__text">
            <span className="wz-brand__name">Whyzzle</span>
            <span className="wz-brand__tag">{ui.tag}</span>
          </span>
        </Link>
        <div className="wz-topbar__controls">
          <Segmented label={ui.layerAria} options={LAYERS.map((id) => ({ id, label: ui.layers[id] }))} value={layer} onChange={setLayer} />
          <button
            type="button"
            className="wz-btn wz-theme"
            aria-pressed={theme === 'dark'}
            aria-label={ui.themeDark}
            title={theme === 'dark' ? ui.themeToLight : ui.themeToDark}
            onClick={toggleTheme}
          >
            {theme === 'dark' ? <SunIcon /> : <MoonIcon />}
          </button>
          <div role="group" aria-label={ui.langAria} className="wz-lang">
            {LANGS.map((l) => (
              <button key={l} type="button" className="wz-btn" aria-pressed={l === lang} onClick={() => setLang(l)}>
                {l.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>
    </header>
  );
}

function MoonIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
    </svg>
  );
}

function SunIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <circle cx="12" cy="12" r="4.5" fill="none" stroke="currentColor" strokeWidth="2" />
      <path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

export function Footer() {
  const { ui } = useApp();
  return (
    <footer className="wz-footer">
      <p>{ui.footer}</p>
    </footer>
  );
}
