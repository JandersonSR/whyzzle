import { useEffect, useMemo, useState } from 'react';
import { useApp } from '../app/state';
import type { Lesson } from '../content';
import { makeRng } from '../engine/text';
import { declarative } from '../models/declarative';
import gallery from '../scenes/gallery.json';
import { WidgetsScene } from '../scenes/Widgets';
import { Segmented } from '../ui/Chrome';

/** /galeria: every reusable widget, driven by the same declarative model lessons use. */
export function GalleryPage() {
  const { lang, layer } = useApp();
  const [incidente, setIncidente] = useState(false);
  const s = gallery.scene[lang] as Record<string, string>;
  const lesson = { def: { data: { sim: gallery.sim } } } as unknown as Lesson;
  const result = useMemo(
    () => declarative.run({ incidente }, { lang, layer, data: { sim: gallery.sim }, text: {}, rng: makeRng(1) }),
    [incidente, lang, layer],
  );
  useEffect(() => {
    document.title = `${s.title} · Whyzzle`;
  }, [s.title]);
  return (
    <main id="main" className="wz-main">
      <div className="wz-stack wz-stack--tight">
        <h1 className="wz-h1">{s.title}</h1>
        <span className="wz-sub">{s.intro}</span>
      </div>
      <Segmented
        label={s.title}
        value={incidente ? 'bad' : 'ok'}
        onChange={(v) => setIncidente(v === 'bad')}
        options={[
          { id: 'ok', label: s.healthy },
          { id: 'bad', label: s.incident },
        ]}
      />
      <section className="wz-card wz-scene">
        <WidgetsScene lesson={lesson} loc={undefined as never} s={s} lang={lang} layer={layer} values={null} preview={null} last={result} runs={[]} />
      </section>
    </main>
  );
}
