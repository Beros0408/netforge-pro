import { createContext, useContext } from 'react';
import type { NetworkDevice } from '../types/network';

interface CanvasCallbacks {
  onOpenCLI:  (device: NetworkDevice) => void;
  onShowInfo: (device: NetworkDevice) => void;
}

export const CanvasCallbacksContext = createContext<CanvasCallbacks>({
  onOpenCLI:  () => {},
  onShowInfo: () => {},
});

export const useCanvasCallbacks = () => useContext(CanvasCallbacksContext);
