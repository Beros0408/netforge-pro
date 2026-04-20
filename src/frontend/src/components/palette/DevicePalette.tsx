import { useState } from 'react';
import type { DeviceType, Vendor } from '../../types/network';

// ---------------------------------------------------------------------------
// Palette item definitions
// ---------------------------------------------------------------------------

interface PaletteDevice {
  deviceType: DeviceType;
  vendor:     Vendor;
  label:      string;
  color:      string;
}

const VENDOR_COLOR: Record<Vendor, string> = {
  cisco:   '#1BA0D7',
  fortinet:'#EE3124',
  huawei:  '#CF0A2C',
  arista:  '#00A3E0',
  unknown: '#6B7280',
};

const NODE_ITEMS: PaletteDevice[] = [
  { deviceType: 'router',   vendor: 'unknown', label: 'Router',       color: '#F97316' },
  { deviceType: 'switch',   vendor: 'unknown', label: 'Switch L2',    color: '#3B82F6' },
  { deviceType: 'switch',   vendor: 'unknown', label: 'Switch L3',    color: '#8B5CF6' },
  { deviceType: 'firewall', vendor: 'unknown', label: 'Firewall',     color: '#EF4444' },
  { deviceType: 'wlc',      vendor: 'unknown', label: 'WLC',          color: '#06B6D4' },
  { deviceType: 'ap',       vendor: 'unknown', label: 'Access Point', color: '#10B981' },
  { deviceType: 'server',   vendor: 'unknown', label: 'Server',       color: '#6B7280' },
  { deviceType: 'cloud',    vendor: 'unknown', label: 'Cloud',        color: '#60A5FA' },
  { deviceType: 'endpoint', vendor: 'unknown', label: 'PC/Endpoint',  color: '#94A3B8' },
];

const VENDOR_ITEMS: { vendor: Vendor; label: string; abbr: string }[] = [
  { vendor: 'cisco',   label: 'Cisco',    abbr: 'C' },
  { vendor: 'fortinet',label: 'Fortinet', abbr: 'F' },
  { vendor: 'huawei',  label: 'Huawei',   abbr: 'H' },
  { vendor: 'arista',  label: 'Arista',   abbr: 'A' },
];

// Small SVG icons for palette items
function PaletteIcon({ deviceType, color }: { deviceType: DeviceType; color: string }) {
  switch (deviceType) {
    case 'router':
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <ellipse cx="12" cy="8" rx="7" ry="2.5" fill={color} opacity="0.9" />
          <rect x="5" y="8" width="14" height="7" fill={color} opacity="0.7" />
          <ellipse cx="12" cy="15" rx="7" ry="2.5" fill={color} opacity="0.9" />
          <path d="M12 3L12 1M12 1L10 3M12 1L14 3" stroke={color} strokeWidth="1.2" strokeLinecap="round"/>
          <path d="M12 19L12 21M12 21L10 19M12 21L14 19" stroke={color} strokeWidth="1.2" strokeLinecap="round"/>
        </svg>
      );
    case 'switch':
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <rect x="2" y="8" width="20" height="8" rx="1.5" fill={color} opacity="0.85" />
          {[4,7,10,13,16].map((x) => <rect key={x} x={x} y="11" width="2" height="3" rx="0.5" fill="white" opacity="0.7" />)}
        </svg>
      );
    case 'firewall':
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <path d="M12 2L20 6V12C20 16.5 16.5 20 12 22C7.5 20 4 16.5 4 12V6Z" fill={color} opacity="0.85" />
          <path d="M12 17C10.5 15.5 10 14 11.5 12.5C11.5 13.5 12.5 13 12.5 11.5C14 13 14.5 15 13 16.5C14 15 14 14 13.5 13C15 14.5 15 16.5 13 17.5Z" fill="white" opacity="0.9"/>
        </svg>
      );
    case 'wlc':
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <rect x="3" y="14" width="18" height="7" rx="1.5" fill={color} opacity="0.8" />
          <path d="M12 12C10 12 8.5 11 7.5 9.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" fill="none"/>
          <path d="M12 12C14 12 15.5 11 16.5 9.5" stroke={color} strokeWidth="1.5" strokeLinecap="round" fill="none"/>
          <circle cx="12" cy="12" r="1.5" fill={color}/>
          <line x1="12" y1="10" x2="12" y2="5" stroke={color} strokeWidth="1.5"/>
        </svg>
      );
    case 'ap':
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <circle cx="12" cy="15" r="3" fill={color} opacity="0.9"/>
          <path d="M7 11C8.5 9.5 10 9 12 9C14 9 15.5 9.5 17 11" stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round"/>
          <path d="M4.5 8.5C7 6 9.5 5 12 5C14.5 5 17 6 19.5 8.5" stroke={color} strokeWidth="1.5" fill="none" strokeLinecap="round" opacity="0.5"/>
          <line x1="12" y1="18" x2="12" y2="22" stroke={color} strokeWidth="2"/>
        </svg>
      );
    case 'server':
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          {[2,8,14].map((y) => <rect key={y} x="3" y={y} width="18" height="5" rx="1" fill={color} opacity={0.85 - y * 0.02} />)}
        </svg>
      );
    case 'cloud':
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <path d="M18 17H7A5 5 0 0 1 7 7A5 5 0 0 1 12 4A6 6 0 0 1 18 10A4 4 0 0 1 18 17Z" fill={color} opacity="0.8"/>
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none">
          <rect x="2" y="4" width="20" height="13" rx="2" fill={color} opacity="0.8"/>
          <rect x="8" y="17" width="8" height="3" fill={color} opacity="0.6"/>
          <rect x="5" y="20" width="14" height="2" rx="1" fill={color} opacity="0.6"/>
        </svg>
      );
  }
}

