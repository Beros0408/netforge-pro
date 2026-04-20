// DeviceIcons.tsx — NetForge Pro
// Icônes SVG reproduisant fidèlement les icônes génériques réseau
// Router, Switch L2, Switch DC, Firewall, WLC, Access Point

import React from 'react';

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
}

// ─────────────────────────────────────────────
// ROUTER — Disque bleu avec flèches blanches
// ─────────────────────────────────────────────
export const RouterIcon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 100 80" className={className}>
    {/* Corps du router - ellipse/disque */}
    <ellipse cx="50" cy="55" rx="45" ry="18" fill="#1a7abf" />
    <ellipse cx="50" cy="45" rx="45" ry="18" fill="#2196F3" />
    <ellipse cx="50" cy="45" rx="45" ry="18" fill="url(#routerGrad)" />
    {/* Face supérieure */}
    <ellipse cx="50" cy="32" rx="45" ry="18" fill="#42A5F5" />
    {/* Flèches blanches */}
    {/* Flèche haut */}
    <polygon points="50,8 44,20 56,20" fill="white" opacity="0.9"/>
    {/* Flèche bas */}
    <polygon points="50,56 44,44 56,44" fill="white" opacity="0.9"/>
    {/* Flèche gauche */}
    <polygon points="8,32 20,26 20,38" fill="white" opacity="0.9"/>
    {/* Flèche droite */}
    <polygon points="92,32 80,26 80,38" fill="white" opacity="0.9"/>
    {/* Cercle central */}
    <circle cx="50" cy="32" r="10" fill="#0D47A1" opacity="0.6"/>
    <circle cx="50" cy="32" r="6" fill="white" opacity="0.8"/>
    <defs>
      <linearGradient id="routerGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#64B5F6"/>
        <stop offset="100%" stopColor="#1565C0"/>
      </linearGradient>
    </defs>
  </svg>
);

// ─────────────────────────────────────────────
// SWITCH L2 / MULTILAYER — Cube rouge avec soleil
// ─────────────────────────────────────────────
export const SwitchL2Icon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 100 100" className={className}>
    {/* Face avant du cube */}
    <rect x="15" y="25" width="60" height="60" rx="4" fill="#E53935"/>
    {/* Face supérieure du cube */}
    <polygon points="15,25 35,5 95,5 75,25" fill="#EF5350"/>
    {/* Face droite du cube */}
    <polygon points="75,25 95,5 95,65 75,85" fill="#B71C1C"/>
    {/* Cercle central rouge foncé */}
    <circle cx="45" cy="55" r="18" fill="#B71C1C"/>
    <circle cx="45" cy="55" r="12" fill="#E53935"/>
    {/* Lignes rayonnantes (style soleil/switch) */}
    {[0,45,90,135,180,225,270,315].map((angle, i) => {
      const rad = (angle * Math.PI) / 180;
      const x1 = 45 + 14 * Math.cos(rad);
      const y1 = 55 + 14 * Math.sin(rad);
      const x2 = 45 + 22 * Math.cos(rad);
      const y2 = 55 + 22 * Math.sin(rad);
      return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke="#FFCDD2" strokeWidth="2.5"/>;
    })}
    {/* Point central */}
    <circle cx="45" cy="55" r="4" fill="white"/>
  </svg>
);

// ─────────────────────────────────────────────
// DATA CENTER SWITCH — Cube rouge avec flèches
// ─────────────────────────────────────────────
export const DataCenterSwitchIcon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 100 110" className={className}>
    {/* Corps principal - rectangle */}
    <rect x="10" y="20" width="65" height="75" rx="3" fill="#E53935"/>
    {/* Face supérieure */}
    <polygon points="10,20 30,5 95,5 75,20" fill="#EF5350"/>
    {/* Face droite */}
    <polygon points="75,20 95,5 95,80 75,95" fill="#C62828"/>
    {/* Cercle central */}
    <circle cx="43" cy="57" r="20" fill="#B71C1C"/>
    <circle cx="43" cy="57" r="14" fill="#E53935"/>
    {/* Flèches sortantes - style Data Center */}
    {/* Droite */}
    <polygon points="80,54 65,48 65,60" fill="white" opacity="0.9"/>
    {/* Gauche */}
    <polygon points="6,54 21,48 21,60" fill="white" opacity="0.9"/>
    {/* Haut */}
    <polygon points="43,10 37,22 49,22" fill="white" opacity="0.9"/>
    {/* Bas */}
    <polygon points="43,98 37,86 49,86" fill="white" opacity="0.9"/>
    {/* Diagonales */}
    <polygon points="70,25 60,30 65,38" fill="white" opacity="0.7"/>
    <polygon points="16,25 26,30 21,38" fill="white" opacity="0.7"/>
    {/* Point central */}
    <circle cx="43" cy="57" r="5" fill="white"/>
  </svg>
);

