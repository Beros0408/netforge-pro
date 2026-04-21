import { useCallback, useEffect, useRef, useState } from 'react';
import { useNetworkData } from '../../hooks/useNetworkData';
import { useProblems } from '../../hooks/useProblems';
import { TopMenuBar, ActiveTool } from './TopMenuBar';
import { DevicePalette } from '../palette/DevicePalette';
import { OutlinePanel } from '../outline/OutlinePanel';
import { PropertiesPanel } from '../properties/PropertiesPanel';
import { NetworkCanvas, NetworkCanvasHandle } from '../canvas/NetworkCanvas';
import type { DeviceNodeData } from '../canvas/DeviceNode';
import type { NetworkDevice } from '../../types/network';

// ---------------------------------------------------------------------------
// Resize divider
// ---------------------------------------------------------------------------

function VDivider({ onDrag }: { onDrag: (delta: number) => void }) {
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startX = e.clientX;
    const onMove = (ev: MouseEvent) => onDrag(ev.clientX - startX);
    const onUp   = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };
  return (
    <div
      onMouseDown={handleMouseDown}
      style={{ width: 4, flexShrink: 0, cursor: 'col-resize', background: '#1E293B', transition: 'background 0.2s' }}
      onMouseEnter={(e) => (e.currentTarget.style.background = '#334155')}
      onMouseLeave={(e) => (e.currentTarget.style.background = '#1E293B')}
    />
  );
}

function HDivider({ onDrag }: { onDrag: (delta: number) => void }) {
  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    const startY = e.clientY;
    const onMove = (ev: MouseEvent) => onDrag(ev.clientY - startY);
    const onUp   = () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
  };
  return (
    <div
      onMouseDown={handleMouseDown}
      style={{ height: 4, flexShrink: 0, cursor: 'row-resize', background: '#1E293B', transition: 'background 0.2s' }}
      onMouseEnter={(e) => (e.currentTarget.style.background = '#334155')}
      onMouseLeave={(e) => (e.currentTarget.style.background = '#1E293B')}
    />
  );
}

// ---------------------------------------------------------------------------
// Collapse button
// ---------------------------------------------------------------------------

