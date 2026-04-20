import { useMemo, useState } from 'react';
import { ChevronDown, ChevronUp, Code, Search } from 'lucide-react';
import { useNetworkData } from '../hooks/useNetworkData';
import { useProblems } from '../hooks/useProblems';
import { SecurityScore } from '../components/dashboard/SecurityScore';
import type { Category, NetworkProblem, Severity } from '../types/network';

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const SEVERITY_ORDER: Record<Severity, number> = { critical: 0, high: 1, medium: 2, low: 3 };

const SEVERITY_BADGE: Record<Severity, string> = {
  critical: 'bg-red-500/20 text-red-400 border border-red-500/40',
  high:     'bg-orange-500/20 text-orange-400 border border-orange-500/40',
  medium:   'bg-yellow-500/20 text-yellow-400 border border-yellow-500/40',
  low:      'bg-blue-500/20 text-blue-400 border border-blue-500/40',
};

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'CRITIQUE',
  high:     'ÉLEVÉ',
  medium:   'MOYEN',
  low:      'FAIBLE',
};

const CATEGORY_LABEL: Record<Category, string> = {
  l2:       'L2',
  l3:       'L3',
  security: 'Sécurité',
};

// ---------------------------------------------------------------------------
// CLI Fix modal
// ---------------------------------------------------------------------------

function CliModal({ fix, onClose }: { fix: string; onClose: () => void }) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
      onClick={onClose}
    >
      <div
        className="bg-slate-900 border border-slate-700 rounded-xl p-6 max-w-lg w-full mx-4 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold text-white">CLI Fix</span>
          <button onClick={onClose} className="text-slate-400 hover:text-white transition-colors text-xs">✕</button>
        </div>
        <pre className="font-mono text-sm text-green-400 bg-slate-950 rounded-lg p-4 overflow-x-auto whitespace-pre-wrap">
          {fix}
        </pre>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Problem row
// ---------------------------------------------------------------------------

