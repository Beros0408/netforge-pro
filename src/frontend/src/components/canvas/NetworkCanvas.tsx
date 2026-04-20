import {
  forwardRef,
  memo,
  useCallback,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
} from 'react';
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MiniMap,
  Node,
  NodeTypes,
  EdgeTypes,
  useEdgesState,
  useNodesState,
  useReactFlow,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';
import type {
  DeviceNodeData,
  DeviceType,
  NetworkDevice,
  NetworkProblem,
  TopologyData,
  TopologyEdge,
  Vendor,
} from '../../types/network';
import { DeviceNode } from './DeviceNode';
import { EdgeWithPorts, EdgeWithPortsData } from './EdgeWithPorts';
import { CanvasToolbar, EdgeVariant, LayoutDirection } from './CanvasToolbar';
import { CanvasCallbacksContext } from '../../contexts/CanvasContext';

// ---------------------------------------------------------------------------
// Node & edge type registries
// ---------------------------------------------------------------------------

const nodeTypes: NodeTypes = { device: DeviceNode as any };
const edgeTypes: EdgeTypes = { withPorts: EdgeWithPorts as any };

// ---------------------------------------------------------------------------
// Layout algorithm (BFS, no external deps)
// ---------------------------------------------------------------------------

const H_LEVEL_GAP = 280;
const V_LEVEL_GAP = 160;
const NODE_GAP     = 140;

function bfsLevels(
  startId: string,
  adj: Map<string, string[]>,
  allIds: string[],
): Map<string, number> {
  const levels = new Map<string, number>();
  const queue  = [startId];
  levels.set(startId, 0);
  while (queue.length) {
    const curr  = queue.shift()!;
    const level = levels.get(curr)!;
    for (const nb of (adj.get(curr) ?? [])) {
      if (!levels.has(nb)) { levels.set(nb, level + 1); queue.push(nb); }
    }
  }
  let max = Math.max(0, ...levels.values());
  for (const id of allIds) if (!levels.has(id)) levels.set(id, ++max);
  return levels;
}

function computeLayout(deviceNodes: Node[], edges: Edge[], direction: LayoutDirection): Node[] {
  const ids = deviceNodes.map((n) => n.id);
  if (!ids.length) return deviceNodes;
  const adj = new Map<string, string[]>();
  for (const id of ids) adj.set(id, []);
  for (const e of edges) {
    if (adj.has(e.source) && adj.has(e.target)) {
      adj.get(e.source)!.push(e.target);
      adj.get(e.target)!.push(e.source);
    }
  }
  const levels  = bfsLevels(ids[0], adj, ids);
  const byLevel = new Map<number, string[]>();
  for (const [id, l] of levels) {
    if (!byLevel.has(l)) byLevel.set(l, []);
    byLevel.get(l)!.push(id);
  }
  const posMap = new Map<string, { x: number; y: number }>();
  for (const [level, hosts] of byLevel) {
    const perp = -(hosts.length * NODE_GAP) / 2 + NODE_GAP / 2;
    hosts.forEach((h, i) => {
      const par  = level * (direction === 'horizontal' ? H_LEVEL_GAP : V_LEVEL_GAP) + 80;
      const p    = perp + i * NODE_GAP + 300;
      posMap.set(h, direction === 'horizontal' ? { x: par, y: p } : { x: p, y: par });
    });
  }
  return deviceNodes.map((n) => ({ ...n, position: posMap.get(n.id) ?? n.position }));
}

// ---------------------------------------------------------------------------
// Data builders
// ---------------------------------------------------------------------------

