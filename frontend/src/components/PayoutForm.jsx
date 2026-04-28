import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { createPayout } from '../lib/api'

function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16)
  })
}

export default function PayoutForm({ bankAccounts, availablePaise, onSuccess }) {
  const [amountINR, setAmountINR] = useState('')
  const [bankId, setBankId] = useState(bankAccounts[0]?.id || '')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null) // { type: 'success'|'error', message }
  const [idempKey, setIdempKey] = useState(generateUUID())

  const amountPaise = Math.round(parseFloat(amountINR || 0) * 100)
  const isValid = amountPaise >= 100 && amountPaise <= availablePaise && bankId

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!isValid) return
    setLoading(true)
    setResult(null)
    try {
      await createPayout({ amount_paise: amountPaise, bank_account_id: bankId }, idempKey)
      setResult({ type: 'success', message: `Payout of ₹${amountINR} queued successfully` })
      setAmountINR('')
      setIdempKey(generateUUID()) // rotate key for next request
      onSuccess()
    } catch (err) {
      const msg = err.response?.data?.error || 'Payout request failed'
      const avail = err.response?.data?.available_paise
      setResult({
        type: 'error',
        message: avail ? `${msg} — available: ₹${(avail/100).toFixed(2)}` : msg
      })
    } finally {
      setLoading(false)
    }
  }

  const percent = availablePaise > 0 ? Math.min((amountPaise / availablePaise) * 100, 100) : 0

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-surface border border-border rounded-2xl p-6 shadow-card relative overflow-hidden"
    >
      {/* Ambient glow top-right */}
      <div className="absolute -top-16 -right-16 w-48 h-48 rounded-full bg-accent/5 blur-3xl pointer-events-none" />

      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="font-display font-bold text-white text-lg">Request Payout</h2>
          <p className="text-muted text-xs font-body mt-0.5">
            Funds settle to your Indian bank account
          </p>
        </div>
        <div className="text-right">
          <p className="text-xs font-mono text-muted">Available</p>
          <p className="font-display font-bold text-emerald text-xl">
            ₹{(availablePaise / 100).toLocaleString('en-IN', { minimumFractionDigits: 2 })}
          </p>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Amount input */}
        <div>
          <label className="text-xs font-mono text-muted uppercase tracking-wider mb-2 block">
            Amount (INR)
          </label>
          <div className="relative">
            <span className="absolute left-4 top-1/2 -translate-y-1/2 text-subtle font-display font-bold text-lg">₹</span>
            <input
              type="number"
              min="1"
              step="0.01"
              value={amountINR}
              onChange={e => setAmountINR(e.target.value)}
              placeholder="0.00"
              className="w-full bg-ink border border-border rounded-xl pl-9 pr-4 py-3.5
                text-white font-display font-semibold text-lg placeholder:text-muted/40
                focus:outline-none focus:border-accent/60 focus:ring-1 focus:ring-accent/20
                transition-all duration-200"
            />
          </div>
          {/* Progress bar */}
          <div className="mt-2 h-1 bg-border rounded-full overflow-hidden">
            <motion.div
              animate={{ width: `${percent}%` }}
              transition={{ duration: 0.3 }}
              className={`h-full rounded-full transition-colors ${
                percent > 90 ? 'bg-coral' : percent > 60 ? 'bg-amber' : 'bg-emerald'
              }`}
            />
          </div>
          {amountPaise > 0 && (
            <p className="text-xs font-mono text-muted mt-1">
              {amountPaise.toLocaleString('en-IN')} paise · {percent.toFixed(1)}% of available
            </p>
          )}
        </div>

        {/* Bank account select */}
        <div>
          <label className="text-xs font-mono text-muted uppercase tracking-wider mb-2 block">
            Bank Account
          </label>
          <select
            value={bankId}
            onChange={e => setBankId(e.target.value)}
            className="w-full bg-ink border border-border rounded-xl px-4 py-3.5
              text-white font-body focus:outline-none focus:border-accent/60
              focus:ring-1 focus:ring-accent/20 transition-all duration-200"
          >
            {bankAccounts.map(ba => (
              <option key={ba.id} value={ba.id}>
                {ba.bank_name} •••• {ba.account_number.slice(-4)} — {ba.account_holder_name}
              </option>
            ))}
          </select>
        </div>

        {/* Idempotency key display */}
        <div className="flex items-center gap-2 p-3 bg-ink rounded-xl border border-border/50">
          <svg className="w-3 h-3 text-muted flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <span className="text-muted text-xs font-mono truncate flex-1">
            {idempKey}
          </span>
          <span className="text-muted/50 text-xs font-mono flex-shrink-0">idempotency key</span>
        </div>

        <motion.button
          type="submit"
          disabled={!isValid || loading}
          whileTap={{ scale: 0.98 }}
          className={`w-full py-3.5 rounded-xl font-display font-semibold text-sm
            transition-all duration-200 relative overflow-hidden
            ${isValid && !loading
              ? 'bg-accent text-white shadow-glow-accent hover:bg-accent-glow cursor-pointer'
              : 'bg-surface-raised text-muted cursor-not-allowed'
            }`}
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              Processing...
            </span>
          ) : 'Request Payout →'}
        </motion.button>
      </form>

      <AnimatePresence>
        {result && (
          <motion.div
            initial={{ opacity: 0, y: 8, height: 0 }}
            animate={{ opacity: 1, y: 0, height: 'auto' }}
            exit={{ opacity: 0, y: -8, height: 0 }}
            className={`mt-4 px-4 py-3 rounded-xl border text-sm font-body
              ${result.type === 'success'
                ? 'bg-emerald/5 border-emerald/20 text-emerald'
                : 'bg-coral/5 border-coral/20 text-coral'
              }`}
          >
            {result.type === 'success' ? '✓ ' : '✗ '}{result.message}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
