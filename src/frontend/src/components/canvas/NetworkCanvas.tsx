/**
 * NetworkCanvas.tsx — NetForge Pro
 * Canvas ReactFlow principal : icônes isométriques, toolbar, minimap, layout zones
 * Refs: CDC §8.1 §8.3 · Enrichissements v4 §1.4 §1.5
 */
import React, {
  forwardRef,
  memo,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
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
  NodeProps,
  NodeTypes,
  useEdgesState,
  useNodesState,
  useReactFlow,
  ReactFlowProvider,
} from 'reactflow';
import 'reactflow/dist/style.css';

import type { DeviceNodeData } from './DeviceNode';
import { DeviceNode } from './DeviceNode';
import type { MockEdgeData } from '../../data/mockTopology';
import { MOCK_EDGES, MOCK_NODES } from '../../data/mockTopology';

// ─── Node type registry ───────────────────────────────────────────────────────

const nodeTypes: NodeTypes = {
  deviceNode: DeviceNode as unknown as React.ComponentType<NodeProps>,
};

// ─── Default edge options ─────────────────────────────────────────────────────

const defaultEdgeOptions = {
  style: { stroke: '#2a3f5f', strokeWidth: 2 },
  labelStyle: { fontSize: 9, fill: '#4a6080', fontFamily: '"JetBrains Mono", monospace' },
  labelBgStyle: { fill: '#0a0f1e', fillOpacity: 0.85 },
  labelBgPadding: [3, 4] as [number, number],
};

// ─── Zone layout ──────────────────────────────────────────────────────────────

const ZONE_Y: Record<string, number> = {
  DMZ:          -200,
  DataCenter:   -200,
  Core:            0,
  Distribution:  300,
  Access:        600,
};

function layoutByZone(nodes: Node<DeviceNodeData>[]): Node<DeviceNodeData>[] {
  const byZone = new Map<string, Node<DeviceNodeData>[]>();
  for (const n of nodes) {
    const z = n.data.zone ?? 'Unknown';
    if (!byZone.has(z)) byZone.set(z, []);
    byZone.get(z)!.push(n);
  }
  return nodes.map((n) => {
    const z       = n.data.zone ?? 'Unknown';
    const group   = byZone.get(z)!;
    const idx     = group.findIndex((g) => g.id === n.id);
    const count   = group.length;
    const y       = ZONE_Y[z] ?? 800;
    const total   = (count - 1) * 220;
    const x       = 400 - total / 2 + idx * 220;
    return { ...n, position: { x, y } };
  });
}

// ─── Layer filter ─────────────────────────────────────────────────────────────

type LayerFilter = 'physical' | 'l2' | 'l3' | 'security' | 'traffic';

function filterEdges(
  edges: Edge<MockEdgeData>[],
  layer: LayerFilter,
): Edge<MockEdgeData>[] {
  if (layer === 'physical' || layer === 'traffic') return edges;
  if (layer === 'security') return edges.filter((e) => e.data?.layer === 'security');
  return edges.filter((e) => e.data?.layer === layer);
}

// ─── Public types ─────────────────────────────────────────────────────────────

export interface NetworkCanvasHandle {
  fitView:    () => void;
  zoomIn:     () => void;
  zoomOut:    () => void;
  fitToNode:  (id: string) => void;
  layoutAuto: () => void;
  layoutH:    () => void;
  layoutV:    () => void;
}

interface NetworkCanvasProps {
  initialNodes?: Node<DeviceNodeData>[];
  initialEdges?: Edge<MockEdgeData>[];
  onDeviceSelect?: (data: DeviceNodeData | null) => void;
  onOpenCLI?: (data: DeviceNodeData) => void;
}

// ─── Inner canvas (needs ReactFlow context) ───────────────────────────────────

