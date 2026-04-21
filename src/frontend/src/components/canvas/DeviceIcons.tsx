/**
 * DeviceIcons.tsx — NetForge Pro
 * Icônes isométriques 3D constructeur-spécifiques
 * Refs: CDC §8, catalyst_9200.md, catalyst_9300.md, Enrichissements v4 §1
 */
import React, { memo } from 'react';

// ─── Type union ───────────────────────────────────────────────────────────────
export type DeviceIconType =
  | 'cisco_catalyst_9200'
  | 'cisco_catalyst_9300'
  | 'cisco_nexus_9300'
  | 'cisco_nexus_9500'
  | 'cisco_isr_4431'
  | 'cisco_asa_5516'
  | 'cisco_wlc_9800'
  | 'cisco_ap_9120'
  | 'fortinet_fg200f'
  | 'huawei_ce6880'
  | 'huawei_s5735'
  | 'arista_7050cx3';

// ─── Chassis palettes [front, top(+15%), right(×0.65)] ───────────────────────
const CISCO = ['#162233', '#394352', '#0e1621'] as const;
const FORT  = ['#1a1018', '#3c343b', '#110a10'] as const;
const HUAW  = ['#161c24', '#393e45', '#0e1217'] as const;
const ARIS  = ['#0d1014', '#313437', '#080a0d'] as const;

// ─── SVG helpers ──────────────────────────────────────────────────────────────
/** Horizontal row of RJ45 port rects */
function rj45(
  x0: number, y: number, n: number,
  w = 2.5, gap = 1, upN?: number,
): React.ReactElement[] {
  return Array.from({ length: n }, (_, i) => (
    <rect
      key={`${y}-${x0}-${i}`}
      x={x0 + i * (w + gap)} y={y}
      width={w} height={w + 2} rx={0.4}
      fill={upN === undefined || i < upN ? '#4ade80' : '#374151'}
    />
  ));
}

/** Horizontal row of SFP/QSFP port rects (darker, bezel style) */
function sfp(
  x0: number, y: number, n: number,
  w = 5, gap = 2,
): React.ReactElement[] {
  return Array.from({ length: n }, (_, i) => (
    <rect
      key={`sfp-${y}-${x0}-${i}`}
      x={x0 + i * (w + gap)} y={y}
      width={w} height={w + 1} rx={0.5}
      fill="#060e1a" stroke="#1e4060" strokeWidth={0.5}
    />
  ));
}

// ─── Isometric chassis frame ──────────────────────────────────────────────────
// 1U: front rect (x=6,y=28,w=92,h=25), iso offset dx=dy=8
// Tall (Nexus 9500): front rect (x=6,y=20,w=92,h=44)
interface ChassisProps {
  front: string;
  top: string;
  right: string;
  accent: string;
  tall?: boolean;
  children?: React.ReactNode;
}
const Chassis: React.FC<ChassisProps> = ({ front, top, right, accent, tall = false, children }) => {
  const x = 6, dx = 8, dy = 8, w = 92;
  const y = tall ? 20 : 28;
  const h = tall ? 44 : 25;
  return (
    <>
      {/* Right face — shadow */}
      <polygon
        points={`${x+w},${y} ${x+w+dx},${y-dy} ${x+w+dx},${y+h-dy} ${x+w},${y+h}`}
        fill={right}
      />
      {/* Top face */}
      <polygon
        points={`${x},${y} ${x+dx},${y-dy} ${x+w+dx},${y-dy} ${x+w},${y}`}
        fill={top}
      />
      {/* Front face base */}
      <rect x={x} y={y} width={w} height={h} fill={front} />
      {/* Accent bar 2px */}
      <rect x={x} y={y} width={w} height={2} fill={accent} />
      {children}
      {/* Status LED — bottom-right of front face */}
      <circle cx={x + w - 4} cy={y + h - 4} r={1.5} fill="#4ade80" />
    </>
  );
};

