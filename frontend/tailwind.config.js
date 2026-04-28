/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"Syne"', 'sans-serif'],
        body: ['"DM Sans"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
      colors: {
        ink: '#0A0A0F',
        'ink-muted': '#1A1A2E',
        surface: '#111118',
        'surface-raised': '#1C1C28',
        border: '#2A2A3E',
        accent: '#6C63FF',
        'accent-glow': '#8B83FF',
        emerald: '#00D68F',
        'emerald-dim': '#00B377',
        coral: '#FF6B6B',
        'coral-dim': '#E55555',
        amber: '#FFB830',
        muted: '#6B7280',
        subtle: '#9CA3AF',
      },
      boxShadow: {
        'glow-accent': '0 0 40px rgba(108,99,255,0.15)',
        'glow-emerald': '0 0 30px rgba(0,214,143,0.12)',
        'glow-coral': '0 0 30px rgba(255,107,107,0.12)',
        'card': '0 1px 3px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.3)',
      }
    },
  },
  plugins: [],
}
