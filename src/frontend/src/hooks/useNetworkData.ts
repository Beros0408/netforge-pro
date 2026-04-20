import { useCallback, useEffect, useRef, useState } from 'react';
import { fetchTopology } from '../api/client';
import type { NetworkDevice, TopologyData, TopologyEdge, Zone } from '../types/network';

// ---------------------------------------------------------------------------
// Mock data — realistic demo topology
// ---------------------------------------------------------------------------

const MOCK_DEVICES: NetworkDevice[] = [
  {
    hostname: 'rtr-wan-01',
    vendor: 'huawei',
    device_type: 'router',
    model: 'NE40E',
    os_version: 'VRP V800R022',
    management_ip: '172.16.0.1',
    interfaces: [
      { name: 'GigabitEthernet0/0/0', status: 'up', ip_address: '203.0.113.2', prefix_length: 30, speed: 1000, switchport_mode: 'routed' },
      { name: 'GigabitEthernet0/0/1', status: 'up', ip_address: '172.16.0.1', prefix_length: 24, speed: 1000, switchport_mode: 'routed' },
    ],
    vlans: [],
  },
  {
    hostname: 'fw-edge-01',
    vendor: 'fortinet',
    device_type: 'firewall',
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
    device_type: 'switch',
    model: 'Catalyst 9300-48P',
    os_version: 'IOS-XE 17.9.4',
    management_ip: '10.10.0.10',
    interfaces: [
      { name: 'GigabitEthernet1/0/1', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 20, 30], native_vlan: 1, speed: 1000 },
      { name: 'GigabitEthernet1/0/2', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 20], native_vlan: 1, speed: 1000 },
      { name: 'GigabitEthernet1/0/3', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 30], native_vlan: 1, speed: 1000 },
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
    device_type: 'switch',
    model: 'Catalyst 2960-24',
    os_version: 'IOS 15.2.7',
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
    device_type: 'switch',
    model: 'Catalyst 2960-24',
    os_version: 'IOS 15.2.7',
    management_ip: '10.10.0.12',
    interfaces: [
      { name: 'GigabitEthernet0/1', status: 'up', switchport_mode: 'trunk', trunk_vlans: [10, 30], native_vlan: 1, speed: 1000 },
      { name: 'FastEthernet0/1', status: 'up', switchport_mode: 'access', access_vlan: 30, speed: 100 },
      { name: 'FastEthernet0/2', status: 'up', switchport_mode: 'access', access_vlan: 30, speed: 100 },
    ],
    vlans: [{ vlan_id: 10, name: 'MGMT' }, { vlan_id: 30, name: 'VOICE' }],
  },
];

const MOCK_EDGES: TopologyEdge[] = [
  {
    id: 'e1',
    source: 'rtr-wan-01',
    target: 'fw-edge-01',
    source_interface: 'Gi0/0/1',
    target_interface: 'port1',
    speed: 1000,
    cable_type: 'fiber_1g',
    status: 'up',
  },
  {
    id: 'e2',
    source: 'fw-edge-01',
    target: 'sw-core-01',
    source_interface: 'port2',
    target_interface: 'Gi1/0/1',
    speed: 1000,
    cable_type: 'fiber_1g',
    status: 'up',
  },
  {
    id: 'e3',
    source: 'sw-core-01',
    target: 'sw-access-01',
    source_interface: 'Gi1/0/2',
    target_interface: 'Gi0/1',
    speed: 1000,
    cable_type: 'fiber_1g',
    status: 'up',
  },
  {
    id: 'e4',
    source: 'sw-core-01',
    target: 'sw-access-02',
    source_interface: 'Gi1/0/3',
    target_interface: 'Gi0/1',
    speed: 1000,
    cable_type: 'fiber_1g',
    status: 'up',
  },
];

const MOCK_ZONES: Zone[] = [
  {
    id: 'zone-wan',
    name: 'WAN',
    zone_type: 'wan',
    security_level: 0,
    device_hostnames: ['rtr-wan-01'],
    position: { x: 20, y: 100 },
    size: { width: 200, height: 180 },
  },
  {
    id: 'zone-dmz',
    name: 'DMZ',
    zone_type: 'dmz',
    security_level: 30,
    device_hostnames: ['fw-edge-01'],
    position: { x: 280, y: 60 },
    size: { width: 220, height: 260 },
  },
  {
    id: 'zone-lan',
    name: 'LAN',
    zone_type: 'lan',
    security_level: 80,
    device_hostnames: ['sw-core-01', 'sw-access-01', 'sw-access-02'],
    position: { x: 560, y: 20 },
    size: { width: 480, height: 440 },
  },
];

const MOCK_TOPOLOGY: TopologyData = {
  devices: MOCK_DEVICES,
  edges:   MOCK_EDGES,
  zones:   MOCK_ZONES,
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
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);
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