// ─── 1. Cisco Catalyst 9200 ───────────────────────────────────────────────────
// 24×1G access + 4×SFP uplinks, StackWise-160  (ref: catalyst_9200.md)
export const CiscoCatalyst9200Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={CISCO[0]} top={CISCO[1]} right={CISCO[2]} accent="#40a9c9">
      {/* Row 1 — 12 RJ45 (ports 1–12) */}
      {rj45(9, 32, 12, 3, 1.5, 10)}
      {/* Row 2 — 12 RJ45 (ports 13–24) */}
      {rj45(9, 42, 12, 3, 1.5, 12)}
      {/* 4 SFP uplinks (2×2 grid) */}
      {sfp(85, 32, 2, 4, 1.5)}
      {sfp(85, 42, 2, 4, 1.5)}
      {/* StackWise-160 indicator */}
      <rect x={6} y={52} width={45} height={1} fill="#f59e0b" opacity={0.5} />
      <text x={9} y={51} fontSize={4} fill="#f59e0b" opacity={0.65} fontFamily="monospace">SW-160</text>
    </Chassis>
  </svg>
));
CiscoCatalyst9200Icon.displayName = 'CiscoCatalyst9200Icon';

// ─── 2. Cisco Catalyst 9300 ───────────────────────────────────────────────────
// 48×1G PoE+ access + 8×SFP+ uplinks, StackWise-480  (ref: catalyst_9300.md)
export const CiscoCatalyst9300Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={CISCO[0]} top={CISCO[1]} right={CISCO[2]} accent="#049fd9">
      {/* Row 1 — 24 RJ45 PoE+ */}
      {rj45(8, 32, 24, 2, 0.8, 20)}
      {/* Row 2 — 24 RJ45 PoE+ */}
      {rj45(8, 42, 24, 2, 0.8, 24)}
      {/* 8 SFP+ uplinks (2×4) */}
      {sfp(82, 32, 4, 3, 1)}
      {sfp(82, 42, 4, 3, 1)}
      <text x={9} y={51} fontSize={4} fill="#3b82f6" opacity={0.7} fontFamily="monospace">PoE+ · SW-480</text>
    </Chassis>
  </svg>
));
CiscoCatalyst9300Icon.displayName = 'CiscoCatalyst9300Icon';

// ─── 3. Cisco Nexus 9300 ─────────────────────────────────────────────────────
// 48×25G SFP28 + 6×100G QSFP28, NX-OS spine/leaf
export const CiscoNexus9300Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={CISCO[0]} top={CISCO[1]} right={CISCO[2]} accent="#f59e0b">
      {/* 48 SFP28 25G (24+24) — spine, all up */}
      {sfp(8, 31, 24, 2.5, 0.5)}
      {sfp(8, 41, 24, 2.5, 0.5)}
      {/* 6 QSFP28 100G (3+3) */}
      {sfp(83, 30, 3, 4, 1)}
      {sfp(83, 41, 3, 4, 1)}
      <text x={9} y={51} fontSize={4} fill="#f59e0b" opacity={0.7} fontFamily="monospace">NX-OS · 25G/100G</text>
    </Chassis>
  </svg>
));
CiscoNexus9300Icon.displayName = 'CiscoNexus9300Icon';

// ─── 4. Cisco Nexus 9500 ─────────────────────────────────────────────────────
// Chassis modulaire 5 linecards + supervisor, viewBox "0 0 120 78"
export const CiscoNexus9500Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 78 / 120)} viewBox="0 0 120 78">
    <Chassis front={CISCO[0]} top={CISCO[1]} right={CISCO[2]} accent="#f59e0b" tall>
      {/* Supervisor module slot (right column, full height) */}
      <rect x={84} y={22} width={13} height={40} rx={1} fill="#1e3040" stroke="#f59e0b" strokeWidth={0.5} />
      <text
        x={90} y={44} fontSize={4} fill="#f59e0b" fontFamily="monospace"
        textAnchor="middle" transform="rotate(-90 90 44)"
      >
        SUP
      </text>
      {/* 5 linecard bays */}
      {[0, 1, 2, 3, 4].map((lc) => {
        const ly = 22 + lc * 8;
        return (
          <g key={lc}>
            <rect x={7} y={ly} width={74} height={7.5} rx={0.5}
              fill="#1a2535" stroke="#2a3a55" strokeWidth={0.3} />
            {sfp(10, ly + 1.5, 14, 3.5, 0.8)}
            <text x={78} y={ly + 5} fontSize={3.5} fill="#4a6080" fontFamily="monospace">
              {`LC${lc}`}
            </text>
          </g>
        );
      })}
    </Chassis>
  </svg>
));
CiscoNexus9500Icon.displayName = 'CiscoNexus9500Icon';