function ProblemRow({ problem, onShowFix }: { problem: NetworkProblem; onShowFix: (fix: string) => void }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <>
      <tr
        className="border-b border-slate-800 hover:bg-slate-800/40 cursor-pointer transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        {/* Severity */}
        <td className="px-4 py-3">
          <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full whitespace-nowrap ${SEVERITY_BADGE[problem.severity]}`}>
            {SEVERITY_LABEL[problem.severity]}
          </span>
        </td>
        {/* Category */}
        <td className="px-4 py-3 text-xs text-slate-400 font-mono">{CATEGORY_LABEL[problem.category]}</td>
        {/* Rule ID */}
        <td className="px-4 py-3">
          <span className="text-xs font-mono text-slate-500">{problem.rule_id}</span>
        </td>
        {/* Device */}
        <td className="px-4 py-3">
          <span className="text-xs font-mono text-blue-400">{problem.device_hostname}</span>
          {problem.interface && (
            <span className="text-xs font-mono text-slate-500 ml-1">/ {problem.interface}</span>
          )}
        </td>
        {/* Title */}
        <td className="px-4 py-3 text-xs text-white max-w-xs">{problem.title}</td>
        {/* Actions */}
        <td className="px-4 py-3">
          <div className="flex items-center gap-2">
            {problem.cli_fix && (
              <button
                onClick={(e) => { e.stopPropagation(); onShowFix(problem.cli_fix!); }}
                className="flex items-center gap-1 px-2 py-1 rounded bg-green-500/10 text-green-400 border border-green-500/20 text-xs hover:bg-green-500/20 transition-colors"
              >
                <Code className="w-3 h-3" /> Fix
              </button>
            )}
            <span className="text-slate-600">
              {expanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            </span>
          </div>
        </td>
      </tr>
      {expanded && (
        <tr className="border-b border-slate-800 bg-slate-900/60">
          <td colSpan={6} className="px-6 py-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Description</div>
                <p className="text-xs text-slate-300 leading-relaxed">{problem.description}</p>
              </div>
              <div>
                <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Recommandation</div>
                <p className="text-xs text-slate-300 leading-relaxed">{problem.recommendation}</p>
              </div>
              {problem.impact && (
                <div className="md:col-span-2">
                  <div className="text-[10px] text-slate-500 uppercase tracking-wide mb-1">Impact</div>
                  <p className="text-xs text-orange-300">{problem.impact}</p>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

// ---------------------------------------------------------------------------
// ProblemsPage
// ---------------------------------------------------------------------------

export function ProblemsPage() {
  const { devices } = useNetworkData();
  const { problems, securityScore } = useProblems(devices);

  const [filterSeverity, setFilterSeverity]   = useState<Severity | 'all'>('all');
  const [filterCategory, setFilterCategory]   = useState<Category | 'all'>('all');
  const [filterDevice,   setFilterDevice]     = useState<string>('all');
  const [search,         setSearch]           = useState('');
  const [clifix,         setCliFix]           = useState<string | null>(null);

  const deviceNames = useMemo(() => {
    const names = [...new Set(problems.map((p) => p.device_hostname))].sort();
    return names;
  }, [problems]);

  const filtered = useMemo(() => {
    return problems
      .filter((p) => filterSeverity === 'all' || p.severity === filterSeverity)
      .filter((p) => filterCategory === 'all' || p.category === filterCategory)
      .filter((p) => filterDevice   === 'all' || p.device_hostname === filterDevice)
      .filter((p) => !search || p.title.toLowerCase().includes(search.toLowerCase()) || p.device_hostname.toLowerCase().includes(search.toLowerCase()))
      .sort((a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity]);
  }, [problems, filterSeverity, filterCategory, filterDevice, search]);

  const selectCls = "bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg px-3 py-1.5 focus:outline-none focus:border-blue-500";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800 bg-slate-900 shrink-0">
        <div className="flex items-center gap-4">
          <h1 className="text-base font-semibold text-white">Problèmes réseau</h1>
          <span className="text-xs text-slate-500">{filtered.length} / {problems.length} problèmes</span>
        </div>
        <SecurityScore score={securityScore} size={80} />
      </div>

      {/* Filters */}
      <div className="flex items-center gap-3 px-6 py-3 border-b border-slate-800 bg-slate-900/60 shrink-0 flex-wrap">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Rechercher…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-slate-800 border border-slate-700 text-slate-300 text-xs rounded-lg pl-8 pr-3 py-1.5 focus:outline-none focus:border-blue-500 w-48"
          />
        </div>

        <select value={filterSeverity} onChange={(e) => setFilterSeverity(e.target.value as Severity | 'all')} className={selectCls}>
          <option value="all">Toutes sévérités</option>
          <option value="critical">Critique</option>
          <option value="high">Élevé</option>
          <option value="medium">Moyen</option>
          <option value="low">Faible</option>
        </select>

        <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value as Category | 'all')} className={selectCls}>
          <option value="all">Toutes catégories</option>
          <option value="l2">L2</option>
          <option value="l3">L3</option>
          <option value="security">Sécurité</option>
        </select>

        <select value={filterDevice} onChange={(e) => setFilterDevice(e.target.value)} className={selectCls}>
          <option value="all">Tous équipements</option>
          {deviceNames.map((d) => <option key={d} value={d}>{d}</option>)}
        </select>

        {(filterSeverity !== 'all' || filterCategory !== 'all' || filterDevice !== 'all' || search) && (
          <button
            onClick={() => { setFilterSeverity('all'); setFilterCategory('all'); setFilterDevice('all'); setSearch(''); }}
            className="text-xs text-slate-500 hover:text-slate-300 transition-colors"
          >
            Réinitialiser
          </button>
        )}
      </div>

      {/* Table */}
      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-green-400 text-4xl mb-3">✓</div>
              <div className="text-slate-400 text-sm">Aucun problème correspondant</div>
            </div>
          </div>
        ) : (
          <table className="w-full">
            <thead className="sticky top-0 bg-slate-900 z-10">
              <tr className="border-b border-slate-800">
                {['Sévérité', 'Catégorie', 'Rule ID', 'Équipement', 'Titre', 'Actions'].map((h) => (
                  <th key={h} className="px-4 py-2 text-left text-[10px] font-semibold text-slate-500 uppercase tracking-wide">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.map((p) => (
                <ProblemRow key={p.id} problem={p} onShowFix={setCliFix} />
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* CLI fix modal */}
      {clifix && <CliModal fix={clifix} onClose={() => setCliFix(null)} />}
    </div>
  );
}
