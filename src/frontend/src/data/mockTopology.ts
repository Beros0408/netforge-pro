/**
 * mockTopology.ts — NetForge Pro
 * 10 devices + 9 connections — demo topology for Module 5 canvas
 */
import type { Edge, Node } from 'reactflow';
import type { DeviceNodeData, DevicePort } from '../components/canvas/DeviceNode';

// ─── Edge metadata ────────────────────────────────────────────────────────────

export interface MockEdgeData {
  layer: 'physical' | 'l2' | 'l3' | 'security';
  speed: string;
}

// ─── Port helper ──────────────────────────────────────────────────────────────

function p(
  id: string,
  name: string,
  normalizedName: string,
  speed: DevicePort['speed'],
  status: DevicePort['status'],
  opts: Partial<Omit<DevicePort, 'id' | 'name' | 'normalizedName' | 'speed' | 'status'>> = {},
): DevicePort {
  return { id, name, normalizedName, speed, status, ...opts };
}

// ─── Edge style ───────────────────────────────────────────────────────────────

function edge(
  id: string,
  source: string,
  target: string,
  speed: string,
  layer: MockEdgeData['layer'] = 'physical',
): Edge<MockEdgeData> {
  return {
    id,
    source,
    target,
    data: { layer, speed },
    label: speed,
    labelStyle: { fontSize: 9, fill: '#4a6080', fontFamily: 'monospace' },
    labelBgStyle: { fill: '#0a0f1e', fillOpacity: 0.85 },
    style: { stroke: '#2a3f5f', strokeWidth: 2 },
  };
}

// ─── Mock nodes ───────────────────────────────────────────────────────────────
// Zone Y offsets: DMZ/DataCenter y=-200, Core y=0, Distribution y=300, Access y=600
// X spacing: 220px between devices in the same zone, centered on x=400

