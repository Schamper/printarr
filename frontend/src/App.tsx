import { Route, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import LibraryPage from './pages/LibraryPage';
import QueuePage from './pages/QueuePage';
import SearchPage from './pages/SearchPage';
import SettingsPage from './pages/SettingsPage';

export default function App() {
  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Routes>
          <Route path="/" element={<SearchPage />} />
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/queue" element={<QueuePage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </div>
  );
}
