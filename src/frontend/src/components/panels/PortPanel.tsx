import { X } from 'lucide-react';
import type { NetworkDevice, NetworkInterface, InterfaceStatus } from '../../types/network';

// ---------------------------------------------------------------------------
// Status LED
// ---------------------------------------------------------------------------

const LED_CLASSES: Record<InterfaceStatus, string> = {
  up: 'bg-green-400 shadow-sm shadow-green-400',
  down: 'bg-red-400 shadow-sm shadow-red-400',
  admin_down: 'bg-slate-500',
  unknown: 'bg-yellow-400 shadow-sm shadow-yellow-400',
};

const STATUS_LABELS: Record<InterfaceStatus, string> = {
  up: 'UP',
  down: 'DOWN',
  admin_down: 'ADM↓',
  unknown: '?',
};

const STATUS_TEXT: Record<InterfaceStatus, string> = {
  up: 'text-green-400',
  down: 'text-red-400',
  admin_down: 'text-slate-500',
  unknown: 'text-yellow-400',
};

function InterfaceRow({ iface }: { iface: NetworkInterface }) {
  const status: InterfaceStatus = iface.status ?? 'unknown';

  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-slate-800/60 transition-colors">
      <div className={`w-2 h-2 rounded-full shrink-0 ${LED_CLASSES[status]}`} />
      <div className="flex-1 min-w-0">
        <div className="font-mono text-xs text-white truncate">{iface.name}</div>
        {iface.ip_address && (
          <div className="font-mono text-[10px] text-slate-500 truncate">{iface.ip_address}</div>
        )}
        {iface.description && (
          <div className="text-[10px] text-slate-500 truncate italic">{iface.description}</div>
        )}
      </div>
      <div className="flex flex-col items-end gap-0.5 shrink-0">
        <span className={`text-[10px] font-semibold ${STATUS_TEXT[status]}`}>
          {STATUS_LABELS[status]}
        </span>
        {iface.speed && (
          <span className="text-[10px] text-slate-600">{iface.speed}</span>
        )}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// PortPanel
// ---------------------------------------------------------------------------

interface PortPanelProps {
  device: NetworkDevice | null;
  onClose: () => void;
}

export function PortPanel({ device, onClose }: PortPanelProps) {
  if (!device) return null;

  const upCount = device.interfaces.filter((i) => i.status === 'up').length;
  const downCount = device.interfaces.filter(
    (i) => i.status === 'down' && i.admin_status !== false,
  ).length;
  const adminDownCount = device.interfaces.filter((i) => i.status === 'admin_down' || i.admin_status === false).length;

  return (
    <aside className="flex flex-col w-72 bg-slate-900 border-l border-slate-800 shrink-0 overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-800">
        <div className="min-w-0">
          <div className="font-mono text-sm font-semibold text-white truncate">{device.hostname}</div>
          <div className="text-xs text-slate-400 capitalize mt-0.5">
            {device.vendor}{device.model ? ` · ${device.model}` : ''}
          </div>
        </div>
        <button
          onClick={onClose}
          className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-white transition-colors shrink-0"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Port summary */}
      <div className="flex items-center gap-3 px-4 py-2 border-b border-slate-800 bg-slate-800/40">
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-green-400" />
          <span className="text-xs text-slate-300">{upCount} up</span>
        </div>
        <div className="flex items-center gap-1.5">
          <div className="w-2 h-2 rounded-full bg-red-400" />
          <span className="text-xs text-slate-300">{downCount} down</span>
        </div>
        {adminDownCount > 0 && (
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-slate-500" />
            <span className="text-xs text-slate-300">{adminDownCount} adm↓</span>
          </div>
        )}
        {device.management_ip && (
          <span className="ml-auto font-mono text-[10px] text-slate-500">{device.management_ip}</span>
        )}
      </div>

      {/* Interface list */}
      <div className="flex-1 overflow-y-auto p-2 space-y-0.5">
        {device.interfaces.length === 0 ? (
          <div className="text-xs text-slate-500 text-center py-8">Aucune interface</div>
        ) : (
          device.interfaces.map((iface) => (
            <InterfaceRow key={iface.name} iface={iface} />
          ))
        )}
      </div>
    </aside>
  );
}
