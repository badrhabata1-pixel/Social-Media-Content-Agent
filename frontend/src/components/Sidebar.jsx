import React from 'react';
import { LayoutDashboard, Calendar, Library, Bot, BarChart2, DollarSign, Plus } from 'lucide-react';

const Sidebar = () => {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="logo-container">
        <h2><Bot className="logo-icon" /> AgentUI</h2>
      </div>

      {/* New Post Button */}
      <button className="new-post-btn">
        <Plus size={18} /> New Post
      </button>

      {/* Navigation Links */}
      <nav className="nav-menu">
        <ul>
          <li className="active"><LayoutDashboard size={20} /> Dashboard</li>
          <li><Calendar size={20} /> Content planner</li>
          <li><Library size={20} /> Posts library</li>
          <li><Bot size={20} /> AI Agent</li>
          <li><BarChart2 size={20} /> Analytics</li>
          <li><DollarSign size={20} /> Monetization</li>
        </ul>
      </nav>
    </aside>
  );
};

export default Sidebar;
