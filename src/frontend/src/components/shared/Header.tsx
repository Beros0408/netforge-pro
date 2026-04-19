import { RefreshCw } from 'lucide-react';
import type { NetworkProblem } from '../../types/network';

interface HeaderProps {
  deviceCount: number;
  problems: NetworkProblem[];
  demoMode: boolean;
  lastUpdated: Date | null;
  onRefresh: () => void;
  loading: boolean;
}

const SEVERITY_COLORS = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
} as const;

function SeverityBadge({ label, count, cls }: { label: string; count: number; cls: string }) {
  if (count === 0) return null;
  return (
    <span className={`flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium border ${cls}`}>
      <span className="font-bold">{count}</span>
      <span className="hidden sm:inline opacity-80">{label}</span>
    </span>
  );
}

export function Header({ deviceCount, problems, demoMode, lastUpdated, onRefresh, loading }: HeaderProps) {
  const counts = { critical: 0, high: 0, medium: 0, low: 0 };
  for (const p of problems) counts[p.severity] = (counts[p.severity] ?? 0) + 1;

  const timeStr = lastUpdated
    ? lastUpdated.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })
    : '—';

  return (
    <header className="flex items-center justify-between gap-4 px-4 h-14 border-b border-slate-800 bg-slate-900 shrink-0">
      {/* Left — device count */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">Équipements</span>
          <span className="text-white font-semibold">{deviceCount}</span>
        </div>

        {demoMode && (
          <span className="hidden sm:flex items-center gap-1 px-2 py-0.5 rounded-full bg-violet-500/20 text-violet-400 border border-violet-500/30 text-xs font-medium">
            Mode Démo
          </span>
        )}
      </div>

      {/* Center — problem badges */}
      <div className="flex items-center gap-2">
        <SeverityBadge label="Critique" count={counts.critical} cls={SEVERITY_COLORS.critical} />
        <SeverityBadge label="Élevé" count={counts.high} cls={SEVERITY_COLORS.high} />
        <SeverityBadge label="Moyen" count={counts.medium} cls={SEVERITY_COLORS.medium} />
        <SeverityBadge label="Faible" count={counts.low} cls={SEVERITY_COLORS.low} />
        {problems.length === 0 && (
          <span className="text-green-400 text-xs font-medium">✓ Aucun problème</span>
        )}
      </div>

      {/* Right — refresh + time */}
      <div className="flex items-center gap-3">
        <span className="hidden md:block text-slate-500 text-xs">Mis à jour {timeStr}</span>
        <button
          onClick={onRefresh}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 text-sm transition-colors disabled:opacity-50"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span className="hidden sm:inline">Rafraîchir</span>
        </button>
      </div>
    </header>
  );
}