// ─────────────────────────────────────────────
// FIREWALL — Mur de briques rouge vertical
// ─────────────────────────────────────────────
export const FirewallIcon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 70 100" className={className}>
    {/* Corps principal du mur */}
    <rect x="5" y="5" width="60" height="90" rx="2" fill="#E53935"/>
    {/* Rangées de briques */}
    {/* Rangée 1 */}
    <rect x="7" y="8" width="27" height="12" rx="1" fill="#C62828" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="36" y="8" width="27" height="12" rx="1" fill="#C62828" stroke="#FFCDD2" strokeWidth="0.5"/>
    {/* Rangée 2 - décalée */}
    <rect x="7" y="22" width="13" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="22" y="22" width="27" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="51" y="22" width="13" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    {/* Rangée 3 */}
    <rect x="7" y="36" width="27" height="12" rx="1" fill="#C62828" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="36" y="36" width="27" height="12" rx="1" fill="#C62828" stroke="#FFCDD2" strokeWidth="0.5"/>
    {/* Rangée 4 - décalée */}
    <rect x="7" y="50" width="13" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="22" y="50" width="27" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="51" y="50" width="13" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    {/* Rangée 5 */}
    <rect x="7" y="64" width="27" height="12" rx="1" fill="#C62828" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="36" y="64" width="27" height="12" rx="1" fill="#C62828" stroke="#FFCDD2" strokeWidth="0.5"/>
    {/* Rangée 6 - décalée */}
    <rect x="7" y="78" width="13" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="22" y="78" width="27" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    <rect x="51" y="78" width="13" height="12" rx="1" fill="#B71C1C" stroke="#FFCDD2" strokeWidth="0.5"/>
    {/* Flamme en haut (optionnelle) */}
    <path d="M30,3 Q35,-2 40,3 Q38,0 35,2 Q32,0 30,3Z" fill="#FF6D00" opacity="0.8"/>
  </svg>
);

// ─────────────────────────────────────────────
// WLC — Contrôleur WLAN, boîte plate bleue
// ─────────────────────────────────────────────
export const WLCIcon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 120 70" className={className}>
    {/* Corps principal - boîte plate */}
    <rect x="5" y="20" width="110" height="40" rx="4" fill="#1565C0"/>
    {/* Face supérieure */}
    <polygon points="5,20 20,8 115,8 110,20" fill="#1976D2"/>
    {/* Face droite */}
    <polygon points="110,20 115,8 115,48 110,60" fill="#0D47A1"/>
    {/* Ondes WiFi - rangée du bas */}
    {[18, 34, 50, 66, 82].map((x, i) => (
      <ellipse key={i} cx={x} cy="40" rx="8" ry="12"
        fill="none" stroke="#90CAF9" strokeWidth="2"
        opacity="0.8"/>
    ))}
    {/* Flèches vers le haut (antennes) */}
    {[18, 34, 50, 66, 82].map((x, i) => (
      <polygon key={i} points={`${x},10 ${x-5},20 ${x+5},20`}
        fill="white" opacity="0.8"/>
    ))}
    {/* LED indicateurs */}
    <circle cx="95" cy="30" r="3" fill="#4CAF50"/>
    <circle cx="103" cy="30" r="3" fill="#4CAF50"/>
  </svg>
);

