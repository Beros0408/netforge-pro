/**
 * DeviceNode.tsx — NetForge Pro
 * Nœud custom React-Flow : icône isométrique, PortPanel, CLI double-clic
 * Refs: CDC Enrichissements v4 §1.3-1.5
 */
import React, { memo, useCallback, useState } from 'react';
import { Handle, NodeProps, Position } from 'reactflow';
import { DeviceIcon } from './DeviceIcons';
import type { DeviceIconType } from './DeviceIcons';
import { PortPanel } from './PortPanel';

// ─── Types ────────────────────────────────────────────────────────────────────

export type VendorType   = 'cisco' | 'fortinet' | 'huawei' | 'arista';
export type DeviceStatus = 'up' | 'down' | 'warning' | 'unknown';

export interface DevicePort {
  id:              string;
  name:            string;
  normalizedName:  string;
  speed:           '100M' | '1G' | '10G' | '25G' | '40G' | '100G';
  status:          'up' | 'down' | 'err-disabled' | 'admin-down';
  mode?:           'access' | 'trunk' | 'routed';
  accessVlan?:     number;
  trunkVlans?:     number[];
  ipv4?:           string;
  neighborDevice?: string;
  neighborPort?:   string;
  description?:    string;
  utilization?:    number;
  errors?:         { crc?: number; collisions?: number; drops?: number };
}

export interface DeviceNodeData {
  hostname:      string;
  vendor:        VendorType;
  iconType:      DeviceIconType;
  model:         string;
  osVersion?:    string;
  managementIp?: string;
  zone?:         string;
  status:        DeviceStatus;
  ports:         DevicePort[];
  onOpenCLI?:    (data: DeviceNodeData) => void;
}

// ─── Static constants ─────────────────────────────────────────────────────────

const HANDLE: React.CSSProperties = {
  width: 8,
  height: 8,
  background: '#2a3f5f',
  border: '1.5px solid #3d5a80',
  borderRadius: '50%',
};

const VENDOR_BADGE: Record<VendorType, { bg: string; color: string; label: string }> = {
  cisco:    { bg: '#172a3a', color: '#40a9c9', label: 'Cisco' },
  fortinet: { bg: '#3a1010', color: '#ef8080', label: 'Fortinet' },
  huawei:   { bg: '#2a1010', color: '#dc6060', label: 'Huawei' },
  arista:   { bg: '#1e1e1e', color: '#8ba3c7', label: 'Arista' },
};

const STATUS_LED: Record<DeviceStatus, { color: string; pulse: boolean }> = {
  up:      { color: '#10b981', pulse: true  },
  down:    { color: '#ef4444', pulse: false },
  warning: { color: '#f59e0b', pulse: false },
  unknown: { color: '#6b7280', pulse: false },
};

// ─── CSS animation (injected once, inline-styles constraint) ─────────────────

let _animInjected = false;
function ensurePulseAnim(): void {
  if (_animInjected || typeof document === 'undefined') return;
  _animInjected = true;
  const el = document.createElement('style');
  el.textContent =
    '@keyframes nf-led-pulse{' +
    '0%,100%{opacity:1;transform:scale(1)}' +
    '50%{opacity:.5;transform:scale(1.4)}' +
    '}';
  document.head.appendChild(el);
}

// ─── DeviceNode ───────────────────────────────────────────────────────────────

