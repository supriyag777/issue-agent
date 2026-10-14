import { CheckCircle2, CircleAlert, FileCode2, GitBranch, Loader2, ShieldCheck } from 'lucide-react'
import type { ReactNode } from 'react'

export function StatusPill({ children, tone = 'neutral' }: { children: ReactNode; tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'ai' }) {
  return <span className={`pill pill-${tone}`}><span className="pill-dot" />{children}</span>
}

export function MetricCard({ label, value, hint, icon: Icon }: { label: string; value: string | number; hint?: string; icon?: typeof GitBranch }) {
  return <div className="metric-card"><div className="metric-top"><span>{label}</span>{Icon && <Icon size={16} />}</div><strong>{value}</strong>{hint && <small>{hint}</small>}</div>
}

export function EmptyState({ icon: Icon = CircleAlert, title, children }: { icon?: typeof CircleAlert; title: string; children: ReactNode }) {
  return <div className="empty-state"><Icon size={22} /><div><strong>{title}</strong><p>{children}</p></div></div>
}

export function LoadingState({ label = 'Loading workspace' }: { label?: string }) {
  return <div className="loading-state"><Loader2 className="spin" size={18} />{label}</div>
}

export function SafetyRail({ status, detail }: { status: string; detail: string }) {
  return <aside className="safety-rail"><div className="eyebrow"><ShieldCheck size={14} /> SAFETY GATE</div><strong>{status}</strong><p>{detail}</p><div className="safety-rule"><CheckCircle2 size={15} /> Default branch protected</div><div className="safety-rule"><CheckCircle2 size={15} /> Human approval required</div><div className="safety-rule"><CheckCircle2 size={15} /> Draft PR only</div></aside>
}

export function CodePanel({ filename, language, code }: { filename: string; language: string; code: string }) {
  return <div className="code-panel"><div className="code-head"><span><FileCode2 size={14} />{filename}</span><span>{language}</span></div><pre><code>{code}</code></pre></div>
}

export function DiffViewer({ diff }: { diff: string }) {
  return <div className="diff-viewer">{diff ? diff.split('\n').map((line, index) => <div className={line.startsWith('+') && !line.startsWith('+++') ? 'diff-add' : line.startsWith('-') && !line.startsWith('---') ? 'diff-remove' : line.startsWith('@@') ? 'diff-hunk' : 'diff-line'} key={`${index}-${line}`}>{line || ' '}</div>) : <div className="diff-line">No diff has been generated yet.</div>}</div>
}
