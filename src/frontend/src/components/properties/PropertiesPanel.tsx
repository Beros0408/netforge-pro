import { useState } from 'react';
import { X } from 'lucide-react';
import type { NetworkDevice, NetworkProblem, TopologyData, InterfaceStatus } from '../../types/network';

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const STATUS_LED: Record<InterfaceStatus, string> = {
  up:         '#22C55E',
  down:       '#EF4444',
  admin_down: '#6B7280',
  unknown:    '#F59E0B',
};

const STATUS_LABEL: Record<InterfaceStatus, string> = {
  up: 'UP', down: 'DOWN', admin_down: 'ADM↓', unknown: '?',
};

function field(label: string, value: React.ReactNode) {
  return (
    <div style={{ display: 'flex', gap: 8, padding: '3px 0', borderBottom: '1px solid #0F172A', alignItems: 'flex-start' }}>
      <span style={{ fontSize: 11, color: '#64748B', minWidth: 100, flexShrink: 0 }}>{label}</span>
      <span style={{ fontSize: 11, color: '#CBD5E1', fontFamily: 'monospace', wordBreak: 'break-all' }}>{value}</span>
    </div>
  );
}

function simulateRunningConfig(device: NetworkDevice): string {
  const lines: string[] = [];
  if (device.vendor === 'cisco') {
    lines.push(`!`, `hostname ${device.hostname}`, `!`);
    lines.push(`version ${device.os_version ?? '17.9'}`, `!`);
    for (const iface of device.interfaces) {
      lines.push(`interface ${iface.name}`);
      if (iface.description) lines.push(` description ${iface.description}`);
      if (iface.ip_address)  lines.push(` ip address ${iface.ip_address} 255.255.255.0`);
      if (iface.admin_status === false) lines.push(` shutdown`);
      lines.push(`!`);
    }
    for (const vlan of device.vlans) {
      lines.push(`vlan ${vlan.vlan_id}`);
      if (vlan.name) lines.push(` name ${vlan.name}`);
      lines.push(`!`);
    }
    lines.push(`end`);
  } else if (device.vendor === 'huawei') {
    lines.push(`#`, `sysname ${device.hostname}`, `#`);
    for (const iface of device.interfaces) {
      lines.push(`interface ${iface.name}`);
      if (iface.ip_address) lines.push(` ip address ${iface.ip_address} ${iface.prefix_length ?? 24}`);
      if (iface.admin_status === false) lines.push(` shutdown`);
      lines.push(`#`);
    }
    lines.push(`return`);
  } else {
    lines.push(`! ${device.vendor} configuration for ${device.hostname}`);
    for (const iface of device.interfaces) {
      lines.push(`interface ${iface.name}`);
      if (iface.ip_address) lines.push(`  ip address ${iface.ip_address}/${iface.prefix_length ?? 24}`);
    }
  }
  return lines.join('\n');
}

// ---------------------------------------------------------------------------
// Tabs
// ---------------------------------------------------------------------------

