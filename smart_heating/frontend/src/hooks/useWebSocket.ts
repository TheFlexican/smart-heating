import { useEffect, useRef, useState, useCallback } from 'react'
import { Zone } from '../types'
import { PollingTransport, TransportMode } from './transports'

interface WebSocketMessage {
  type: string
  id?: number
  data?: {
    areas?: Zone[]
    area?: Zone
    area_id?: string
  }
  error?: {
    code: string
    message: string
  }
  success?: boolean
  result?: any
  ha_version?: string
}

interface UseWebSocketOptions {
  onZonesUpdate?: (areas: Zone[]) => void
  onZoneUpdate?: (area: Zone) => void
  onZoneDelete?: (areaId: string) => void
  onConnect?: () => void
  onDisconnect?: () => void
  onError?: (error: string) => void
}

interface WebSocketMetrics {
  totalConnectionAttempts: number
  successfulConnections: number
  failedConnections: number
  unexpectedDisconnects: number
  averageConnectionDuration: number
  lastFailureReason: string
  lastConnectedAt: string | null
  lastDisconnectedAt: string | null
  connectionDurations: number[]
  deviceInfo: {
    userAgent: string
    platform: string
    isIframe: boolean
    isiOS: boolean
    isAndroid: boolean
    browserName: string
  }
}

// Helper to detect device info
const getDeviceInfo = () => {
  const ua = navigator.userAgent
  const isIframe = window.self !== window.top
  const isiOS = /iPad|iPhone|iPod/.test(ua)
  const isAndroid = /Android/.test(ua)

  let browserName = 'Unknown'
  if (ua.includes('Chrome') && !ua.includes('Edg')) browserName = 'Chrome'
  else if (ua.includes('Safari') && !ua.includes('Chrome')) browserName = 'Safari'
  else if (ua.includes('Firefox')) browserName = 'Firefox'
  else if (ua.includes('Edg')) browserName = 'Edge'

  return {
    userAgent: ua,
    platform: navigator.platform,
    isIframe,
    isiOS,
    isAndroid,
    browserName,
  }
}