// ─────────────────────────────────────────────
// ACCESS POINT — Boîte plate bleue avec ondes
// ─────────────────────────────────────────────
export const AccessPointIcon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 120 65" className={className}>
    {/* Corps principal - boîte plate */}
    <rect x="5" y="18" width="110" height="38" rx="4" fill="#1E88E5"/>
    {/* Face supérieure */}
    <polygon points="5,18 20,6 115,6 110,18" fill="#42A5F5"/>
    {/* Face droite */}
    <polygon points="110,18 115,6 115,44 110,56" fill="#1565C0"/>
    {/* Cercles/ondes WiFi dans le corps */}
    {[20, 36, 52, 68, 84, 100].map((x, i) => (
      <g key={i}>
        <circle cx={x} cy="37" r="10" fill="none"
          stroke="#BBDEFB" strokeWidth="1.5" opacity="0.6"/>
        <circle cx={x} cy="37" r="6" fill="none"
          stroke="#BBDEFB" strokeWidth="1.5" opacity="0.8"/>
        <circle cx={x} cy="37" r="3" fill="#E3F2FD" opacity="0.9"/>
      </g>
    ))}
    {/* LED */}
    <circle cx="105" cy="28" r="3" fill="#4CAF50"/>
  </svg>
);

// ─────────────────────────────────────────────
// SERVEUR GÉNÉRIQUE
// ─────────────────────────────────────────────
export const ServerIcon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 80 100" className={className}>
    {/* Chassis serveur */}
    <rect x="5" y="5" width="70" height="90" rx="5" fill="#37474F"/>
    {/* Unités rack */}
    {[15, 32, 49, 66].map((y, i) => (
      <g key={i}>
        <rect x="10" y={y} width="60" height="12" rx="2" fill="#455A64"/>
        <circle cx="65" cy={y+6} r="3" fill={i === 0 ? "#4CAF50" : "#2196F3"}/>
        <rect x="14" y={y+4} width="35" height="4" rx="1" fill="#546E7A"/>
      </g>
    ))}
  </svg>
);

// ─────────────────────────────────────────────
// CLOUD / INTERNET
// ─────────────────────────────────────────────
export const CloudIcon: React.FC<IconProps> = ({ size = 48, className }) => (
  <svg width={size} height={size} viewBox="0 0 100 70" className={className}>
    <path d="M25,55 Q10,55 10,42 Q10,30 22,28 Q20,15 35,12 Q45,5 58,12 Q70,5 80,15 Q92,15 92,28 Q98,30 95,42 Q92,55 78,55 Z"
      fill="#64B5F6" stroke="#1565C0" strokeWidth="2"/>
    <path d="M25,55 Q10,55 10,42 Q10,30 22,28 Q20,15 35,12 Q45,5 58,12 Q70,5 80,15 Q92,15 92,28 Q98,30 95,42 Q92,55 78,55 Z"
      fill="url(#cloudGrad)" stroke="#1976D2" strokeWidth="1.5"/>
    <defs>
      <linearGradient id="cloudGrad" x1="0%" y1="0%" x2="0%" y2="100%">
        <stop offset="0%" stopColor="#90CAF9"/>
        <stop offset="100%" stopColor="#42A5F5"/>
      </linearGradient>
    </defs>
  </svg>
);

// ─────────────────────────────────────────────
// EXPORT — Map type → composant icon
// ─────────────────────────────────────────────
export const getDeviceIcon = (deviceType: string, size = 48) => {
  const type = deviceType.toLowerCase();
  if (type.includes('router') || type === 'router') return <RouterIcon size={size}/>;
  if (type.includes('firewall') || type === 'firewall') return <FirewallIcon size={size}/>;
  if (type.includes('wlc') || type.includes('wireless') || type.includes('controller')) return <WLCIcon size={size}/>;
  if (type.includes('ap') || type.includes('access_point') || type.includes('access point')) return <AccessPointIcon size={size}/>;
  if (type.includes('dc_switch') || type.includes('datacenter') || type.includes('spine') || type.includes('core')) return <DataCenterSwitchIcon size={size}/>;
  if (type.includes('switch') || type.includes('sw')) return <SwitchL2Icon size={size}/>;
  if (type.includes('server')) return <ServerIcon size={size}/>;
  if (type.includes('cloud') || type.includes('internet')) return <CloudIcon size={size}/>;
  // Défaut
  return <SwitchL2Icon size={size}/>;
};