function NodeTab({ device, topology, problems }: {
  device: NetworkDevice; topology: TopologyData; problems: NetworkProblem[];
}) {
  const hasDown = device.interfaces.some((i) => i.status === 'down' && i.admin_status !== false);
  const up = device.interfaces.filter((i) => i.status === 'up').length;
  const deviceProblems = problems.filter((p) => p.device_hostname === device.hostname);

  const connections = topology.edges
    .filter((e) => e.source === device.hostname || e.target === device.hostname)
    .map((e) => ({
      localIface:  e.source === device.hostname ? (e.source_interface ?? '—') : (e.target_interface ?? '—'),
      remoteHost:  e.source === device.hostname ? e.target : e.source,
      remoteIface: e.source === device.hostname ? (e.target_interface ?? '—') : (e.source_interface ?? '—'),
      speed:       e.speed,
      status:      e.status ?? 'up',
    }));

  return (
    <div style={{ padding: '8px 12px', overflowY: 'auto', height: '100%' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0 16px' }}>
        <div>
          {field('Nom',      device.hostname)}
          {field('Type',     device.device_type ?? '—')}
          {field('Vendor',   device.vendor)}
          {field('Modèle',   device.model ?? '—')}
          {field('IP Mgmt',  device.management_ip ?? '—')}
        </div>
        <div>
          {field('OS',       device.os_version ?? '—')}
          {field('Série',    device.serial_number ?? '—')}
          {field('Ports UP', `${up} / ${device.interfaces.length}`)}
          {field('Statut',   (
            <span style={{ color: hasDown ? '#EF4444' : '#22C55E', fontWeight: 600 }}>
              {hasDown ? '● DOWN' : '● UP'}
            </span>
          ))}
          {field('Problèmes', deviceProblems.length > 0
            ? <span style={{ color: '#F87171' }}>⚠ {deviceProblems.length}</span>
            : <span style={{ color: '#22C55E' }}>✓ Aucun</span>
          )}
        </div>
      </div>

      {connections.length > 0 && (
        <div style={{ marginTop: 10 }}>
          <div style={{ fontSize: 10, color: '#475569', textTransform: 'uppercase', letterSpacing: '0.08em', marginBottom: 6, fontWeight: 700 }}>
            Ports connectés
          </div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
            <thead>
              <tr>
                {['Interface locale', 'Équipement distant', 'Interface distante', 'Vitesse', 'État'].map((h) => (
                  <th key={h} style={{ textAlign: 'left', padding: '3px 6px', color: '#475569', borderBottom: '1px solid #1E293B', fontWeight: 600 }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {connections.map((c, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #0F172A' }}>
                  <td style={{ padding: '3px 6px', fontFamily: 'monospace', color: '#38BDF8' }}>{c.localIface}</td>
                  <td style={{ padding: '3px 6px', fontFamily: 'monospace', color: '#94A3B8' }}>{c.remoteHost}</td>
                  <td style={{ padding: '3px 6px', fontFamily: 'monospace', color: '#64748B' }}>{c.remoteIface}</td>
                  <td style={{ padding: '3px 6px', color: '#94A3B8' }}>{c.speed ? `${c.speed >= 1000 ? `${c.speed / 1000}G` : `${c.speed}M`}` : '—'}</td>
                  <td style={{ padding: '3px 6px' }}>
                    <span style={{ color: c.status === 'up' ? '#22C55E' : '#EF4444' }}>● {c.status.toUpperCase()}</span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function ConfigTab({ device }: { device: NetworkDevice }) {
  const config = simulateRunningConfig(device);
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <pre style={{
        flex: 1, margin: 0, padding: '8px 12px', fontFamily: 'JetBrains Mono, monospace',
        fontSize: 11, color: '#86EFAC', background: '#020617', overflowY: 'auto',
        lineHeight: 1.6, whiteSpace: 'pre-wrap', wordBreak: 'break-word',
      }}>
        {config}
      </pre>
    </div>
  );
}

function InterfacesTab({ device }: { device: NetworkDevice }) {
  return (
    <div style={{ height: '100%', overflowY: 'auto', padding: '6px 0' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
        <thead style={{ position: 'sticky', top: 0, background: '#0F172A' }}>
          <tr>
            {['', 'Interface', 'IP / Masque', 'Mode', 'VLAN', 'Vitesse', 'Statut'].map((h) => (
              <th key={h} style={{ textAlign: 'left', padding: '4px 8px', color: '#475569', borderBottom: '1px solid #1E293B', fontWeight: 600, whiteSpace: 'nowrap' }}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {device.interfaces.map((iface) => {
            const status: InterfaceStatus = iface.status ?? 'unknown';
            return (
              <tr key={iface.name} style={{ borderBottom: '1px solid #0F172A' }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#0F172A')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <td style={{ padding: '3px 8px' }}>
                  <div style={{ width: 7, height: 7, borderRadius: '50%', background: STATUS_LED[status], boxShadow: `0 0 4px ${STATUS_LED[status]}` }} />
                </td>
                <td style={{ padding: '3px 8px', fontFamily: 'monospace', color: '#60A5FA', whiteSpace: 'nowrap' }}>{iface.name}</td>
                <td style={{ padding: '3px 8px', fontFamily: 'monospace', color: '#94A3B8' }}>
                  {iface.ip_address ? `${iface.ip_address}/${iface.prefix_length ?? 24}` : '—'}
                </td>
                <td style={{ padding: '3px 8px', color: '#64748B' }}>{iface.switchport_mode ?? 'routed'}</td>
                <td style={{ padding: '3px 8px', color: '#64748B' }}>{iface.access_vlan ?? (iface.trunk_vlans?.join(',') ?? '—')}</td>
                <td style={{ padding: '3px 8px', color: '#64748B' }}>{iface.speed ? (iface.speed >= 1000 ? `${iface.speed / 1000}G` : `${iface.speed}M`) : '—'}</td>
                <td style={{ padding: '3px 8px' }}>
                  <span style={{ fontSize: 9, padding: '1px 5px', borderRadius: 8, background: `${STATUS_LED[status]}20`, color: STATUS_LED[status], border: `1px solid ${STATUS_LED[status]}40` }}>
                    {STATUS_LABEL[status]}
                  </span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PropertiesPanel
// ---------------------------------------------------------------------------

const TABS = ['Node', 'Configuration', 'Interfaces'] as const;
type Tab = typeof TABS[number];

interface PropertiesPanelProps {
  device:   NetworkDevice;
  topology: TopologyData;
  problems: NetworkProblem[];
  onClose:  () => void;
}

export function PropertiesPanel({ device, topology, problems, onClose }: PropertiesPanelProps) {
  const [activeTab, setActiveTab] = useState<Tab>('Node');

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', background: '#0A0E1A', borderTop: '1px solid #1E293B' }}>
      {/* Tab bar */}
      <div style={{ display: 'flex', alignItems: 'center', borderBottom: '1px solid #1E293B', background: '#0F172A', flexShrink: 0 }}>
        {TABS.map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '6px 14px', background: 'transparent', border: 'none',
              borderBottom: activeTab === tab ? '2px solid #3B82F6' : '2px solid transparent',
              color: activeTab === tab ? '#60A5FA' : '#64748B', fontSize: 11, cursor: 'pointer',
              transition: 'color 0.15s',
            }}
          >
            {tab}
          </button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 8, paddingRight: 10 }}>
          <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#60A5FA', fontWeight: 600 }}>{device.hostname}</span>
          <button
            onClick={onClose}
            style={{ padding: 4, background: 'transparent', border: 'none', color: '#475569', cursor: 'pointer', borderRadius: 4, display: 'flex', alignItems: 'center' }}
            onMouseEnter={(e) => (e.currentTarget.style.color = '#CBD5E1')}
            onMouseLeave={(e) => (e.currentTarget.style.color = '#475569')}
          >
            <X size={13} />
          </button>
        </div>
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {activeTab === 'Node'          && <NodeTab device={device} topology={topology} problems={problems} />}
        {activeTab === 'Configuration' && <ConfigTab device={device} />}
        {activeTab === 'Interfaces'    && <InterfacesTab device={device} />}
      </div>
    </div>
  );
}
