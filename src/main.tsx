import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { App } from './app/App';
import { AppProvider } from './app/state';
import { loadTopics } from './content';
import { connectEvents, createLocalStore } from './engine/progress';
import { registerAllModels } from './models';
import './styles.css';

registerAllModels();
const topics = loadTopics();
const store = createLocalStore();
connectEvents(store);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProvider topics={topics} store={store}>
      <App />
    </AppProvider>
  </StrictMode>,
);