// ─── 5. Cisco ISR 4431 ───────────────────────────────────────────────────────
// Router, 4 NIM WAN modules + management ports
export const CiscoISR4431Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={CISCO[0]} top={CISCO[1]} right={CISCO[2]} accent="#049fd9">
      {/* Left: console (gray) + GE mgmt (green) + 2 USB */}
      <rect x={8}  y={32} width={4} height={6} rx={0.5} fill="#374151" stroke="#4b5563" strokeWidth={0.3} />
      <rect x={13} y={32} width={4} height={6} rx={0.5} fill="#4ade80" />
      <rect x={18} y={34} width={3} height={4} rx={0.3} fill="#374151" />
      <rect x={22} y={34} width={3} height={4} rx={0.3} fill="#374151" />
      {/* 4 NIM/SM WAN module bays */}
      {[0, 1, 2, 3].map((m) => (
        <g key={m}>
          <rect x={30 + m * 14} y={30} width={12} height={12} rx={1}
            fill="#1e3040" stroke="#3d5a80" strokeWidth={0.5} />
          {sfp(32 + m * 14, 33, 2, 3, 1.5)}
          <text x={36 + m * 14} y={43} fontSize={3.5} fill="#4a6080"
            fontFamily="monospace" textAnchor="middle">NIM</text>
        </g>
      ))}
      <text x={9} y={51} fontSize={4} fill="#049fd9" opacity={0.65} fontFamily="monospace">ISR4431 · IOS-XE</text>
    </Chassis>
  </svg>
));
CiscoISR4431Icon.displayName = 'CiscoISR4431Icon';

// ─── 6. Cisco ASA 5516 ───────────────────────────────────────────────────────
// NGFW, 3 zones visuellement séparées WAN / LAN / DMZ
export const CiscoASA5516Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={CISCO[0]} top={CISCO[1]} right={CISCO[2]} accent="#f59e0b">
      {/* Zone dividers */}
      <line x1={30} y1={30} x2={30} y2={52} stroke="#2a3a55" strokeWidth={0.5} />
      <line x1={70} y1={30} x2={70} y2={52} stroke="#2a3a55" strokeWidth={0.5} />
      {/* WAN zone (x=6–30) */}
      <text x={18} y={35} fontSize={4} fill="#ef4444" fontFamily="monospace" textAnchor="middle">WAN</text>
      {sfp(8, 38, 2, 5, 3)}
      {/* LAN zone (x=30–70) */}
      <text x={50} y={35} fontSize={4} fill="#4ade80" fontFamily="monospace" textAnchor="middle">LAN</text>
      {rj45(32, 39, 8, 3, 1, 7)}
      {/* DMZ zone (x=70–98) */}
      <text x={83} y={35} fontSize={4} fill="#f59e0b" fontFamily="monospace" textAnchor="middle">DMZ</text>
      {sfp(72, 38, 2, 5, 3)}
    </Chassis>
  </svg>
));
CiscoASA5516Icon.displayName = 'CiscoASA5516Icon';

// ─── 7. Cisco WLC 9800 ───────────────────────────────────────────────────────
// Wireless LAN Controller, arcs Wi-Fi sur face top isométrique
export const CiscoWLC9800Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={CISCO[0]} top={CISCO[1]} right={CISCO[2]} accent="#049fd9">
      {/* 8 GE management + uplink ports */}
      {rj45(9, 33, 8, 3, 1.5, 6)}
      {/* 2 SFP+ uplinks */}
      {sfp(50, 33, 2, 5, 2)}
      {/* Wi-Fi arcs on front face */}
      {[0, 1, 2].map((i) => (
        <path
          key={i}
          d={`M${70 + i * 2},${46 - i * 3} A${5 + i * 4},${3 + i * 1.5} 0 0 1 ${82 - i * 2},${46 - i * 3}`}
          fill="none" stroke="#049fd9" strokeWidth={0.9} opacity={0.7 - i * 0.15}
        />
      ))}
      {/* Wi-Fi arcs on isometric TOP face */}
      {[1, 2, 3].map((i) => (
        <ellipse key={i}
          cx={52} cy={22} rx={4 + i * 5} ry={1.5 + i * 1.2}
          fill="none" stroke="#049fd9" strokeWidth={0.6} opacity={0.45 - i * 0.08}
        />
      ))}
      <text x={9} y={50} fontSize={4} fill="#049fd9" opacity={0.65} fontFamily="monospace">WLC9800 · Wi-Fi 6</text>
    </Chassis>
  </svg>
));
CiscoWLC9800Icon.displayName = 'CiscoWLC9800Icon';

