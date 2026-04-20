import { useCallback, useState } from 'react';
import type { NetworkDevice } from '../types/network';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface CLIColors {
  bg:       string;
  text:     string;
  font:     string;
  fontSize: number;
}

export interface CLILine {
  type: 'output' | 'input' | 'error' | 'prompt';
  text: string;
}

export interface CLISession {
  id:          string;
  device:      NetworkDevice;
  position:    { x: number; y: number };
  size:        { width: number; height: number };
  isMinimized: boolean;
  colors:      CLIColors;
  zIndex:      number;
  lines:       CLILine[];
  cmdHistory:  string[];
}

const DEFAULT_COLORS: CLIColors = {
  bg:       '#000000',
  text:     '#00FF00',
  font:     'JetBrains Mono',
  fontSize: 13,
};

let _zTop = 2000;

// ---------------------------------------------------------------------------
// Hook
// ---------------------------------------------------------------------------

export function useCLISessions() {
  const [sessions, setSessions] = useState<CLISession[]>([]);

  const openSession = useCallback((device: NetworkDevice) => {
    const offset = sessions.length * 32;
    _zTop += 1;
    const id = `cli-${Date.now()}`;
    const newSession: CLISession = {
      id,
      device,
      position:    { x: 120 + offset, y: 80 + offset },
      size:        { width: 700, height: 420 },
      isMinimized: false,
      colors:      { ...DEFAULT_COLORS },
      zIndex:      _zTop,
      lines: [
        { type: 'output', text: `Connecting to ${device.hostname} (${device.management_ip ?? 'N/A'})…` },
        { type: 'output', text: 'Session established (simulated). Type "?" for commands.' },
        { type: 'output', text: '' },
      ],
      cmdHistory: [],
    };
    setSessions((prev) => [...prev, newSession]);
  }, [sessions.length]);

  const closeSession = useCallback((id: string) => {
    setSessions((prev) => prev.filter((s) => s.id !== id));
  }, []);

  const focusSession = useCallback((id: string) => {
    _zTop += 1;
    setSessions((prev) =>
      prev.map((s) => s.id === id ? { ...s, zIndex: _zTop, isMinimized: false } : s),
    );
  }, []);

  const toggleMinimize = useCallback((id: string) => {
    setSessions((prev) =>
      prev.map((s) => s.id === id ? { ...s, isMinimized: !s.isMinimized } : s),
    );
  }, []);

  const updateSession = useCallback(<K extends keyof CLISession>(
    id: string,
    key: K,
    value: CLISession[K],
  ) => {
    setSessions((prev) => prev.map((s) => s.id === id ? { ...s, [key]: value } : s));
  }, []);

  const appendLines = useCallback((id: string, lines: CLILine[]) => {
    setSessions((prev) =>
      prev.map((s) => s.id === id ? { ...s, lines: [...s.lines, ...lines] } : s),
    );
  }, []);

  const pushCmd = useCallback((id: string, cmd: string) => {
    setSessions((prev) =>
      prev.map((s) => s.id === id
        ? { ...s, cmdHistory: [...s.cmdHistory.filter((c) => c !== cmd), cmd].slice(-50) }
        : s,
      ),
    );
  }, []);

  return {
    sessions,
    openSession,
    closeSession,
    focusSession,
    toggleMinimize,
    updateSession,
    appendLines,
    pushCmd,
  };
}
