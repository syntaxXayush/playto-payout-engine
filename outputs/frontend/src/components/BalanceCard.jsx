import { motion, useSpring, useTransform, animate } from 'framer-motion'
import { useEffect, useRef } from 'react'

function AnimatedNumber({ value }) {
  const ref = useRef(null)

  useEffect(() => {
    const node = ref.current
    if (!node) return
    const controls = animate(parseFloat(node.textContent) || 0, value, {
      duration: 0.8,
      ease: [0.22, 1, 0.36, 1],
      onUpdate(v) {
        node.textContent = v.toLocaleString('en-IN', {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        })
      },
    })
    return () => controls.stop()
  }, [value])

  return <span ref={ref}>0.00</span>
}

const COLOR_MAP = {
  emerald: {
    glow: 'shadow-glow-emerald',
    badge: 'bg-emerald/10 text-emerald border-emerald/20',
    bar: 'bg-emerald',
    icon: 'text-emerald',
    border: 'hover:border-emerald/30',
  },
  amber: {
    glow: '',
    badge: 'bg-amber/10 text-amber border-amber/20',
    bar: 'bg-amber',
    icon: 'text-amber',
    border: 'hover:border-amber/30',
  },
  accent: {
    glow: 'shadow-glow-accent',
    badge: 'bg-accent/10 text-accent-glow border-accent/20',
    bar: 'bg-accent',
    icon: 'text-accent-glow',
    border: 'hover:border-accent/30',
  },
}

export default function BalanceCard({ label, paise, color = 'emerald', icon }) {
  const inr = paise / 100
  const c = COLOR_MAP[color]

  return (
    <motion.div
      whileHover={{ y: -2 }}
      transition={{ duration: 0.2 }}
      className={`bg-surface border border-border rounded-2xl p-5 shadow-card ${c.glow} ${c.border} transition-all duration-300 relative overflow-hidden`}
    >
      {/* Subtle gradient */}
      <div className={`absolute top-0 right-0 w-32 h-32 rounded-full ${c.bar} opacity-[0.04] blur-3xl pointer-events-none`} />

      <div className="flex items-start justify-between mb-4 relative">
        <span className={`text-xs font-mono uppercase tracking-widest ${c.badge} border px-2 py-0.5 rounded-md`}>
          {label}
        </span>
        <span className={`text-lg ${c.icon} font-display font-bold`}>{icon}</span>
      </div>

      <div className="relative">
        <div className="flex items-baseline gap-1">
          <span className="text-subtle font-body text-sm">₹</span>
          <span className="text-white font-display font-bold text-3xl tracking-tight">
            <AnimatedNumber value={inr} />
          </span>
        </div>
        <p className="text-muted text-xs font-mono mt-1">
          {paise.toLocaleString('en-IN')} paise
        </p>
      </div>

      {/* Bottom bar */}
      <div className="mt-4 h-0.5 w-full bg-border rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: paise > 0 ? '60%' : '0%' }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1], delay: 0.3 }}
          className={`h-full ${c.bar} rounded-full`}
        />
      </div>
    </motion.div>
  )
}
