import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navigation from '../components/Navigation';
import HeatmapPage from '../pages/HeatmapPage';
import EntityPage from '../pages/EntityPage';
import RunsPage from '../pages/RunsPage';
import ResolveQueuePage from '../pages/ResolveQueuePage';

function App() {
  return (
    <BrowserRouter>
      <Navigation />
      <Routes>
        <Route path="/" element={<HeatmapPage />} />
        <Route path="/entity/:entityId" element={<EntityPage />} />
        <Route path="/runs" element={<RunsPage />} />
        <Route path="/resolve-queue" element={<ResolveQueuePage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
