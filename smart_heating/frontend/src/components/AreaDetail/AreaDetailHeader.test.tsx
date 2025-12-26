import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaDetailHeader } from './AreaDetailHeader'

describe('AreaDetailHeader', () => {
  const mockOnBack = vi.fn()
  const mockOnToggle = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <AreaDetailHeader
        areaName="Living Room"
        state="heating"
        enabled={true}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    expect(screen.getByText('Living Room')).toBeInTheDocument()
  })

  it('displays area name correctly', () => {
    render(
      <AreaDetailHeader
        areaName="Kitchen"
        state="idle"
        enabled={false}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    expect(screen.getByText('Kitchen')).toBeInTheDocument()
  })

  it('displays state chip with correct label', () => {
    render(
      <AreaDetailHeader
        areaName="Bedroom"
        state="heating"
        enabled={true}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    expect(screen.getByText('HEATING')).toBeInTheDocument()
  })

  it('displays enabled status chip', () => {
    render(
      <AreaDetailHeader
        areaName="Office"
        state="idle"
        enabled={true}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    expect(screen.getByText('ENABLED')).toBeInTheDocument()
  })

  it('displays disabled status chip when disabled', () => {
    render(
      <AreaDetailHeader
        areaName="Garage"
        state="off"
        enabled={false}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    expect(screen.getByText('DISABLED')).toBeInTheDocument()
  })

  it('calls onBack when back button is clicked', () => {
    render(
      <AreaDetailHeader
        areaName="Living Room"
        state="heating"
        enabled={true}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    const backButton = screen.getByTestId('area-top-back-button')
    fireEvent.click(backButton)
    expect(mockOnBack).toHaveBeenCalledTimes(1)
  })

  it('calls onToggle when switch is clicked', async () => {
    mockOnToggle.mockResolvedValue(undefined)
    render(
      <AreaDetailHeader
        areaName="Living Room"
        state="heating"
        enabled={true}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    const toggle = screen.getByRole('switch')
    fireEvent.click(toggle)
    await waitFor(() => {
      expect(mockOnToggle).toHaveBeenCalledTimes(1)
    })
  })

  it('shows switch as checked when enabled', () => {
    render(
      <AreaDetailHeader
        areaName="Living Room"
        state="heating"
        enabled={true}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    const toggle = screen.getByRole('switch')
    expect(toggle).toBeChecked()
  })

  it('shows switch as unchecked when disabled', () => {
    render(
      <AreaDetailHeader
        areaName="Living Room"
        state="off"
        enabled={false}
        onBack={mockOnBack}
        onToggle={mockOnToggle}
      />,
    )
    const toggle = screen.getByRole('switch')
    expect(toggle).not.toBeChecked()
  })
})
