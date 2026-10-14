import { Bot, CircleUserRound, GitBranch, Github, LayoutDashboard, LogOut, Settings, ShieldCheck, Sparkles } from 'lucide-react'
import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { GuidePanel } from '../components/GuidePanel'

const nav = [{ to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard }, { to: '/repositories', label: 'Repositories', icon: Github }, { to: '/settings', label: 'Settings', icon: Settings }]

export function AppShell() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()
  return <div className="app-shell"><aside className="sidebar"><div className="brand"><div className="brand-mark"><Bot size={18} /></div><div><strong>ISSUE AGENT</strong><span>AI code review control room</span></div></div><div className="workspace-label">WORKSPACE</div><nav>{nav.map(({ to, label, icon: Icon }) => <NavLink key={to} to={to} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}><Icon size={17} />{label}</NavLink>)}</nav><div className="sidebar-spacer" /><div className="sidebar-footer"><div className="provider-line"><span className="status-dot live" />API services online</div><button className="nav-link logout" onClick={async () => { await signOut(); navigate('/') }}><LogOut size={16} />Sign out</button></div></aside><main className="main-shell"><header className="topbar"><div className="breadcrumbs"><Sparkles size={15} />REVIEW WORKSPACE <span>/</span> SAFE BY DEFAULT</div><div className="user-chip"><CircleUserRound size={16} /><span>{user?.name || 'Operator'}</span></div></header><div className="page-content"><Outlet /></div><GuidePanel /></main></div>
}
