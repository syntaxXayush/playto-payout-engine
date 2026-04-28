import { motion } from 'framer-motion'

export default function Header({ merchant, onLogout }) {
  return (
    <motion.header
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      className="border-b border-border bg-ink/80 backdrop-blur-xl sticky top-0 z-50"
    >
      <div className="max-w-6xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-8 h-8 rounded-lg bg-accent flex items-center justify-center shadow-glow-accent">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5">
              <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </div>
          <span className="font-display font-bold text-white text-lg tracking-tight">
            Playto <span className="text-accent">Pay</span>
          </span>
          <div className="hidden sm:block h-4 w-px bg-border mx-1" />
          <span className="hidden sm:block text-subtle text-sm font-body">
            {merchant?.business_name}
          </span>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-surface-raised border border-border">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald animate-pulse" />
            <span className="text-xs font-mono text-subtle">Engine Active</span>
          </div>
          <button
            onClick={onLogout}
            className="text-muted hover:text-coral text-sm font-body transition-colors px-3 py-1.5 rounded-lg hover:bg-coral/5"
          >
            Switch →
          </button>
        </div>
      </div>
    </motion.header>
  )
}
