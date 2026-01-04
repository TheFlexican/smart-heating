import axios from 'axios'

/**
 * Get HA auth token from various sources.
 * Shared by HTTP client and WebSocket transport.
 */
export const getAuthToken = (): string | null => {
  // Try URL parameter
  try {
    const params = new URLSearchParams(globalThis.location.search)
    const urlToken = params.get('hassToken') || params.get('token')
    if (urlToken) return urlToken
  } catch {
    // Ignore URL parsing errors
  }

  // Try parent window (iframe context)
  try {
    if ((globalThis as any).parent && (globalThis as any).parent !== globalThis) {
      const parentConnection = (globalThis as any).parent?.hassConnection
      if (parentConnection?.auth?.data?.access_token) {
        return parentConnection.auth.data.access_token
      }
    }
  } catch {
    // Ignore iframe access errors
  }

  // Try localStorage
  try {
    const haTokens = localStorage.getItem('hassTokens')
    if (haTokens) {
      const tokens = JSON.parse(haTokens)
      if (tokens.access_token) {
        return tokens.access_token
      }
    }
  } catch {
    // Ignore localStorage errors
  }

  return null
}

/**
 * Pre-configured axios client with HA authentication.
 * Use this for all API requests to ensure proper auth headers.
 */
export const apiClient = axios.create({
  baseURL: '/api/smart_heating',
  withCredentials: true, // Send cookies for session-based auth
})

// Add auth token to requests if available (for non-session auth contexts)
apiClient.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  // If no token, rely on session cookies (mobile app)
  return config
})

// Handle 401 errors by refreshing token and retrying once
apiClient.interceptors.response.use(
  response => response,
  async error => {
    const originalRequest = error.config

    // If 401 and haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const requestUrl = originalRequest.url || 'unknown'
      console.warn(`[API] 401 Unauthorized on ${requestUrl} - attempting to refresh token`)

      // Small delay to allow parent window to refresh token
      await new Promise(resolve => setTimeout(resolve, 100))

      // Get fresh token (parent window in HA iframe should have refreshed it)
      const newToken = getAuthToken()

      if (newToken) {
        console.log(`[API] Got fresh token (length: ${newToken.length}), retrying request`)

        // Update authorization header with fresh token
        originalRequest.headers.Authorization = `Bearer ${newToken}`

        // Retry original request
        try {
          return await apiClient(originalRequest)
        } catch (retryError: any) {
          if (retryError.response?.status === 401) {
            console.error('[API] Still 401 after retry - token may be genuinely invalid')
            console.error(
              '[API] User may need to reload page or re-authenticate with Home Assistant',
            )
          }
          throw retryError
        }
      } else {
        console.error('[API] No token available after 401 - cannot retry request')
        console.error('[API] Possible causes:')
        console.error('  1. Not running in Home Assistant iframe')
        console.error('  2. Parent window token expired')
        console.error('  3. No token in localStorage')
        console.error('[API] User should reload the page or re-authenticate')
      }
    }

    // Log other error types for debugging
    if (error.response?.status && error.response.status !== 401) {
      console.warn(
        `[API] Request failed with status ${error.response.status}: ${originalRequest.url}`,
      )
    }

    return Promise.reject(error)
  },
)
