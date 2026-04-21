/**
 * NetForge Pro — PortPanel
 *
 * Overlay panel displayed when a DeviceNode is clicked.
 * Shows all ports with: status LED, speed, mode, VLAN, neighbor.
 */

import React, { memo } from 'react';
import type { DevicePort } from './DeviceNode';

// ─── Port LED ─────────────────────────────────────────────────────────────────

const portStatusColor: Record<DevicePort['status'], string> = {
  'up':           '#10b981',
  'down':         '#ef4444',
  'err-disabled': '#f59e0b',
  'admin-down':   '#4a6080',
};

const PortLed: React.FC<{ status: DevicePort['status'] }> = ({ status }) => (
  <span style={{
    display: 'inline-block',
    width: 7, height: 7, borderRadius: '50%',
    flexShrink: 0,
    background: portStatusColor[status],
    boxShadow: status === 'up' ? `0 0 4px ${portStatusColor['up']}99` : 'none',
  }} />
);

// ─── Utilization bar ──────────────────────────────────────────────────────────

const UtilBar: React.FC<{ value: number }> = ({ value }) => {
  const color = value > 80 ? '#ef4444' : value > 50 ? '#f59e0b' : '#10b981';
  return (
    <div style={{
      width: 40, height: 4, background: '#1e2d45', borderRadius: 2, overflow: 'hidden',
    }}>
      <div style={{
        width: `${value}%`, height: '100%',
        background: color, borderRadius: 2,
        transition: 'width .3s',
      }} />
    </div>
  );
};

// ─── Speed badge ──────────────────────────────────────────────────────────────

const speedColor: Partial<Record<DevicePort['speed'], string>> = {
  '100G': '#8b5cf6',
  '40G':  '#3b82f6',
  '25G':  '#06b6d4',
  '10G':  '#049fd9',
  '1G':   '#4a6080',
  '100M': '#374151',
};

const SpeedBadge: React.FC<{ speed: DevicePort['speed'] }> = ({ speed }) => (
  <span style={{
    fontSize: 9, padding: '1px 5px', borderRadius: 3, fontWeight: 600,
    background: '#0a0f1e', color: speedColor[speed] ?? '#6b7280',
    border: `1px solid ${speedColor[speed] ?? '#6b7280'}44`,
    fontFamily: 'monospace',
  }}>
    {speed}
  </span>
);

// ─── PortPanel ────────────────────────────────────────────────────────────────

interface PortPanelProps {
  hostname: string;
  ports: DevicePort[];
  onClose: () => void;
}

