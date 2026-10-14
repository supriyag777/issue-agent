import type { Analysis, AuthResponse, Change, Dashboard, Issue, Repository, User } from '../types'

const API = import.meta.env.VITE_API_BASE || '/api/v1'

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) { super(message); this.status = status }
}

export type GuideAnswer = { answer: string; provider_mode: string; suggestions: string[] }

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('issueagent_token')
  const headers = new Headers(options.headers)
  headers.set('Content-Type', 'application/json')
  if (token) headers.set('Authorization', `Bearer ${token}`)
  const response = await fetch(`${API}${path}`, { ...options, headers })
  const body = await response.json().catch(() => ({}))
  if (!response.ok) {
    const detail = typeof body.detail === 'string' ? body.detail : body.detail?.message || 'Request failed'
    throw new ApiError(detail, response.status)
  }
  return body as T
}

export const api = {
  register: (payload: { name: string; email: string; password: string }) => request<AuthResponse>('/auth/register', { method: 'POST', body: JSON.stringify(payload) }),
  login: (payload: { email: string; password: string }) => request<AuthResponse>('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),
  me: () => request<User>('/auth/me'),
  logout: () => request<{ status: string }>('/auth/logout', { method: 'POST' }),
  repositories: () => request<Repository[]>('/repositories'),
  connectRepository: (payload: { github_token?: string; owner: string; name: string; demo_mode: boolean }) => request<Repository>('/repositories/connect', { method: 'POST', body: JSON.stringify(payload) }),
  repository: (id: number) => request<Repository>(`/repositories/${id}`),
  dashboard: (id: number) => request<Dashboard>(`/repositories/${id}/dashboard`),
  issues: (id: number, params: { state: string; search: string }) => request<Issue[]>(`/repositories/${id}/issues?state=${encodeURIComponent(params.state)}&search=${encodeURIComponent(params.search)}`),
  issue: (id: number) => request<Issue>(`/issues/${id}`),
  analyze: (issueId: number) => request<Analysis>(`/issues/${issueId}/analyze`, { method: 'POST' }),
  analysis: (id: number) => request<Analysis>(`/analyses/${id}`),
  change: (analysisId: number) => request<Change>(`/analyses/${analysisId}/change`),
  approve: (changeId: number, approved: boolean) => request<Change>(`/changes/${changeId}/approve`, { method: 'POST', body: JSON.stringify({ approved }) }),
  branch: (changeId: number) => request<Change>(`/changes/${changeId}/branch`, { method: 'POST' }),
  validate: (changeId: number) => request<{ status: string; passed: boolean; output: string }>(`/changes/${changeId}/validate`, { method: 'POST' }),
  commit: (changeId: number) => request<Change>(`/changes/${changeId}/commit`, { method: 'POST' }),
  draftPr: (changeId: number) => request<Change>(`/changes/${changeId}/draft-pr`, { method: 'POST' }),
  guideContext: (path: string) => request<GuideAnswer>(`/guide/context?path=${encodeURIComponent(path)}`),
  askGuide: (question: string, path: string) => request<GuideAnswer>('/guide/ask', { method: 'POST', body: JSON.stringify({ question, path }) }),
}
