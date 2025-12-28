import axios from 'axios'

/**
 * Get HA auth token from various sources.
 * Shared by HTTP client and WebSocket transport.
 */
export const getAuthToken = (): string | null => {
  // Try URL parameter
  try {
    const params = new URLSearchParams(window.location.search)
    const urlToken = params.get('hassToken') || params.get('token')
    if (urlToken) return urlToken
  } catch {
    // Ignore URL parsing errors
  }

  // Try parent window (iframe context)
  try {
    if (window.parent && window.parent !== window) {
      const parentConnection = (window.parent as any).hassConnection
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
    // Ignore localStorage access errors
  }

  return null
}

/**
 * Pre-configured axios client with HA authentication.
 * Use this for all API requests to ensure proper auth headers.
 */
export const apiClient = axios.create({
  baseURL: '/api/smart_heating',
})

// Add auth token to all requests
apiClient.interceptors.request.use(config => {
  const token = getAuthToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
