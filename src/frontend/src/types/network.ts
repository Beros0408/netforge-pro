// TypeScript types for NetForge Pro — mirrors FastAPI models

export type Vendor = 'cisco' | 'huawei' | 'fortinet' | 'arista' | 'unknown';
export type InterfaceStatus = 'up' | 'down' | 'admin_down' | 'unknown';
export type SwitchportMode = 'access' | 'trunk' | 'routed' | 'hybrid' | 'unknown';
export type Severity = 'low' | 'medium' | 'high' | 'critical';
export type Category = 'l2' | 'l3' | 'security';
export type ZoneType = 'wan' | 'dmz' | 'lan' | 'mgmt' | 'server' | 'core';

export interface NetworkInterface {
  name: string;
  description?: string;
  interface_type?: string;
  admin_status?: boolean;
  status: InterfaceStatus;
  ip_address?: string;
  prefix_length?: number;
  mtu?: number;
  speed?: number;
  duplex?: string;
  switchport_mode?: SwitchportMode;
  access_vlan?: number;
  trunk_vlans?: number[];
  native_vlan?: number;
  vrf?: string;
  channel_group?: number;
}

export interface NetworkVLAN {
  vlan_id: number;
  name?: string;
  status?: string;
}

export interface NetworkDevice {
  hostname: string;
  vendor: Vendor;
  model?: string;
  os_version?: string;
  serial_number?: string;
  management_ip?: string;
  interfaces: NetworkInterface[];
  vlans: NetworkVLAN[];
}

export interface NetworkProblem {
  id: string;
  rule_id: string;
  category: Category;
  severity: Severity;
  device_hostname: string;
  interface?: string;
  title: string;
  description: string;
  impact: string;
  recommendation: string;
  cli_fix?: string;
  cli_fix_vendor?: string;
  evidence: Record<string, unknown>;
  detected_at?: string;
}

export interface ProblemSummary {
  total: number;
  by_severity: Record<Severity, number>;
  by_category: Record<Category, number>;
  by_rule: Record<string, number>;
}

export interface Zone {
  id: string;
  name: string;
  zone_type: ZoneType;
  security_level?: number;
  device_hostnames: string[];
  /** Canvas position */
  position?: { x: number; y: number };
  /** Canvas size */
  size?: { width: number; height: number };
}

export interface TopologyEdge {
  id: string;
  source: string;
  target: string;
  source_interface?: string;
  target_interface?: string;
  speed?: number;
  status?: string;
}

export interface TopologyData {
  devices: NetworkDevice[];
  edges: TopologyEdge[];
  zones: Zone[];
}

// ReactFlow node data payloads
export interface DeviceNodeData {
  device: NetworkDevice;
  problemCount: number;
  zone?: string;
}

export interface ZoneNodeData {
  zone: Zone;
  label: string;
  zoneType: ZoneType;
  width: number;
  height: number;
}
