import { AlignHorizontalDistributeCenter, AlignVerticalDistributeCenter, GitMerge, Minus, Spline } from 'lucide-react';

export type EdgeVariant = 'bezier' | 'smoothstep' | 'straight';
export type LayoutDirection = 'horizontal' | 'vertical';

interface CanvasToolbarProps {
  edgeVariant: EdgeVariant;
  onEdgeVariantChange: (v: EdgeVariant) => void;
  onLayout: (direction: LayoutDirection) => void;
}

const EDGE_VARIANTS: { value: EdgeVariant; label: string; Icon: React.FC<{ className?: string }> }[] = [
  { value: 'smoothstep', label: 'Courbe',        Icon: Spline },
  { value: 'bezier',     label: 'Bezier',        Icon: GitMerge },
  { value: 'straight',   label: 'Droit',         Icon: Minus },
];

export function CanvasToolbar({ edgeVariant, onEdgeVariantChange, onLayout }: CanvasToolbarProps) {
  return (
    <div
      style={{
        position: 'absolute',
        top: 12,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 20,
        display: 'flex',
        alignItems: 'center',
        gap: 6,
        background: '#0F172A',
        border: '1px solid #1E293B',
        borderRadius: 10,
        padding: '5px 8px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.4)',
      }}
    >
      {/* Separator label */}
      <span style={{ fontSize: 10, color: '#475569', paddingRight: 4 }}>LIENS</span>

      {EDGE_VARIANTS.map(({ value, label, Icon }) => (
        <button
          key={value}
          title={label}
          onClick={() => onEdgeVariantChange(value)}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            padding: '4px 8px',
            borderRadius: 6,
            fontSize: 11,
            cursor: 'pointer',
            border: 'none',
            background: edgeVariant === value ? '#1D4ED8' : 'transparent',
            color: edgeVariant === value ? 'white' : '#64748B',
            transition: 'all 0.15s',
          }}
        >
          <Icon className="w-3 h-3" />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}

      <div style={{ width: 1, height: 20, background: '#1E293B', margin: '0 4px' }} />

      {/* Layout buttons */}
      <span style={{ fontSize: 10, color: '#475569', paddingRight: 4 }}>LAYOUT</span>

      <button
        title="Layout Horizontal"
        onClick={() => onLayout('horizontal')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          padding: '4px 8px',
          borderRadius: 6,
          fontSize: 11,
          cursor: 'pointer',
          border: 'none',
          background: 'transparent',
          color: '#64748B',
          transition: 'all 0.15s',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = '#CBD5E1')}
        onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
      >
        <AlignHorizontalDistributeCenter className="w-3 h-3" />
        <span className="hidden sm:inline">H</span>
      </button>

      <button
        title="Layout Vertical"
        onClick={() => onLayout('vertical')}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 4,
          padding: '4px 8px',
          borderRadius: 6,
          fontSize: 11,
          cursor: 'pointer',
          border: 'none',
          background: 'transparent',
          color: '#64748B',
          transition: 'all 0.15s',
        }}
        onMouseEnter={(e) => (e.currentTarget.style.color = '#CBD5E1')}
        onMouseLeave={(e) => (e.currentTarget.style.color = '#64748B')}
      >
        <AlignVerticalDistributeCenter className="w-3 h-3" />
        <span className="hidden sm:inline">V</span>
      </button>
    </div>
  );
}
