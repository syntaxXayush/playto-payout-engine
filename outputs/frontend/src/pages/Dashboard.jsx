import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import { getMerchantDashboard, getLedger, getPayouts } from '../lib/api'
import BalanceCard from '../components/BalanceCard'
import PayoutForm from '../components/PayoutForm'
import PayoutTable from '../components/PayoutTable'
import LedgerFeed from '../components/LedgerFeed'
import Header from '../components/Header'

export default function Dashboard({ onLogout }) {
  const [activeTab, setActiveTab] = useState('payouts')
  const qc = useQueryClient()

  const { data: merchant, isLoading: mLoading } = useQuery({
    queryKey: ['merchant'],
    queryFn: () => getMerchantDashboard().then(r => r.data),
  })

  const { data: payouts = [] } = useQuery({
    queryKey: ['payouts'],
    queryFn: () => getPayouts().then(r => r.data),
  })

  const { data: ledger = [] } = useQuery({
    queryKey: ['ledger'],
    queryFn: () => getLedger().then(r => r.data),
  })

  const onPayoutSuccess = () => {
    qc.invalidateQueries(['merchant'])
    qc.invalidateQueries(['payouts'])
    qc.invalidateQueries(['ledger'])
  }

  if (mLoading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="w-6 h-6 border-2 border-accent border-t-transparent rounded-full animate-spin" />
    </div>
  )

  const TABS = [
    { id: 'payouts', label: 'Payouts' },
    { id: 'ledger',  label: 'Ledger' },
  ]

  return (
    <div className="min-h-screen">
      <Header merchant={merchant} onLogout={onLogout} />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 py-8 space-y-6">
        {/* Balance Cards */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="grid grid-cols-1 sm:grid-cols-3 gap-4"
        >
          <BalanceCard
            label="Available Balance"
            paise={merchant?.available_balance_paise || 0}
            color="emerald"
            icon="₹"
          />
          <BalanceCard
            label="Held Balance"
            paise={merchant?.held_balance_paise || 0}
            color="amber"
            icon="⏳"
          />
          <BalanceCard
            label="Total Received"
            paise={merchant?.total_credits_paise || 0}
            color="accent"
            icon="↑"
          />
        </motion.div>

        {/* Payout Form */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <PayoutForm
            bankAccounts={merchant?.bank_accounts || []}
            availablePaise={merchant?.available_balance_paise || 0}
            onSuccess={onPayoutSuccess}
          />
        </motion.div>

        {/* Tabs */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-surface border border-border rounded-2xl overflow-hidden"
        >
          <div className="flex border-b border-border">
            {TABS.map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`relative px-6 py-4 text-sm font-display font-semibold transition-colors
                  ${activeTab === tab.id ? 'text-white' : 'text-muted hover:text-subtle'}`}
              >
                {tab.label}
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                  />
                )}
              </button>
            ))}
            <div className="ml-auto flex items-center px-4">
              <span className="text-xs font-mono text-muted">
                Live · updates every 5s
              </span>
              <span className="ml-2 w-1.5 h-1.5 rounded-full bg-emerald animate-pulse" />
            </div>
          </div>

          <AnimatePresence mode="wait">
            {activeTab === 'payouts' ? (
              <motion.div key="payouts"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <PayoutTable payouts={payouts} />
              </motion.div>
            ) : (
              <motion.div key="ledger"
                initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
                <LedgerFeed entries={ledger} />
              </motion.div>
            )}
          </AnimatePresence>
        </motion.div>
      </main>
    </div>
  )
}
