import {
  KeyboardEvent,
  useCallback,
  useEffect,
  useRef,
  useState,
} from 'react';
import { Minus, Settings, X } from 'lucide-react';
import type { CLIColors, CLILine, CLISession } from '../../hooks/useCLISessions';
import type { NetworkDevice } from '../../types/network';

// ---------------------------------------------------------------------------
// Command simulator
// ---------------------------------------------------------------------------

function showVersion(d: NetworkDevice): string[] {
  if (d.vendor === 'cisco') return [
    `Cisco IOS XE Software, Version ${d.os_version ?? '17.09.04'}`,
    'Copyright (c) 1986-2024 by Cisco Systems, Inc.',
    '',
    `Model             : ${d.model ?? 'Unknown'}`,
    `Hostname          : ${d.hostname}`,
    `System IP         : ${d.management_ip ?? 'N/A'}`,
    `Uptime            : 14 days, 3 hours, 22 minutes`,
    `ROM               : Bootstrap program is C9K Boot Loader`,
  ];
  if (d.vendor === 'huawei') return [
    'Huawei Versatile Routing Platform Software',
    `VRP (R) software, Version ${d.os_version ?? 'V800R022C10'} (${d.model ?? 'NE40E'})`,
    'Copyright (C) 2000-2024 HUAWEI TECH CO., LTD',
    '',
    `HUAWEI ${d.model ?? 'NE40E'} uptime is 21 days, 8 hours, 04 minutes`,
    `BKP   0 ONLINE`,
    `MPU   0 ONLINE`,
  ];
  if (d.vendor === 'fortinet') return [
    `FortiGate-${d.model ?? '100F'} (FortiOS v${d.os_version ?? '7.4.2'})`,
    `Serial-Number : FG${Math.random().toString(36).slice(2, 12).toUpperCase()}`,
    `BIOS version  : 05000014`,
    `Hostname      : ${d.hostname}`,
    `Build         : 0396`,
  ];
  return [`${d.hostname} — vendor: ${d.vendor}, model: ${d.model ?? 'N/A'}`, `OS: ${d.os_version ?? 'N/A'}`];
}

function showInterfaces(d: NetworkDevice): string[] {
  if (d.interfaces.length === 0) return ['No interfaces configured.'];
  const lines: string[] = [];
  for (const iface of d.interfaces) {
    const adminStr = iface.admin_status === false ? 'administratively down' : 'up';
    const opStr    = iface.status === 'up' ? 'up' : iface.status === 'down' ? 'down' : iface.status;
    lines.push(`${iface.name} is ${adminStr}, line protocol is ${opStr}`);
    if (iface.ip_address) lines.push(`  Internet address is ${iface.ip_address}/${iface.prefix_length ?? 24}`);
    if (iface.mtu)        lines.push(`  MTU ${iface.mtu} bytes`);
    if (iface.speed)      lines.push(`  ${iface.speed >= 1000 ? `${iface.speed / 1000}Gb/s` : `${iface.speed}Mb/s`}, Full Duplex`);
    lines.push('');
  }
  return lines;
}

function showIpRoute(d: NetworkDevice): string[] {
  const lines: string[] = ['Codes: C - connected, S - static, O - OSPF, B - BGP', ''];
  for (const iface of d.interfaces) {
    if (iface.ip_address && iface.prefix_length) {
      lines.push(`C    ${iface.ip_address}/${iface.prefix_length} is directly connected, ${iface.name}`);
    }
  }
  lines.push('S*   0.0.0.0/0 [1/0] via 203.0.113.1');
  return lines;
}

function showVlan(d: NetworkDevice): string[] {
  if (d.vlans.length === 0) return ['No VLANs configured.'];
  const lines: string[] = ['VLAN  Name              Status', '----  ----------------  ------'];
  for (const v of d.vlans) {
    lines.push(`${String(v.vlan_id).padEnd(6)}${(v.name ?? 'VLAN' + v.vlan_id).padEnd(18)}active`);
  }
  return lines;
}

function simulatePing(cmd: string): string[] {
  const ip = cmd.split(/\s+/)[1] ?? '8.8.8.8';
  return [
    `Type escape sequence to abort.`,
    `Sending 5, 100-byte ICMP Echos to ${ip}, timeout is 2 seconds:`,
    `!!!!!`,
    `Success rate is 100 percent (5/5), round-trip min/avg/max = 1/2/4 ms`,
  ];
}

const HELP_TEXT = [
  'Available commands:',
  '  show version         Display system software and hardware version',
  '  show interfaces      Display interface status and configuration',
  '  show ip route        Display IP routing table',
  '  show vlan            Display VLAN database (switches)',
  '  ping <ip>            Ping an IP address',
  '  clear                Clear the terminal screen',
  '  exit                 Close the session',
  '  ?                    Show this help',
];

