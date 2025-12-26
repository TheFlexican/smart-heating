import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'
import { TrvList } from './TrvList'
import { Zone } from '../../types'

// Mock translation
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}))

describe('TrvList', () => {
  const mockArea: Zone = {
    id: 'living_room',
    name: 'Living Room',
    state: 'heating',
    enabled: true,
    target_temperature: 21.0,
    current_temperature: 20.5,
    preset_mode: 'none',
    devices: [],
    trv_entities: [
      { entity_id: 'climate.trv1', role: 'both', name: 'TRV 1' },
      { entity_id: 'climate.trv2', role: 'position', name: 'TRV 2' },
    ],
    trvs: [
      { entity_id: 'climate.trv1', name: 'TRV 1', open: true, position: 75 },
      { entity_id: 'climate.trv2', name: 'TRV 2', open: false, position: 25 },
    ],
  } as Zone

  const mockHandlers = {
    onTrvDialogOpen: vi.fn(),
    onStartEditingTrv: vi.fn(),
    onEditingTrvNameChange: vi.fn(),
    onEditingTrvRoleChange: vi.fn(),
    onSaveTrv: vi.fn(),
    onCancelEditingTrv: vi.fn(),
    onDeleteTrv: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders TRV list correctly', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('TRV 1')).toBeInTheDocument()
    expect(screen.getByText('TRV 2')).toBeInTheDocument()
  })

  it('displays TRV roles correctly', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByText('both')).toBeInTheDocument()
    expect(screen.getByText('position')).toBeInTheDocument()
  })

  it('calls onTrvDialogOpen when Add TRV button clicked', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    const addButton = screen.getByTestId('trv-add-button-overview')
    fireEvent.click(addButton)
    expect(mockHandlers.onTrvDialogOpen).toHaveBeenCalledTimes(1)
  })

  it('calls onStartEditingTrv when edit button clicked', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    const editButton = screen.getByTestId('trv-edit-climate.trv1')
    fireEvent.click(editButton)
    expect(mockHandlers.onStartEditingTrv).toHaveBeenCalledWith(mockArea.trv_entities[0])
  })

  it('calls onDeleteTrv when delete button clicked', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    const deleteButton = screen.getByTestId('trv-delete-climate.trv1')
    fireEvent.click(deleteButton)
    expect(mockHandlers.onDeleteTrv).toHaveBeenCalledWith('climate.trv1')
  })

  it('shows edit form when TRV is being edited', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId="climate.trv1"
        editingTrvName="New TRV Name"
        editingTrvRole="position"
        {...mockHandlers}
      />,
    )
    expect(screen.getByTestId('trv-edit-name-climate.trv1')).toBeInTheDocument()
    expect(screen.getByTestId('trv-edit-role-climate.trv1')).toBeInTheDocument()
  })

  it('calls onEditingTrvNameChange when name is changed', async () => {
    const user = userEvent.setup()
    render(
      <TrvList
        area={mockArea}
        editingTrvId="climate.trv1"
        editingTrvName="Old Name"
        editingTrvRole="both"
        {...mockHandlers}
      />,
    )
    const nameInput = screen.getByTestId('trv-edit-name-climate.trv1').querySelector('input')!
    await user.clear(nameInput)
    await user.type(nameInput, 'New Name')
    expect(mockHandlers.onEditingTrvNameChange).toHaveBeenCalled()
  })

  it('calls onSaveTrv when save button clicked', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId="climate.trv1"
        editingTrvName="Updated Name"
        editingTrvRole="position"
        {...mockHandlers}
      />,
    )
    const saveButton = screen.getByTestId('trv-save-climate.trv1')
    fireEvent.click(saveButton)
    expect(mockHandlers.onSaveTrv).toHaveBeenCalledWith(mockArea.trv_entities[0])
  })

  it('calls onCancelEditingTrv when cancel button clicked', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId="climate.trv1"
        editingTrvName="Updated Name"
        editingTrvRole="position"
        {...mockHandlers}
      />,
    )
    const cancelButton = screen.getByTestId('trv-cancel-edit-climate.trv1')
    fireEvent.click(cancelButton)
    expect(mockHandlers.onCancelEditingTrv).toHaveBeenCalledTimes(1)
  })

  it('shows info message when no TRVs configured', () => {
    const areaWithoutTrvs = { ...mockArea, trv_entities: [] }
    render(
      <TrvList
        area={areaWithoutTrvs}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(
      screen.getByText('No TRVs configured for this area. Click Add TRV to add one.'),
    ).toBeInTheDocument()
  })

  it('displays TRV open/closed status correctly', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByTestId('trv-open-climate.trv1')).toBeInTheDocument()
    expect(screen.getByTestId('trv-open-climate.trv2')).toBeInTheDocument()
  })

  it('displays TRV position percentage correctly', () => {
    render(
      <TrvList
        area={mockArea}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByTestId('trv-position-climate.trv1')).toHaveTextContent('75%')
    expect(screen.getByTestId('trv-position-climate.trv2')).toHaveTextContent('25%')
  })

  it('shows dash when TRV position is undefined', () => {
    const areaWithUndefinedPosition = {
      ...mockArea,
      trvs: [{ entity_id: 'climate.trv1', name: 'TRV 1', open: true, position: undefined }],
    }
    render(
      <TrvList
        area={areaWithUndefinedPosition}
        editingTrvId={null}
        editingTrvName={null}
        editingTrvRole={null}
        {...mockHandlers}
      />,
    )
    expect(screen.getByTestId('trv-position-climate.trv1')).toHaveTextContent('—')
  })
})
