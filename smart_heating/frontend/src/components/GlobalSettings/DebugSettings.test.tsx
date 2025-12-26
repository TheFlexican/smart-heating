import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect } from 'vitest'
import { DebugSettings } from './DebugSettings'

describe('DebugSettings', () => {
  it('shows info when no metrics', () => {
    render(<DebugSettings />)
    expect(screen.getByText(/WebSocket metrics not available/i)).toBeInTheDocument()
  })

  it('renders metrics when provided', () => {
    const metrics = {
      totalConnectionAttempts: 2,
      successfulConnections: 1,
      failedConnections: 1,
      unexpectedDisconnects: 0,
      averageConnectionDuration: 1000,
      lastFailureReason: 'timeout',
      lastConnectedAt: new Date().toISOString(),
      lastDisconnectedAt: null,
      connectionDurations: [1000],
      deviceInfo: {
        userAgent: 'ua',
        platform: 'Web',
        isIframe: false,
        isiOS: false,
        isAndroid: false,
        browserName: 'Chrome',
      },
    }

    render(<DebugSettings wsMetrics={metrics as any} />)
    expect(screen.getByText(/Device Information/i)).toBeInTheDocument()
    expect(screen.getByText(/Connection Statistics/i)).toBeInTheDocument()
  })
})
