import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({ baseURL: BASE_URL })

api.interceptors.request.use(config => {
  const token = localStorage.getItem('auth_token')
  if (token) config.headers.Authorization = `Token ${token}`
  return config
})

export const setAuthToken = (token) => localStorage.setItem('auth_token', token)
export const getAuthToken = () => localStorage.getItem('auth_token')
export const clearAuthToken = () => localStorage.removeItem('auth_token')

export const getMerchants = () => api.get('/merchants/')
export const getMerchantDashboard = () => api.get('/merchants/me/')
export const getLedger = () => api.get('/ledger/')
export const getPayouts = () => api.get('/payouts/')
export const createPayout = (data, idempotencyKey) =>
  api.post('/payouts/', data, { headers: { 'Idempotency-Key': idempotencyKey } })

export default api
