import { memo } from 'react';

interface SecurityScoreProps {
  score: number;
  size?: number;
}

export const SecurityScore = memo(function SecurityScore({ score, size = 120 }: SecurityScoreProps) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const clampedScore = Math.max(0, Math.min(100, score));
  const dashOffset = circumference * (1 - clampedScore / 100);

  const color =
    clampedScore >= 80 ? '#4ade80' : clampedScore >= 60 ? '#facc15' : '#f87171';
  const trackColor = '#1e293b';
  const label =
    clampedScore >= 80 ? 'Bon' : clampedScore >= 60 ? 'Moyen' : 'Critique';

  return (
    <div className="flex flex-col items-center gap-1">
      <svg width={size} height={size} style={{ transform: 'rotate(-90deg)' }}>
        {/* Track */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={trackColor}
          strokeWidth={10}
        />
        {/* Progress */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={dashOffset}
          style={{ transition: 'stroke-dashoffset 0.6s ease, stroke 0.4s ease' }}
        />
        {/* Score text */}
        <text
          x={size / 2}
          y={size / 2 + 2}
          textAnchor="middle"
          dominantBaseline="middle"
          style={{
            transform: 'rotate(90deg)',
            transformOrigin: `${size / 2}px ${size / 2}px`,
            fontFamily: 'Inter, system-ui, sans-serif',
            fontSize: size * 0.22,
            fontWeight: 700,
            fill: color,
          }}
        >
          {clampedScore}
        </text>
      </svg>
      <span className="text-xs font-medium" style={{ color }}>{label}</span>
    </div>
  );
});
