import { LayoutDashboard, Calendar, Library, Bot, BarChart2, DollarSign, Plus } from 'lucide-react';

// Items with a `view` switch App's tab; the others are placeholders for later modules.
const NAV_ITEMS = [
  { label: 'Dashboard', icon: LayoutDashboard, view: 'create' },
  { label: 'Content planner', icon: Calendar },
  { label: 'Posts library', icon: Library },
  { label: 'AI Agent', icon: Bot },
  { label: 'Analytics', icon: BarChart2, view: 'analytics' },
  { label: 'Monetization', icon: DollarSign },
];

const Sidebar = ({ activeView, onNavigate }) => {
  const activate = (event, view) => {
    if (event.type === 'click' || event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      onNavigate(view);
    }
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="logo-container">
        <h2><Bot className="logo-icon" /> AgentUI</h2>
      </div>

      {/* New Post Button */}
      <button className="new-post-btn" onClick={() => onNavigate('create')}>
        <Plus size={18} /> New Post
      </button>

      {/* Navigation Links */}
      <nav className="nav-menu">
        <ul>
          {NAV_ITEMS.map(({ label, icon: Icon, view }) => (
            view ? (
              <li
                key={label}
                className={activeView === view ? 'active' : ''}
                role="button"
                tabIndex={0}
                aria-current={activeView === view ? 'page' : undefined}
                onClick={event => activate(event, view)}
                onKeyDown={event => activate(event, view)}
              >
                <Icon size={20} /> {label}
              </li>
            ) : (
              <li key={label} aria-disabled="true" title="Coming soon">
                <Icon size={20} /> {label}
              </li>
            )
          ))}
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