function buildDeviceNodes(topology: TopologyData, problems: NetworkProblem[]): Node<DeviceNodeData>[] {
  const problemCount: Record<string, number> = {};
  for (const p of problems) problemCount[p.device_hostname] = (problemCount[p.device_hostname] ?? 0) + 1;

  const connMap: Record<string, Array<{ local_interface: string; remote_hostname: string }>> = {};
  for (const e of topology.edges) {
    if (!connMap[e.source]) connMap[e.source] = [];
    if (!connMap[e.target]) connMap[e.target] = [];
    if (e.source_interface) connMap[e.source].push({ local_interface: e.source_interface, remote_hostname: e.target });
    if (e.target_interface) connMap[e.target].push({ local_interface: e.target_interface, remote_hostname: e.source });
  }

  return topology.devices.map((device, di) => {
    const zone = topology.zones.find((z) => z.device_hostnames.includes(device.hostname));
    let x = 0, y = 0;
    if (zone) {
      const zW   = zone.size?.width ?? 280;
      const inZone = topology.devices.filter((d) => zone.device_hostnames.includes(d.hostname));
      const idx  = inZone.findIndex((d) => d.hostname === device.hostname);
      const cols = Math.ceil(Math.sqrt(inZone.length));
      const col  = idx % cols, row = Math.floor(idx / cols);
      const cW   = (zW - 80) / cols;
      x = (zone.position?.x ?? 0) + 40 + col * cW + (cW - 72) / 2;
      y = (zone.position?.y ?? 0) + 60 + row * 112;
    } else {
      x = 900 + (di % 3) * 96;
      y = 60 + Math.floor(di / 3) * 112;
    }
    return {
      id:       device.hostname,
      type:     'device',
      position: { x, y },
      data:     { device, problemCount: problemCount[device.hostname] ?? 0, connections: connMap[device.hostname] ?? [] },
      zIndex:   10,
    };
  });
}

function buildEdges(topology: TopologyData, variant: EdgeVariant): Edge<EdgeWithPortsData>[] {
  return topology.edges.map((e: TopologyEdge) => ({
    id: e.id, source: e.source, target: e.target, type: 'withPorts',
    data: { sourcePort: e.source_interface, targetPort: e.target_interface, cableType: e.cable_type, speed: e.speed, edgeVariant: variant },
  }));
}

// ---------------------------------------------------------------------------
// New device dialog
// ---------------------------------------------------------------------------

interface PendingDrop {
  deviceType: DeviceType;
  vendor:     Vendor;
  position:   { x: number; y: number };
}

function NewDeviceDialog({
  pending, onConfirm, onCancel,
}: {
  pending: PendingDrop;
  onConfirm: (device: NetworkDevice) => void;
  onCancel:  () => void;
}) {
  const [hostname, setHostname] = useState(`new-${pending.deviceType}-01`);
  const [ip,       setIp]       = useState('');
  const [model,    setModel]    = useState('');
  const [vendor,   setVendor]   = useState<Vendor>(pending.vendor === 'unknown' ? 'cisco' : pending.vendor);

  const VENDORS: Vendor[] = ['cisco', 'fortinet', 'huawei', 'arista', 'unknown'];

  const confirm = () => onConfirm({
    hostname, vendor, device_type: pending.deviceType, model: model || undefined,
    management_ip: ip || undefined, interfaces: [], vlans: [],
  });

  const inputStyle: React.CSSProperties = {
    width: '100%', background: '#0F172A', border: '1px solid #334155', borderRadius: 5,
    padding: '5px 8px', color: '#CBD5E1', fontSize: 11, outline: 'none', boxSizing: 'border-box',
  };

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.6)', zIndex: 8000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
      onClick={onCancel}>
      <div style={{ background: '#1E293B', border: '1px solid #334155', borderRadius: 10, padding: 20, width: 340, boxShadow: '0 16px 48px rgba(0,0,0,0.6)' }}
        onClick={(e) => e.stopPropagation()}>
        <div style={{ fontSize: 13, fontWeight: 700, color: '#F8FAFC', marginBottom: 14 }}>
          Nouveau device — {pending.deviceType}
        </div>
        {[
          { label: 'Nom (hostname) *', value: hostname, set: setHostname, type: 'text' },
          { label: 'IP management',    value: ip,       set: setIp,       type: 'text' },
          { label: 'Modèle',           value: model,    set: setModel,    type: 'text' },
        ].map(({ label, value, set, type }) => (
          <div key={label} style={{ marginBottom: 10 }}>
            <div style={{ fontSize: 10, color: '#64748B', marginBottom: 3 }}>{label}</div>
            <input type={type} value={value} onChange={(e) => set(e.target.value)} style={inputStyle} />
          </div>
        ))}
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontSize: 10, color: '#64748B', marginBottom: 3 }}>Vendor</div>
          <select value={vendor} onChange={(e) => setVendor(e.target.value as Vendor)} style={{ ...inputStyle, cursor: 'pointer' }}>
            {VENDORS.map((v) => <option key={v} value={v}>{v}</option>)}
          </select>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <button onClick={onCancel} style={{ padding: '6px 14px', background: '#334155', border: 'none', borderRadius: 6, color: '#94A3B8', fontSize: 11, cursor: 'pointer' }}>Annuler</button>
          <button onClick={confirm} disabled={!hostname.trim()} style={{ padding: '6px 14px', background: hostname.trim() ? '#1D4ED8' : '#1E293B', border: 'none', borderRadius: 6, color: hostname.trim() ? 'white' : '#475569', fontSize: 11, cursor: hostname.trim() ? 'pointer' : 'default' }}>
            Ajouter
          </button>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Public handle type
