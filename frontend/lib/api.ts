const API_BASE = process.env.NEXT_PUBLIC_API_URL || '/api/v1'

interface RequestOptions {
  method?: string
  body?: unknown
  token?: string
}

async function request(path: string, options: RequestOptions = {}) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (options.token) {
    headers['Authorization'] = `Bearer ${options.token}`
  }

  const res = await fetch(`${API_BASE}${path}`, {
    method: options.method || 'GET',
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined,
  })

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(error.detail || 'API Error')
  }

  if (res.status === 204) return null
  return res.json()
}

// ── Auth ────────────────────────────────────────────────────────────

export function login(email: string, password: string) {
  return request('/auth/login', { method: 'POST', body: { email, password } })
}

export function register(email: string, password: string, displayName: string, tenantName: string, tenantSlug: string) {
  return request('/auth/register', {
    method: 'POST',
    body: { email, password, display_name: displayName, tenant_name: tenantName, tenant_slug: tenantSlug },
  })
}

// ── Personas ────────────────────────────────────────────────────────

export function listPersonas(token: string) {
  return request('/personas', { token })
}

export function createPersona(token: string, data: Record<string, unknown>) {
  return request('/personas', { method: 'POST', body: data, token })
}

// ── Contents ────────────────────────────────────────────────────────

export function listContents(token: string, params?: Record<string, string>) {
  const query = params ? '?' + new URLSearchParams(params).toString() : ''
  return request(`/contents${query}`, { token })
}

export function createContent(token: string, data: Record<string, unknown>) {
  return request('/contents', { method: 'POST', body: data, token })
}

export function approveContent(token: string, id: string, finalContent?: string) {
  return request(`/contents/${id}/approve`, { method: 'POST', body: { final_content: finalContent }, token })
}