function simulateCommand(cmd: string, device: NetworkDevice): CLILine[] {
  const t = cmd.trim().toLowerCase();
  if (t === '')        return [];
  if (t === 'clear')   return [{ type: 'output', text: '__CLEAR__' }];
  if (t === 'exit')    return [
    { type: 'output', text: `Closing session to ${device.hostname}…` },
    { type: 'output', text: 'Goodbye.' },
  ];
  if (t === '?' || t === 'help')     return HELP_TEXT.map((l) => ({ type: 'output', text: l }));
  if (t === 'show version')          return showVersion(device).map((l) => ({ type: 'output', text: l }));
  if (t === 'show interfaces' || t === 'show int') return showInterfaces(device).map((l) => ({ type: 'output', text: l }));
  if (t === 'show ip route')         return showIpRoute(device).map((l) => ({ type: 'output', text: l }));
  if (t === 'show vlan')             return showVlan(device).map((l) => ({ type: 'output', text: l }));
  if (t.startsWith('ping'))          return simulatePing(t).map((l) => ({ type: 'output', text: l }));
  return [{ type: 'error', text: `% Unknown command: "${cmd}". Type "?" for help.` }];
}

// ---------------------------------------------------------------------------
// Color picker panel
// ---------------------------------------------------------------------------

const BG_PRESETS   = [['#000000','Noir'],['#0D1117','Sombre'],['#0A0E1A','Marine'],['#1A1A2E','Nuit']];
const TEXT_PRESETS = [['#00FF00','Vert'],['#00FFFF','Cyan'],['#FFFFFF','Blanc'],['#FFB000','Ambre'],['#F8F8F2','Crème']];
const FONTS        = ['JetBrains Mono','Courier New','Fira Code','monospace'];

function ColorPanel({ colors, onChange }: {
  colors: CLIColors;
  onChange: (c: Partial<CLIColors>) => void;
}) {
  const swatch = (color: string, active: boolean, onClick: () => void) => (
    <button
      key={color}
      onClick={onClick}
      style={{
        width: 16, height: 16, borderRadius: 3, background: color, border: active ? '2px solid white' : '2px solid #334155',
        cursor: 'pointer', flexShrink: 0,
      }}
    />
  );

  return (
    <div style={{ width: 180, borderLeft: '1px solid #1E293B', padding: '12px 10px', overflowY: 'auto', fontSize: 11 }}>
      <div style={{ color: '#94A3B8', fontWeight: 700, marginBottom: 10 }}>Personnalisation</div>

      <div style={{ color: '#64748B', marginBottom: 6 }}>Fond :</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
        {BG_PRESETS.map(([c, label]) => swatch(c, colors.bg === c, () => onChange({ bg: c })))}
      </div>
      <div style={{ display: 'flex', gap: 4, marginBottom: 12, alignItems: 'center' }}>
        <span style={{ color: '#64748B' }}>Custom:</span>
        <input type="color" value={colors.bg} onChange={(e) => onChange({ bg: e.target.value })}
          style={{ width: 28, height: 20, border: 'none', background: 'none', cursor: 'pointer', padding: 0 }} />
      </div>

      <div style={{ color: '#64748B', marginBottom: 6 }}>Texte :</div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, marginBottom: 8 }}>
        {TEXT_PRESETS.map(([c]) => swatch(c, colors.text === c, () => onChange({ text: c })))}
      </div>
      <div style={{ display: 'flex', gap: 4, marginBottom: 12, alignItems: 'center' }}>
        <span style={{ color: '#64748B' }}>Custom:</span>
        <input type="color" value={colors.text} onChange={(e) => onChange({ text: e.target.value })}
          style={{ width: 28, height: 20, border: 'none', background: 'none', cursor: 'pointer', padding: 0 }} />
      </div>

      <div style={{ color: '#64748B', marginBottom: 4 }}>Police :</div>
      <select
        value={colors.font}
        onChange={(e) => onChange({ font: e.target.value })}
        style={{ width: '100%', background: '#0F172A', color: '#CBD5E1', border: '1px solid #334155', borderRadius: 4, padding: '2px 4px', fontSize: 10, marginBottom: 12 }}
      >
        {FONTS.map((f) => <option key={f} value={f}>{f}</option>)}
      </select>

      <div style={{ color: '#64748B', marginBottom: 4 }}>Taille : {colors.fontSize}px</div>
      <input
        type="range" min="10" max="18" value={colors.fontSize}
        onChange={(e) => onChange({ fontSize: +e.target.value })}
        style={{ width: '100%', marginBottom: 8 }}
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// CLITerminal
// ---------------------------------------------------------------------------