// ─── 8. Cisco AP 9120 ────────────────────────────────────────────────────────
// Access Point disque plat + bras montage + arcs signal, viewBox "0 0 120 78"
export const CiscoAP9120Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 78 / 120)} viewBox="0 0 120 78">
    {/* Mounting arm */}
    <rect x={56} y={56} width={8} height={15} rx={2} fill="#394352" />
    <rect x={38} y={69} width={44} height={4} rx={2} fill="#394352" />
    {/* AP disc — side profile (isometric ellipse) */}
    <ellipse cx={60} cy={44} rx={40} ry={14} fill="#1e3042" />
    {/* Disc top face */}
    <ellipse cx={60} cy={40} rx={40} ry={13} fill="#253d55" />
    {/* Accent ring */}
    <ellipse cx={60} cy={40} rx={40} ry={13} fill="none" stroke="#049fd9" strokeWidth={1.5} />
    {/* Wi-Fi signal arcs (concentric ellipses radiating out) */}
    {[1, 2, 3].map((i) => (
      <ellipse key={i}
        cx={60} cy={40}
        rx={10 + i * 10} ry={3.5 + i * 3.2}
        fill="none" stroke="#049fd9" strokeWidth={0.9}
        opacity={0.65 - i * 0.12}
      />
    ))}
    {/* Center LED */}
    <circle cx={60} cy={40} r={3.5} fill="#4ade80" />
    <circle cx={60} cy={40} r={1.8} fill="#a7f3d0" />
    {/* Lateral status LEDs */}
    <circle cx={92} cy={40} r={1.5} fill="#4ade80" />
    <circle cx={28} cy={40} r={1.5} fill="#4ade80" />
    {/* Label */}
    <text x={60} y={55} fontSize={4.5} fill="#049fd9"
      fontFamily="monospace" textAnchor="middle" opacity={0.8}>AP9120</text>
  </svg>
));
CiscoAP9120Icon.displayName = 'CiscoAP9120Icon';

// ─── 9. Fortinet FortiGate 200F ──────────────────────────────────────────────
// NGFW, 3 zones WAN / LAN+SFP / DMZ
export const FortinetFG200FIcon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={FORT[0]} top={FORT[1]} right={FORT[2]} accent="#ef4444">
      {/* Zone dividers */}
      <line x1={28} y1={30} x2={28} y2={52} stroke="#2a1018" strokeWidth={0.5} />
      <line x1={72} y1={30} x2={72} y2={52} stroke="#2a1018" strokeWidth={0.5} />
      {/* WAN zone (x=6–28) */}
      <text x={17} y={35} fontSize={4} fill="#ef4444" fontFamily="monospace" textAnchor="middle">WAN</text>
      {sfp(8, 38, 2, 5, 3)}
      {/* LAN zone (x=28–72) — 8 GE + 2 SFP+ */}
      <text x={50} y={35} fontSize={4} fill="#4ade80" fontFamily="monospace" textAnchor="middle">LAN</text>
      {rj45(30, 39, 8, 3, 1, 7)}
      {sfp(58, 38, 2, 4, 1.5)}
      {/* SFP/DMZ zone (x=72–98) */}
      <text x={84} y={35} fontSize={4} fill="#f59e0b" fontFamily="monospace" textAnchor="middle">SFP</text>
      {sfp(74, 38, 2, 5, 3)}
    </Chassis>
  </svg>
));
FortinetFG200FIcon.displayName = 'FortinetFG200FIcon';

// ─── 10. Huawei CloudEngine 6880 ─────────────────────────────────────────────
// DC Switch haute densité 48×10G SFP+ + 6×40G QSFP+
export const HuaweiCE6880Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={HUAW[0]} top={HUAW[1]} right={HUAW[2]} accent="#dc2626">
      {/* 48 SFP+ 10G (24+24) */}
      {sfp(8, 31, 24, 2.5, 0.5)}
      {sfp(8, 41, 24, 2.5, 0.5)}
      {/* 6 QSFP+ 40G (3+3) */}
      {sfp(83, 30, 3, 4, 1)}
      {sfp(83, 41, 3, 4, 1)}
      <text x={9} y={51} fontSize={4} fill="#dc2626" opacity={0.65} fontFamily="monospace">CE6880 · 10G/40G</text>
    </Chassis>
  </svg>
));
HuaweiCE6880Icon.displayName = 'HuaweiCE6880Icon';

