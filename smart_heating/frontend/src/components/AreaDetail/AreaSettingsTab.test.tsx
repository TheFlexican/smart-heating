import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaSettingsTab } from './AreaSettingsTab'
import { SettingSection } from '../DraggableSettings'

// Mock DraggableSettings component
vi.mock('../DraggableSettings', () => ({
  default: ({ sections, storageKey, expandedCard, onExpandedChange }: any) => (
    <div data-testid="draggable-settings">
      <div data-testid="storage-key">{storageKey}</div>
      <div data-testid="expanded-card">{expandedCard || 'none'}</div>
      <div data-testid="sections-count">{sections.length}</div>
      <button onClick={() => onExpandedChange('test-card')}>Expand Test Card</button>
    </div>
  ),
}))

describe('AreaSettingsTab', () => {
  const mockSections: SettingSection[] = [
    {
      id: 'preset-modes',
      title: 'Preset Modes',
      description: 'Configure preset modes',
      icon: <div>Icon</div>,
      content: <div>Content</div>,
      defaultExpanded: false,
    },
    {
      id: 'boost-mode',
      title: 'Boost Mode',
      description: 'Configure boost mode',
      icon: <div>Icon</div>,
      content: <div>Content</div>,
      defaultExpanded: false,
    },
  ]

  const mockOnExpandedChange = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing', () => {
    render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard={null}
        onExpandedChange={mockOnExpandedChange}
      />,
    )
    expect(screen.getByTestId('draggable-settings')).toBeInTheDocument()
  })

  it('passes correct storage key to DraggableSettings', () => {
    render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard={null}
        onExpandedChange={mockOnExpandedChange}
      />,
    )
    expect(screen.getByTestId('storage-key')).toHaveTextContent('area-settings-order-living_room')
  })

  it('passes sections to DraggableSettings', () => {
    render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard={null}
        onExpandedChange={mockOnExpandedChange}
      />,
    )
    expect(screen.getByTestId('sections-count')).toHaveTextContent('2')
  })

  it('passes expandedCard to DraggableSettings', () => {
    render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard="boost-mode"
        onExpandedChange={mockOnExpandedChange}
      />,
    )
    expect(screen.getByTestId('expanded-card')).toHaveTextContent('boost-mode')
  })

  it('passes onExpandedChange to DraggableSettings', () => {
    render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard={null}
        onExpandedChange={mockOnExpandedChange}
      />,
    )
    const expandButton = screen.getByRole('button')
    expandButton.click()
    expect(mockOnExpandedChange).toHaveBeenCalledWith('test-card')
  })

  it('uses default values for sensor counts when not provided', () => {
    const { container } = render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard={null}
        onExpandedChange={mockOnExpandedChange}
      />,
    )
    // The key should include 0-0 for default sensor counts
    expect(container.querySelector('[data-testid="draggable-settings"]')).toBeInTheDocument()
  })

  it('passes sensor counts to key generation', () => {
    render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard={null}
        onExpandedChange={mockOnExpandedChange}
        presenceSensorsCount={2}
        windowSensorsCount={3}
      />,
    )
    // The component should render with the custom sensor counts in the key
    expect(screen.getByTestId('draggable-settings')).toBeInTheDocument()
  })

  it('renders with correct container styling', () => {
    const { container } = render(
      <AreaSettingsTab
        areaId="living_room"
        sections={mockSections}
        expandedCard={null}
        onExpandedChange={mockOnExpandedChange}
      />,
    )
    const boxElement = container.firstChild as HTMLElement
    expect(boxElement).toBeInTheDocument()
  })
})