export const DeviceNode = memo(function DeviceNode({
  data,
  selected,
}: NodeProps<DeviceNodeData>) {
  ensurePulseAnim();

  const [hovered,  setHovered]  = useState(false);
  const [showPort, setShowPort] = useState(false);

  const { hostname, vendor, iconType, model, status, ports } = data;

  const badge = VENDOR_BADGE[vendor] ?? VENDOR_BADGE.cisco;
  const led   = STATUS_LED[status]   ?? STATUS_LED.unknown;

  const upCount   = ports.filter((p) => p.status === 'up').length;
  const downCount = ports.filter((p) => p.status !== 'up').length;

  // ─── Handlers ───────────────────────────────────────────────────────────────

  const handleMouseEnter = useCallback(() => setHovered(true),  []);
  const handleMouseLeave = useCallback(() => setHovered(false), []);

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    setShowPort((v) => !v);
  }, []);

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    data.onOpenCLI?.(data);
  }, [data]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'Enter') setShowPort((v) => !v);
  }, []);

  const handleClosePort = useCallback(() => setShowPort(false), []);

  // ─── Derived styles ─────────────────────────────────────────────────────────

  const borderColor: string = selected
    ? '#049fd9'
    : hovered
    ? '#3d5a80'
    : '#1e2d45';

  const boxShadow: string = selected
    ? '0 0 0 2px #049fd9, 0 0 20px #049fd940'
    : hovered
    ? '0 6px 28px rgba(0,0,0,0.6)'
    : '0 2px 10px rgba(0,0,0,0.35)';

  // ─── Render ─────────────────────────────────────────────────────────────────

  return (
    <div
      style={{ position: 'relative' }}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
    >
      {/* ── React-Flow Handles ────────────────────────────────────────────── */}
      <Handle type="target" position={Position.Top}    style={HANDLE} />
      <Handle type="source" position={Position.Right}  style={HANDLE} />
      <Handle type="source" position={Position.Bottom} style={HANDLE} />
      <Handle type="target" position={Position.Left}   style={HANDLE} />

      {/* ── Main card ─────────────────────────────────────────────────────── */}
      <div
        role="button"
        tabIndex={0}
        aria-label={`Équipement ${hostname} — statut ${status}`}
        onClick={handleClick}
        onDoubleClick={handleDoubleClick}
        onKeyDown={handleKeyDown}
        style={{
          position: 'relative',
          width: 120,
          background: '#0f1729',
          border: `1.5px solid ${borderColor}`,
          borderRadius: 10,
          padding: '10px 10px 8px',
          cursor: 'pointer',
          outline: 'none',
          userSelect: 'none',
          transition: 'border-color 0.15s ease, box-shadow 0.15s ease',
          boxShadow,
        }}
      >
        {/* Status LED — top-right */}
        <div
          aria-hidden="true"
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: led.color,
            boxShadow: `0 0 6px ${led.color}`,
            animation: led.pulse ? 'nf-led-pulse 2s ease-in-out infinite' : 'none',
          }}
        />

        {/* Device icon (isometric 3D) */}
        <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 4 }}>
          <DeviceIcon type={iconType} size={100} />
        </div>

        {/* Port counters ↑up  ↓down */}
        {ports.length > 0 && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: 8,
            marginTop: 2,
          }}>
            {upCount > 0 && (
              <span style={{
                fontSize: 10,
                fontFamily: '"JetBrains Mono", monospace',
                fontWeight: 700,
                color: '#10b981',
              }}>
                {`↑${upCount}`}
              </span>
            )}
            {downCount > 0 && (
              <span style={{
                fontSize: 10,
                fontFamily: '"JetBrains Mono", monospace',
                fontWeight: 700,
                color: '#ef4444',
              }}>
                {`↓${downCount}`}
              </span>
            )}
          </div>
        )}
      </div>

      {/* ── Label block (below card) ───────────────────────────────────────── */}
      <div style={{
        textAlign: 'center',
        marginTop: 5,
        maxWidth: 120,
        overflow: 'hidden',
      }}>
        {/* Hostname */}
        <div style={{
          fontSize: 11,
          fontFamily: '"JetBrains Mono", monospace',
          fontWeight: 700,
          color: '#e8edf5',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}>
          {hostname}
        </div>

        {/* Vendor · Model badge */}
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 3,
          marginTop: 3,
          background: badge.bg,
          borderRadius: 4,
          padding: '1px 6px',
          maxWidth: '100%',
          overflow: 'hidden',
        }}>
          <span style={{
            fontSize: 9,
            color: badge.color,
            fontWeight: 700,
            whiteSpace: 'nowrap',
          }}>
            {badge.label}
          </span>
          {model && (
            <>
              <span style={{ fontSize: 9, color: '#4a6080' }}>·</span>
              <span style={{
                fontSize: 9,
                color: '#8ba3c7',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                maxWidth: 60,
              }}>
                {model}
              </span>
            </>
          )}
        </div>
      </div>

      {/* ── PortPanel overlay (clic simple) ───────────────────────────────── */}
      {showPort && (
        <PortPanel
          hostname={hostname}
          ports={ports}
          onClose={handleClosePort}
        />
      )}
    </div>
  );
});

DeviceNode.displayName = 'DeviceNode';

export default DeviceNode;
