import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchTopology } from '../api/client';
import type { NetworkDevice, TopologyData, TopologyEdge, Zone } from '../types/network';

// ---------------------------------------------------------------------------
// Mock data — used when the API is unavailable (demo mode)
// ---------------------------------------------------------------------------

const MOCK_DEVICES: NetworkDevice[] = [
  {
    hostname: 'fw-edge-01',
    vendor: 'fortinet',
    model: 'FortiGate 100F',
    os_version: '7.4.2',
    management_ip: '10.0.0.1',
    interfaces: [
      { name: 'port1', status: 'up', ip_address: '203.0.113.1', prefix_length: 30, speed: 1000, switchport_mode: 'routed' },
      { name: 'port2', status: 'up', ip_address: '10.10.0.1', prefix_length: 24, speed: 1000, switchport_mode: 'routed' },
      { name: 'port3', status: 'down', speed: 1000, switchport_mode: 'routed' },
    ],
    vlans: [],
  },
  {
    hostname: 'sw-core-01',
    vendor: 'cisco',
    model: 'Catalyst 9300',
    os_version: '17.9.4',
    management_ip: '10.10.0.10',
    interfaces: [
      { name: 'GigabitEthernet1/0/1', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 20, 30], native_vlan: 1, speed: 1000 },
      { name: 'GigabitEthernet1/0/2', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 20], native_vlan: 1, speed: 1000 },
      { name: 'GigabitEthernet1/0/24', status: 'up', ip_address: '10.10.0.10', prefix_length: 24, switchport_mode: 'routed', speed: 1000 },
    ],
    vlans: [
      { vlan_id: 10, name: 'MGMT' },
      { vlan_id: 20, name: 'DATA' },
      { vlan_id: 30, name: 'VOICE' },
    ],
  },
  {
    hostname: 'sw-access-01',
    vendor: 'cisco',
    model: 'Catalyst 2960',
    os_version: '15.2.7',
    management_ip: '10.10.0.11',
    interfaces: [
      { name: 'GigabitEthernet0/1', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 20], native_vlan: 1, speed: 1000 },
      { name: 'FastEthernet0/1', status: 'up', switchport_mode: 'access', access_vlan: 20, speed: 100 },
      { name: 'FastEthernet0/2', status: 'up', switchport_mode: 'access', access_vlan: 20, speed: 100 },
      { name: 'FastEthernet0/3', status: 'down', admin_status: true, switchport_mode: 'access', access_vlan: 20, speed: 100 },
    ],
    vlans: [{ vlan_id: 10, name: 'MGMT' }, { vlan_id: 20, name: 'DATA' }],
  },
  {
    hostname: 'sw-access-02',
    vendor: 'cisco',
    model: 'Catalyst 2960',
    os_version: '15.2.7',
    management_ip: '10.10.0.12',
    interfaces: [
      { name: 'GigabitEthernet0/1', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 30], native_vlan: 1, speed: 1000 },
      { name: 'FastEthernet0/1', status: 'up', switchport_mode: 'access', access_vlan: 30, speed: 100 },
      { name: 'FastEthernet0/2', status: 'up', switchport_mode: 'access', access_vlan: 30, speed: 100 },
    ],
    vlans: [{ vlan_id: 10, name: 'MGMT' }, { vlan_id: 30, name: 'VOICE' }],
  },
  {
    hostname: 'rtr-wan-01',
    vendor: 'huawei',
    model: 'NE40E',
    os_version: 'VRP V800R022',
    management_ip: '172.16.0.1',
    interfaces: [
      { name: 'GigabitEthernet0/0/0', status: 'up', ip_address: '203.0.113.2', prefix_length: 30, speed: 1000, switchport_mode: 'routed' },
      { name: 'GigabitEthernet0/0/1', status: 'up', ip_address: '172.16.0.1', prefix_length: 24, speed: 1000, switchport_mode: 'routed' },
    ],
    vlans: [],
  },
];

const MOCK_EDGES: TopologyEdge[] = [
  { id: 'e1', source: 'rtr-wan-01', target: 'fw-edge-01', speed: 1000, status: 'up' },
  { id: 'e2', source: 'fw-edge-01', target: 'sw-core-01', speed: 1000, status: 'up' },
  { id: 'e3', source: 'sw-core-01', target: 'sw-access-01', speed: 1000, status: 'up' },
  { id: 'e4', source: 'sw-core-01', target: 'sw-access-02', speed: 1000, status: 'up' },
];

const MOCK_ZONES: Zone[] = [
  {
    id: 'zone-wan',
    name: 'WAN',
    zone_type: 'wan',
    security_level: 0,
    device_hostnames: ['rtr-wan-01'],
    position: { x: 20, y: 80 },
    size: { width: 220, height: 180 },
  },
  {
    id: 'zone-dmz',
    name: 'DMZ',
    zone_type: 'dmz',
    security_level: 30,
    device_hostnames: ['fw-edge-01'],
    position: { x: 300, y: 40 },
    size: { width: 240, height: 260 },
  },
  {
    id: 'zone-lan',
    name: 'LAN',
    zone_type: 'lan',
    security_level: 80,
    device_hostnames: ['sw-core-01', 'sw-access-01', 'sw-access-02'],
    position: { x: 600, y: 20 },
    size: { width: 420, height: 400 },
  },
];

const MOCK_TOPOLOGY: TopologyData = {
  devices: MOCK_DEVICES,
  edges: MOCK_EDGES,
  zones: MOCK_ZONES,
};

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

interface UseNetworkDataResult {
  topology: TopologyData;
  devices: NetworkDevice[];
  loading: boolean;
  error: string | null;
  demoMode: boolean;
  refresh: () => void;
  lastUpdated: Date | null;
}

const POLL_INTERVAL = 30_000;

export function useNetworkData(): UseNetworkDataResult {
  const [topology, setTopology] = useState<TopologyData>(MOCK_TOPOLOGY);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [demoMode, setDemoMode] = useState(false);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await fetchTopology();
      setTopology(data);
      setDemoMode(false);
      setLastUpdated(new Date());
    } catch {
      // API unavailable — use mock data transparently
      setTopology(MOCK_TOPOLOGY);
      setDemoMode(true);
      setLastUpdated(new Date());
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
    timerRef.current = setInterval(load, POLL_INTERVAL);
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [load]);

  return {
    topology,
    devices: topology.devices,
    loading,
    error,
    demoMode,
    refresh: load,
    lastUpdated,
  };
}
