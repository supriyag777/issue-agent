import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from 'react'
import { api } from '../services/api'
import type { User } from '../types'

type AuthContextValue = { user: User | null; loading: boolean; signIn: (email: string, password: string) => Promise<void>; signUp: (name: string, email: string, password: string) => Promise<void>; signOut: () => Promise<void> }
const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  useEffect(() => {
    const token = localStorage.getItem('issueagent_token')
    if (!token) { setLoading(false); return }
    api.me().then(setUser).catch(() => { localStorage.removeItem('issueagent_token') }).finally(() => setLoading(false))
  }, [])
  const value = useMemo<AuthContextValue>(() => ({
    user,
    loading,
    async signIn(email, password) { const response = await api.login({ email, password }); localStorage.setItem('issueagent_token', response.access_token); setUser(response.user) },
    async signUp(name, email, password) { const response = await api.register({ name, email, password }); localStorage.setItem('issueagent_token', response.access_token); setUser(response.user) },
    async signOut() { try { await api.logout() } finally { localStorage.removeItem('issueagent_token'); setUser(null) } },
  }), [user, loading])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used inside AuthProvider')
  return context
}
