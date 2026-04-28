import { motion, AnimatePresence } from 'framer-motion'
import { formatDistanceToNow } from 'date-fns'

const STATUS_CONFIG = {
  pending: {
    label: 'Pending',
    dot: 'bg-amber animate-pulse',
    badge: 'bg-amber/10 text-amber border-amber/20',
    icon: '⏳',
  },
  processing: {
    label: 'Processing',
    dot: 'bg-accent animate-pulse',
    badge: 'bg-accent/10 text-accent-glow border-accent/20',
    icon: '⚡',
  },
  completed: {
    label: 'Completed',
    dot: 'bg-emerald',
    badge: 'bg-emerald/10 text-emerald border-emerald/20',
    icon: '✓',
  },
  failed: {
    label: 'Failed',
    dot: 'bg-coral',
    badge: 'bg-coral/10 text-coral border-coral/20',
    icon: '✗',
  },
}

function StatusBadge({ status }) {
  const c = STATUS_CONFIG[status] || STATUS_CONFIG.pending
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-xs font-mono border ${c.badge}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {c.label}
    </span>
  )
}

export default function PayoutTable({ payouts }) {
  if (!payouts.length) return (
    <div className="py-20 text-center">
      <p className="text-muted font-body text-sm">No payouts yet</p>
      <p className="text-muted/50 font-mono text-xs mt-1">Request your first payout above</p>
    </div>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead>
          <tr className="border-b border-border">
            {['Amount', 'Status', 'Bank Account', 'Retries', 'Created'].map(h => (
              <th key={h} className="px-5 py-3 text-left text-xs font-mono text-muted uppercase tracking-widest">
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          <AnimatePresence initial={false}>
            {payouts.map((p, i) => (
              <motion.tr
                key={p.id}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0 }}
                transition={{ delay: i * 0.04 }}
                className="border-b border-border/50 hover:bg-surface-raised/50 transition-colors group"
              >
                <td className="px-5 py-4">
                  <div className="font-display font-bold text-white text-sm">
                    ₹{(p.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                  </div>
                  <div className="text-muted/60 text-xs font-mono mt-0.5">
                    {p.amount_paise.toLocaleString()} p
                  </div>
                </td>
                <td className="px-5 py-4">
                  <StatusBadge status={p.status} />
                  {p.failure_reason && (
                    <div className="text-coral/70 text-xs font-mono mt-1 max-w-[180px] truncate" title={p.failure_reason}>
                      {p.failure_reason}
                    </div>
                  )}
                </td>
                <td className="px-5 py-4 text-subtle text-xs font-mono">
                  {p.bank_account_display || '—'}
                </td>
                <td className="px-5 py-4">
                  {p.retry_count > 0 ? (
                    <span className="text-amber text-xs font-mono">{p.retry_count}×</span>
                  ) : (
                    <span className="text-muted/40 text-xs font-mono">—</span>
                  )}
                </td>
                <td className="px-5 py-4 text-muted text-xs font-mono">
                  {formatDistanceToNow(new Date(p.created_at), { addSuffix: true })}
                </td>
              </motion.tr>
            ))}
          </AnimatePresence>
        </tbody>
      </table>
    </div>
  )
}
