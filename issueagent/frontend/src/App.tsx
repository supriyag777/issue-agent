import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Navigate, Route, Routes } from 'react-router-dom'
import { useAuth } from './hooks/useAuth'
import { AppShell } from './layouts/AppShell'
import { DashboardPage, HomePage, LoginPage, RegisterPage, RepositoriesPage, RepositoryPage, IssuePage, AnalysisPage, SettingsPage } from './pages'

const queryClient = new QueryClient({ defaultOptions: { queries: { staleTime: 20_000, retry: 1 } } })

function Protected() {
  const { user, loading } = useAuth()
  if (loading) return <div className="boot-screen"><div className="brand-mark">AI</div><span>Loading secure workspace…</span></div>
  return user ? <AppShell /> : <Navigate to="/login" replace />
}

export default function App() {
  return <QueryClientProvider client={queryClient}><Routes><Route path="/" element={<HomePage />} /><Route path="/login" element={<LoginPage />} /><Route path="/register" element={<RegisterPage />} /><Route element={<Protected />}><Route path="/dashboard" element={<DashboardPage />} /><Route path="/repositories" element={<RepositoriesPage />} /><Route path="/repositories/:id" element={<RepositoryPage />} /><Route path="/issues/:id" element={<IssuePage />} /><Route path="/analysis/:id" element={<AnalysisPage />} /><Route path="/settings" element={<SettingsPage />} /></Route><Route path="*" element={<Navigate to="/" replace />} /></Routes></QueryClientProvider>
}