function CollapseBtn({
  collapsed, direction, onClick,
}: { collapsed: boolean; direction: 'left' | 'right'; onClick: () => void }) {
  const arrow = direction === 'left'
    ? (collapsed ? '›' : '‹')
    : (collapsed ? '‹' : '›');
  return (
    <button
      onClick={onClick}
      style={{
        position: 'absolute',
        top: '50%', transform: 'translateY(-50%)',
        [direction === 'left' ? 'right' : 'left']: -10,
        zIndex: 10, width: 14, height: 40, background: '#1E293B',
        border: '1px solid #334155', borderRadius: direction === 'left' ? '0 6px 6px 0' : '6px 0 0 6px',
        cursor: 'pointer', color: '#64748B', fontSize: 10, padding: 0,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}
      onMouseEnter={(e) => (e.currentTarget.style.color = '#CBD5E1')}
      onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
    >
      {arrow}
    </button>
  );
}

// ---------------------------------------------------------------------------
// MainLayout
// ---------------------------------------------------------------------------

export function MainLayout() {
  const { topology, devices, loading, demoMode, lastUpdated, refresh } = useNetworkData();
  const { problems, refresh: refreshProblems } = useProblems(devices);

  const [selectedDevice, setSelectedDevice] = useState<NetworkDevice | null>(null);
  const handleDeviceSelect = useCallback((_data: DeviceNodeData | null) => {
    setSelectedDevice(null);
  }, []);
  const [activeTool,     setActiveTool]     = useState<ActiveTool>('select');

  // Panel sizes
  const [leftW,    setLeftW]    = useState(220);
  const [rightW,   setRightW]   = useState(220);
  const [bottomH,  setBottomH]  = useState(220);

  // Collapse states
  const [leftCollapsed,   setLeftCollapsed]   = useState(false);
  const [rightCollapsed,  setRightCollapsed]  = useState(false);
  const [bottomCollapsed, setBottomCollapsed] = useState(false);

  const canvasRef = useRef<NetworkCanvasHandle>(null);

  const handleRefresh = () => { refresh(); refreshProblems(); };

  // Resize handlers (delta from drag start, clamped)
  const leftDragBase  = useRef(leftW);
  const rightDragBase = useRef(rightW);
  const bottomDragBase = useRef(bottomH);

  useEffect(() => { leftDragBase.current  = leftW;  }, [leftW]);
  useEffect(() => { rightDragBase.current = rightW; }, [rightW]);
  useEffect(() => { bottomDragBase.current = bottomH; }, [bottomH]);

  // Keyboard shortcuts
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 's' || e.key === 'S') setActiveTool('select');
      if (e.key === 'c' || e.key === 'C') setActiveTool('connect');
      if (e.key === 'Escape') setSelectedDevice(null);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const problemCount = problems.length;

  const panelHeader = (title: string, onCollapse: () => void, isCollapsed: boolean) => (
    <div style={{ padding: '8px 10px', fontSize: 11, fontWeight: 700, color: '#64748B', borderBottom: '1px solid #1E293B', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      {title}
      <button onClick={onCollapse} style={{ background: 'none', border: 'none', color: '#475569', cursor: 'pointer', fontSize: 12 }}>
        {isCollapsed ? '+' : '−'}
      </button>
    </div>
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%', overflow: 'hidden', background: '#020617' }}>
      {/* ── Top menu bar ── */}
      <TopMenuBar
        activeTool={activeTool}
        onToolChange={setActiveTool}
        onFitView={() => canvasRef.current?.fitView()}
        onZoomIn={() => canvasRef.current?.zoomIn()}
        onZoomOut={() => canvasRef.current?.zoomOut()}
        onLayoutH={() => canvasRef.current?.layoutH()}
        onLayoutV={() => canvasRef.current?.layoutV()}
        deviceCount={devices.length}
        problemCount={problemCount}
        demoMode={demoMode}
      />

      {/* ── Middle row: palette | canvas | outline ── */}
      <div style={{ display: 'flex', flex: 1, minHeight: 0, overflow: 'hidden' }}>

        {/* Left palette */}
        <div style={{ position: 'relative', width: leftCollapsed ? 0 : leftW, flexShrink: 0, overflow: 'hidden', transition: 'width 0.2s' }}>
          {!leftCollapsed && (
            <DevicePalette activeTool={activeTool} onToolChange={setActiveTool} />
          )}
          <CollapseBtn
            collapsed={leftCollapsed}
            direction="left"
            onClick={() => setLeftCollapsed((v) => !v)}
          />
        </div>

        {!leftCollapsed && (
          <VDivider onDrag={(delta) => setLeftW(Math.max(140, Math.min(400, leftDragBase.current + delta)))} />
        )}

        {/* Canvas + bottom properties */}
        <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0, overflow: 'hidden' }}>
          {/* Canvas area */}
          <div style={{ flex: 1, minHeight: 0, position: 'relative' }}>
            {!loading ? (
              <NetworkCanvas
                ref={canvasRef}
                onDeviceSelect={handleDeviceSelect}
              />
            ) : loading ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569', fontSize: 13 }}>
                Chargement…
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#475569', fontSize: 13 }}>
                Aucune donnée
              </div>
            )}
          </div>

          {/* Properties panel */}
          {selectedDevice && (
            <>
              <HDivider onDrag={(delta) => setBottomH(Math.max(120, Math.min(500, bottomDragBase.current - delta)))} />
              <div style={{ height: bottomCollapsed ? 28 : bottomH, flexShrink: 0, overflow: 'hidden', transition: 'height 0.15s' }}>
                {bottomCollapsed
                  ? panelHeader(`Properties — ${selectedDevice.hostname}`, () => setBottomCollapsed(false), true)
                  : (
                    <PropertiesPanel
                      device={selectedDevice}
                      topology={topology ?? { devices: [], edges: [], zones: [] }}
                      problems={problems}
                      onClose={() => setSelectedDevice(null)}
                    />
                  )
                }
              </div>
            </>
          )}
        </div>

        {!rightCollapsed && (
          <VDivider onDrag={(delta) => setRightW(Math.max(140, Math.min(400, rightDragBase.current - delta)))} />
        )}

        {/* Right outline */}
        <div style={{ position: 'relative', width: rightCollapsed ? 0 : rightW, flexShrink: 0, overflow: 'hidden', transition: 'width 0.2s' }}>
          <CollapseBtn
            collapsed={rightCollapsed}
            direction="right"
            onClick={() => setRightCollapsed((v) => !v)}
          />
          {!rightCollapsed && topology && (
            <OutlinePanel
              topology={topology}
              selectedDevice={selectedDevice}
              onSelectDevice={setSelectedDevice}
              onFitToNode={(hostname) => canvasRef.current?.fitToNode(hostname)}
            />
          )}
        </div>
      </div>
    </div>
  );
}