// Helper to load metrics from localStorage
const loadMetrics = (): WebSocketMetrics => {
  try {
    const stored = localStorage.getItem('wsMetrics')
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (e) {
    console.error('Failed to load WebSocket metrics:', e)
  }

  return {
    totalConnectionAttempts: 0,
    successfulConnections: 0,
    failedConnections: 0,
    unexpectedDisconnects: 0,
    averageConnectionDuration: 0,
    lastFailureReason: '',
    lastConnectedAt: null,
    lastDisconnectedAt: null,
    connectionDurations: [],
    deviceInfo: getDeviceInfo(),
  }
}

// Helper to save metrics to localStorage
const saveMetrics = (metrics: WebSocketMetrics) => {
  try {
    localStorage.setItem('wsMetrics', JSON.stringify(metrics))
  } catch (e) {
    console.error('Failed to save WebSocket metrics:', e)
  }
}

export const useWebSocket = (options: UseWebSocketOptions = {}) => {
  const [isConnected, setIsConnected] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<WebSocketMetrics>(loadMetrics)
  const [transportMode, setTransportMode] = useState<TransportMode>('websocket')
  const wsRef = useRef<WebSocket | null>(null)
  const pollingTransportRef = useRef<PollingTransport | null>(null)
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined)
  const reconnectAttempts = useRef(0)
  const wsFailureCount = useRef(0)
  const maxReconnectAttempts = 10 // Increased for mobile
  const maxWsFailuresBeforeFallback = 3 // Fall back to polling after 3 WebSocket failures
  const wsRetryIntervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined)
  const messageIdRef = useRef(1)
  const isAuthenticatedRef = useRef(false)
  const pingIntervalRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined)
  const lastPongRef = useRef<number>(Date.now())
  const intentionalCloseRef = useRef(false)
  const optionsRef = useRef(options)
  const connectionStartTimeRef = useRef<number | null>(null)
  const metricsRef = useRef<WebSocketMetrics>(metrics)

  // Detect iOS for platform-specific optimizations
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)

  // Keep latest options and metrics in refs to avoid recreating callbacks
  useEffect(() => {
    optionsRef.current = options
  }, [options])

  useEffect(() => {
    metricsRef.current = metrics
  }, [metrics])

  // Update metrics and persist to localStorage
  const updateMetrics = useCallback((update: Partial<WebSocketMetrics>) => {
    setMetrics(prev => {
      const updated = { ...prev, ...update }

      // Recalculate average connection duration if durations changed
      if (update.connectionDurations) {
        const durations = updated.connectionDurations
        if (durations.length > 0) {
          updated.averageConnectionDuration =
            durations.reduce((a, b) => a + b, 0) / durations.length
        }
        // Keep only last 20 durations to avoid growing too large
        if (durations.length > 20) {
          updated.connectionDurations = durations.slice(-20)
        }
      }

      saveMetrics(updated)
      return updated
    })
  }, [])

  // Start polling transport as fallback
  const startPollingFallback = useCallback(() => {
    console.log('[WebSocket] Falling back to polling transport')
    setTransportMode('polling')
    setError('Using polling mode (limited connectivity)')

    // Clean up existing WebSocket
    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    // Create and start polling transport
    const polling = new PollingTransport({
      onConnect: () => {
        setIsConnected(true)
        optionsRef.current?.onConnect?.()
      },
      onDisconnect: () => {
        setIsConnected(false)
        optionsRef.current?.onDisconnect?.()
      },
      onZonesUpdate: areas => {
        optionsRef.current?.onZonesUpdate?.(areas)
      },
      onError: err => {
        console.error('[PollingTransport] Error:', err)
        optionsRef.current?.onError?.(err)
      },
    })

    pollingTransportRef.current = polling
    polling.connect()

    // Retry WebSocket every 60 seconds
    if (wsRetryIntervalRef.current) {
      clearInterval(wsRetryIntervalRef.current)
    }
    wsRetryIntervalRef.current = setInterval(() => {
      console.log('[WebSocket] Retrying WebSocket connection...')
      wsFailureCount.current = 0
      reconnectAttempts.current = 0
      connect()
    }, 60000)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Stop polling and clean up
  const stopPollingFallback = useCallback(() => {
    if (pollingTransportRef.current) {
      pollingTransportRef.current.disconnect()
      pollingTransportRef.current = null
    }
    if (wsRetryIntervalRef.current) {
      clearInterval(wsRetryIntervalRef.current)
      wsRetryIntervalRef.current = undefined
    }
  }, [])

  // Helper: Try to get token from meta tag
  const tryGetTokenFromMetaTag = useCallback((isiOS: boolean): string | null => {
    try {
      const metaTag = document.querySelector('meta[name="ha-auth-token"]')
      if (!metaTag) {
        if (isiOS) console.warn('[WebSocket] iOS: No auth meta tag found')
        return null
      }

      const metaToken = metaTag.getAttribute('content')
      if (metaToken) {
        console.log(`[WebSocket] ✓ Using auth token from meta tag (length: ${metaToken.length})`)
        console.log('[WebSocket] Meta tag token injection working - iOS compatible!')
        return metaToken
      }
    } catch (e) {
      console.error('[WebSocket] Error reading meta tag:', e)
    }
    return null
  }, [])

  // Helper: Try to get token from URL parameters
  const tryGetTokenFromUrl = useCallback((isiOS: boolean): string | null => {
    try {
      const params = new URLSearchParams(window.location.search)
      const urlToken = params.get('hassToken') || params.get('token')

      if (urlToken) {
        console.log(
          `[WebSocket] ✓ Using auth token from URL parameter (length: ${urlToken.length})`,
        )
        return urlToken
      }

      if (isiOS) {
        console.warn('[WebSocket] iOS: No token in URL parameters')
        console.log(
          '[WebSocket] Available URL params:',
          Array.from(params.keys()).join(', ') || 'none',
        )
      }
    } catch (e) {
      console.error('[WebSocket] Error reading URL parameters:', e)
    }
    return null
  }, [])

  // Helper: Try to get token from parent window (iframe)
  const tryGetTokenFromParent = useCallback(
    (isiOS: boolean, isInIframe: boolean): string | null => {
      try {
        if (!window.parent || window.parent === window) {
          return null
        }

        const parentConnection = (window.parent as any).hassConnection
        if (parentConnection?.auth?.data?.access_token) {
          console.log('[WebSocket] ✓ Using auth token from parent window')
          return parentConnection.auth.data.access_token
        }

        if (isiOS && isInIframe) {
          console.warn('[WebSocket] iOS iframe: Parent window accessible but no auth token found')
        }
      } catch {
        if (isiOS && isInIframe) {
          console.warn(
            '[WebSocket] iOS iframe: Cannot access parent window (Safari privacy restriction)',
          )
        } else {
          console.debug('[WebSocket] Cannot access parent window (expected in iframe)')
        }
      }
      return null
    },
    [],
  )

  // Helper: Try to get token from localStorage
  const tryGetTokenFromLocalStorage = useCallback((isiOS: boolean): string | null => {
    try {
      const haTokens = localStorage.getItem('hassTokens')
      if (!haTokens) {
        if (isiOS) console.warn('[WebSocket] iOS: No tokens in localStorage')
        return null
      }

      const tokens = JSON.parse(haTokens)
      if (tokens.access_token) {
        console.log('[WebSocket] ✓ Using auth token from localStorage')
        return tokens.access_token
      }
    } catch (e) {
      console.error('[WebSocket] Failed to parse HA tokens from localStorage:', e)
    }
    return null
  }, [])

  // Helper: Log token not found error
  const logTokenNotFound = useCallback((isiOS: boolean, isInIframe: boolean) => {
    if (isiOS && isInIframe) {
      console.error('[WebSocket] ❌ iOS iframe: No auth token found via any method!')
      console.error(
        '[WebSocket] iOS iframe: This usually means the panel URL is missing ?hassToken={%token%}',
      )
      console.error(
        '[WebSocket] iOS iframe: Please ensure the HA panel config includes the token parameter',
      )
    } else {
      console.warn('[WebSocket] No auth token found - WebSocket will be disabled')
    }
  }, [])

  const getAuthToken = useCallback((): string | null => {
    const isiOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
    const isInIframe = window.self !== window.top

    console.log(`[WebSocket] Device: ${isiOS ? 'iOS' : 'Other'} | iframe: ${isInIframe}`)
    console.log(`[WebSocket] Full URL: ${window.location.href}`)
    console.log(`[WebSocket] Search params: ${window.location.search || '(none)'}`)
    console.log(`[WebSocket] Hash: ${window.location.hash || '(none)'}`)

    if (isiOS) {
      console.log('[WebSocket] iOS-specific auth flow starting...')
    }

    // Try each method in order
    const token =
      tryGetTokenFromMetaTag(isiOS) ||
      tryGetTokenFromUrl(isiOS) ||
      tryGetTokenFromParent(isiOS, isInIframe) ||
      tryGetTokenFromLocalStorage(isiOS)

    if (!token) {
      logTokenNotFound(isiOS, isInIframe)
      return null
    }

    return token
  }, [
    tryGetTokenFromMetaTag,
    tryGetTokenFromUrl,
    tryGetTokenFromParent,
    tryGetTokenFromLocalStorage,
    logTokenNotFound,
  ])

  // Helper: Handle auth_required message
  const handleAuthRequired = useCallback(
    (ws: WebSocket) => {
      console.log('[WebSocket] Authentication required, getting token...')
      const token = getAuthToken()

      if (!token) {
        console.error('[WebSocket] ❌ No authentication token available!')
        setError('No authentication token available')
        ws.close()
        return
      }

      ws.send(JSON.stringify({ type: 'auth', access_token: token }))
      console.log('[WebSocket] Auth message sent')
    },
    [getAuthToken],
  )

  // Helper: Setup keepalive ping
  const setupKeepalivePing = useCallback(
    (ws: WebSocket) => {
      const pingInterval = isIOS ? 15000 : 30000
      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
      }
      lastPongRef.current = Date.now()

      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState !== WebSocket.OPEN) return

        const timeSinceLastPong = Date.now() - lastPongRef.current
        if (timeSinceLastPong > 20000) {
          console.warn('[WebSocket] No pong received in 20s, forcing reconnect')
          ws.close()
          return
        }

        ws.send(JSON.stringify({ id: messageIdRef.current++, type: 'ping' }))
      }, pingInterval)

      console.log(
        `[WebSocket] Keepalive ping interval set to ${pingInterval}ms ${isIOS ? '(iOS optimized)' : ''}`,
      )
    },
    [isIOS],
  )

  // Helper: Handle auth_ok message
  const handleAuthOk = useCallback(
    (ws: WebSocket) => {
      console.log('[WebSocket] ✓ Authenticated successfully!')
      isAuthenticatedRef.current = true
      setIsConnected(true)
      setError(null)
      reconnectAttempts.current = 0
      wsFailureCount.current = 0

      if (transportMode === 'polling') {
        console.log('[WebSocket] Switching from polling back to WebSocket')
        setTransportMode('websocket')
        stopPollingFallback()
      }

      updateMetrics({
        successfulConnections: metricsRef.current.successfulConnections + 1,
        lastConnectedAt: new Date().toISOString(),
      })

      optionsRef.current?.onConnect?.()
      setupKeepalivePing(ws)

      ws.send(JSON.stringify({ id: messageIdRef.current++, type: 'smart_heating/subscribe' }))
    },
    [transportMode, stopPollingFallback, updateMetrics, setupKeepalivePing],
  )

  // Helper: Handle auth_invalid message
  const handleAuthInvalid = useCallback(
    (ws: WebSocket, message: WebSocketMessage) => {
      console.error('Authentication failed:', message.error)
      setError('Authentication failed')

      updateMetrics({
        failedConnections: metricsRef.current.failedConnections + 1,
        lastFailureReason: `Authentication failed: ${message.error?.message || 'Unknown error'}`,
      })

      ws.close()
    },
    [updateMetrics],
  )

  // Helper: Handle result message
  const handleResultMessage = useCallback((message: WebSocketMessage) => {
    // Check if this is a subscription update
    if (message.result?.event === 'update' && message.result?.data?.areas) {
      const areasArray = Object.values(message.result.data.areas) as Zone[]
      optionsRef.current?.onZonesUpdate?.(areasArray)
      return
    }

    // Handle live device events
    if (message.result?.event === 'device_event' && message.result?.data) {
      try {
        const evt = message.result.data
        try {
          window.dispatchEvent(new CustomEvent('smart_heating.device_event', { detail: evt }))
        } catch {
          ;(window as any).smart_heating_device_event = evt
        }
      } catch (e) {
        console.error('Failed to handle device_event:', e)
      }
      return
    }

    if (!message.success) {
      console.error('Command failed:', message.error)
      setError(message.error?.message || 'Command failed')
    }
  }, [])

  // Helper: Handle event message
  const handleEventMessage = useCallback((message: WebSocketMessage) => {
    const event = message.result || message
    if (event.data?.areas) {
      optionsRef.current?.onZonesUpdate?.(event.data.areas)
    } else if (event.data?.area) {
      optionsRef.current?.onZoneUpdate?.(event.data.area)
    } else if (event.data?.area_id) {
      optionsRef.current?.onZoneDelete?.(event.data.area_id)
    }
  }, [])

  // Helper: Handle legacy messages
  const handleLegacyMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'pong':
        lastPongRef.current = Date.now()
        break
      case 'areas_updated':
        if (message.data?.areas) {
          optionsRef.current?.onZonesUpdate?.(message.data.areas)
        }
        break
      case 'area_updated':
        if (message.data?.area) {
          optionsRef.current?.onZoneUpdate?.(message.data.area)
        }
        break
      case 'area_deleted':
        if (message.data?.area_id) {
          optionsRef.current?.onZoneDelete?.(message.data.area_id)
        }
        break
    }
  }, [])

  // Helper: Record connection duration on disconnect
  const recordDisconnection = useCallback(
    (wasAuthenticated: boolean, wasIntentional: boolean) => {
      if (!connectionStartTimeRef.current) return

      const duration = Date.now() - connectionStartTimeRef.current

      if (wasAuthenticated && !wasIntentional) {
        updateMetrics({
          unexpectedDisconnects: metricsRef.current.unexpectedDisconnects + 1,
          lastDisconnectedAt: new Date().toISOString(),
          connectionDurations: [...metricsRef.current.connectionDurations, duration],
        })
      } else if (wasAuthenticated) {
        updateMetrics({
          lastDisconnectedAt: new Date().toISOString(),
          connectionDurations: [...metricsRef.current.connectionDurations, duration],
        })
      }

      connectionStartTimeRef.current = null
    },
    [updateMetrics],
  )

  // Helper: Schedule reconnection attempt with exponential backoff
  const scheduleReconnect = useCallback(
    (connectFn: () => void) => {
      const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
      console.log(
        `[WebSocket] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`,
      )

      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttempts.current++
        connectFn()
      }, delay)
    },
    [maxReconnectAttempts],
  )

  // Helper: Handle max reconnect attempts reached
  const handleMaxReconnectFailure = useCallback(() => {
    console.error('[WebSocket] Failed to connect after maximum attempts')
    setError('Failed to connect after multiple attempts')

    updateMetrics({
      failedConnections: metricsRef.current.failedConnections + 1,
      lastFailureReason: 'Failed to connect after maximum attempts',
    })

    wsFailureCount.current++
    console.log(
      `[WebSocket] Failure count: ${wsFailureCount.current}/${maxWsFailuresBeforeFallback}`,
    )

    if (wsFailureCount.current >= maxWsFailuresBeforeFallback && transportMode !== 'polling') {
      console.log('[WebSocket] Max failures reached, falling back to polling')
      startPollingFallback()
    }

    optionsRef.current?.onError?.('Connection failed')
  }, [updateMetrics, transportMode, startPollingFallback, maxWsFailuresBeforeFallback])

  // Helper: Handle WebSocket message
  const handleWebSocketMessage = useCallback(
    (ws: WebSocket, event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data)

        if (message.type === 'auth_required') {
          handleAuthRequired(ws)
          return
        }

        if (message.type === 'auth_ok') {
          handleAuthOk(ws)
          return
        }

        if (message.type === 'auth_invalid') {
          handleAuthInvalid(ws, message)
          return
        }

        if (message.type === 'result') {
          handleResultMessage(message)
          return
        }

        if (message.type === 'event') {
          handleEventMessage(message)
          return
        }

        handleLegacyMessage(message)
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err)
      }
    },
    [
      handleAuthRequired,
      handleAuthOk,
      handleAuthInvalid,
      handleResultMessage,
      handleEventMessage,
      handleLegacyMessage,
    ],
  )

  // `options` is accessed via `optionsRef` to avoid reconnect churn when the object identity changes
  const connect = useCallback(() => {
    try {
      // Don't create new connection if one already exists and is open/connecting
      if (
        wsRef.current &&
        (wsRef.current.readyState === WebSocket.OPEN ||
          wsRef.current.readyState === WebSocket.CONNECTING)
      ) {
        console.log('[WebSocket] Already connected or connecting')
        return
      }

      // Track connection attempt
      updateMetrics({
        totalConnectionAttempts: metricsRef.current.totalConnectionAttempts + 1,
      })
      connectionStartTimeRef.current = Date.now()

      // Connect to Home Assistant WebSocket API
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/api/websocket`

      console.log(`[WebSocket] Connecting to ${wsUrl}...`)
      const ws = new WebSocket(wsUrl)
      wsRef.current = ws
      isAuthenticatedRef.current = false

      ws.onopen = () => {
        console.log('[WebSocket] Connection opened')
      }

      ws.onmessage = event => {
        handleWebSocketMessage(ws, event)
      }

      ws.onerror = event => {
        console.error('[WebSocket] Error:', event)
        setError('WebSocket connection error')
        optionsRef.current?.onError?.('Connection error')
      }

      ws.onclose = () => {
        console.log('[WebSocket] Connection closed')
        setIsConnected(false)
        wsRef.current = null

        // Track connection duration and disconnection
        recordDisconnection(isAuthenticatedRef.current, intentionalCloseRef.current)
        optionsRef.current?.onDisconnect?.()

        // Clear ping interval
        if (pingIntervalRef.current) {
          clearInterval(pingIntervalRef.current)
          pingIntervalRef.current = undefined
        }

        // Don't reconnect if this was an intentional close
        if (intentionalCloseRef.current) {
          console.log('[WebSocket] Closed intentionally, not reconnecting')
          intentionalCloseRef.current = false
          return
        }

        // Attempt to reconnect with exponential backoff
        if (reconnectAttempts.current < maxReconnectAttempts) {
          scheduleReconnect(connect)
        } else {
          handleMaxReconnectFailure()
        }
      }
    } catch (err) {
      console.error('Failed to create WebSocket:', err)
      setError('Failed to create WebSocket connection')

      // Track error
      updateMetrics({
        failedConnections: metricsRef.current.failedConnections + 1,
        lastFailureReason: `Failed to create WebSocket: ${err instanceof Error ? err.message : 'Unknown error'}`,
      })
    }
  }, [
    handleWebSocketMessage,
    updateMetrics,
    recordDisconnection,
    scheduleReconnect,
    handleMaxReconnectFailure,
  ])

  const disconnect = useCallback(() => {
    console.log('[WebSocket] Disconnecting')
    intentionalCloseRef.current = true

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = undefined
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    // Also disconnect polling transport if active
    stopPollingFallback()

    setIsConnected(false)
  }, [stopPollingFallback])

  const send = (data: any) => {
    try {
      if (!data || typeof data !== 'object') return false

      // Ensure command has an id field expected by Home Assistant websocket handlers
      if (data.id == null) {
        // Assign a monotonic id from our messageIdRef
        data.id = messageIdRef.current++
      }

      if (
        wsRef.current &&
        (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === 1)
      ) {
        wsRef.current.send(JSON.stringify(data))
        return true
      }
      return false
    } catch (e) {
      console.error('[WebSocket] send error', e)
      return false
    }
  }

  useEffect(() => {
    connect()

    // Handle page visibility changes (critical for mobile browsers)
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log('[WebSocket] Page hidden')
      } else {
        console.log('[WebSocket] Page visible - checking connection')
        // Reconnect if connection was lost while page was hidden
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          console.log('[WebSocket] Reconnecting after page became visible')
          reconnectAttempts.current = 0
          connect()
        }
      }
    }

    // Handle window focus (iOS Safari specific)
    const handleFocus = () => {
      console.log('[WebSocket] Window focused - verifying connection')
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        reconnectAttempts.current = 0
        connect()
      }
    }

    // Handle pagehide event (iOS specific - fires before unload)
    const handlePageHide = (event: PageTransitionEvent) => {
      if (event.persisted) {
        // Page is being cached (bfcache) - keep connection alive
        console.log('[WebSocket] Page hidden (bfcache) - will reconnect when restored')
      } else {
        // Page is being unloaded - close connection gracefully
        console.log('[WebSocket] Page unloading - closing connection')
        intentionalCloseRef.current = true
        if (wsRef.current) {
          wsRef.current.close()
        }
      }
    }

    // Handle beforeunload event (graceful disconnect)
    const handleBeforeUnload = () => {
      console.log('[WebSocket] Page unloading - closing connection gracefully')
      intentionalCloseRef.current = true
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close()
      }
    }

    // Handle pageshow event (restore from bfcache)
    const handlePageShow = (event: PageTransitionEvent) => {
      if (event.persisted) {
        console.log('[WebSocket] Page restored from bfcache - reconnecting')
        reconnectAttempts.current = 0
        connect()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    window.addEventListener('focus', handleFocus)
    window.addEventListener('pagehide', handlePageHide as EventListener)
    window.addEventListener('beforeunload', handleBeforeUnload)
    window.addEventListener('pageshow', handlePageShow as EventListener)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      window.removeEventListener('focus', handleFocus)
      window.removeEventListener('pagehide', handlePageHide as EventListener)
      window.removeEventListener('beforeunload', handleBeforeUnload)
      window.removeEventListener('pageshow', handlePageShow as EventListener)
      disconnect()
    }
  }, [connect, disconnect])

  return {
    isConnected,
    error,
    send,
    reconnect: connect,
    metrics,
    transportMode,
  }
}
