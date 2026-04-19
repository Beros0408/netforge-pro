import axios from 'axios';
import type { NetworkDevice, NetworkProblem, ProblemSummary, TopologyData } from '../types/network';

const BASE_URL = import.meta.env.VITE_API_URL ?? '';

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 15_000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail ?? err.message ?? 'API error';
    console.error('[NetForge API]', msg);
    return Promise.reject(new Error(msg));
  },
);

// ---------------------------------------------------------------------------
// Devices
// ---------------------------------------------------------------------------

export async function fetchDevices(): Promise<NetworkDevice[]> {
  const { data } = await api.get<NetworkDevice[]>('/api/v1/parser/devices');
  return data;
}

// ---------------------------------------------------------------------------
// Graph / Topology
// ---------------------------------------------------------------------------

export async function fetchTopology(): Promise<TopologyData> {
  const { data } = await api.get<TopologyData>('/api/v1/graph/topology');
  return data;
}

export async function fetchGraphStats() {
  const { data } = await api.get('/api/v1/graph/stats');
  return data;
}

// ---------------------------------------------------------------------------
// Rule Engine
// ---------------------------------------------------------------------------

export async function analyseProblems(devices: NetworkDevice[]): Promise<{
  problems: NetworkProblem[];
  summary: ProblemSummary;
  total: number;
}> {
  const { data } = await api.post('/api/v1/rules/analyse', { devices });
  return data;
}

export async function fetchRules() {
  const { data } = await api.get('/api/v1/rules/');
  return data;
}
