import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  AlignHorizontalDistributeCenter,
  AlignVerticalDistributeCenter,
  Crosshair,
  Download,
  FolderOpen,
  Maximize2,
  MousePointer,
  Network,
  Plus,
  Save,
  Settings,
  ZoomIn,
  ZoomOut,
} from 'lucide-react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type ActiveTool = 'select' | 'connect';

interface TopMenuBarProps {
  activeTool:    ActiveTool;
  onToolChange:  (tool: ActiveTool) => void;
  onFitView:     () => void;
  onZoomIn:      () => void;
  onZoomOut:     () => void;
  onLayoutH:     () => void;
  onLayoutV:     () => void;
  deviceCount:   number;
  problemCount:  number;
  demoMode:      boolean;
}

// ---------------------------------------------------------------------------
// Dropdown menu
// ---------------------------------------------------------------------------

interface MenuItem {
  label?:   string;
  icon?:    React.ReactNode;
  action?:  () => void;
  divider?: boolean;
  shortcut?:string;
}

function DropdownMenu({ items, onClose }: { items: MenuItem[]; onClose: () => void }) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('mousedown', handler);
    document.addEventListener('keydown', esc);
    return () => { document.removeEventListener('mousedown', handler); document.removeEventListener('keydown', esc); };
  }, [onClose]);

  return (
    <div
      ref={ref}
      style={{
        position: 'absolute', top: '100%', left: 0, zIndex: 9000,
        minWidth: 200, background: '#1E293B', border: '1px solid #334155',
        borderRadius: 6, boxShadow: '0 8px 24px rgba(0,0,0,0.5)', overflow: 'hidden',
        marginTop: 2,
      }}
    >
      {items.map((item, i) =>
        item.divider ? (
          <div key={i} style={{ height: 1, background: '#334155', margin: '2px 0' }} />
        ) : (
          <button
            key={i}
            onClick={() => { item.action?.(); onClose(); }}
            style={{
              display: 'flex', alignItems: 'center', gap: 8, width: '100%',
              padding: '7px 14px', background: 'transparent', border: 'none',
              color: '#CBD5E1', fontSize: 12, cursor: 'pointer', textAlign: 'left',
              justifyContent: 'space-between',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = '#334155')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              {item.icon && <span style={{ color: '#64748B', display: 'flex' }}>{item.icon}</span>}
              {item.label ?? ''}
            </span>
            {item.shortcut && <span style={{ color: '#475569', fontSize: 10 }}>{item.shortcut}</span>}
          </button>
        ),
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Toolbar button
// ---------------------------------------------------------------------------

function ToolBtn({
  icon, label, active = false, onClick, title,
}: {
  icon: React.ReactNode; label?: string; active?: boolean; onClick: () => void; title?: string;
}) {
  return (
    <button
      title={title ?? label}
      onClick={onClick}
      style={{
        display: 'flex', alignItems: 'center', gap: 4, padding: '4px 8px',
        borderRadius: 5, border: 'none', cursor: 'pointer', fontSize: 11,
        background: active ? '#1D4ED8' : 'transparent',
        color: active ? 'white' : '#94A3B8',
        transition: 'all 0.15s',
      }}
      onMouseEnter={(e) => { if (!active) e.currentTarget.style.background = '#1E293B'; }}
      onMouseLeave={(e) => { if (!active) e.currentTarget.style.background = 'transparent'; }}
    >
      {icon}
      {label && <span className="hidden md:inline">{label}</span>}
    </button>
  );
}

// ---------------------------------------------------------------------------
// TopMenuBar
// ---------------------------------------------------------------------------

export function TopMenuBar({
  activeTool, onToolChange, onFitView, onZoomIn, onZoomOut, onLayoutH, onLayoutV,
  deviceCount, problemCount, demoMode,
}: TopMenuBarProps) {
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const navigate = useNavigate();

  const toggle = (menu: string) => setOpenMenu((v) => (v === menu ? null : menu));

  const MENUS: Record<string, MenuItem[]> = {
    fichier: [
      { label: 'Nouvelle topologie',    icon: <Plus size={13} />,       action: () => window.location.reload() },
      { label: 'Ouvrir…',              icon: <FolderOpen size={13} />,  action: () => {} },
      { label: 'Sauvegarder',          icon: <Save size={13} />,        shortcut: 'Ctrl+S', action: () => {} },
      { divider: true },
      { label: 'Exporter PNG',         icon: <Download size={13} />,   action: () => {} },
    ],
    vue: [
      { label: 'Zoom avant',           icon: <ZoomIn size={13} />,      action: onZoomIn,   shortcut: '+' },
      { label: 'Zoom arrière',         icon: <ZoomOut size={13} />,     action: onZoomOut,  shortcut: '-' },
      { label: 'Ajuster tout',         icon: <Maximize2 size={13} />,   action: onFitView,  shortcut: 'Ctrl+Shift+H' },
      { divider: true },
      { label: 'Layout Horizontal',    icon: <AlignHorizontalDistributeCenter size={13} />, action: onLayoutH },
      { label: 'Layout Vertical',      icon: <AlignVerticalDistributeCenter size={13} />,   action: onLayoutV },
    ],
    config: [
      { label: 'Paramètres',           icon: <Settings size={13} />,    action: () => navigate('/settings') },
    ],
    simulation: [
      { label: 'Analyser problèmes',   action: () => navigate('/problems') },
      { label: 'Voir équipements',     action: () => navigate('/devices') },
      { label: 'Santé réseau',         action: () => navigate('/health') },
    ],
  };

  const menuLabels: Record<string, string> = {
    fichier: 'Fichier', vue: 'Vue', config: 'Config', simulation: 'Simulation',
  };

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', background: '#0F172A',
      borderBottom: '1px solid #1E293B', flexShrink: 0,
    }}>
      {/* Menu bar row */}
      <div style={{ display: 'flex', alignItems: 'center', height: 28, paddingLeft: 8, gap: 0 }}>
        {/* Logo */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, paddingRight: 16, borderRight: '1px solid #1E293B' }}>
          <div style={{ width: 20, height: 20, borderRadius: 5, background: '#1D4ED8', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Network size={12} color="white" />
          </div>
          <span style={{ fontSize: 11, fontWeight: 700, color: '#F8FAFC' }}>NetForge Pro</span>
        </div>

        {/* Menu items */}
        {Object.entries(menuLabels).map(([key, label]) => (
          <div key={key} style={{ position: 'relative' }}>
            <button
              onClick={() => toggle(key)}
              style={{
                padding: '0 10px', height: 28, background: openMenu === key ? '#1E293B' : 'transparent',
                border: 'none', color: '#CBD5E1', fontSize: 11, cursor: 'pointer', borderRadius: 0,
              }}
              onMouseEnter={(e) => { if (openMenu && openMenu !== key) { setOpenMenu(key); } else { e.currentTarget.style.background = '#1E293B'; } }}
              onMouseLeave={(e) => { if (openMenu !== key) e.currentTarget.style.background = 'transparent'; }}
            >
              {label}
            </button>
            {openMenu === key && (
              <DropdownMenu items={MENUS[key]} onClose={() => setOpenMenu(null)} />
            )}
          </div>
        ))}

        {/* Right side stats */}
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 12, paddingRight: 12 }}>
          {demoMode && (
            <span style={{ fontSize: 10, padding: '1px 7px', borderRadius: 10, background: '#4C1D95', color: '#C4B5FD', border: '1px solid #6D28D9' }}>
              Mode Démo
            </span>
          )}
          <span style={{ fontSize: 10, color: '#64748B' }}>
            <span style={{ color: '#94A3B8' }}>{deviceCount}</span> devices
          </span>
          {problemCount > 0 && (
            <span style={{ fontSize: 10, padding: '1px 7px', borderRadius: 10, background: '#450A0A', color: '#F87171', border: '1px solid #7F1D1D', cursor: 'pointer' }}
              onClick={() => navigate('/problems')}>
              ⚠ {problemCount}
            </span>
          )}
        </div>
      </div>

      {/* Toolbar row */}
      <div style={{ display: 'flex', alignItems: 'center', height: 32, padding: '0 8px', gap: 2, borderTop: '1px solid #1E293B', background: '#0A0E1A' }}>
        {/* Tool selection */}
        <ToolBtn icon={<MousePointer size={13} />} label="Sélection" active={activeTool === 'select'} onClick={() => onToolChange('select')} title="Outil Sélection (S)" />
        <ToolBtn icon={<Crosshair size={13} />}   label="Connecter"  active={activeTool === 'connect'} onClick={() => onToolChange('connect')} title="Outil Connexion (C)" />

        <div style={{ width: 1, height: 16, background: '#1E293B', margin: '0 4px' }} />

        {/* Zoom */}
        <ToolBtn icon={<ZoomIn size={13} />}   onClick={onZoomIn}   title="Zoom avant (+)" />
        <ToolBtn icon={<ZoomOut size={13} />}  onClick={onZoomOut}  title="Zoom arrière (-)" />
        <ToolBtn icon={<Maximize2 size={13} />} onClick={onFitView} title="Ajuster tout (Ctrl+Shift+H)" />

        <div style={{ width: 1, height: 16, background: '#1E293B', margin: '0 4px' }} />

        {/* Layout */}
        <ToolBtn icon={<AlignHorizontalDistributeCenter size={13} />} label="H" onClick={onLayoutH} title="Layout Horizontal" />
        <ToolBtn icon={<AlignVerticalDistributeCenter size={13} />}   label="V" onClick={onLayoutV} title="Layout Vertical" />
      </div>
    </div>
  );
}
