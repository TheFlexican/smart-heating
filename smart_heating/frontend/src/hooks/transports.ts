import { Zone } from '../types'
import { getAuthToken, apiClient } from '../api/client'

export type TransportMode = 'websocket' | 'polling'

export interface TransportCallbacks {
  onConnect?: () => void
  onDisconnect?: () => void
  onZonesUpdate?: (areas: Zone[]) => void
  onZoneUpdate?: (area: Zone) => void
  onZoneDelete?: (areaId: string) => void
  onError?: (error: string) => void
}

export interface TransportAdapter {
  mode: TransportMode
  connect(): Promise<void>
  disconnect(): void
  send(data: any): boolean
  isConnected(): boolean
}

export class PollingTransport implements TransportAdapter {
  mode: TransportMode = 'polling'
  private intervalId: ReturnType<typeof setInterval> | null = null
  private connected: boolean = false
  private callbacks: TransportCallbacks

  constructor(callbacks: TransportCallbacks) {
    this.callbacks = callbacks
  }

  async connect(): Promise<void> {
    console.log('[PollingTransport] Starting polling (every 5 seconds)')
    this.connected = true
    this.callbacks.onConnect?.()

    // Poll immediately
    await this.poll()

    // Then poll every 5 seconds
    this.intervalId = setInterval(() => {
      this.poll()
    }, 5000)
  }

  disconnect(): void {
    console.log('[PollingTransport] Stopping polling')
    this.connected = false

    if (this.intervalId) {
      clearInterval(this.intervalId)
      this.intervalId = null
    }

    this.callbacks.onDisconnect?.()
  }

  send(data: any): boolean {
    console.log('[PollingTransport] Send not supported in polling mode:', data)
    return false
  }

  isConnected(): boolean {
    return this.connected
  }

  private async poll(): Promise<void> {
    try {
      // Use apiClient which includes auth headers
      const response = await apiClient.get('/areas')

      const data = response.data

      // Convert areas object to array if needed
      let areas: Zone[]
      if (Array.isArray(data)) {
        areas = data
      } else if (data.areas) {
        // If response has an areas property
        areas = Array.isArray(data.areas) ? data.areas : Object.values(data.areas)
      } else {
        // Assume data is an object with area IDs as keys
        areas = Object.values(data)
      }

      this.callbacks.onZonesUpdate?.(areas)
    } catch (error) {
      console.error('[PollingTransport] Poll error:', error)
      this.callbacks.onError?.(error instanceof Error ? error.message : 'Polling failed')
    }
  }
}

export class WebSocketTransport implements TransportAdapter {
  mode: TransportMode = 'websocket'
  private ws: WebSocket | null = null
  private callbacks: TransportCallbacks
  private messageId: number = 1
  private isAuthenticated: boolean = false
  private pingInterval: ReturnType<typeof setInterval> | null = null
  private lastPong: number = Date.now()
  private isIOS: boolean

  constructor(callbacks: TransportCallbacks) {
    this.callbacks = callbacks
    this.isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent)
  }

  async connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
      const wsUrl = `${protocol}//${window.location.host}/api/websocket`

      console.log(`[WebSocketTransport] Connecting to ${wsUrl}...`)
      this.ws = new WebSocket(wsUrl)

      this.ws.onopen = () => {
        console.log('[WebSocketTransport] Connection opened')
      }

      this.ws.onmessage = event => {
        try {
          const message = JSON.parse(event.data)

          if (message.type === 'auth_required') {
            // Use shared getAuthToken from api/client
            const token = getAuthToken()
            if (!token) {
              reject(new Error('No auth token available'))
              this.ws?.close()
              return
            }

            this.ws?.send(
              JSON.stringify({
                type: 'auth',
                access_token: token,
              }),
            )
            return
          }

          if (message.type === 'auth_ok') {
            console.log('[WebSocketTransport] Authenticated successfully')
            this.isAuthenticated = true
            this.callbacks.onConnect?.()
            this.startKeepalive()

            // Subscribe to events
            this.ws?.send(
              JSON.stringify({
                id: this.messageId++,
                type: 'smart_heating/subscribe',
              }),
            )

            resolve()
            return
          }

          if (message.type === 'auth_invalid') {
            reject(new Error('Authentication failed'))
            this.ws?.close()
            return
          }

          if (
            message.type === 'result' &&
            message.result?.event === 'update' &&
            message.result?.data?.areas
          ) {
            const areasData = message.result.data.areas
            const areasArray = Object.values(areasData) as Zone[]
            this.callbacks.onZonesUpdate?.(areasArray)
            return
          }

          if (message.type === 'pong') {
            this.lastPong = Date.now()
          }
        } catch (err) {
          console.error('[WebSocketTransport] Message parse error:', err)
        }
      }

      this.ws.onerror = event => {
        console.error('[WebSocketTransport] Error:', event)
        reject(new Error('WebSocket error'))
      }

      this.ws.onclose = () => {
        console.log('[WebSocketTransport] Connection closed')
        this.isAuthenticated = false
        this.stopKeepalive()
        this.callbacks.onDisconnect?.()
      }
    })
  }

  disconnect(): void {
    console.log('[WebSocketTransport] Disconnecting')
    this.stopKeepalive()

    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any): boolean {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
      return true
    }
    return false
  }

  isConnected(): boolean {
    return this.isAuthenticated && this.ws?.readyState === WebSocket.OPEN
  }

  private startKeepalive(): void {
    const pingInterval = this.isIOS ? 15000 : 30000
    this.lastPong = Date.now()

    this.pingInterval = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        // Check heartbeat
        const timeSinceLastPong = Date.now() - this.lastPong
        if (timeSinceLastPong > 20000) {
          console.warn('[WebSocketTransport] No pong in 20s, connection dead')
          this.ws.close()
          return
        }

        this.ws.send(
          JSON.stringify({
            id: this.messageId++,
            type: 'ping',
          }),
        )
      }
    }, pingInterval)
  }

  private stopKeepalive(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval)
      this.pingInterval = null
    }
  }
}
