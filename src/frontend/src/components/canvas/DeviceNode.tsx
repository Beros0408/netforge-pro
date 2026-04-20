import { memo, useState } from 'react';
import { Handle, NodeProps, Position } from 'reactflow';
import type { DeviceNodeData, DeviceType, Vendor } from '../../types/network';

// ---------------------------------------------------------------------------
// Vendor colours
// ---------------------------------------------------------------------------

const VENDOR_COLOR: Record<Vendor, string> = {
  cisco:   '#1BA0D7',
  fortinet:'#EE3124',
  huawei:  '#CF0A2C',
  arista:  '#00A3E0',
  unknown: '#6B7280',
};

// ---------------------------------------------------------------------------
// Professional SVG device icons (EVE-NG / PNETLab style)
// ---------------------------------------------------------------------------

interface IconProps { color: string }

function RouterIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      {/* Cylinder body */}
      <ellipse cx="32" cy="20" rx="20" ry="7" fill={color} opacity="0.9" />
      <rect x="12" y="20" width="40" height="18" fill={color} opacity="0.75" />
      <ellipse cx="32" cy="38" rx="20" ry="7" fill={color} opacity="0.9" />
      {/* Arrows */}
      <path d="M32 8 L32 2 M32 2 L28 6 M32 2 L36 6" stroke="white" strokeWidth="2" strokeLinecap="round" />
      <path d="M32 50 L32 56 M32 56 L28 52 M32 56 L36 52" stroke="white" strokeWidth="2" strokeLinecap="round" />
      <path d="M4 29 L10 29 M4 29 L8 25 M4 29 L8 33" stroke="white" strokeWidth="2" strokeLinecap="round" />
      <path d="M60 29 L54 29 M60 29 L56 25 M60 29 L56 33" stroke="white" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

function SwitchL2Icon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      {/* 1U chassis */}
      <rect x="4" y="20" width="56" height="24" rx="3" fill={color} opacity="0.85" />
      <rect x="4" y="20" width="56" height="5" rx="2" fill="white" opacity="0.15" />
      {/* Ports row */}
      {[10, 16, 22, 28, 34, 40, 46].map((x) => (
        <rect key={x} x={x} y="28" width="5" height="8" rx="1" fill="white" opacity="0.7" />
      ))}
      {/* Status LEDs */}
      {[10, 16, 22, 28, 34].map((x, i) => (
        <circle key={x} cx={x + 2.5} cy="41" r="1.5" fill={i < 3 ? '#22C55E' : '#EF4444'} />
      ))}
    </svg>
  );
}

function SwitchL3Icon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      {/* 1U chassis */}
      <rect x="4" y="18" width="56" height="24" rx="3" fill={color} opacity="0.85" />
      <rect x="4" y="18" width="56" height="5" rx="2" fill="white" opacity="0.15" />
      {/* Ports */}
      {[8, 14, 20, 26, 32, 38].map((x) => (
        <rect key={x} x={x} y="26" width="5" height="8" rx="1" fill="white" opacity="0.7" />
      ))}
      {/* Routing triangle badge */}
      <polygon points="52,38 60,38 56,30" fill="white" opacity="0.9" />
      {/* LEDs */}
      {[8, 14, 20, 26].map((x, i) => (
        <circle key={x} cx={x + 2.5} cy="39" r="1.5" fill={i < 3 ? '#22C55E' : '#EF4444'} />
      ))}
    </svg>
  );
}

function FirewallIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      {/* Shield */}
      <path d="M32 6 L54 16 L54 34 C54 46 43 55 32 58 C21 55 10 46 10 34 L10 16 Z"
        fill={color} opacity="0.85" />
      <path d="M32 6 L54 16 L54 34 C54 46 43 55 32 58 C21 55 10 46 10 34 L10 16 Z"
        stroke="white" strokeWidth="1" fill="none" opacity="0.3" />
      {/* Flame */}
      <path d="M32 46 C28 42 26 38 30 34 C30 38 33 36 33 32 C36 35 38 40 34 44 C36 41 37 39 36 36 C39 39 40 44 36 47 Z"
        fill="white" opacity="0.9" />
    </svg>
  );
}

function WLCIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      <rect x="10" y="36" width="44" height="18" rx="3" fill={color} opacity="0.85" />
      {/* Wifi waves */}
      <path d="M32 30 C26 30 21 27 18 22" stroke={color} strokeWidth="3" strokeLinecap="round" fill="none" />
      <path d="M32 30 C38 30 43 27 46 22" stroke={color} strokeWidth="3" strokeLinecap="round" fill="none" />
      <path d="M32 30 C22 30 14 25 10 17" stroke={color} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.6" />
      <path d="M32 30 C42 30 50 25 54 17" stroke={color} strokeWidth="2.5" strokeLinecap="round" fill="none" opacity="0.6" />
      <circle cx="32" cy="30" r="3" fill={color} />
      {/* Antenna */}
      <line x1="32" y1="27" x2="32" y2="12" stroke={color} strokeWidth="2" />
      <circle cx="32" cy="10" r="2.5" fill={color} opacity="0.7" />
    </svg>
  );
}

function APIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      <circle cx="32" cy="38" r="8" fill={color} opacity="0.9" />
      {/* Wifi arcs */}
      <path d="M18 30 A20 20 0 0 1 46 30" stroke={color} strokeWidth="3" fill="none" strokeLinecap="round" />
      <path d="M10 22 A30 30 0 0 1 54 22" stroke={color} strokeWidth="2" fill="none" strokeLinecap="round" opacity="0.5" />
      <line x1="32" y1="38" x2="32" y2="56" stroke={color} strokeWidth="2.5" />
      <path d="M22 56 L42 56" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  );
}

function ServerIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      {[0, 14, 28, 42].map((y, i) => (
        <g key={y}>
          <rect x="10" y={8 + y} width="44" height="10" rx="2" fill={color} opacity={0.9 - i * 0.1} />
          <circle cx="49" cy={13 + y} r="2" fill="#22C55E" />
          <rect x="14" y={11 + y} width="20" height="4" rx="1" fill="white" opacity="0.2" />
        </g>
      ))}
    </svg>
  );
}

function EndpointIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      {/* Monitor */}
      <rect x="8" y="10" width="48" height="32" rx="3" fill={color} opacity="0.85" />
      <rect x="12" y="14" width="40" height="24" rx="1" fill="white" opacity="0.15" />
      {/* Stand */}
      <rect x="28" y="42" width="8" height="8" fill={color} opacity="0.7" />
      <rect x="18" y="50" width="28" height="4" rx="2" fill={color} opacity="0.7" />
    </svg>
  );
}

function CloudIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      <path
        d="M48 44 H18 A14 14 0 0 1 18 16 A14 14 0 0 1 32 8 A16 16 0 0 1 48 24 A10 10 0 0 1 48 44 Z"
        fill={color} opacity="0.8" />
      <path
        d="M48 44 H18 A14 14 0 0 1 18 16 A14 14 0 0 1 32 8 A16 16 0 0 1 48 24 A10 10 0 0 1 48 44 Z"
        stroke="white" strokeWidth="1" fill="none" opacity="0.2" />
    </svg>
  );
}

function UnknownIcon({ color }: IconProps) {
  return (
    <svg viewBox="0 0 64 64" width="48" height="48" fill="none">
      <rect x="8" y="8" width="48" height="48" rx="6" fill={color} opacity="0.7" />
      <text x="32" y="40" textAnchor="middle" fill="white" fontSize="24" fontWeight="bold">?</text>
    </svg>
  );
}

function DeviceIcon({ deviceType, color }: { deviceType: DeviceType; color: string }) {
  switch (deviceType) {
    case 'router':   return <RouterIcon color={color} />;
    case 'switch':   return <SwitchL2Icon color={color} />;
    case 'firewall': return <FirewallIcon color={color} />;
    case 'wlc':      return <WLCIcon color={color} />;
    case 'ap':       return <APIcon color={color} />;
    case 'server':   return <ServerIcon color={color} />;
    case 'endpoint': return <EndpointIcon color={color} />;
    case 'cloud':    return <CloudIcon color={color} />;
    default:         return <UnknownIcon color={color} />;
  }
}

// ---------------------------------------------------------------------------
// Tooltip
// ---------------------------------------------------------------------------