const InnerCanvas = forwardRef<NetworkCanvasHandle, Required<NetworkCanvasProps>>(
  function InnerCanvas({ initialNodes, initialEdges, onDeviceSelect, onOpenCLI }, ref) {
    const { fitView, zoomIn, zoomOut, setCenter, getNode } = useReactFlow();

    const [nodes, setNodes, onNodesChange] = useNodesState<DeviceNodeData>(initialNodes);
    const [edges, , onEdgesChange]         = useEdgesState<MockEdgeData>(initialEdges);
    const [activeLayer, setActiveLayer]    = useState<LayerFilter>('physical');

    // Stable callback ref — avoids re-enriching nodes when parent re-renders
    const onOpenCLIRef = useRef(onOpenCLI);
    useEffect(() => { onOpenCLIRef.current = onOpenCLI; }, [onOpenCLI]);

    const stableOpenCLI = useCallback((data: DeviceNodeData) => {
      onOpenCLIRef.current(data);
    }, []);

    // Inject onOpenCLI into node data at render time (avoids stale callback)
    const enrichedNodes = useMemo((): Node<DeviceNodeData>[] =>
      nodes.map((n) => ({
        ...n,
        data: { ...n.data, onOpenCLI: stableOpenCLI },
      })),
      [nodes, stableOpenCLI],
    );

    const visibleEdges = useMemo(
      () => filterEdges(edges, activeLayer),
      [edges, activeLayer],
    );

    const runLayout = useCallback(() => {
      setNodes((prev) => layoutByZone(prev));
      setTimeout(() => fitView({ padding: 0.15, duration: 400 }), 50);
    }, [setNodes, fitView]);

    // Imperative handle
    useImperativeHandle(ref, () => ({
      fitView:    () => fitView({ padding: 0.15, duration: 400 }),
      zoomIn:     () => zoomIn({ duration: 200 }),
      zoomOut:    () => zoomOut({ duration: 200 }),
      fitToNode:  (id) => {
        const node = getNode(id);
        if (node) setCenter(node.position.x + 60, node.position.y + 60, { zoom: 1.5, duration: 500 });
      },
      layoutAuto: runLayout,
      layoutH:    runLayout,
      layoutV:    runLayout,
    }), [fitView, zoomIn, zoomOut, setCenter, getNode, runLayout]);

    const onNodeClick = useCallback(
      (_: React.MouseEvent, node: Node) => {
        onDeviceSelect((node as Node<DeviceNodeData>).data);
      },
      [onDeviceSelect],
    );

    const onPaneClick = useCallback(() => {
      onDeviceSelect(null);
    }, [onDeviceSelect]);

    return (
      <div style={{ width: '100%', height: '100%', position: 'relative' }}>

        {/* ReactFlow controls dark theme injection */}
        <style>{`
          .react-flow__controls {
            background: #0f1729 !important;
            border: 1px solid #1e2d45 !important;
            border-radius: 8px !important;
            box-shadow: 0 4px 16px rgba(0,0,0,0.5) !important;
          }
          .react-flow__controls-button {
            background: transparent !important;
            border-bottom: 1px solid #1e2d45 !important;
          }
          .react-flow__controls-button:last-child { border-bottom: none !important; }
          .react-flow__controls-button svg { fill: #8ba3c7 !important; }
          .react-flow__controls-button:hover { background: #1e2d45 !important; }
          .react-flow__edge-label { font-family: "JetBrains Mono", monospace; }
        `}</style>

        {/* Floating toolbar — top-left */}
        <CanvasToolbar
          activeLayer={activeLayer}
          onLayerChange={setActiveLayer}
          onFitView={() => fitView({ padding: 0.15, duration: 400 })}
          onLayoutAuto={runLayout}
        />

        <ReactFlow
          nodes={enrichedNodes}
          edges={visibleEdges}
          nodeTypes={nodeTypes}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onNodeClick={onNodeClick}
          onPaneClick={onPaneClick}
          fitView
          fitViewOptions={{ padding: 0.2 }}
          snapToGrid
          snapGrid={[16, 16]}
          defaultEdgeOptions={defaultEdgeOptions}
          deleteKeyCode={null}
          minZoom={0.1}
          maxZoom={4}
          style={{ background: '#0a0f1e' }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            color="#1e2d45"
            gap={24}
            size={1}
          />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={(n) => {
              const v = (n as Node<DeviceNodeData>).data?.vendor;
              const MAP: Record<string, string> = {
                cisco:    '#049fd9',
                fortinet: '#ef4444',
                huawei:   '#dc2626',
                arista:   '#6b7280',
              };
              return MAP[v] ?? '#4a6080';
            }}
            maskColor="rgba(10,15,30,0.72)"
            style={{
              background: '#0f1729',
              border: '1px solid #1e2d45',
              borderRadius: 8,
            }}
          />
        </ReactFlow>
      </div>
    );
  },
);

// ─── Floating toolbar ─────────────────────────────────────────────────────────

interface CanvasToolbarProps {
  activeLayer:    LayerFilter;
  onLayerChange:  (l: LayerFilter) => void;
  onFitView:      () => void;
  onLayoutAuto:   () => void;
}

const LAYER_BTNS: { value: LayerFilter; label: string }[] = [
  { value: 'physical',  label: 'Physique' },
  { value: 'l2',        label: 'L2'       },
  { value: 'l3',        label: 'L3'       },
  { value: 'security',  label: 'Sécurité' },
  { value: 'traffic',   label: 'Flux'     },
];

function CanvasToolbar({ activeLayer, onLayerChange, onFitView, onLayoutAuto }: CanvasToolbarProps) {
  const btnBase: React.CSSProperties = {
    padding: '4px 10px',
    borderRadius: 5,
    border: 'none',
    fontSize: 11,
    cursor: 'pointer',
    transition: 'all .12s',
    fontFamily: '"JetBrains Mono", monospace',
    fontWeight: 600,
  };

  return (
    <div
      style={{
        position: 'absolute',
        top: 12,
        left: 12,
        zIndex: 20,
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        background: '#0f1729',
        border: '1px solid #1e2d45',
        borderRadius: 10,
        padding: '5px 8px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.5)',
      }}
    >
      {/* Action buttons */}
      <button
        onClick={onFitView}
        style={{ ...btnBase, background: '#1e2d45', color: '#8ba3c7' }}
        onMouseEnter={(e) => (e.currentTarget.style.background = '#2a3f5f')}
        onMouseLeave={(e) => (e.currentTarget.style.background = '#1e2d45')}
        title="Ajuster la vue"
      >
        Fit View
      </button>

      <button
        onClick={onLayoutAuto}
        style={{ ...btnBase, background: '#1e2d45', color: '#8ba3c7' }}
        onMouseEnter={(e) => (e.currentTarget.style.background = '#2a3f5f')}
        onMouseLeave={(e) => (e.currentTarget.style.background = '#1e2d45')}
        title="Layout automatique par zones"
      >
        Layout Auto
      </button>

      {/* Separator */}
      <div style={{ width: 1, height: 20, background: '#1e2d45', margin: '0 2px' }} />

      {/* Layer filter */}
      {LAYER_BTNS.map(({ value, label }) => (
        <button
          key={value}
          onClick={() => onLayerChange(value)}
          style={{
            ...btnBase,
            background: activeLayer === value ? '#049fd9' : 'transparent',
            color:      activeLayer === value ? '#fff'    : '#4a6080',
          }}
          onMouseEnter={(e) => {
            if (activeLayer !== value) e.currentTarget.style.color = '#8ba3c7';
          }}
          onMouseLeave={(e) => {
            if (activeLayer !== value) e.currentTarget.style.color = '#4a6080';
          }}
          title={`Filtrer couche ${label}`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}

// ─── NetworkCanvas — public component ────────────────────────────────────────

export const NetworkCanvas = memo(
  forwardRef<NetworkCanvasHandle, NetworkCanvasProps>(function NetworkCanvas(
    { initialNodes, initialEdges, onDeviceSelect, onOpenCLI },
    ref,
  ) {
    const nodes  = initialNodes  ?? MOCK_NODES;
    const edges  = initialEdges  ?? MOCK_EDGES;
    const select = onDeviceSelect ?? (() => undefined);
    const cli    = onOpenCLI     ?? (() => undefined);

    return (
      <ReactFlowProvider>
        <InnerCanvas
          ref={ref}
          initialNodes={nodes}
          initialEdges={edges}
          onDeviceSelect={select}
          onOpenCLI={cli}
        />
      </ReactFlowProvider>
    );
  }),
);

NetworkCanvas.displayName = 'NetworkCanvas';
