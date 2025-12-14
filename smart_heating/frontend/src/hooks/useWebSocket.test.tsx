import React from 'react'
import { render, screen, act } from '@testing-library/react'
import { vi } from 'vitest'
import { useWebSocket } from './useWebSocket'

class MockWebSocket {
  static readonly instances: MockWebSocket[] = [] as MockWebSocket[]
  public url!: string
  public onopen: any = null
  public onmessage: any = null
  public onclose: any = null
  public onerror: any = null
  public readyState = MockWebSocket.CONNECTING
  public sent: any[] = []
  constructor(url: string) { this.url = url; MockWebSocket.instances.push(this) }
  send(data: any) { this.sent.push(data) }
  close() { this.readyState = MockWebSocket.CLOSED; if (this.onclose) this.onclose() }
  _open() { this.readyState = MockWebSocket.OPEN; if (this.onopen) this.onopen() }
  _message(data: any) { if (this.onmessage) this.onmessage({ data: JSON.stringify(data) }) }
}
MockWebSocket.CONNECTING = 0
MockWebSocket.OPEN = 1
MockWebSocket.CLOSING = 2
MockWebSocket.CLOSED = 3

describe('useWebSocket hook (clean)', () => {
  beforeEach(() => { (globalThis as any).WebSocket = MockWebSocket as any; vi.clearAllMocks() })
  afterEach(() => { MockWebSocket.instances.length = 0; delete (globalThis as any).WebSocket; localStorage.clear() })

  it('shows error when auth_required and no token', () => {
    const TestComp = () => { const { error } = useWebSocket({ onError: vi.fn() } as any); return <div>{error}</div> }
    render(<TestComp />)
    const ws = MockWebSocket.instances[0]
    act(() => ws._open())
    act(() => ws._message({ type: 'auth_required' }))
    expect(screen.getByText('No authentication token available')).toBeInTheDocument()
  })

  it('auth flow calls onConnect and onZoneUpdate', () => {
    localStorage.setItem('hassTokens', JSON.stringify({ access_token: 'tok' }))
    const onConnect = vi.fn(), onZoneUpdate = vi.fn()
    const TestComp = () => { const hook = useWebSocket({ onConnect, onZoneUpdate } as any); return <div>{hook.isConnected ? 'connected' : 'disconnected'}</div> }
    render(<TestComp />)
    const ws = MockWebSocket.instances[0]
    act(() => ws._open())
    act(() => ws._message({ type: 'auth_required' }))
    expect(ws.sent.some(s => s.includes('auth'))).toBeTruthy()
    act(() => ws._message({ type: 'auth_ok' }))
    expect(onConnect).toHaveBeenCalled()
    act(() => ws._message({ type: 'event', result: { data: { area: { id: 'a1' } } } }))
    expect(onZoneUpdate).toHaveBeenCalledWith({ id: 'a1' })
  })

  it('send() returns false when not open and true when open', async () => {
    const TestComp = () => { const hook = useWebSocket(); const [result, setResult] = React.useState<boolean | null>(null); return <div><button onClick={() => setResult(hook.send({ a: 1 }))}>send</button><div>{String(result)}</div></div> }
    render(<TestComp />)
    const ws = MockWebSocket.instances[0]
    await act(async () => { const btn = screen.getByRole('button', { name: 'send' }); await btn.click() })
    expect(screen.getByText('false')).toBeInTheDocument()
    act(() => ws._open())
    await act(async () => { const btn = screen.getByRole('button', { name: 'send' }); await btn.click() })
    expect(ws.sent.length).toBeGreaterThan(0)
  })
})