interface CLITerminalProps {
  session:        CLISession;
  onClose:        () => void;
  onFocus:        () => void;
  onToggleMin:    () => void;
  onUpdateColors: (c: Partial<CLIColors>) => void;
  onUpdatePos:    (p: { x: number; y: number }) => void;
  onUpdateSize:   (s: { width: number; height: number }) => void;
  onCommand:      (cmd: string) => void;
  onPushHistory:  (cmd: string) => void;
}

export function CLITerminal({
  session, onClose, onFocus, onToggleMin, onUpdateColors, onUpdatePos, onUpdateSize, onCommand, onPushHistory,
}: CLITerminalProps) {
  const [showColors, setShowColors] = useState(false);
  const [inputVal,   setInputVal]   = useState('');
  const [histIdx,    setHistIdx]    = useState(-1);
  const [startTime]                 = useState(Date.now());
  const [elapsed,    setElapsed]    = useState('00:00:00');

  const outputRef  = useRef<HTMLDivElement>(null);
  const inputRef   = useRef<HTMLInputElement>(null);
  const isDrag     = useRef(false);
  const dragOff    = useRef({ x: 0, y: 0 });
  const isResize   = useRef(false);
  const resizeStart= useRef({ x: 0, y: 0, w: 0, h: 0 });

  const { id, device, position: pos, size, isMinimized, colors, zIndex, lines, cmdHistory } = session;

  // Elapsed timer
  useEffect(() => {
    const t = setInterval(() => {
      const s = Math.floor((Date.now() - startTime) / 1000);
      const h = String(Math.floor(s / 3600)).padStart(2, '0');
      const m = String(Math.floor((s % 3600) / 60)).padStart(2, '0');
      const ss = String(s % 60).padStart(2, '0');
      setElapsed(`${h}:${m}:${ss}`);
    }, 1000);
    return () => clearInterval(t);
  }, [startTime]);

  // Auto-scroll
  useEffect(() => {
    if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [lines]);

  // Drag
  useEffect(() => {
    const onMove = (e: MouseEvent) => {
      if (isDrag.current) onUpdatePos({ x: e.clientX - dragOff.current.x, y: e.clientY - dragOff.current.y });
      if (isResize.current) {
        const dw = e.clientX - resizeStart.current.x;
        const dh = e.clientY - resizeStart.current.y;
        onUpdateSize({
          width:  Math.max(400, resizeStart.current.w + dw),
          height: Math.max(200, resizeStart.current.h + dh),
        });
      }
    };
    const onUp = () => { isDrag.current = false; isResize.current = false; };
    window.addEventListener('mousemove', onMove);
    window.addEventListener('mouseup', onUp);
    return () => { window.removeEventListener('mousemove', onMove); window.removeEventListener('mouseup', onUp); };
  }, [onUpdatePos, onUpdateSize]);

  const startDrag = (e: React.MouseEvent) => {
    if (e.button !== 0) return;
    isDrag.current = true;
    dragOff.current = { x: e.clientX - pos.x, y: e.clientY - pos.y };
    onFocus();
    e.preventDefault();
  };

  const startResize = (e: React.MouseEvent) => {
    isResize.current = true;
    resizeStart.current = { x: e.clientX, y: e.clientY, w: size.width, h: size.height };
    e.preventDefault();
    e.stopPropagation();
  };

  const handleKeyDown = useCallback((e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      const cmd = inputVal.trim();
      setInputVal('');
      setHistIdx(-1);
      if (cmd) {
        onPushHistory(cmd);
        onCommand(cmd);
      } else {
        onCommand('');
      }
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      const newIdx = Math.min(histIdx + 1, cmdHistory.length - 1);
      setHistIdx(newIdx);
      setInputVal(cmdHistory[cmdHistory.length - 1 - newIdx] ?? '');
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const newIdx = Math.max(histIdx - 1, -1);
      setHistIdx(newIdx);
      setInputVal(newIdx < 0 ? '' : (cmdHistory[cmdHistory.length - 1 - newIdx] ?? ''));
    }
  }, [inputVal, histIdx, cmdHistory, onCommand, onPushHistory]);

  const prompt = `${device.hostname}# `;

  return (
    <div
      style={{
        position:  'fixed',
        left:      pos.x,
        top:       pos.y,
        width:     isMinimized ? 300 : size.width,
        height:    isMinimized ? 34  : size.height,
        zIndex,
        display:   'flex',
        flexDirection: 'column',
        borderRadius: 8,
        overflow:  'hidden',
        boxShadow: '0 16px 48px rgba(0,0,0,0.7)',
        border:    '1px solid #334155',
        userSelect: 'none',
      }}
      onMouseDown={onFocus}
    >
      {/* ── Header ── */}
      <div
        onMouseDown={startDrag}
        style={{
          display:        'flex',
          alignItems:     'center',
          gap:            8,
          padding:        '0 10px',
          height:         34,
          background:     '#0F172A',
          borderBottom:   isMinimized ? 'none' : '1px solid #1E293B',
          cursor:         'move',
          flexShrink:     0,
        }}
      >
        <span style={{ fontSize: 13 }}>🖥</span>
        <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#94A3B8', flex: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
          {device.hostname}  {device.management_ip ? `(${device.management_ip})` : ''}
        </span>
        <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
          {[
            { icon: <Settings size={12} />, title: 'Couleurs', onClick: (e: React.MouseEvent) => { e.stopPropagation(); setShowColors((v) => !v); } },
            { icon: <Minus size={12} />,    title: 'Minimiser', onClick: (e: React.MouseEvent) => { e.stopPropagation(); onToggleMin(); } },
            { icon: <X size={12} />,        title: 'Fermer',    onClick: (e: React.MouseEvent) => { e.stopPropagation(); onClose(); } },
          ].map(({ icon, title, onClick }) => (
            <button key={title} title={title} onClick={onClick} onMouseDown={(e) => e.stopPropagation()}
              style={{ display:'flex', alignItems:'center', justifyContent:'center', width:18, height:18, borderRadius:4,
                       border:'none', cursor:'pointer', background:'transparent', color:'#64748B',
                       transition:'color 0.15s', padding: 0 }}
              onMouseEnter={(e) => (e.currentTarget.style.color = '#CBD5E1')}
              onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
            >
              {icon}
            </button>
          ))}
        </div>
      </div>

      {/* ── Body ── */}
      {!isMinimized && (
        <div style={{ display: 'flex', flex: 1, minHeight: 0, background: colors.bg }}>

          {/* Terminal area */}
          <div style={{ display: 'flex', flexDirection: 'column', flex: 1, minWidth: 0 }}>
            {/* Output */}
            <div
              ref={outputRef}
              onClick={() => inputRef.current?.focus()}
              style={{
                flex: 1,
                overflowY: 'auto',
                padding: '8px 12px',
                fontFamily: `"${colors.font}", monospace`,
                fontSize:   colors.fontSize,
                color:      colors.text,
                lineHeight: 1.5,
                cursor:     'text',
              }}
            >
              {lines.map((line, i) => (
                <div key={i} style={{ color: line.type === 'error' ? '#EF4444' : line.type === 'input' ? '#60A5FA' : colors.text, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                  {line.text}
                </div>
              ))}
            </div>

            {/* Input row */}
            <div style={{ display: 'flex', alignItems: 'center', padding: '4px 12px 6px', borderTop: '1px solid #0F172A', flexShrink: 0 }}>
              <span style={{ fontFamily: `"${colors.font}", monospace`, fontSize: colors.fontSize, color: colors.text, whiteSpace: 'nowrap', marginRight: 4 }}>
                {prompt}
              </span>
              <input
                ref={inputRef}
                autoFocus
                value={inputVal}
                onChange={(e) => setInputVal(e.target.value)}
                onKeyDown={handleKeyDown}
                spellCheck={false}
                style={{
                  flex:       1,
                  background: 'transparent',
                  border:     'none',
                  outline:    'none',
                  fontFamily: `"${colors.font}", monospace`,
                  fontSize:   colors.fontSize,
                  color:      colors.text,
                  caretColor: colors.text,
                }}
              />
            </div>

            {/* Status bar */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '2px 12px', background: '#0A0E1A', borderTop: '1px solid #0F172A', fontSize: 10, color: '#475569', flexShrink: 0 }}>
              <span style={{ color: '#22C55E' }}>● Connecté (simulé)</span>
              <span>SSH</span>
              <span>{device.management_ip ?? 'N/A'}</span>
              <span style={{ marginLeft: 'auto' }}>{elapsed}</span>
            </div>
          </div>

          {/* Color picker panel */}
          {showColors && (
            <ColorPanel
              colors={colors}
              onChange={(partial) => onUpdateColors(partial)}
            />
          )}
        </div>
      )}

      {/* Resize handle */}
      {!isMinimized && (
        <div
          onMouseDown={startResize}
          style={{
            position:  'absolute',
            right:     0,
            bottom:    0,
            width:     14,
            height:    14,
            cursor:    'se-resize',
            background: 'linear-gradient(135deg, transparent 50%, #334155 50%)',
          }}
        />
      )}
    </div>
  );
}