// ---------------------------------------------------------------------------
// Section wrapper
// ---------------------------------------------------------------------------

function Section({ title, children, defaultOpen = true }: {
  title: string; children: React.ReactNode; defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div style={{ marginBottom: 2 }}>
      <button
        onClick={() => setOpen((v) => !v)}
        style={{
          display: 'flex', alignItems: 'center', gap: 4, width: '100%',
          padding: '5px 10px', background: 'transparent', border: 'none',
          color: '#64748B', fontSize: 10, fontWeight: 700, letterSpacing: '0.08em',
          textTransform: 'uppercase', cursor: 'pointer', textAlign: 'left',
        }}
      >
        <span style={{ transition: 'transform 0.15s', transform: open ? 'rotate(90deg)' : 'none', fontSize: 8 }}>▶</span>
        {title}
      </button>
      {open && <div style={{ paddingBottom: 4 }}>{children}</div>}
    </div>
  );
}

// ---------------------------------------------------------------------------
// DevicePalette
// ---------------------------------------------------------------------------

interface DevicePaletteProps {
  activeTool:   'select' | 'connect';
  onToolChange: (t: 'select' | 'connect') => void;
}

export function DevicePalette({ activeTool, onToolChange }: DevicePaletteProps) {
  const handleDragStart = (e: React.DragEvent, deviceType: DeviceType, vendor: Vendor) => {
    e.dataTransfer.setData('application/netforge-device', JSON.stringify({ deviceType, vendor }));
    e.dataTransfer.effectAllowed = 'copy';
  };

  const itemStyle = (draggable = true): React.CSSProperties => ({
    display: 'flex', alignItems: 'center', gap: 8, padding: '5px 12px',
    cursor: draggable ? 'grab' : 'pointer',
    fontSize: 11, color: '#94A3B8', userSelect: 'none',
    borderRadius: 4, margin: '0 4px',
    transition: 'background 0.1s',
  });

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: '#0A0E1A', borderRight: '1px solid #1E293B', overflowY: 'auto',
    }}>
      {/* Header */}
      <div style={{ padding: '10px 12px 6px', borderBottom: '1px solid #1E293B', flexShrink: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#F8FAFC', marginBottom: 2 }}>Topology Palette</div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
        {/* Tools section */}
        <Section title="Tools">
          {[
            { tool: 'select' as const, icon: '↖', label: 'Sélection' },
            { tool: 'connect' as const, icon: '🔗', label: 'Connecter' },
          ].map(({ tool, icon, label }) => (
            <div
              key={tool}
              onClick={() => onToolChange(tool)}
              style={{
                ...itemStyle(false),
                background: activeTool === tool ? '#1D4ED820' : 'transparent',
                color: activeTool === tool ? '#60A5FA' : '#94A3B8',
                cursor: 'pointer',
              }}
              onMouseEnter={(e) => { if (activeTool !== tool) e.currentTarget.style.background = '#1E293B'; }}
              onMouseLeave={(e) => { if (activeTool !== tool) e.currentTarget.style.background = 'transparent'; }}
            >
              <span style={{ fontSize: 13, width: 18, textAlign: 'center' }}>{icon}</span>
              <span>{label}</span>
            </div>
          ))}
        </Section>

        {/* Nodes section */}
        <Section title="Nodes">
          {NODE_ITEMS.map((item) => (
            <div
              key={`${item.deviceType}-${item.label}`}
              draggable
              onDragStart={(e) => handleDragStart(e, item.deviceType, item.vendor)}
              style={{ ...itemStyle() }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#1E293B')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <PaletteIcon deviceType={item.deviceType} color={item.color} />
              <span>{item.label}</span>
            </div>
          ))}
        </Section>

        {/* Vendors section */}
        <Section title="Vendors" defaultOpen={false}>
          {VENDOR_ITEMS.map((v) => (
            <div
              key={v.vendor}
              draggable
              onDragStart={(e) => handleDragStart(e, 'unknown', v.vendor)}
              style={{ ...itemStyle() }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#1E293B')}
              onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
            >
              <div style={{
                width: 18, height: 18, borderRadius: 4, background: VENDOR_COLOR[v.vendor],
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 8, fontWeight: 800, color: 'white', flexShrink: 0,
              }}>
                {v.abbr}
              </div>
              <span>{v.label}</span>
            </div>
          ))}
        </Section>

        {/* Annotations section */}
        <Section title="Annotations" defaultOpen={false}>
          {[
            { icon: '□', label: 'Rectangle' },
            { icon: '○', label: 'Ellipse' },
            { icon: '—', label: 'Ligne' },
            { icon: 'T', label: 'Texte' },
          ].map(({ icon, label }) => (
            <div
              key={label}
              style={{ ...itemStyle(false), opacity: 0.5, cursor: 'not-allowed' }}
              title="Bientôt disponible"
            >
              <span style={{ fontSize: 14, width: 18, textAlign: 'center', fontFamily: 'monospace' }}>{icon}</span>
              <span>{label}</span>
            </div>
          ))}
        </Section>
      </div>
    </div>
  );
}
