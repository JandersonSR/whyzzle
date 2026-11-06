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
  const { ui, lang, setLang, layer, setLayer } = useApp();
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

export function Footer() {
  const { ui } = useApp();
  return (
    <footer className="wz-footer">
      <p>{ui.footer}</p>
    </footer>
  );
}