// ---------------------------------------------------------------------------

export interface NetworkCanvasHandle {
  fitToNode:  (hostname: string) => void;
  zoomIn:     () => void;
  zoomOut:    () => void;
  fitView:    () => void;
  layoutH:    () => void;
  layoutV:    () => void;
}

// ---------------------------------------------------------------------------
// Inner canvas (needs ReactFlow context)
// ---------------------------------------------------------------------------

interface InnerCanvasProps {
  topology:       TopologyData;
  problems:       NetworkProblem[];
  activeTool:     'select' | 'connect';
  onDeviceSelect: (device: NetworkDevice | null) => void;
}

const InnerCanvas = forwardRef<NetworkCanvasHandle, InnerCanvasProps>(function InnerCanvas(
  { topology, problems, activeTool, onDeviceSelect }, ref,
) {
  const [edgeVariant, setEdgeVariant] = useState<EdgeVariant>('smoothstep');
  const [nodes, setNodes, onNodesChange] = useNodesState<DeviceNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<EdgeWithPortsData>([]);
  const [pendingDrop, setPendingDrop]    = useState<PendingDrop | null>(null);
  const nodesRef = useRef<Node[]>([]);

  const { setCenter, zoomIn, zoomOut, fitView, screenToFlowPosition } = useReactFlow();

  // keep nodesRef in sync for imperative handle
  useEffect(() => { nodesRef.current = nodes; }, [nodes]);

  // Rebuild nodes when topology/problems change
  useEffect(() => { setNodes(buildDeviceNodes(topology, problems)); }, [topology, problems, setNodes]);
  useEffect(() => { setEdges(buildEdges(topology, edgeVariant)); }, [topology, edgeVariant, setEdges]);

  const handleLayout = useCallback((direction: LayoutDirection) => {
    setNodes((prev) => {
      const laid = computeLayout(prev, edges, direction);
      return laid;
    });
    setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 50);
  }, [edges, setNodes, fitView]);

  useImperativeHandle(ref, () => ({
    fitToNode: (hostname) => {
      const node = nodesRef.current.find((n) => n.id === hostname);
      if (node) setCenter(node.position.x + 36, node.position.y + 44, { zoom: 1.5, duration: 500 });
    },
    zoomIn:  () => zoomIn({ duration: 200 }),
    zoomOut: () => zoomOut({ duration: 200 }),
    fitView: () => fitView({ padding: 0.15, duration: 400 }),
    layoutH: () => handleLayout('horizontal'),
    layoutV: () => handleLayout('vertical'),
  }), [setCenter, zoomIn, zoomOut, fitView, handleLayout]);

  const onNodeClick = useCallback((_: React.MouseEvent, node: Node) => {
    if (node.type !== 'device') return;
    onDeviceSelect((node.data as DeviceNodeData).device);
  }, [onDeviceSelect]);

  const onPaneClick = useCallback(() => onDeviceSelect(null), [onDeviceSelect]);

  // Drag & drop from palette
  const onDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'copy';
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const raw = e.dataTransfer.getData('application/netforge-device');
    if (!raw) return;
    const { deviceType, vendor } = JSON.parse(raw) as { deviceType: DeviceType; vendor: Vendor };
    const position = screenToFlowPosition({ x: e.clientX, y: e.clientY });
    setPendingDrop({ deviceType, vendor, position });
  }, [screenToFlowPosition]);

  const addDevice = useCallback((device: NetworkDevice) => {
    const position = pendingDrop?.position ?? { x: 200, y: 200 };
    setNodes((prev) => {
      // Dedup: don't add if hostname already exists
      if (prev.some((n) => n.id === device.hostname)) {
        const unique = `${device.hostname}-${Date.now()}`;
        device = { ...device, hostname: unique };
      }
      const node: Node<DeviceNodeData> = {
        id: device.hostname, type: 'device', position,
        data: { device, problemCount: 0, connections: [] }, zIndex: 10,
      };
      return [...prev, node];
    });
    setPendingDrop(null);
  }, [pendingDrop, setNodes]);

  const canvasCallbacks = {
    onOpenCLI:  () => {},
    onShowInfo: (device: NetworkDevice) => onDeviceSelect(device),
  };

  return (
    <CanvasCallbacksContext.Provider value={canvasCallbacks}>
      <div style={{ position: 'relative', width: '100%', height: '100%', cursor: activeTool === 'connect' ? 'crosshair' : 'default' }}>
        <CanvasToolbar
          edgeVariant={edgeVariant}
          onEdgeVariantChange={setEdgeVariant}
          onLayout={handleLayout}
        />

        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          edgeTypes={edgeTypes}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          onDrop={onDrop}
          onDragOver={onDragOver}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          minZoom={0.15}
          maxZoom={3}
          deleteKeyCode={null}
          className="bg-slate-950"
        >
          <Background variant={BackgroundVariant.Dots} color="#1e293b" gap={24} size={1} />
          <Controls className="!bg-slate-900 !border-slate-700" />
          <MiniMap
            nodeColor={(n) => {
              const d = (n.data as DeviceNodeData)?.device;
              const colors: Record<string, string> = { cisco: '#1BA0D7', fortinet: '#EE3124', huawei: '#CF0A2C', arista: '#00A3E0' };
              return colors[d?.vendor ?? ''] ?? '#6B7280';
            }}
            maskColor="rgba(10,14,26,0.7)"
            style={{ bottom: 56, right: 8, width: 160, height: 100 }}
          />
        </ReactFlow>

        {pendingDrop && (
          <NewDeviceDialog
            pending={pendingDrop}
            onConfirm={addDevice}
            onCancel={() => setPendingDrop(null)}
          />
        )}
      </div>
    </CanvasCallbacksContext.Provider>
  );
});

// ---------------------------------------------------------------------------
// NetworkCanvas — wraps with ReactFlowProvider + forwards ref
// ---------------------------------------------------------------------------

interface NetworkCanvasProps {
  topology:       TopologyData;
  problems:       NetworkProblem[];
  activeTool:     'select' | 'connect';
  onDeviceSelect: (device: NetworkDevice | null) => void;
}

export const NetworkCanvas = memo(forwardRef<NetworkCanvasHandle, NetworkCanvasProps>(
  function NetworkCanvas(props, ref) {
    return (
      <ReactFlowProvider>
        <InnerCanvas {...props} ref={ref} />
      </ReactFlowProvider>
    );
  },
));
