import { useState, useEffect } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { motion, AnimatePresence } from 'framer-motion'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import { getAuthToken } from './lib/api'

const queryClient = new QueryClient({
  defaultOptions: { queries: { refetchInterval: 5000, staleTime: 2000 } }
})

export default function App() {
  const [authed, setAuthed] = useState(!!getAuthToken())

  return (
    <QueryClientProvider client={queryClient}>
      <div className="noise-bg min-h-screen bg-ink">
        <AnimatePresence mode="wait">
          {authed ? (
            <motion.div key="dashboard"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Dashboard onLogout={() => { localStorage.clear(); setAuthed(false) }} />
            </motion.div>
          ) : (
            <motion.div key="login"
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              <Login onLogin={() => setAuthed(true)} />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </QueryClientProvider>
  )
}
