import { motion, AnimatePresence } from 'framer-motion'
import { formatDistanceToNow } from 'date-fns'

const REF_LABELS = {
  customer_payment: 'Customer Payment',
  payout_hold:      'Payout Hold',
  payout_refund:    'Payout Refund',
  fee:              'Fee',
}

export default function LedgerFeed({ entries }) {
  if (!entries.length) return (
    <div className="py-20 text-center">
      <p className="text-muted font-body text-sm">No ledger entries yet</p>
    </div>
  )

  return (
    <div className="divide-y divide-border/40">
      <AnimatePresence initial={false}>
        {entries.map((e, i) => {
          const isCredit = e.entry_type === 'credit'
          return (
            <motion.div
              key={e.id}
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.03 }}
              className="flex items-center gap-4 px-5 py-4 hover:bg-surface-raised/40 transition-colors"
            >
              {/* Icon */}
              <div className={`w-9 h-9 rounded-xl flex items-center justify-center flex-shrink-0
                ${isCredit ? 'bg-emerald/10 text-emerald' : 'bg-coral/10 text-coral'}`}>
                <span className="text-sm font-bold">{isCredit ? '+' : '−'}</span>
              </div>

              {/* Description */}
              <div className="flex-1 min-w-0">
                <p className="text-white text-sm font-body truncate">
                  {e.description || REF_LABELS[e.reference_type] || e.reference_type}
                </p>
                <p className="text-muted text-xs font-mono mt-0.5">
                  {REF_LABELS[e.reference_type]} ·{' '}
                  {formatDistanceToNow(new Date(e.created_at), { addSuffix: true })}
                </p>
              </div>

              {/* Amount */}
              <div className="text-right flex-shrink-0">
                <p className={`font-display font-bold text-sm ${isCredit ? 'text-emerald' : 'text-coral'}`}>
                  {isCredit ? '+' : '−'}₹{(e.amount_paise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                </p>
                <p className="text-muted/50 text-xs font-mono mt-0.5">
                  {e.amount_paise.toLocaleString()} p
                </p>
              </div>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
