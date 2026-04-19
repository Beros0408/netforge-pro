import { memo } from 'react';
import { Handle, NodeProps, Position } from 'reactflow';
import type { DeviceNodeData, InterfaceStatus, Vendor } from '../../types/network';

// ---------------------------------------------------------------------------
// Vendor SVG icons (inline, no image imports)
// ---------------------------------------------------------------------------

function VendorIcon({ vendor }: { vendor: Vendor }) {
  const cls = 'w-5 h-5';
  switch (vendor) {
    case 'cisco':
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="currentColor">
          <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10 10-4.5 10-10S17.5 2 12 2zm0 3c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm5 8H7v-2h10v2zm-2 4H9v-2h6v2z" />
        </svg>
      );
    case 'fortinet':
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="currentColor">
          <path d="M12 1L3 5v6c0 5.5 3.8 10.7 9 12 5.2-1.3 9-6.5 9-12V5L12 1zm0 4l6 2.7V11c0 3.8-2.6 7.4-6 8.8-3.4-1.4-6-5-6-8.8V7.7L12 5z" />
        </svg>
      );
    case 'huawei':
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="currentColor">
          <path d="M12 2a10 10 0 100 20A10 10 0 0012 2zm-1 5h2v8h-2V7zm-3 2h2v6H8V9zm6 0h2v6h-2V9z" />
        </svg>
      );
    case 'arista':
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="currentColor">
          <rect x="3" y="6" width="18" height="12" rx="2" />
          <rect x="5" y="9" width="2" height="6" rx="1" className="fill-slate-900" />
          <rect x="9" y="9" width="2" height="6" rx="1" className="fill-slate-900" />
          <rect x="13" y="9" width="2" height="6" rx="1" className="fill-slate-900" />
          <rect x="17" y="9" width="2" height="6" rx="1" className="fill-slate-900" />
        </svg>
      );
    default:
      return (
        <svg viewBox="0 0 24 24" className={cls} fill="currentColor">
          <rect x="2" y="6" width="20" height="12" rx="3" />
          <circle cx="6" cy="12" r="1.5" className="fill-slate-900" />
          <circle cx="10" cy="12" r="1.5" className="fill-slate-900" />
        </svg>
      );
  }
}

// ---------------------------------------------------------------------------
// Status LED
// ---------------------------------------------------------------------------

const STATUS_COLORS: Record<string, string> = {
  up: 'bg-green-400 shadow-green-400',
  down: 'bg-red-400 shadow-red-400',
  admin_down: 'bg-slate-500',
  unknown: 'bg-yellow-400 shadow-yellow-400',
};

const VENDOR_COLORS: Record<Vendor, string> = {
  cisco: 'text-blue-400',
  fortinet: 'text-red-400',
  huawei: 'text-red-500',
  arista: 'text-emerald-400',
  unknown: 'text-slate-400',
};

function portStatusSummary(interfaces: Array<{ status: InterfaceStatus; admin_status?: boolean }>) {
  const up = interfaces.filter((i) => i.status === 'up').length;
  const down = interfaces.filter((i) => i.status === 'down' && i.admin_status !== false).length;
  return { up, down, total: interfaces.length };
}

// ---------------------------------------------------------------------------
// DeviceNode
// ---------------------------------------------------------------------------

export const DeviceNode = memo(function DeviceNode({ data, selected }: NodeProps<DeviceNodeData>) {
  const { device, problemCount } = data;
  const { up, down, total } = portStatusSummary(device.interfaces);
  const overallStatus = down > 0 ? 'down' : up > 0 ? 'up' : 'unknown';

  return (
    <>
      <Handle type="target" position={Position.Left} className="!w-2 !h-2 !bg-slate-500 !border-slate-600" />

      <div
        className={`
          min-w-[160px] bg-slate-800 border rounded-xl p-3 cursor-pointer
          transition-all duration-150
          ${selected ? 'border-blue-400 shadow-lg shadow-blue-400/20' : 'border-slate-700 hover:border-slate-500'}
        `}
      >
        {/* Header row: vendor icon + LED */}
        <div className="flex items-center justify-between mb-2">
          <div className={`${VENDOR_COLORS[device.vendor] ?? 'text-slate-400'}`}>
            <VendorIcon vendor={device.vendor} />
          </div>
          <div
            className={`w-2.5 h-2.5 rounded-full shadow-md ${STATUS_COLORS[overallStatus] ?? 'bg-slate-500'}`}
          />
        </div>

        {/* Hostname */}
        <div className="font-mono text-sm font-semibold text-white truncate max-w-[148px]">
          {device.hostname}
        </div>

        {/* Model / vendor */}
        <div className="text-xs text-slate-400 capitalize mt-0.5 truncate">
          {device.vendor}{device.model ? ` · ${device.model}` : ''}
        </div>

        {/* Port summary + problems */}
        <div className="flex items-center gap-2 mt-2">
          <span className="text-xs text-slate-500">
            <span className="text-green-400 font-medium">{up}</span>
            <span className="text-slate-600">/</span>
            <span className="text-slate-400">{total}</span>
            {' '}ports up
          </span>
          {problemCount > 0 && (
            <span className="flex items-center gap-0.5 text-xs bg-red-500/20 text-red-400 border border-red-500/30 px-1.5 rounded-full">
              ⚠ {problemCount}
            </span>
          )}
        </div>

        {/* Management IP */}
        {device.management_ip && (
          <div className="mt-1 text-xs font-mono text-slate-500 truncate">{device.management_ip}</div>
        )}
      </div>

      <Handle type="source" position={Position.Right} className="!w-2 !h-2 !bg-slate-500 !border-slate-600" />
    </>
  );
});
