import { memo, useCallback, useMemo } from 'react';
import ReactFlow, {
  Background,
  BackgroundVariant,
  Controls,
  Edge,
  MiniMap,
  Node,
  NodeTypes,
  useEdgesState,
  useNodesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import type { NetworkDevice, NetworkProblem, TopologyData, ZoneNodeData, DeviceNodeData } from '../../types/network';
import { DeviceNode } from './DeviceNode';
import { ZoneOverlay } from './ZoneOverlay';

// ---------------------------------------------------------------------------
// Node types — defined outside component to prevent re-renders
// ---------------------------------------------------------------------------

const nodeTypes: NodeTypes = {
  device: DeviceNode as any,
  zone: ZoneOverlay as any,
};

// ---------------------------------------------------------------------------
// Layout helpers
// ---------------------------------------------------------------------------

const ZONE_PADDING = 40;
const NODE_WIDTH = 180;
const NODE_HEIGHT = 110;

function buildNodes(
  topology: TopologyData,
  problems: NetworkProblem[],
): Node[] {
  const problemCountByDevice: Record<string, number> = {};
  for (const p of problems) {
    problemCountByDevice[p.device_hostname] = (problemCountByDevice[p.device_hostname] ?? 0) + 1;
  }

  const zoneNodes: Node[] = topology.zones.map((zone, zi) => {
    const width = zone.size?.width ?? 280;
    const height = zone.size?.height ?? 220;
    const x = zone.position?.x ?? zi * 320 + 20;
    const y = zone.position?.y ?? 60;

    const nodeData: ZoneNodeData = {
      zone,
      label: zone.name,
      zoneType: zone.zone_type,
      width,
      height,
    };

    return {
      id: `zone-${zone.id}`,
      type: 'zone',
      position: { x, y },
      data: nodeData,
      selectable: false,
      draggable: false,
      zIndex: -1,
      style: { width, height },
    };
  });

  const deviceNodes: Node[] = topology.devices.map((device, di) => {
    const zone = topology.zones.find((z) => z.device_hostnames.includes(device.hostname));
    let x: number;
    let y: number;

    if (zone) {
      const zoneX = zone.position?.x ?? 0;
      const zoneY = zone.position?.y ?? 0;
      const zoneWidth = zone.size?.width ?? 280;
      const devicesInZone = topology.devices.filter((d) =>
        zone.device_hostnames.includes(d.hostname),
      );
      const idx = devicesInZone.findIndex((d) => d.hostname === device.hostname);
      const cols = Math.ceil(Math.sqrt(devicesInZone.length));
      const col = idx % cols;
      const row = Math.floor(idx / cols);
      const colWidth = (zoneWidth - ZONE_PADDING * 2) / cols;
      x = zoneX + ZONE_PADDING + col * colWidth + (colWidth - NODE_WIDTH) / 2;
      y = zoneY + 50 + row * (NODE_HEIGHT + 16);
    } else {
      x = 900 + (di % 3) * (NODE_WIDTH + 20);
      y = 60 + Math.floor(di / 3) * (NODE_HEIGHT + 20);
    }

    const nodeData: DeviceNodeData = {
      device,
      problemCount: problemCountByDevice[device.hostname] ?? 0,
    };

    return {
      id: device.hostname,
      type: 'device',
      position: { x, y },
      data: nodeData,
      zIndex: 10,
    };
  });

  return [...zoneNodes, ...deviceNodes];
}

function buildEdges(topology: TopologyData): Edge[] {
  return topology.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'smoothstep',
    style: { stroke: '#475569', strokeWidth: 1.5 },
    animated: false,
  }));
}

// ---------------------------------------------------------------------------
// NetworkCanvas
// ---------------------------------------------------------------------------

interface NetworkCanvasProps {
  topology: TopologyData;
  problems: NetworkProblem[];
  onDeviceSelect: (device: NetworkDevice | null) => void;
}

export const NetworkCanvas = memo(function NetworkCanvas({
  topology,
  problems,
  onDeviceSelect,
}: NetworkCanvasProps) {
  const initialNodes = useMemo(() => buildNodes(topology, problems), [topology, problems]);
  const initialEdges = useMemo(() => buildEdges(topology), [topology]);

  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      if (node.type !== 'device') return;
      const data = node.data as DeviceNodeData;
      onDeviceSelect(data.device);
    },
    [onDeviceSelect],
  );

  const onPaneClick = useCallback(() => {
    onDeviceSelect(null);
  }, [onDeviceSelect]);

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      fitView
      fitViewOptions={{ padding: 0.15 }}
      minZoom={0.25}
      maxZoom={2}
      className="bg-slate-950"
    >
      <Background variant={BackgroundVariant.Dots} color="#1e293b" gap={20} size={1} />
      <Controls className="!bg-slate-800 !border-slate-700 !shadow-none" />
      <MiniMap
        className="!bg-slate-900 !border-slate-700"
        nodeColor={(n) => {
          if (n.type === 'zone') return '#1e293b';
          const d = n.data as DeviceNodeData;
          const hasProblems = (d?.problemCount ?? 0) > 0;
          return hasProblems ? '#ef4444' : '#3b82f6';
        }}
        maskColor="rgba(15,23,42,0.6)"
      />
    </ReactFlow>
  );
});
