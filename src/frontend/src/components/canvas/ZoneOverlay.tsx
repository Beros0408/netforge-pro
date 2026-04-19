import { memo } from 'react';
import type { NodeProps } from 'reactflow';
import type { ZoneNodeData, ZoneType } from '../../types/network';

// ---------------------------------------------------------------------------
// Zone colour palette
// ---------------------------------------------------------------------------

interface ZonePalette {
  bg: string;
  border: string;
  text: string;
  label: string;
}

const ZONE_PALETTES: Record<ZoneType, ZonePalette> = {
  wan: {
    bg: 'rgba(124, 58, 237, 0.08)',
    border: '#7c3aed',
    text: '#a78bfa',
    label: 'WAN',
  },
  dmz: {
    bg: 'rgba(220, 38, 38, 0.08)',
    border: '#dc2626',
    text: '#fca5a5',
    label: 'DMZ',
  },
  lan: {
    bg: 'rgba(37, 99, 235, 0.08)',
    border: '#2563eb',
    text: '#93c5fd',
    label: 'LAN',
  },
  mgmt: {
    bg: 'rgba(5, 150, 105, 0.08)',
    border: '#059669',
    text: '#6ee7b7',
    label: 'MGMT',
  },
  server: {
    bg: 'rgba(217, 119, 6, 0.08)',
    border: '#d97706',
    text: '#fcd34d',
    label: 'SERVERS',
  },
  core: {
    bg: 'rgba(71, 85, 105, 0.12)',
    border: '#475569',
    text: '#94a3b8',
    label: 'CORE',
  },
};

// ---------------------------------------------------------------------------
// ZoneOverlay — rendered as a ReactFlow node with selectable: false
// ---------------------------------------------------------------------------

export const ZoneOverlay = memo(function ZoneOverlay({ data }: NodeProps<ZoneNodeData>) {
  const palette = ZONE_PALETTES[data.zoneType] ?? ZONE_PALETTES.lan;

  return (
    <div
      style={{
        width: data.width,
        height: data.height,
        backgroundColor: palette.bg,
        border: `2px dashed ${palette.border}`,
        borderRadius: '16px',
        position: 'relative',
        pointerEvents: 'none',
        userSelect: 'none',
      }}
    >
      {/* Zone label — top-left corner */}
      <div
        style={{
          position: 'absolute',
          top: 8,
          left: 12,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
        }}
      >
        <div
          style={{
            width: 6,
            height: 6,
            borderRadius: '50%',
            backgroundColor: palette.border,
          }}
        />
        <span
          style={{
            fontSize: 10,
            fontWeight: 700,
            color: palette.text,
            letterSpacing: '0.12em',
            fontFamily: 'Inter, system-ui, sans-serif',
          }}
        >
          {data.label}
        </span>
      </div>
    </div>
  );
});
