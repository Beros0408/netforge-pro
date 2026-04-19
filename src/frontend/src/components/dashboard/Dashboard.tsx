import { useState } from 'react';
import { useNetworkData } from '../../hooks/useNetworkData';
import { useProblems } from '../../hooks/useProblems';
import { Header } from '../shared/Header';
import { NetworkCanvas } from '../canvas/NetworkCanvas';
import { PortPanel } from '../panels/PortPanel';
import { ProblemsPanel } from '../panels/ProblemsPanel';
import type { NetworkDevice } from '../../types/network';

export function Dashboard() {
  const { topology, devices, loading, demoMode, lastUpdated, refresh } = useNetworkData();
  const { problems, securityScore, loading: probLoading, refresh: refreshProblems } = useProblems(devices);
  const [selectedDevice, setSelectedDevice] = useState<NetworkDevice | null>(null);

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
        {/* Canvas area */}
        <div className="flex-1 relative min-w-0">
          {topology ? (
            <NetworkCanvas
              topology={topology}
              problems={problems}
              onDeviceSelect={setSelectedDevice}
            />
          ) : loading ? (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              Chargement…
            </div>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              Aucune donnée de topologie
            </div>
          )}
        </div>

        {/* Right panels */}
        {selectedDevice && (
          <PortPanel device={selectedDevice} onClose={() => setSelectedDevice(null)} />
        )}
        <ProblemsPanel problems={problems} securityScore={securityScore} />
      </div>
    </div>
  );
}
