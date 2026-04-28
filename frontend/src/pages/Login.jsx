import { useState } from 'react'
import { motion } from 'framer-motion'
import api, { setAuthToken } from '../lib/api'

const DEMO_ACCOUNTS = [
  { username: 'designhive', label: 'DesignHive Studio', sub: 'UI/UX Agency' },
  { username: 'devcraft',   label: 'DevCraft Labs',     sub: 'Software Studio' },
  { username: 'contentwave',label: 'ContentWave Agency',sub: 'Content Marketing' },
]

export default function Login({ onLogin }) {
  const [loading, setLoading] = useState(null)
  const [error, setError] = useState('')

  const loginAs = async (username) => {
    setLoading(username)
    setError('')
    try {
      const res = await api.post('/auth/token/', { username, password: 'playto@123' })
      setAuthToken(res.data.token)
      onLogin()
    } catch (e) {
      setError('Login failed. Make sure the backend is running and seeded.')
    } finally {
      setLoading(null)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-6 relative overflow-hidden">
      {/* Ambient glow */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full bg-accent/5 blur-[120px] pointer-events-none" />

      <motion.div
        initial={{ opacity: 0, y: 32 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
        className="w-full max-w-md relative z-10"
      >
        {/* Logo */}
        <div className="mb-10 text-center">
          <motion.div
            initial={{ scale: 0.8, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="inline-flex items-center gap-3 mb-4"
          >
            <div className="w-10 h-10 rounded-xl bg-accent flex items-center justify-center shadow-glow-accent">
              <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
              </svg>
            </div>
            <span className="font-display font-bold text-2xl text-white">Playto Pay</span>
          </motion.div>
          <p className="text-muted text-sm font-body">Payout Engine · Demo</p>
        </div>

        <div className="bg-surface border border-border rounded-2xl p-6 shadow-card">
          <p className="text-subtle text-xs font-mono uppercase tracking-widest mb-5">
            Select Demo Merchant
          </p>
          <div className="space-y-3">
            {DEMO_ACCOUNTS.map((acc, i) => (
              <motion.button
                key={acc.username}
                initial={{ opacity: 0, x: -16 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.2 + i * 0.08 }}
                onClick={() => loginAs(acc.username)}
                disabled={!!loading}
                className="w-full flex items-center justify-between p-4 rounded-xl
                  bg-surface-raised border border-border hover:border-accent/50
                  hover:bg-accent/5 transition-all duration-200 group disabled:opacity-50"
              >
                <div className="text-left">
                  <div className="font-display font-semibold text-white text-sm group-hover:text-accent-glow transition-colors">
                    {acc.label}
                  </div>
                  <div className="text-muted text-xs mt-0.5">{acc.sub}</div>
                </div>
                {loading === acc.username ? (
                  <div className="w-4 h-4 border-2 border-accent border-t-transparent rounded-full animate-spin" />
                ) : (
                  <svg className="w-4 h-4 text-muted group-hover:text-accent-glow transition-colors" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
              </motion.button>
            ))}
          </div>

          {error && (
            <motion.p initial={{ opacity: 0 }} animate={{ opacity: 1 }}
              className="mt-4 text-coral text-xs text-center font-mono"
            >
              {error}
            </motion.p>
          )}
        </div>

        <p className="text-center text-muted text-xs mt-6 font-mono">
          password: playto@123
        </p>
      </motion.div>
    </div>
  )
}
