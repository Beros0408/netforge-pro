import { memo, useState } from 'react';
import {
  EdgeLabelRenderer,
  EdgeProps,
  getBezierPath,
  getSmoothStepPath,
  getStraightPath,
} from 'reactflow';
import type { CableType } from '../../types/network';

// ---------------------------------------------------------------------------
// Cable styles
// ---------------------------------------------------------------------------

interface CableStyle {
  stroke: string;
  strokeWidth: number;
  strokeDasharray?: string;
}

function getCableStyle(cableType: CableType | undefined, speed?: number): CableStyle {
  // Infer from speed if cable_type not set
  if (!cableType || cableType === 'unknown') {
    if (!speed) return { stroke: '#475569', strokeWidth: 1.5 };
    if (speed >= 100000) cableType = 'fiber_100g';
    else if (speed >= 10000) cableType = 'fiber_10g';
    else if (speed >= 1000)  cableType = 'fiber_1g';
    else                     cableType = 'copper';
  }

  switch (cableType) {
    case 'copper':      return { stroke: '#92400E', strokeWidth: 2, strokeDasharray: '8 4' };
    case 'fiber_1g':    return { stroke: '#22C55E', strokeWidth: 2 };
    case 'fiber_10g':   return { stroke: '#16A34A', strokeWidth: 3 };
    case 'fiber_100g':  return { stroke: '#15803D', strokeWidth: 4 };
    case 'stack':       return { stroke: '#F59E0B', strokeWidth: 4 };
    default:            return { stroke: '#475569', strokeWidth: 1.5 };
  }
}

const CABLE_LABEL: Record<CableType, string> = {
  copper:     'Cuivre RJ45',
  fiber_1g:   'Fibre 1G',
  fiber_10g:  'Fibre 10G',
  fiber_100g: 'Fibre 100G',
  stack:      'StackWise',
  unknown:    'Inconnu',
};

// ---------------------------------------------------------------------------
// Port label pill
// ---------------------------------------------------------------------------

function PortLabel({ x, y, label }: { x: number; y: number; label: string }) {
  return (
    <div
      style={{
        position: 'absolute',
        transform: `translate(-50%, -50%) translate(${x}px,${y}px)`,
        background: '#0F172A',
        border: '1px solid #334155',
        borderRadius: 3,
        padding: '2px 5px',
        fontFamily: 'JetBrains Mono, monospace',
        fontSize: 9,
        color: '#94A3B8',
        whiteSpace: 'nowrap',
        pointerEvents: 'none',
        userSelect: 'none',
      }}
    >
      {label}
    </div>
  );
}

// ---------------------------------------------------------------------------
// EdgeWithPorts
// ---------------------------------------------------------------------------

export interface EdgeWithPortsData {
  sourcePort?: string;
  targetPort?: string;
  cableType?: CableType;
  speed?: number;
  edgeVariant?: 'bezier' | 'smoothstep' | 'straight';
}

function lerp(a: number, b: number, t: number) {
  return a + (b - a) * t;
}

export const EdgeWithPorts = memo(function EdgeWithPorts({
  id,
  sourceX, sourceY,
  targetX, targetY,
  sourcePosition, targetPosition,
  data,
  selected,
}: EdgeProps<EdgeWithPortsData>) {
  const [hovered, setHovered] = useState(false);
  const variant = data?.edgeVariant ?? 'smoothstep';
  const cableStyle = getCableStyle(data?.cableType, data?.speed);

  let edgePath = '';
  let labelX = 0;
  let labelY = 0;

  if (variant === 'straight') {
    [edgePath, labelX, labelY] = getStraightPath({ sourceX, sourceY, targetX, targetY });
  } else if (variant === 'bezier') {
    [edgePath, labelX, labelY] = getBezierPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  } else {
    [edgePath, labelX, labelY] = getSmoothStepPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition, borderRadius: 8 });
  }

  // 15% and 85% positions (linear — close enough for port labels)
  const x15 = lerp(sourceX, targetX, 0.15);
  const y15 = lerp(sourceY, targetY, 0.15);
  const x85 = lerp(sourceX, targetX, 0.85);
  const y85 = lerp(sourceY, targetY, 0.85);

  const isStack = data?.cableType === 'stack';
  const strokeColor = selected || hovered ? '#60A5FA' : cableStyle.stroke;

  return (
    <>
      {/* Invisible wide path for easier hover */}
      <path
        d={edgePath}
        fill="none"
        stroke="transparent"
        strokeWidth={16}
        style={{ cursor: 'pointer' }}
        onMouseEnter={() => setHovered(true)}
        onMouseLeave={() => setHovered(false)}
      />
      {/* Visible edge */}
      <path
        id={id}
        d={edgePath}
        fill="none"
        stroke={strokeColor}
        strokeWidth={cableStyle.strokeWidth}
        strokeDasharray={cableStyle.strokeDasharray}
        strokeLinecap="round"
        style={{ transition: 'stroke 0.2s' }}
      />

      <EdgeLabelRenderer>
        {/* Source port label */}
        {data?.sourcePort && (
          <PortLabel x={x15} y={y15} label={data.sourcePort} />
        )}

        {/* Target port label */}
        {data?.targetPort && (
          <PortLabel x={x85} y={y85} label={data.targetPort} />
        )}

        {/* STACK badge */}
        {isStack && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
              background: '#F59E0B',
              borderRadius: 4,
              padding: '1px 6px',
              fontSize: 9,
              fontWeight: 700,
              color: '#0F172A',
              pointerEvents: 'none',
            }}
          >
            STACK
          </div>
        )}

        {/* Tooltip on hover */}
        {hovered && (data?.cableType || data?.speed) && (
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -100%) translate(${labelX}px,${labelY - 8}px)`,
              background: '#1E293B',
              border: '1px solid #475569',
              borderRadius: 6,
              padding: '5px 8px',
              fontSize: 10,
              color: '#CBD5E1',
              fontFamily: 'monospace',
              pointerEvents: 'none',
              whiteSpace: 'nowrap',
              zIndex: 9999,
            }}
          >
            <div>{data.cableType ? CABLE_LABEL[data.cableType] : '—'}</div>
            {data.speed && <div style={{ color: '#64748B' }}>{data.speed >= 1000 ? `${data.speed / 1000}G` : `${data.speed}M`}</div>}
          </div>
        )}
      </EdgeLabelRenderer>
    </>
  );
});
