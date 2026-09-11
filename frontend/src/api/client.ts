import { clearToken, getToken } from "@/lib/auth"

const API_BASE = "/api/v1"

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (response.status === 401) {
    clearToken()
    if (!window.location.pathname.startsWith("/login")) {
      window.location.href = "/login"
    }
    throw new ApiError(401, "Unauthorized")
  }

  if (!response.ok) {
    let message = response.statusText
    try {
      const body = await response.json()
      message = body.detail ?? body.message ?? message
    } catch {
      // ignore parse errors
    }
    throw new ApiError(response.status, String(message))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)

  if (token) {
    headers.set("Authorization", `Bearer ${token}`)
  }

  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json")
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  })

  return handleResponse<T>(response)
}

export function getApiBase(): string {
  return API_BASE
}