export const MOCK_NODES: Node<DeviceNodeData>[] = [

  // ── DMZ (y = -200, x = 290) ──────────────────────────────────────────────
  {
    id: 'FW-EXT-01',
    type: 'deviceNode',
    position: { x: 290, y: -200 },
    data: {
      hostname: 'FW-EXT-01',
      vendor: 'fortinet',
      iconType: 'fortinet_fg200f',
      model: 'FortiGate 200F',
      osVersion: 'FortiOS 7.4.3',
      managementIp: '10.0.0.1',
      zone: 'DMZ',
      status: 'up',
      ports: [
        p('fw1-p1', 'port1', 'port1', '10G', 'up', {
          mode: 'routed', ipv4: '203.0.113.1/30',
          neighborDevice: 'CORE-SW-01', neighborPort: 'Eth1/3',
          utilization: 45, description: 'WAN Uplink',
        }),
        p('fw1-p2', 'port2', 'port2', '10G', 'up', {
          mode: 'routed', ipv4: '10.0.0.1/24',
          utilization: 23, description: 'Internal DMZ',
        }),
        p('fw1-p3', 'port3', 'port3', '1G', 'down', { description: 'Backup WAN' }),
        p('fw1-p4', 'port4', 'port4', '1G', 'admin-down', { description: 'Unused' }),
      ],
    },
  },

  // ── DataCenter (y = -200, x = 510) ───────────────────────────────────────
  {
    id: 'DC-SPINE-01',
    type: 'deviceNode',
    position: { x: 510, y: -200 },
    data: {
      hostname: 'DC-SPINE-01',
      vendor: 'arista',
      iconType: 'arista_7050cx3',
      model: '7050CX3-32S',
      osVersion: 'EOS 4.32.0F',
      managementIp: '10.0.0.10',
      zone: 'DataCenter',
      status: 'up',
      ports: [
        p('dc1-e11', 'Ethernet1/1', 'Et1/1', '100G', 'up', {
          mode: 'routed', neighborDevice: 'CORE-SW-02', neighborPort: 'Eth1/2',
          utilization: 71,
        }),
        p('dc1-e21', 'Ethernet2/1', 'Et2/1', '100G', 'up', {
          mode: 'routed', utilization: 34,
        }),
        p('dc1-e31', 'Ethernet3/1', 'Et3/1', '100G', 'up', {
          mode: 'routed', utilization: 56,
        }),
        p('dc1-e41', 'Ethernet4/1', 'Et4/1', '100G', 'admin-down'),
      ],
    },
  },

  // ── Core (y = 0) ─────────────────────────────────────────────────────────
  {
    id: 'CORE-SW-01',
    type: 'deviceNode',
    position: { x: 290, y: 0 },
    data: {
      hostname: 'CORE-SW-01',
      vendor: 'cisco',
      iconType: 'cisco_nexus_9500',
      model: 'Nexus 9504',
      osVersion: 'NX-OS 10.3.3',
      managementIp: '10.0.0.2',
      zone: 'Core',
      status: 'up',
      ports: [
        p('co1-e11', 'Ethernet1/1', 'Eth1/1', '100G', 'up', {
          mode: 'trunk', neighborDevice: 'DIST-SW-01', neighborPort: 'Te1/1/1',
          utilization: 45,
        }),
        p('co1-e12', 'Ethernet1/2', 'Eth1/2', '100G', 'up', {
          mode: 'trunk', neighborDevice: 'DIST-SW-02', neighborPort: 'Te1/1/1',
          utilization: 62,
        }),
        p('co1-e13', 'Ethernet1/3', 'Eth1/3', '10G', 'up', {
          mode: 'routed', neighborDevice: 'FW-EXT-01', neighborPort: 'port1',
          utilization: 23,
        }),
        p('co1-mgmt', 'mgmt0', 'mgmt0', '1G', 'up', {
          mode: 'routed', ipv4: '10.0.0.2/24',
        }),
        p('co1-e21', 'Ethernet2/1', 'Eth2/1', '100G', 'admin-down'),
      ],
    },
  },

  {
    id: 'CORE-SW-02',
    type: 'deviceNode',
    position: { x: 510, y: 0 },
    data: {
      hostname: 'CORE-SW-02',
      vendor: 'cisco',
      iconType: 'cisco_nexus_9300',
      model: 'Nexus 9336C-FX2',
      osVersion: 'NX-OS 10.3.3',
      managementIp: '10.0.0.3',
      zone: 'Core',
      status: 'up',
      ports: [
        p('co2-e11', 'Ethernet1/1', 'Eth1/1', '100G', 'up', {
          mode: 'trunk', neighborDevice: 'DIST-SW-01', neighborPort: 'Te1/1/2',
          utilization: 38,
        }),
        p('co2-e12', 'Ethernet1/2', 'Eth1/2', '100G', 'up', {
          mode: 'routed', neighborDevice: 'DC-SPINE-01', neighborPort: 'Et1/1',
          utilization: 71,
        }),
        p('co2-mgmt', 'mgmt0', 'mgmt0', '1G', 'up', {
          mode: 'routed', ipv4: '10.0.0.3/24',
        }),
        p('co2-e21', 'Ethernet2/1', 'Eth2/1', '100G', 'admin-down'),
      ],
    },
  },

  // ── Distribution (y = 300) ────────────────────────────────────────────────
  {
    id: 'DIST-SW-01',
    type: 'deviceNode',
    position: { x: 290, y: 300 },
    data: {
      hostname: 'DIST-SW-01',
      vendor: 'cisco',
      iconType: 'cisco_catalyst_9300',
      model: 'Catalyst 9300-48P',
      osVersion: 'IOS-XE 17.12.1',
      managementIp: '10.0.1.1',
      zone: 'Distribution',
      status: 'up',
      ports: [
        p('ds1-te11', 'TenGigabitEthernet1/1/1', 'Te1/1/1', '100G', 'up', {
          mode: 'trunk', neighborDevice: 'CORE-SW-01', neighborPort: 'Eth1/1',
          utilization: 45,
        }),
        p('ds1-te12', 'TenGigabitEthernet1/1/2', 'Te1/1/2', '100G', 'up', {
          mode: 'trunk', neighborDevice: 'CORE-SW-02', neighborPort: 'Eth1/1',
          utilization: 38,
        }),
        p('ds1-gi11', 'GigabitEthernet1/0/1', 'Gi1/0/1', '10G', 'up', {
          mode: 'trunk', neighborDevice: 'ACC-SW-01', neighborPort: 'Gi1/0/1',
          utilization: 34,
        }),
        p('ds1-gi12', 'GigabitEthernet1/0/2', 'Gi1/0/2', '10G', 'up', {
          mode: 'trunk', neighborDevice: 'ACC-SW-02', neighborPort: 'GE1/0/0',
          utilization: 28,
        }),
        p('ds1-gi13', 'GigabitEthernet1/0/3', 'Gi1/0/3', '1G', 'down'),
      ],
    },
  },

  {
    id: 'DIST-SW-02',
    type: 'deviceNode',
    position: { x: 510, y: 300 },
    data: {
      hostname: 'DIST-SW-02',
      vendor: 'cisco',
      iconType: 'cisco_catalyst_9300',
      model: 'Catalyst 9300-24T',
      osVersion: 'IOS-XE 17.12.1',
      managementIp: '10.0.1.2',
      zone: 'Distribution',
      status: 'warning',
      ports: [
        p('ds2-te11', 'TenGigabitEthernet1/1/1', 'Te1/1/1', '100G', 'up', {
          mode: 'trunk', neighborDevice: 'CORE-SW-01', neighborPort: 'Eth1/2',
          utilization: 62,
        }),
        p('ds2-gi11', 'GigabitEthernet1/0/1', 'Gi1/0/1', '10G', 'up', {
          mode: 'trunk', neighborDevice: 'WLC-01', neighborPort: 'Gi1',
          utilization: 12,
        }),
        p('ds2-gi12', 'GigabitEthernet1/0/2', 'Gi1/0/2', '10G', 'err-disabled', {
          errors: { crc: 1248, drops: 0 },
        }),
        p('ds2-gi13', 'GigabitEthernet1/0/3', 'Gi1/0/3', '1G', 'admin-down'),
      ],
    },
  },

  // ── Access (y = 600) ─────────────────────────────────────────────────────
  {
    id: 'ACC-SW-01',
    type: 'deviceNode',
    position: { x: 70, y: 600 },
    data: {
      hostname: 'ACC-SW-01',
      vendor: 'cisco',
      iconType: 'cisco_catalyst_9200',
      model: 'Catalyst 9200-24P',
      osVersion: 'IOS-XE 17.12.1',
      managementIp: '10.0.2.1',
      zone: 'Access',
      status: 'up',
      ports: [
        p('ac1-gi11', 'GigabitEthernet1/0/1', 'Gi1/0/1', '10G', 'up', {
          mode: 'trunk', neighborDevice: 'DIST-SW-01', neighborPort: 'Gi1/0/1',
          utilization: 34,
        }),
        p('ac1-fa11', 'FastEthernet1/0/1', 'Fa1/0/1', '1G', 'up', {
          mode: 'access', accessVlan: 10, utilization: 18,
        }),
        p('ac1-fa12', 'FastEthernet1/0/2', 'Fa1/0/2', '1G', 'up', {
          mode: 'access', accessVlan: 10, utilization: 5,
        }),
        p('ac1-fa13', 'FastEthernet1/0/3', 'Fa1/0/3', '1G', 'down'),
        p('ac1-fa14', 'FastEthernet1/0/4', 'Fa1/0/4', '1G', 'admin-down'),
      ],
    },
  },

  {
    id: 'ACC-SW-02',
    type: 'deviceNode',
    position: { x: 290, y: 600 },
    data: {
      hostname: 'ACC-SW-02',
      vendor: 'huawei',
      iconType: 'huawei_s5735',
      model: 'S5735-L24T4S-A',
      osVersion: 'VRP V200R022',
      managementIp: '10.0.2.2',
      zone: 'Access',
      status: 'up',
      ports: [
        p('ac2-ge0', 'GigabitEthernet1/0/0', 'GE1/0/0', '10G', 'up', {
          mode: 'trunk', neighborDevice: 'DIST-SW-01', neighborPort: 'Gi1/0/2',
          utilization: 28,
        }),
        p('ac2-ge1', 'GigabitEthernet1/0/1', 'GE1/0/1', '1G', 'up', {
          mode: 'access', accessVlan: 20, utilization: 12,
        }),
        p('ac2-ge2', 'GigabitEthernet1/0/2', 'GE1/0/2', '1G', 'up', {
          mode: 'access', accessVlan: 20, utilization: 9,
        }),
        p('ac2-ge3', 'GigabitEthernet1/0/3', 'GE1/0/3', '1G', 'down'),
      ],
    },
  },

  {
    id: 'WLC-01',
    type: 'deviceNode',
    position: { x: 510, y: 600 },
    data: {
      hostname: 'WLC-01',
      vendor: 'cisco',
      iconType: 'cisco_wlc_9800',
      model: 'Catalyst 9800-40',
      osVersion: 'IOS-XE 17.12.1',
      managementIp: '10.0.2.3',
      zone: 'Access',
      status: 'up',
      ports: [
        p('wlc-gi1', 'GigabitEthernet1', 'Gi1', '10G', 'up', {
          mode: 'trunk', neighborDevice: 'DIST-SW-02', neighborPort: 'Gi1/0/1',
          utilization: 12,
        }),
        p('wlc-gi2', 'GigabitEthernet2', 'Gi2', '1G', 'up', {
          mode: 'trunk', neighborDevice: 'AP-HALL-01', neighborPort: 'Gi0',
          utilization: 8,
        }),
        p('wlc-gi3', 'GigabitEthernet3', 'Gi3', '1G', 'admin-down'),
      ],
    },
  },

  {
    id: 'AP-HALL-01',
    type: 'deviceNode',
    position: { x: 730, y: 600 },
    data: {
      hostname: 'AP-HALL-01',
      vendor: 'cisco',
      iconType: 'cisco_ap_9120',
      model: 'Catalyst AP 9120AXI',
      osVersion: 'AP IOS 17.12.1',
      managementIp: '10.0.2.4',
      zone: 'Access',
      status: 'up',
      ports: [
        p('ap-gi0', 'GigabitEthernet0', 'Gi0', '1G', 'up', {
          mode: 'trunk', neighborDevice: 'WLC-01', neighborPort: 'Gi2',
          utilization: 8,
        }),
        p('ap-r0', 'dot11Radio0', 'Radio0', '1G', 'up', {
          description: '2.4 GHz — 802.11ax', utilization: 42,
        }),
        p('ap-r1', 'dot11Radio1', 'Radio1', '1G', 'up', {
          description: '5 GHz — 802.11ax', utilization: 67,
        }),
      ],
    },
  },
];

// ─── Mock edges (9 connections) ───────────────────────────────────────────────

export const MOCK_EDGES: Edge<MockEdgeData>[] = [
  edge('e-co1-di1', 'CORE-SW-01', 'DIST-SW-01',  '100G', 'l2'),
  edge('e-co1-di2', 'CORE-SW-01', 'DIST-SW-02',  '100G', 'l2'),
  edge('e-co2-di1', 'CORE-SW-02', 'DIST-SW-01',  '100G', 'l2'),
  edge('e-di1-ac1', 'DIST-SW-01', 'ACC-SW-01',   '10G',  'l2'),
  edge('e-di1-ac2', 'DIST-SW-01', 'ACC-SW-02',   '10G',  'l2'),
  edge('e-di2-wlc', 'DIST-SW-02', 'WLC-01',      '10G',  'l2'),
  edge('e-wlc-ap',  'WLC-01',     'AP-HALL-01',  '1G',   'l2'),
  edge('e-fw-co1',  'FW-EXT-01',  'CORE-SW-01',  '10G',  'security'),
  edge('e-dc-co2',  'DC-SPINE-01','CORE-SW-02',  '100G', 'l3'),
];
