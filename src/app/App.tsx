import { GalleryPage } from '../pages/GalleryPage';
import { Home } from '../pages/Home';
import { KeyPage } from '../pages/KeyPage';
import { StepPage } from '../pages/StepPage';
import { TopicPage } from '../pages/TopicPage';
import { RecipesPage, TeacherPage, TrackPage } from '../pages/TrackPage';
import { TRACKS, type TrackId } from '../engine/schema';
import { Footer, Header } from '../ui/Chrome';
import { Link, usePath } from './router';
import { useApp } from './state';

/** Routes: / · /:topic · /:topic/:track · /:topic/:track/:step · /:topic/:track/receitas · /:topic/:track/professor */
export function App() {
  const path = usePath();
  const { topics } = useApp();
  const parts = path.split('/').filter(Boolean);
  let page = <NotFound />;

  if (parts.length === 0) page = <Home />;
  else if (parts.length === 1 && parts[0] === 'galeria') page = <GalleryPage />;
  else if (parts.length === 1 && parts[0] === 'sua-chave') page = <KeyPage />;
  else {
    const topic = topics.find((t) => t.def.id === parts[0]);
    if (topic && parts.length === 1) page = <TopicPage topic={topic} />;
    if (topic && parts.length >= 2 && (TRACKS as readonly string[]).includes(parts[1])) {
      const track = parts[1] as TrackId;
      if (parts.length === 2) page = <TrackPage topic={topic} track={track} />;
      else if (parts[2] === 'receitas') page = <RecipesPage topic={topic} track={track} />;
      else if (parts[2] === 'professor') page = <TeacherPage topic={topic} track={track} />;
      else {
        const lesson = topic.lessons.find((l) => l.track === track && l.slug === parts[2]);
        if (lesson) page = <StepPage key={lesson.def.id} topic={topic} lesson={lesson} />;
      }
    }
  }

  return (
    <div className="wz-root">
      <Header />
      {page}
      <Footer />
    </div>
  );
}

function NotFound() {
  const { ui } = useApp();
  return (
    <main id="main" className="wz-main">
      <h1 className="wz-h1">{ui.notFound}</h1>
      <Link className="wz-btn wz-cta" href="/">
        {ui.nav.home}
      </Link>
    </main>
  );
}
