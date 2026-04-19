import { Activity, LayoutDashboard, Network, Server, Settings, Shield } from 'lucide-react';
import { NavLink } from 'react-router-dom';

const NAV_ITEMS = [
  { to: '/', icon: LayoutDashboard, label: 'Dashboard', end: true },
  { to: '/topology', icon: Network, label: 'Topologie' },
  { to: '/devices', icon: Server, label: 'Équipements' },
  { to: '/problems', icon: Shield, label: 'Problèmes' },
  { to: '/health', icon: Activity, label: 'Santé' },
];

export function Sidebar() {
  return (
    <aside className="flex flex-col w-16 lg:w-56 bg-slate-900 border-r border-slate-800 shrink-0 transition-all duration-200">
      {/* Logo */}
      <div className="flex items-center gap-3 px-3 py-4 border-b border-slate-800 h-14">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center shrink-0">
          <Network className="w-4 h-4 text-white" />
        </div>
        <span className="hidden lg:block font-bold text-white text-sm tracking-wide truncate">
          NetForge Pro
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 space-y-1 overflow-y-auto">
        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `flex items-center gap-3 px-2 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? 'bg-blue-600/20 text-blue-400'
                  : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
              }`
            }
          >
            <Icon className="w-4 h-4 shrink-0" />
            <span className="hidden lg:block">{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Settings */}
      <div className="p-2 border-t border-slate-800">
        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `flex items-center gap-3 px-2 py-2 rounded-lg text-sm font-medium transition-colors ${
              isActive
                ? 'bg-blue-600/20 text-blue-400'
                : 'text-slate-400 hover:text-slate-100 hover:bg-slate-800'
            }`
          }
        >
          <Settings className="w-4 h-4 shrink-0" />
          <span className="hidden lg:block">Paramètres</span>
        </NavLink>
      </div>
    </aside>
  );
}
