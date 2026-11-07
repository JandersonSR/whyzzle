import { useEffect, useState } from 'react';
import { useApp } from '../app/state';
import { forgetKey, getKeyConfig, listModels, PROVIDERS, saveKeyConfig, suggestModel, ByokError, type ProviderId } from '../runtime/byok';

/** /sua-chave: set up the person's own API key (stored only on this device, if they choose). */
export function KeyPage() {
  const { ui, t } = useApp();
  const k = ui.key;
  const saved = getKeyConfig();
  const [provider, setProvider] = useState<ProviderId>(saved?.provider ?? 'anthropic');
  const [baseUrl, setBaseUrl] = useState(saved?.baseUrl ?? PROVIDERS.find((p) => p.id === 'compatible')!.defaultBase!);
  const [key, setKey] = useState(saved?.key ?? '');
  const [remember, setRemember] = useState(saved?.remember ?? false);
  const [models, setModels] = useState<string[]>(saved?.model ? [saved.model] : []);
  const [model, setModel] = useState(saved?.model ?? '');
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    document.title = `${k.title} · Whyzzle`;
  }, [k.title]);

  const test = async () => {
    setBusy(true);
    setMsg(null);
    try {
      const list = await listModels({ provider, key: key.trim(), baseUrl });
      setModels(list);
      const pick = list.includes(model) ? model : suggestModel(provider, list);
      setModel(pick);
      setMsg({ ok: true, text: t(k.found, { n: list.length }) });
    } catch (e) {
      const kind = e instanceof ByokError ? e.kind : 'other';
      setMsg({ ok: false, text: t((ui.real.errors as Record<string, string>)[kind], { value: (e as Error).message.slice(0, 160) }) });
    }
    setBusy(false);
  };

  return (
    <main id="main" className="wz-main wz-keypage">
      <div className="wz-stack wz-stack--tight">
        <h1 className="wz-h1">{k.title}</h1>
        <span className="wz-sub">{k.intro}</span>
      </div>
      <p className="wz-note wz-note--warn">{k.warn}</p>
      {saved && <span className="wz-badge wz-badge--green">{t(k.current, { provider: PROVIDERS.find((p) => p.id === saved.provider)?.label, model: saved.model })}</span>}
      <div className="wz-card wz-panel">
        <div className="wz-field">
          <label className="wz-field__label" htmlFor="wz-prov">
            {k.provider}
          </label>
          <select id="wz-prov" className="wz-input" value={provider} onChange={(e) => { setProvider(e.target.value as ProviderId); setModels([]); setModel(''); }}>
            {PROVIDERS.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
        </div>
        {provider === 'compatible' && (
          <div className="wz-field">
            <label className="wz-field__label" htmlFor="wz-base">
              {k.baseUrl}
            </label>
            <input id="wz-base" className="wz-input" type="url" value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)} />
          </div>
        )}
        <div className="wz-field">
          <label className="wz-field__label" htmlFor="wz-key">
            {k.key}
          </label>
          <input id="wz-key" className="wz-input wz-mono" type="password" autoComplete="off" spellCheck={false} placeholder={PROVIDERS.find((p) => p.id === provider)?.keyHint} value={key} onChange={(e) => setKey(e.target.value)} />
        </div>
        <label className="wz-check">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          <span>{k.remember}</span>
        </label>
        <button type="button" className="wz-btn wz-ghost" disabled={!key.trim() || busy} onClick={test}>
          {busy ? k.testing : k.test}
        </button>
        {msg && <span className={msg.ok ? 'wz-small' : 'wz-small wz-red'} role="status">{msg.text}</span>}
        {models.length > 0 && (
          <div className="wz-field">
            <label className="wz-field__label" htmlFor="wz-model">
              {k.model}
            </label>
            <select id="wz-model" className="wz-input" value={model} onChange={(e) => setModel(e.target.value)}>
              {models.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        )}
        <div className="wz-row wz-wrap">
          <button
            type="button"
            className="wz-btn wz-cta"
            disabled={!key.trim() || !model}
            onClick={() => {
              saveKeyConfig({ provider, key: key.trim(), model, baseUrl: provider === 'compatible' ? baseUrl : undefined, remember });
              setMsg({ ok: true, text: k.saved });
            }}
          >
            {k.save}
          </button>
          <button
            type="button"
            className="wz-btn wz-ghost"
            onClick={() => {
              forgetKey();
              setKey('');
              setModels([]);
              setModel('');
              setMsg({ ok: true, text: k.forgotten });
            }}
          >
            {k.forget}
          </button>
        </div>
      </div>
    </main>
  );
}