export const PortPanel = memo(function PortPanel({
  hostname, ports, onClose,
}: PortPanelProps) {
  const upPorts      = ports.filter(p => p.status === 'up').length;
  const downPorts    = ports.filter(p => p.status === 'down').length;
  const errPorts     = ports.filter(p => p.status === 'err-disabled').length;
  const adminPorts   = ports.filter(p => p.status === 'admin-down').length;

  return (
    <div
      style={{
        position: 'absolute',
        left: '110%',
        top: 0,
        zIndex: 1000,
        width: 360,
        background: '#0f1729',
        border: '1px solid #1e2d45',
        borderRadius: 10,
        boxShadow: '0 16px 40px #00000088',
        overflow: 'hidden',
        animation: 'nf-slideIn .15s ease-out',
      }}
      onClick={e => e.stopPropagation()}
    >
      <style>{`
        @keyframes nf-slideIn {
          from { opacity: 0; transform: translateX(-6px); }
          to   { opacity: 1; transform: translateX(0); }
        }
      `}</style>

      {/* Header */}
      <div style={{
        padding: '10px 12px',
        borderBottom: '1px solid #1e2d45',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <span style={{ fontSize: 12, fontWeight: 600, color: '#e8edf5',
            fontFamily: '"JetBrains Mono", monospace' }}>
            {hostname}
          </span>
          <span style={{ fontSize: 10, color: '#4a6080', marginLeft: 8 }}>
            {ports.length} ports
          </span>
        </div>
        {/* Summary counters */}
        <div style={{ display: 'flex', gap: 6 }}>
          {upPorts > 0 && (
            <Counter value={upPorts} label="up" color="#10b981" />
          )}
          {downPorts > 0 && (
            <Counter value={downPorts} label="dn" color="#ef4444" />
          )}
          {errPorts > 0 && (
            <Counter value={errPorts} label="err" color="#f59e0b" />
          )}
          {adminPorts > 0 && (
            <Counter value={adminPorts} label="adm" color="#4a6080" />
          )}
        </div>
        {/* Close button */}
        <button
          onClick={onClose}
          aria-label="Close port panel"
          style={{
            background: 'none', border: 'none', cursor: 'pointer',
            color: '#4a6080', fontSize: 16, lineHeight: 1, padding: '0 0 0 8px',
          }}
        >
          ×
        </button>
      </div>

      {/* Column headers */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '16px 88px 44px 52px 1fr 44px',
        gap: 4,
        padding: '6px 12px',
        borderBottom: '1px solid #1e2d45',
      }}>
        {['', 'Port', 'Speed', 'Mode', 'Neighbor', 'Util'].map(h => (
          <span key={h} style={{ fontSize: 9, color: '#4a6080',
            fontWeight: 600, letterSpacing: '.5px', textTransform: 'uppercase' }}>
            {h}
          </span>
        ))}
      </div>

      {/* Port rows */}
      <div style={{ maxHeight: 320, overflowY: 'auto' }}>
        {ports.map(port => (
          <PortRow key={port.id} port={port} />
        ))}
      </div>
    </div>
  );
});

// ─── Port row ─────────────────────────────────────────────────────────────────

const PortRow: React.FC<{ port: DevicePort }> = ({ port }) => {
  const isConnected = !!port.neighborDevice;

  return (
    <div
      style={{
        display: 'grid',
        gridTemplateColumns: '16px 88px 44px 52px 1fr 44px',
        gap: 4,
        padding: '5px 12px',
        borderBottom: '1px solid #0f1729',
        background: port.status === 'up' ? 'transparent' : '#0a0f1a',
        alignItems: 'center',
        transition: 'background .1s',
        cursor: 'default',
      }}
      onMouseEnter={e => {
        (e.currentTarget as HTMLElement).style.background = '#1a2236';
      }}
      onMouseLeave={e => {
        (e.currentTarget as HTMLElement).style.background =
          port.status === 'up' ? 'transparent' : '#0a0f1a';
      }}
    >
      {/* LED */}
      <PortLed status={port.status} />

      {/* Port name */}
      <span style={{
        fontSize: 10, color: port.status === 'up' ? '#e8edf5' : '#4a6080',
        fontFamily: '"JetBrains Mono", monospace',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}
        title={port.description || port.name}
      >
        {port.normalizedName || port.name}
      </span>

      {/* Speed */}
      <SpeedBadge speed={port.speed} />

      {/* Mode + VLAN */}
      <span style={{ fontSize: 10, color: '#8ba3c7' }}>
        {port.mode === 'access' && port.accessVlan
          ? <><span style={{ color: '#4a6080' }}>acc</span> {port.accessVlan}</>
          : port.mode === 'trunk'
          ? <span style={{ color: '#3b82f6' }}>trunk</span>
          : port.mode === 'routed'
          ? <span style={{ color: '#8b5cf6' }}>routed</span>
          : '—'}
      </span>

      {/* Neighbor */}
      <span style={{
        fontSize: 10,
        color: isConnected ? '#049fd9' : '#4a6080',
        overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
      }}
        title={port.neighborDevice ? `${port.neighborDevice} ${port.neighborPort ?? ''}` : ''}
      >
        {port.neighborDevice
          ? `${port.neighborDevice}${port.neighborPort ? ` ${port.neighborPort}` : ''}`
          : '—'}
      </span>

      {/* Utilization */}
      <div>
        {port.utilization !== undefined
          ? <UtilBar value={port.utilization} />
          : <span style={{ fontSize: 10, color: '#4a6080' }}>—</span>}
      </div>
    </div>
  );
};

// ─── Counter badge ────────────────────────────────────────────────────────────

const Counter: React.FC<{ value: number; label: string; color: string }> = ({
  value, label, color,
}) => (
  <span style={{
    fontSize: 9, padding: '1px 5px', borderRadius: 3,
    background: `${color}22`, color,
    fontWeight: 600, fontFamily: 'monospace',
  }}>
    {value} {label}
  </span>
);

export default PortPanel;
