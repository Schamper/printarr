import { BookMarked, Layers, Search, Settings } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export default function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <svg viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
          <rect width="32" height="32" rx="6" fill="#3B82F6" />
          <path d="M8 22V12l8-5 8 5v10l-8 5-8-5z" stroke="white" strokeWidth="2" fill="none" />
          <path d="M8 12l8 5 8-5" stroke="white" strokeWidth="2" />
          <path d="M16 17v10" stroke="white" strokeWidth="2" />
        </svg>
        <span>Printarr</span>
      </div>
      <nav className="sidebar-nav">
        <NavLink to="/" end>
          <Search size={18} />
          Search
        </NavLink>
        <NavLink to="/library">
          <BookMarked size={18} />
          Library
        </NavLink>
        <NavLink to="/queue">
          <Layers size={18} />
          Queue
        </NavLink>
        <NavLink to="/settings">
          <Settings size={18} />
          Settings
        </NavLink>
      </nav>
      <div className="sidebar-version">v0.1.0</div>
    </aside>
  );
}
