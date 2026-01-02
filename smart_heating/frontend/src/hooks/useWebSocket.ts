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
  const isIframe = globalThis.self !== globalThis.top
  const isiOS = /iPad|iPhone|iPod/.test(ua)
  const isAndroid = /Android/.test(ua)

  let browserName = 'Unknown'
  if (ua.includes('Chrome') && !ua.includes('Edg')) browserName = 'Chrome'
  else if (ua.includes('Safari') && !ua.includes('Chrome')) browserName = 'Safari'
  else if (ua.includes('Firefox')) browserName = 'Firefox'
  else if (ua.includes('Edg')) browserName = 'Edge'

  // Use userAgentData.platform when available (modern API) and fall back to userAgent string
  const platform = navigator.userAgent

  return {
    userAgent: ua,
    platform,
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
  const lastPingSentRef = useRef<number>(0) // Track when we last sent a ping
  const intentionalCloseRef = useRef(false)
  const optionsRef = useRef(options)
  const connectionStartTimeRef = useRef<number | null>(null)
  const metricsRef = useRef<WebSocketMetrics>(metrics)
  const iosHeartbeatRef = useRef<ReturnType<typeof setInterval> | undefined>(undefined)

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
      const params = new URLSearchParams(globalThis.location.search)
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

  // Helper: Try to get token from parent globalThis (iframe)
  const tryGetTokenFromParent = useCallback(
    (isiOS: boolean, isInIframe: boolean): string | null => {
      try {
        if (!globalThis.parent) {
          return null
        }

        const parentConnection = (globalThis.parent as any).hassConnection
        if (parentConnection?.auth?.data?.access_token) {
          console.log('[WebSocket] ✓ Using auth token from parent globalThis')
          return parentConnection.auth.data.access_token
        }

        if (isiOS && isInIframe) {
          console.warn(
            '[WebSocket] iOS iframe: Parent globalThis accessible but no auth token found',
          )
        }
      } catch {
        if (isiOS && isInIframe) {
          console.warn(
            '[WebSocket] iOS iframe: Cannot access parent globalThis (Safari privacy restriction)',
          )
        } else {
          console.debug('[WebSocket] Cannot access parent globalThis (expected in iframe)')
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
    const isInIframe = globalThis.self !== globalThis.top

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
      const token = getAuthToken()

      if (!token) {
        console.error('[WebSocket] ❌ No authentication token available!')
        setError('No authentication token available')
        ws.close()
        return
      }
      ws.send(JSON.stringify({ type: 'auth', access_token: token }))
    },
    [getAuthToken],
  )

  // Helper: Setup keepalive ping
  const setupKeepalivePing = useCallback(
    (ws: WebSocket) => {
      // iOS Safari needs very aggressive keepalive to prevent disconnections
      // Use 8s for iOS (Safari aggressively suspends connections)
      // Use 30s for other browsers
      const pingInterval = isIOS ? 8000 : 30000
      const pongTimeout = isIOS ? 12000 : 20000 // Shorter timeout for iOS

      if (pingIntervalRef.current) {
        clearInterval(pingIntervalRef.current)
      }

      // Reset ping/pong tracking on new connection
      lastPongRef.current = Date.now()
      lastPingSentRef.current = 0 // No ping sent yet

      console.log(
        `[WebSocket] Setting up keepalive with ${pingInterval / 1000}s interval (iOS: ${isIOS})`,
      )

      pingIntervalRef.current = setInterval(() => {
        if (ws.readyState !== WebSocket.OPEN) {
          console.warn('[WebSocket] Keepalive found connection not OPEN, clearing interval')
          return
        }

        // Only check for missing pong if we've sent a ping previously
        if (lastPingSentRef.current > 0) {
          const timeSinceLastPong = Date.now() - lastPongRef.current
          if (timeSinceLastPong > pongTimeout) {
            console.warn(
              `[WebSocket] No pong received in ${pongTimeout / 1000}s, forcing reconnect`,
            )
            ws.close()
            return
          }
        }

        // Send ping and track when it was sent
        try {
          ws.send(JSON.stringify({ id: messageIdRef.current++, type: 'ping' }))
          lastPingSentRef.current = Date.now()
          if (isIOS) {
            console.debug('[WebSocket] iOS ping sent')
          }
        } catch (err) {
          console.error('[WebSocket] Failed to send ping:', err)
          ws.close()
        }
      }, pingInterval)
    },
    [isIOS],
  )

  // Forward ref for connect function to break circular dependency
  const connectRef = useRef<(() => void) | null>(null)

  // Helper: Handle auth_ok message
  const handleAuthOk = useCallback(
    (ws: WebSocket) => {
      isAuthenticatedRef.current = true
      setIsConnected(true)
      setError(null)
      reconnectAttempts.current = 0
      wsFailureCount.current = 0

      if (transportMode === 'polling') {
        setTransportMode('websocket')
        stopPollingFallback()
      }

      updateMetrics({
        successfulConnections: metricsRef.current.successfulConnections + 1,
        lastConnectedAt: new Date().toISOString(),
      })

      optionsRef.current?.onConnect?.()
      setupKeepalivePing(ws)

      // iOS Safari: Additional heartbeat monitor to detect silent connection drops
      if (isIOS && !iosHeartbeatRef.current) {
        console.log('[WebSocket] iOS: Starting heartbeat monitor')
        iosHeartbeatRef.current = setInterval(() => {
          if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
            console.warn('[WebSocket] iOS: Heartbeat detected closed connection, reconnecting')
            if (iosHeartbeatRef.current) {
              clearInterval(iosHeartbeatRef.current)
              iosHeartbeatRef.current = undefined
            }
            reconnectAttempts.current = 0
            connectRef.current?.()
          } else {
            // Verify connection is actually working by checking last pong time
            const timeSinceLastPong = Date.now() - lastPongRef.current
            if (timeSinceLastPong > 25000) {
              console.warn(
                `[WebSocket] iOS: Heartbeat detected stale connection (${timeSinceLastPong}ms since pong)`,
              )
              wsRef.current.close()
            }
          }
        }, 20000) // Check every 20 seconds
      }

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
      const areasArray: Zone[] = Object.values(message.result.data.areas)
      optionsRef.current?.onZonesUpdate?.(areasArray)
      return
    }

    // Handle live device events
    if (message.result?.event === 'device_event' && message.result?.data) {
      try {
        const evt = message.result.data
        try {
          globalThis.dispatchEvent(new CustomEvent('smart_heating.device_event', { detail: evt }))
        } catch {
          ;(globalThis as any).smart_heating_device_event = evt
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
      // iOS Safari: Use faster reconnection schedule
      // First attempt: immediate (0ms)
      // Second attempt: 500ms
      // Third attempt: 1s
      // Fourth+ attempts: exponential backoff up to 10s max (not 30s)
      let delay: number
      if (isIOS) {
        if (reconnectAttempts.current === 0) {
          delay = 0 // Immediate first retry for iOS
        } else if (reconnectAttempts.current === 1) {
          delay = 500 // Quick second retry
        } else {
          delay = Math.min(1000 * Math.pow(1.5, reconnectAttempts.current - 2), 10000)
        }
        console.log(
          `[WebSocket] iOS: Scheduling reconnect attempt ${reconnectAttempts.current + 1} in ${delay}ms`,
        )
      } else {
        delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000)
      }

      reconnectTimeoutRef.current = setTimeout(() => {
        reconnectAttempts.current++
        connectFn()
      }, delay)
    },
    [isIOS],
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

    if (wsFailureCount.current >= maxWsFailuresBeforeFallback && transportMode !== 'polling') {
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
  const connect = useCallback((): void => {
    try {
      // Don't create new connection if one already exists and is open/connecting
      if (
        wsRef.current &&
        (wsRef.current.readyState === WebSocket.OPEN ||
          wsRef.current.readyState === WebSocket.CONNECTING)
      ) {
        return
      }

      // Track connection attempt
      updateMetrics({
        totalConnectionAttempts: metricsRef.current.totalConnectionAttempts + 1,
      })
      connectionStartTimeRef.current = Date.now()

      // Connect to Home Assistant WebSocket API
      const protocol = globalThis.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${globalThis.location.host}/api/websocket`

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
        if (isIOS) {
          console.error('[WebSocket] iOS: Connection error occurred')
          console.error('[WebSocket] iOS: This may be due to Safari suspending the connection')
          console.error('[WebSocket] iOS: readyState:', ws.readyState)
        }
        setError('WebSocket connection error')
        optionsRef.current?.onError?.('Connection error')
      }

      ws.onclose = event => {
        console.log('[WebSocket] Connection closed')
        if (isIOS) {
          console.log('[WebSocket] iOS: Connection closed')
          console.log('[WebSocket] iOS: Close code:', event.code)
          console.log('[WebSocket] iOS: Close reason:', event.reason || 'none')
          console.log('[WebSocket] iOS: Was clean:', event.wasClean)

          // Common iOS Safari close codes:
          // 1000: Normal closure
          // 1001: Going away (page unload/navigation)
          // 1006: Abnormal closure (no close frame - common when Safari suspends)
          if (event.code === 1006) {
            console.warn('[WebSocket] iOS: Abnormal closure (1006) - likely Safari suspension')
          }
        }

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

        // Clear iOS heartbeat monitor
        if (iosHeartbeatRef.current) {
          clearInterval(iosHeartbeatRef.current)
          iosHeartbeatRef.current = undefined
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

  // Assign to ref for use in callbacks that can't depend on connect directly
  connectRef.current = connect

  const disconnect = useCallback(() => {
    intentionalCloseRef.current = true

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
    }

    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current)
      pingIntervalRef.current = undefined
    }

    if (iosHeartbeatRef.current) {
      clearInterval(iosHeartbeatRef.current)
      iosHeartbeatRef.current = undefined
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
      // Assign a monotonic id from our messageIdRef using nullish coalescing assignment
      data.id ??= messageIdRef.current++

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
        if (isIOS) {
          console.log('[WebSocket] iOS: Page hidden, connection may be suspended by Safari')
        }
      } else {
        console.log('[WebSocket] Page visible - checking connection')
        // Reconnect if connection was lost while page was hidden
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          console.log('[WebSocket] Reconnecting after page became visible')
          reconnectAttempts.current = 0
          connect()
        } else if (isIOS) {
          // On iOS, even if connection appears open, verify with a ping
          console.log('[WebSocket] iOS: Sending verification ping after page visible')
          try {
            wsRef.current.send(JSON.stringify({ id: messageIdRef.current++, type: 'ping' }))
          } catch (err) {
            console.error('[WebSocket] iOS: Failed to send verification ping, reconnecting', err)
            reconnectAttempts.current = 0
            connect()
          }
        }
      }
    }

    // Handle globalThis focus (iOS Safari specific)
    const handleFocus = () => {
      console.log('[WebSocket] Window focused')
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.log('[WebSocket] Reconnecting after window focus')
        reconnectAttempts.current = 0
        connect()
      } else if (isIOS) {
        // iOS Safari: verify connection is actually working
        console.log('[WebSocket] iOS: Verifying connection after focus')
        try {
          wsRef.current.send(JSON.stringify({ id: messageIdRef.current++, type: 'ping' }))
        } catch (err) {
          console.error('[WebSocket] iOS: Connection verification failed, reconnecting', err)
          reconnectAttempts.current = 0
          connect()
        }
      }
    }

    // Handle pagehide event (iOS specific - fires before unload)
    const handlePageHide = (event: PageTransitionEvent) => {
      if (event.persisted) {
        // Page is being cached (bfcache) - keep connection alive
        console.log('[WebSocket] Page hidden (bfcache) - will reconnect when restored')
        if (isIOS) {
          // On iOS, clear the ping interval to reduce battery usage
          if (pingIntervalRef.current) {
            clearInterval(pingIntervalRef.current)
            pingIntervalRef.current = undefined
          }
        }
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
        intentionalCloseRef.current = false
        connect()
      }
    }

    // Handle online/offline events (network state changes - critical for iOS)
    const handleOnline = () => {
      console.log('[WebSocket] Network online')
      if (isIOS) {
        console.log('[WebSocket] iOS: Network online, reconnecting')
      }
      reconnectAttempts.current = 0
      connect()
    }

    const handleOffline = () => {
      console.log('[WebSocket] Network offline')
      if (wsRef.current) {
        wsRef.current.close()
      }
    }

    // iOS-specific: Handle resume event (when device wakes from sleep)
    const handleResume = () => {
      if (isIOS) {
        console.log('[WebSocket] iOS: Device resumed from sleep, verifying connection')
        if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
          reconnectAttempts.current = 0
          connect()
        }
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)
    globalThis.addEventListener('focus', handleFocus)
    globalThis.addEventListener('pagehide', handlePageHide as EventListener)
    globalThis.addEventListener('beforeunload', handleBeforeUnload)
    globalThis.addEventListener('pageshow', handlePageShow as EventListener)
    globalThis.addEventListener('online', handleOnline)
    globalThis.addEventListener('offline', handleOffline)
    globalThis.addEventListener('resume', handleResume)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
      globalThis.removeEventListener('focus', handleFocus)
      globalThis.removeEventListener('pagehide', handlePageHide as EventListener)
      globalThis.removeEventListener('beforeunload', handleBeforeUnload)
      globalThis.removeEventListener('pageshow', handlePageShow as EventListener)
      globalThis.removeEventListener('online', handleOnline)
      globalThis.removeEventListener('offline', handleOffline)
      globalThis.removeEventListener('resume', handleResume)
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
