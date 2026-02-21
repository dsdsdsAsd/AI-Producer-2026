import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Lightbulb, Plus, Settings, Zap, Bot, ShieldCheck } from 'lucide-react';
import PlannerBoard from './components/PlannerBoard';
import IdeaGenerator from './components/IdeaGenerator';
import KnowledgeGraph from './components/KnowledgeGraph';
import ProducerChat from './components/ProducerChat';
import StrategyDashboard from './components/StrategyDashboard';

function NavItem({ to, icon: Icon, label }) {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link
      to={to}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${isActive
        ? 'bg-primary/20 text-blue-400 font-medium'
        : 'text-textMuted hover:bg-surface hover:text-white'
        }`}
    >
      <Icon size={20} />
      <span>{label}</span>
      {isActive && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-blue-400" />}
    </Link>
  );
}

function Layout({ children }) {
  return (
    <div className="flex h-screen bg-background text-text overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-white/5 flex flex-col p-4">
        <div className="flex items-center gap-3 px-4 mb-8 mt-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center font-bold text-white">
            V
          </div>
          <span className="font-bold text-lg tracking-tight">VibePlanner</span>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          <NavItem to="/" icon={LayoutDashboard} label="Доска Идей" />
          <NavItem to="/strategy" icon={ShieldCheck} label="Позиционирование" />
          <NavItem to="/generator" icon={Lightbulb} label="Генератор (Pain)" />
          <NavItem to="/chat" icon={Bot} label="Чат с Продюсером" />
          <NavItem to="/graph" icon={Zap} label="3D Граф Знаний" />
        </nav>

        <div className="mt-auto pt-4 border-t border-white/5">
          <button className="flex items-center gap-3 px-4 py-3 text-textMuted hover:text-white transition-colors w-full text-left">
            <Settings size={20} />
            <span>Настройки</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto relative">
        {children}
      </main>
    </div>
  );
}

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<PlannerBoard />} />
          <Route path="/strategy" element={<StrategyDashboard />} />
          <Route path="/generator" element={<IdeaGenerator />} />
          <Route path="/chat" element={<ProducerChat />} />
          <Route path="/graph" element={<KnowledgeGraph />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
