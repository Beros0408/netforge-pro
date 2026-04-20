import { BrowserRouter, Route, Routes } from 'react-router-dom';
import { Sidebar } from './components/shared/Sidebar';
import { MainLayout } from './components/layout/MainLayout';
import { ProblemsPage } from './pages/ProblemsPage';

function PlaceholderPage({ title }: { title: string }) {
  return (
    <div className="flex flex-col flex-1 items-center justify-center h-full gap-3">
      <span className="text-slate-400 text-2xl font-semibold">{title}</span>
      <span className="text-slate-600 text-sm">Page en construction</span>
    </div>
  );
}

// Simple layout wrapper for secondary pages (keeps sidebar nav)
function WithSidebar({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-full w-full overflow-hidden">
      <Sidebar />
      <main className="flex flex-col flex-1 min-w-0 overflow-hidden">
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* CML-style layout for topology */}
        <Route path="/"         element={<MainLayout />} />
        <Route path="/topology" element={<MainLayout />} />

        {/* Secondary pages keep the sidebar */}
        <Route path="/problems" element={<WithSidebar><ProblemsPage /></WithSidebar>} />
        <Route path="/devices"  element={<WithSidebar><PlaceholderPage title="Équipements" /></WithSidebar>} />
        <Route path="/health"   element={<WithSidebar><PlaceholderPage title="Santé réseau" /></WithSidebar>} />
        <Route path="/settings" element={<WithSidebar><PlaceholderPage title="Paramètres" /></WithSidebar>} />
      </Routes>
    </BrowserRouter>
  );
}
