import { useState } from 'react';
import type { NetworkDevice, TopologyData, ZoneType } from '../../types/network';

// ---------------------------------------------------------------------------
// Zone icon + colour
// ---------------------------------------------------------------------------

const ZONE_ICON: Record<ZoneType, string> = {
  wan:    '📡',
  dmz:    '🛡',
  lan:    '🖧',
  mgmt:   '🔧',
  server: '🖥',
  core:   '⬡',
};

const ZONE_COLOR: Record<ZoneType, string> = {
  wan:    '#7C3AED',
  dmz:    '#DC2626',
  lan:    '#2563EB',
  mgmt:   '#059669',
  server: '#D97706',
  core:   '#475569',
};

function statusDot(device: NetworkDevice) {
  const hasDown = device.interfaces.some((i) => i.status === 'down' && i.admin_status !== false);
  return (
    <span style={{
      display: 'inline-block', width: 6, height: 6, borderRadius: '50%',
      background: hasDown ? '#EF4444' : '#22C55E', flexShrink: 0,
      boxShadow: hasDown ? '0 0 4px #EF4444' : '0 0 4px #22C55E',
    }} />
  );
}

// ---------------------------------------------------------------------------
// OutlinePanel
// ---------------------------------------------------------------------------

interface OutlinePanelProps {
  topology:       TopologyData;
  selectedDevice: NetworkDevice | null;
  onSelectDevice: (d: NetworkDevice) => void;
  onFitToNode:    (hostname: string) => void;
}

export function OutlinePanel({
  topology, selectedDevice, onSelectDevice, onFitToNode,
}: OutlinePanelProps) {
  // Track which zones are expanded
  const [expandedZones, setExpandedZones] = useState<Record<string, boolean>>(
    Object.fromEntries(topology.zones.map((z) => [z.id, true])),
  );

  const toggleZone = (id: string) =>
    setExpandedZones((prev) => ({ ...prev, [id]: !prev[id] }));

  // Devices NOT in any zone
  const zoneDeviceNames = new Set(topology.zones.flatMap((z) => z.device_hostnames));
  const unzoned = topology.devices.filter((d) => !zoneDeviceNames.has(d.hostname));

  return (
    <div style={{
      display: 'flex', flexDirection: 'column', height: '100%',
      background: '#0A0E1A', borderLeft: '1px solid #1E293B', overflowY: 'auto',
    }}>
      {/* Header */}
      <div style={{ padding: '10px 12px 6px', borderBottom: '1px solid #1E293B', flexShrink: 0 }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: '#F8FAFC' }}>📋 Outline</div>
        <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>
          {topology.devices.length} équipements · {topology.edges.length} liens
        </div>
      </div>

      <div style={{ flex: 1, overflowY: 'auto', padding: '6px 0' }}>
        {/* Root → Topologie */}
        <div style={{ padding: '4px 10px 2px', fontSize: 10, color: '#64748B', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
          Topologie
        </div>

        {/* Zones with devices */}
        {topology.zones.map((zone) => {
          const devicesInZone = topology.devices.filter((d) => zone.device_hostnames.includes(d.hostname));
          const zoneColor = ZONE_COLOR[zone.zone_type];
          const isOpen = expandedZones[zone.id] !== false;

          return (
            <div key={zone.id}>
              {/* Zone row */}
              <button
                onClick={() => toggleZone(zone.id)}
                style={{
                  display: 'flex', alignItems: 'center', gap: 5, width: '100%',
                  padding: '4px 10px', background: 'transparent', border: 'none',
                  color: '#94A3B8', fontSize: 11, cursor: 'pointer', textAlign: 'left',
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#1E293B')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <span style={{ fontSize: 8, color: '#475569', transition: 'transform 0.15s', transform: isOpen ? 'rotate(90deg)' : 'none' }}>▶</span>
                <span style={{ fontSize: 13 }}>{ZONE_ICON[zone.zone_type]}</span>
                <span style={{ color: zoneColor, fontWeight: 600 }}>{zone.name}</span>
                <span style={{ marginLeft: 'auto', fontSize: 9, color: '#475569' }}>{devicesInZone.length}</span>
              </button>

              {/* Devices in zone */}
              {isOpen && devicesInZone.map((device, i) => {
                const isLast = i === devicesInZone.length - 1;
                const isSelected = selectedDevice?.hostname === device.hostname;
                return (
                  <button
                    key={device.hostname}
                    onClick={() => { onSelectDevice(device); onFitToNode(device.hostname); }}
                    style={{
                      display: 'flex', alignItems: 'center', gap: 6, width: '100%',
                      padding: '3px 10px 3px 24px', background: isSelected ? '#1D4ED820' : 'transparent',
                      border: 'none', cursor: 'pointer', textAlign: 'left',
                    }}
                    onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = '#1E293B'; }}
                    onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                  >
                    <span style={{ color: '#334155', fontSize: 10, fontFamily: 'monospace' }}>
                      {isLast ? '└' : '├'}
                    </span>
                    {statusDot(device)}
                    <span style={{ fontFamily: 'monospace', fontSize: 10, color: isSelected ? '#60A5FA' : '#94A3B8', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {device.hostname}
                    </span>
                  </button>
                );
              })}
            </div>
          );
        })}

        {/* Unzoned devices */}
        {unzoned.length > 0 && (
          <div>
            <div style={{ padding: '4px 10px 2px', fontSize: 10, color: '#475569', fontWeight: 700, letterSpacing: '0.08em', textTransform: 'uppercase' }}>
              Non classifiés
            </div>
            {unzoned.map((device) => {
              const isSelected = selectedDevice?.hostname === device.hostname;
              return (
                <button
                  key={device.hostname}
                  onClick={() => { onSelectDevice(device); onFitToNode(device.hostname); }}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 6, width: '100%',
                    padding: '3px 10px 3px 18px', background: isSelected ? '#1D4ED820' : 'transparent',
                    border: 'none', cursor: 'pointer', textAlign: 'left',
                  }}
                  onMouseEnter={(e) => { if (!isSelected) e.currentTarget.style.background = '#1E293B'; }}
                  onMouseLeave={(e) => { if (!isSelected) e.currentTarget.style.background = 'transparent'; }}
                >
                  {statusDot(device)}
                  <span style={{ fontFamily: 'monospace', fontSize: 10, color: isSelected ? '#60A5FA' : '#94A3B8', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {device.hostname}
                  </span>
                </button>
              );
            })}
          </div>
        )}

        {topology.devices.length === 0 && (
          <div style={{ padding: '20px 12px', textAlign: 'center', fontSize: 11, color: '#334155' }}>
            Aucun équipement
          </div>
        )}
      </div>
    </div>
  );
}
