import { useState } from 'react';
import { useNetworkData } from '../../hooks/useNetworkData';
import { useProblems } from '../../hooks/useProblems';
import { Header } from '../shared/Header';
import { NetworkCanvas } from '../canvas/NetworkCanvas';
import type { DeviceNodeData } from '../canvas/DeviceNode';

export function Dashboard() {
  const { devices, loading, demoMode, lastUpdated, refresh } = useNetworkData();
  const { problems, loading: probLoading, refresh: refreshProblems } = useProblems(devices);
  const [selectedDevice, setSelectedDevice] = useState<DeviceNodeData | null>(null);

  const handleRefresh = () => {
    refresh();
    refreshProblems();
  };

  return (
    <div className="flex flex-col h-full">
      <Header
        deviceCount={devices.length}
        problems={problems}
        demoMode={demoMode}
        lastUpdated={lastUpdated}
        onRefresh={handleRefresh}
        loading={loading || probLoading}
      />

      <div className="flex flex-1 min-h-0">
        <div className="flex-1 relative min-w-0">
          {!loading ? (
            <NetworkCanvas onDeviceSelect={setSelectedDevice} />
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              Chargement…
            </div>
          )}
        </div>

        {selectedDevice && (
          <div style={{ width: 200, background: '#0f1729', borderLeft: '1px solid #1e2d45', padding: 12 }}>
            <div style={{ fontSize: 12, color: '#e8edf5', fontWeight: 600, marginBottom: 4 }}>
              {selectedDevice.hostname}
            </div>
            <div style={{ fontSize: 10, color: '#4a6080' }}>{selectedDevice.model}</div>
            {selectedDevice.managementIp && (
              <div style={{ fontSize: 10, color: '#4a6080', fontFamily: 'monospace', marginTop: 2 }}>
                {selectedDevice.managementIp}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
