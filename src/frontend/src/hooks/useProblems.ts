import { useCallback, useEffect, useState } from 'react';
import { analyseProblems } from '../api/client';
import type { NetworkDevice, NetworkProblem, ProblemSummary, Severity } from '../types/network';

// ---------------------------------------------------------------------------
// Mock problems for demo mode
// ---------------------------------------------------------------------------

const MOCK_PROBLEMS: NetworkProblem[] = [
  {
    id: 'mock-1',
    rule_id: 'L2_PORT_001',
    category: 'l2',
    severity: 'high',
    device_hostname: 'sw-access-01',
    interface: 'FastEthernet0/3',
    title: 'Interface operationally down (possible err-disabled)',
    description: 'FastEthernet0/3 is admin-up but operationally DOWN.',
    impact: 'Devices connected to this port are unreachable.',
    recommendation: "Check for err-disabled. Issue 'shutdown / no shutdown'.",
    evidence: { admin_status: true, operational_status: 'down' },
  },
  {
    id: 'mock-2',
    rule_id: 'L2_VLAN_001',
    category: 'l2',
    severity: 'high',
    device_hostname: 'sw-access-02',
    interface: 'GigabitEthernet0/1',
    title: 'Trunk carries undefined VLANs',
    description: 'Trunk GigabitEthernet0/1 allows VLAN 30 not defined on sw-core-01.',
    impact: 'Traffic on VLAN 30 may be silently dropped.',
    recommendation: 'Synchronise VLAN databases between sw-access-02 and sw-core-01.',
    evidence: { missing_vlans: [30] },
  },
  {
    id: 'mock-3',
    rule_id: 'L3_BGP_001',
    category: 'l3',
    severity: 'critical',
    device_hostname: 'rtr-wan-01',
    title: 'BGP neighbor shut down',
    description: 'BGP session to 203.0.113.1 (AS 65001) is administratively shut down.',
    impact: 'No BGP routes received from upstream ISP.',
    recommendation: "Remove 'neighbor 203.0.113.1 shutdown'.",
    cli_fix: 'router bgp 65000\n no neighbor 203.0.113.1 shutdown',
    evidence: { neighbor_ip: '203.0.113.1', remote_as: 65001 },
  },
];

// ---------------------------------------------------------------------------
// Security score calculation
// ---------------------------------------------------------------------------

const SEVERITY_WEIGHTS: Record<Severity, number> = {
  critical: 20,
  high: 10,
  medium: 4,
  low: 1,
};

function computeSecurityScore(problems: NetworkProblem[]): number {
  const penalty = problems.reduce((acc, p) => acc + (SEVERITY_WEIGHTS[p.severity] ?? 0), 0);
  return Math.max(0, Math.min(100, 100 - penalty));
}

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

interface UseProblemsResult {
  problems: NetworkProblem[];
  summary: ProblemSummary | null;
  securityScore: number;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useProblems(devices: NetworkDevice[]): UseProblemsResult {
  const [problems, setProblems] = useState<NetworkProblem[]>(MOCK_PROBLEMS);
  const [summary, setSummary] = useState<ProblemSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const analyse = useCallback(async () => {
    if (devices.length === 0) return;
    try {
      setLoading(true);
      setError(null);
      const result = await analyseProblems(devices);
      setProblems(result.problems);
      setSummary(result.summary);
    } catch {
      setProblems(MOCK_PROBLEMS);
      setSummary(null);
    } finally {
      setLoading(false);
    }
  }, [devices]);

  useEffect(() => {
    void analyse();
  }, [analyse]);

  return {
    problems,
    summary,
    securityScore: computeSecurityScore(problems),
    loading,
    error,
    refresh: analyse,
  };
}
