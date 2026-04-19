import { AlertTriangle, CheckCircle, ChevronDown, ChevronUp } from 'lucide-react';
import { useState } from 'react';
import type { NetworkProblem, Severity } from '../../types/network';

// ---------------------------------------------------------------------------
// Severity styles
// ---------------------------------------------------------------------------

const SEVERITY_BADGE: Record<Severity, string> = {
  critical: 'bg-red-500/20 text-red-400 border-red-500/30',
  high: 'bg-orange-500/20 text-orange-400 border-orange-500/30',
  medium: 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30',
  low: 'bg-blue-500/20 text-blue-400 border-blue-500/30',
};

const SEVERITY_LABEL: Record<Severity, string> = {
  critical: 'Critique',
  high: 'Élevé',
  medium: 'Moyen',
  low: 'Faible',
};

const SEVERITY_ORDER: Record<Severity, number> = {
  critical: 0,
  high: 1,
  medium: 2,
  low: 3,
};

// ---------------------------------------------------------------------------
// ProblemCard
// ---------------------------------------------------------------------------

function ProblemCard({ problem }: { problem: NetworkProblem }) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="rounded-lg border border-slate-700/60 bg-slate-800/40 overflow-hidden">
      <button
        className="w-full flex items-start gap-3 p-3 text-left hover:bg-slate-800/60 transition-colors"
        onClick={() => setExpanded((v) => !v)}
      >
        <AlertTriangle className="w-3.5 h-3.5 text-slate-400 mt-0.5 shrink-0" />
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span
              className={`text-[10px] font-semibold px-1.5 py-0.5 rounded-full border ${SEVERITY_BADGE[problem.severity]}`}
            >
              {SEVERITY_LABEL[problem.severity]}
            </span>
            <span className="font-mono text-[10px] text-slate-500">{problem.rule_id}</span>
          </div>
          <div className="text-xs text-white font-medium mt-1 leading-snug">{problem.title}</div>
          <div className="text-[10px] text-slate-400 font-mono mt-0.5">{problem.device_hostname}</div>
        </div>
        <div className="shrink-0 text-slate-500">
          {expanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
        </div>
      </button>

      {expanded && (
        <div className="px-3 pb-3 space-y-2 border-t border-slate-700/40 pt-2">
          <p className="text-xs text-slate-300 leading-relaxed">{problem.description}</p>

          {problem.impact && (
            <div>
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mb-0.5">Impact</div>
              <p className="text-xs text-slate-400">{problem.impact}</p>
            </div>
          )}

          {problem.recommendation && (
            <div>
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mb-0.5">Recommandation</div>
              <p className="text-xs text-slate-400">{problem.recommendation}</p>
            </div>
          )}

          {problem.cli_fix && (
            <div>
              <div className="text-[10px] text-slate-500 font-semibold uppercase tracking-wide mb-0.5">CLI Fix</div>
              <pre className="text-[10px] font-mono bg-slate-900 text-green-400 rounded p-2 overflow-x-auto whitespace-pre-wrap">
                {problem.cli_fix}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// ProblemsPanel
// ---------------------------------------------------------------------------

interface ProblemsPanelProps {
  problems: NetworkProblem[];
  securityScore: number;
}

export function ProblemsPanel({ problems, securityScore }: ProblemsPanelProps) {
  const sorted = [...problems].sort(
    (a, b) => SEVERITY_ORDER[a.severity] - SEVERITY_ORDER[b.severity],
  );

  const scoreColor =
    securityScore >= 80 ? 'text-green-400' : securityScore >= 60 ? 'text-yellow-400' : 'text-red-400';

  return (
    <aside className="flex flex-col w-80 bg-slate-900 border-l border-slate-800 shrink-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <span className="text-sm font-semibold text-white">Problèmes</span>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${scoreColor}`}>{securityScore}</span>
          <span className="text-xs text-slate-500">/100</span>
        </div>
      </div>

      {/* Problem list */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {sorted.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <CheckCircle className="w-8 h-8 text-green-400" />
            <span className="text-sm text-green-400 font-medium">Aucun problème détecté</span>
          </div>
        ) : (
          sorted.map((p) => <ProblemCard key={p.id} problem={p} />)
        )}
      </div>
    </aside>
  );
}