// ─── 11. Huawei S5735 ────────────────────────────────────────────────────────
// Campus Access Switch 48×1G + 4×10G SFP+, VRP
export const HuaweiS5735Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={HUAW[0]} top={HUAW[1]} right={HUAW[2]} accent="#b91c1c">
      {/* Row 1 — 24 RJ45 GE */}
      {rj45(8, 32, 24, 2, 0.8, 22)}
      {/* Row 2 — 24 RJ45 GE */}
      {rj45(8, 42, 24, 2, 0.8, 23)}
      {/* 4 SFP+ 10G (2×2) */}
      {sfp(84, 32, 2, 4, 1.5)}
      {sfp(84, 42, 2, 4, 1.5)}
      <text x={9} y={51} fontSize={4} fill="#b91c1c" opacity={0.65} fontFamily="monospace">S5735 · VRP</text>
    </Chassis>
  </svg>
));
HuaweiS5735Icon.displayName = 'HuaweiS5735Icon';

// ─── 12. Arista 7050CX3 ──────────────────────────────────────────────────────
// Spine DC 32×100G QSFP28, chassis noir
export const Arista7050CX3Icon: React.FC<{ size?: number }> = memo(({ size = 120 }) => (
  <svg aria-hidden="true" width={size} height={Math.round(size * 65 / 120)} viewBox="0 0 120 65">
    <Chassis front={ARIS[0]} top={ARIS[1]} right={ARIS[2]} accent="#6b7280">
      {/* 32 QSFP28 100G (16+16) */}
      {sfp(8, 31, 16, 4, 0.8)}
      {sfp(8, 42, 16, 4, 0.8)}
      <text x={9} y={51} fontSize={4} fill="#9095a0" opacity={0.75} fontFamily="monospace">7050CX3 · 100G</text>
    </Chassis>
  </svg>
));
Arista7050CX3Icon.displayName = 'Arista7050CX3Icon';

// ─── Registry & exports ───────────────────────────────────────────────────────
export const ICON_REGISTRY: Record<DeviceIconType, React.FC<{ size?: number }>> = {
  cisco_catalyst_9200: CiscoCatalyst9200Icon,
  cisco_catalyst_9300: CiscoCatalyst9300Icon,
  cisco_nexus_9300:    CiscoNexus9300Icon,
  cisco_nexus_9500:    CiscoNexus9500Icon,
  cisco_isr_4431:      CiscoISR4431Icon,
  cisco_asa_5516:      CiscoASA5516Icon,
  cisco_wlc_9800:      CiscoWLC9800Icon,
  cisco_ap_9120:       CiscoAP9120Icon,
  fortinet_fg200f:     FortinetFG200FIcon,
  huawei_ce6880:       HuaweiCE6880Icon,
  huawei_s5735:        HuaweiS5735Icon,
  arista_7050cx3:      Arista7050CX3Icon,
};

export const DeviceIcon: React.FC<{ type: DeviceIconType; size?: number }> = memo(
  ({ type, size }) => {
    const Icon = ICON_REGISTRY[type];
    return <Icon size={size} />;
  },
);
DeviceIcon.displayName = 'DeviceIcon';

/** Backward-compat wrapper — maps generic device-type strings to specific icons */
export function getDeviceIcon(deviceType: string, size = 48): React.ReactElement {
  const t = deviceType.toLowerCase();
  if (t in ICON_REGISTRY) return <DeviceIcon type={t as DeviceIconType} size={size} />;
  if (t.includes('9200'))                       return <DeviceIcon type="cisco_catalyst_9200" size={size} />;
  if (t.includes('9300') && !t.includes('nexus')) return <DeviceIcon type="cisco_catalyst_9300" size={size} />;
  if (t.includes('nexus') || t.includes('9500')) return <DeviceIcon type="cisco_nexus_9300" size={size} />;
  if (t.includes('isr') || t.includes('router')) return <DeviceIcon type="cisco_isr_4431" size={size} />;
  if (t.includes('asa') || t.includes('firewall')) return <DeviceIcon type="cisco_asa_5516" size={size} />;
  if (t.includes('wlc'))                         return <DeviceIcon type="cisco_wlc_9800" size={size} />;
  if (t.includes('ap') || t.includes('access_point')) return <DeviceIcon type="cisco_ap_9120" size={size} />;
  if (t.includes('fortinet') || t.includes('forti')) return <DeviceIcon type="fortinet_fg200f" size={size} />;
  if (t.includes('ce') || t.includes('huawei'))  return <DeviceIcon type="huawei_ce6880" size={size} />;
  if (t.includes('arista'))                      return <DeviceIcon type="arista_7050cx3" size={size} />;
  return <DeviceIcon type="cisco_catalyst_9300" size={size} />;
}