function DeviceTooltip({ data }: { data: DeviceNodeData }) {
  const { device, problemCount, connections = [] } = data;
  const up = device.interfaces.filter((i) => i.status === 'up').length;
  const vendorColor = VENDOR_COLOR[device.vendor];

  return (
    <div
      style={{
        position: 'absolute',
        left: 'calc(100% + 12px)',
        top: '50%',
        transform: 'translateY(-50%)',
        zIndex: 9999,
        minWidth: 240,
        background: '#1E293B',
        border: `1px solid ${vendorColor}`,
        borderRadius: 8,
        padding: '10px 12px',
        boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
        pointerEvents: 'none',
      }}
    >
      {/* Title */}
      <div style={{ fontFamily: 'monospace', fontSize: 12, fontWeight: 700, color: '#F8FAFC', marginBottom: 6 }}>
        {device.hostname}
      </div>
      <div style={{ height: 1, background: '#334155', marginBottom: 6 }} />

      {/* Fields */}
      {[
        ['Modèle',   device.model ?? '—'],
        ['IP Mgmt',  device.management_ip ?? '—'],
        ['Vendor',   device.vendor],
        ['OS',       device.os_version ?? '—'],
        ['Ports UP', `${up}/${device.interfaces.length}`],
        ['Problèmes', problemCount > 0 ? `⚠ ${problemCount}` : '✓ Aucun'],
      ].map(([label, value]) => (
        <div key={label} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, marginBottom: 3 }}>
          <span style={{ color: '#64748B', minWidth: 70 }}>{label}</span>
          <span style={{ fontFamily: 'monospace', color: '#CBD5E1', textAlign: 'right', maxWidth: 150, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {value}
          </span>
        </div>
      ))}

      {/* Connections */}
      {connections.length > 0 && (
        <>
          <div style={{ height: 1, background: '#334155', margin: '6px 0' }} />
          <div style={{ fontSize: 10, color: '#64748B', marginBottom: 4 }}>Connexions :</div>
          {connections.map((c) => (
            <div key={c.local_interface} style={{ fontFamily: 'monospace', fontSize: 10, color: '#94A3B8', marginBottom: 2 }}>
              <span style={{ color: '#38BDF8' }}>{c.local_interface}</span>
              <span style={{ color: '#475569' }}> → </span>
              {c.remote_hostname}
            </div>
          ))}
        </>
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// DeviceNode — EVE-NG / PNETLab style
// ---------------------------------------------------------------------------

export const DeviceNode = memo(function DeviceNode({ data, selected }: NodeProps<DeviceNodeData>) {
  const [hovered, setHovered] = useState(false);
  const { device, problemCount } = data;
  const deviceType: DeviceType = device.device_type ?? 'unknown';
  const vendorColor = VENDOR_COLOR[device.vendor] ?? '#6B7280';
  const hasProblems = problemCount > 0;
  const hasDown = device.interfaces.some((i) => i.status === 'down' && i.admin_status !== false);

  return (
    <div
      style={{ position: 'relative', width: 72, textAlign: 'center' }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
    >
      {/* Handles — all 4 sides, invisible */}
      <Handle type="target" position={Position.Left}   style={{ opacity: 0, width: 8, height: 8, left: -4 }} />
      <Handle type="target" position={Position.Top}    style={{ opacity: 0, width: 8, height: 8, top: -4 }} />
      <Handle type="source" position={Position.Right}  style={{ opacity: 0, width: 8, height: 8, right: -4 }} />
      <Handle type="source" position={Position.Bottom} style={{ opacity: 0, width: 8, height: 8, bottom: -4 }} />

      {/* Icon container */}
      <div
        style={{
          position: 'relative',
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: 64,
          height: 64,
          borderRadius: 12,
          background: selected ? `${vendorColor}22` : 'transparent',
          border: selected ? `2px solid ${vendorColor}` : '2px solid transparent',
          transition: 'all 0.15s',
          cursor: 'pointer',
        }}
      >
        <DeviceIcon deviceType={deviceType} color={vendorColor} />

        {/* Status LED — top-right */}
        <div
          style={{
            position: 'absolute',
            top: 4,
            right: 4,
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: hasDown ? '#EF4444' : '#22C55E',
            boxShadow: `0 0 4px ${hasDown ? '#EF4444' : '#22C55E'}`,
          }}
        />

        {/* Problem badge — top-left */}
        {hasProblems && (
          <div
            style={{
              position: 'absolute',
              top: 2,
              left: 2,
              minWidth: 16,
              height: 16,
              borderRadius: 8,
              background: '#EF4444',
              color: 'white',
              fontSize: 9,
              fontWeight: 700,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0 4px',
            }}
          >
            {problemCount}
          </div>
        )}
      </div>

      {/* Hostname label */}
      <div
        style={{
          marginTop: 4,
          fontSize: 10,
          fontFamily: 'JetBrains Mono, monospace',
          fontWeight: 600,
          color: selected ? vendorColor : '#CBD5E1',
          whiteSpace: 'nowrap',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          maxWidth: 80,
          textAlign: 'center',
        }}
      >
        {device.hostname}
      </div>

      {/* Tooltip on hover */}
      {hovered && <DeviceTooltip data={data} />}
    </div>
  );
});
