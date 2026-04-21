/**
 * App.tsx — NetForge Pro
 * Shell principal : Sidebar 240px + TopBar + contenu
 */
import { useRef, useState } from 'react';
import { BrowserRouter, NavLink, Route, Routes } from 'react-router-dom';
import {
  Activity,
  LayoutDashboard,
  Network,
  Server,
  Settings,
  Shield,
} from 'lucide-react';

import { NetworkCanvas } from './components/canvas/NetworkCanvas';
import type { NetworkCanvasHandle } from './components/canvas/NetworkCanvas';
import type { DeviceNodeData } from './components/canvas/DeviceNode';
import { ProblemsPage } from './pages/ProblemsPage';

// ─── Sidebar ──────────────────────────────────────────────────────────────────

const NAV = [
  { to: '/',         icon: LayoutDashboard, label: 'Dashboard',   end: true },
  { to: '/topology', icon: Network,         label: 'Topologie',   end: false },
  { to: '/devices',  icon: Server,          label: 'Équipements', end: false },
  { to: '/problems', icon: Shield,          label: 'Problèmes',   end: false },
  { to: '/health',   icon: Activity,        label: 'Santé',       end: false },
];

function AppSidebar() {
  return (
    <aside style={{
      width: 240,
      flexShrink: 0,
      background: '#0f1729',
      borderRight: '1px solid #1e2d45',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
    }}>
      {/* Logo */}
      <div style={{
        height: 48,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        padding: '0 16px',
        borderBottom: '1px solid #1e2d45',
        flexShrink: 0,
      }}>
        <div style={{
          width: 28,
          height: 28,
          borderRadius: 6,
          background: '#049fd9',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}>
          <Network size={14} color="#fff" />
        </div>
        <span style={{
          fontSize: 13,
          fontWeight: 700,
          color: '#e8edf5',
          fontFamily: '"JetBrains Mono", monospace',
          letterSpacing: '.5px',
        }}>
          NetForge Pro
        </span>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '8px 8px', overflowY: 'auto' }}>
        {NAV.map(({ to, icon: Icon, label, end }) => (
          <NavLink key={to} to={to} end={end}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '7px 10px',
              borderRadius: 6,
              fontSize: 12,
              fontWeight: 500,
              textDecoration: 'none',
              color: isActive ? '#049fd9' : '#4a6080',
              background: isActive ? '#049fd910' : 'transparent',
              marginBottom: 2,
              transition: 'color .1s, background .1s',
            })}
          >
            <Icon size={14} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      {/* Settings */}
      <div style={{ padding: '8px', borderTop: '1px solid #1e2d45', flexShrink: 0 }}>
        <NavLink to="/settings"
          style={({ isActive }) => ({
            display: 'flex',
            alignItems: 'center',
            gap: 10,
            padding: '7px 10px',
            borderRadius: 6,
            fontSize: 12,
            fontWeight: 500,
            textDecoration: 'none',
            color: isActive ? '#049fd9' : '#4a6080',
            background: isActive ? '#049fd910' : 'transparent',
          })}
        >
          <Settings size={14} />
          <span>Paramètres</span>
        </NavLink>
      </div>
    </aside>
  );
}

// ─── TopBar ───────────────────────────────────────────────────────────────────

interface TopBarProps {
  breadcrumb: string;
  device?: DeviceNodeData | null;
}

function TopBar({ breadcrumb, device }: TopBarProps) {
  return (
    <div style={{
      height: 40,
      background: '#0f1729',
      borderBottom: '1px solid #1e2d45',
      display: 'flex',
      alignItems: 'center',
      padding: '0 16px',
      gap: 6,
      flexShrink: 0,
    }}>
      <span style={{ fontSize: 11, color: '#4a6080' }}>NetForge Pro</span>
      <span style={{ color: '#1e2d45', fontSize: 14 }}>/</span>
      <span style={{ fontSize: 11, color: '#8ba3c7', fontWeight: 600 }}>{breadcrumb}</span>

      {device && (
        <>
          <span style={{ color: '#1e2d45', fontSize: 14, marginLeft: 6 }}>›</span>
          <span style={{
            fontSize: 11,
            color: '#049fd9',
            fontFamily: '"JetBrains Mono", monospace',
            fontWeight: 600,
          }}>
            {device.hostname}
          </span>
          <span style={{ fontSize: 10, color: '#4a6080', marginLeft: 4 }}>
            {device.model}
          </span>
          {device.managementIp && (
            <span style={{
              fontSize: 10,
              color: '#4a6080',
              fontFamily: '"JetBrains Mono", monospace',
              marginLeft: 4,
            }}>
              {device.managementIp}
            </span>
          )}
        </>
      )}
    </div>
  );
}

// ─── Pages ────────────────────────────────────────────────────────────────────

function TopologyPage() {
  const canvasRef = useRef<NetworkCanvasHandle>(null);
  const [selected, setSelected] = useState<DeviceNodeData | null>(null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar breadcrumb="Topologie" device={selected} />
      <div style={{ flex: 1, minHeight: 0 }}>
        <NetworkCanvas
          ref={canvasRef}
          onDeviceSelect={(data) => setSelected(data)}
        />
      </div>
    </div>
  );
}

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar breadcrumb={title} />
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
      }}>
        <span style={{ color: '#4a6080', fontSize: 20, fontWeight: 600 }}>{title}</span>
        <span style={{ color: '#2a3f5f', fontSize: 12 }}>Page en construction</span>
      </div>
    </div>
  );
}

// ─── App ──────────────────────────────────────────────────────────────────────

export default function App() {
  return (
    <BrowserRouter>
      <div style={{
        display: 'flex',
        height: '100vh',
        width: '100vw',
        overflow: 'hidden',
        background: '#0a0f1e',
      }}>
        <AppSidebar />

        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minWidth: 0 }}>
          <Routes>
            <Route path="/"         element={<TopologyPage />} />
            <Route path="/topology" element={<TopologyPage />} />
            <Route path="/problems" element={
              <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
                <TopBar breadcrumb="Problèmes" />
                <div style={{ flex: 1, overflow: 'auto' }}>
                  <ProblemsPage />
                </div>
              </div>
            } />
            <Route path="/devices"  element={<PlaceholderPage title="Équipements" />} />
            <Route path="/health"   element={<PlaceholderPage title="Santé réseau" />} />
            <Route path="/settings" element={<PlaceholderPage title="Paramètres" />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}
