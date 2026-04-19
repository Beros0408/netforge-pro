/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      colors: {
        canvas: {
          bg: '#020617',
          grid: '#0f172a',
        },
        zone: {
          wan: '#7c3aed',
          dmz: '#dc2626',
          lan: '#2563eb',
          mgmt: '#059669',
          server: '#d97706',
          core: '#475569',
        },
        severity: {
          critical: '#ef4444',
          high: '#f97316',
          medium: '#f59e0b',
          low: '#3b82f6',
        },
        status: {
          up: '#22c55e',
          down: '#ef4444',
          unknown: '#f59e0b',
          admin_down: '#6b7280',
        },
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.2s ease-out',
        'slide-in-right': 'slideInRight 0.3s ease-out',
        'slide-in-up': 'slideInUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: { from: { opacity: '0' }, to: { opacity: '1' } },
        slideInRight: { from: { transform: 'translateX(100%)' }, to: { transform: 'translateX(0)' } },
        slideInUp: { from: { transform: 'translateY(100%)' }, to: { transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [],
};
