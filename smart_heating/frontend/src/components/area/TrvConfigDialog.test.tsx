import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import '@testing-library/jest-dom'
import * as api from '../../api/sensors'
import { describe, beforeEach, vi, expect, it } from 'vitest'
import TrvConfigDialog from './TrvConfigDialog'

// Mock translation
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

describe('TrvConfigDialog', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('loads candidates and allows adding a TRV', async () => {
    vi.spyOn(api, 'getTrvCandidates').mockResolvedValue([
      {
        entity_id: 'sensor.trv_position',
        name: 'Trv Position',
        state: '50',
        attributes: { friendly_name: 'TRV Position' },
      },
      {
        entity_id: 'binary_sensor.trv_open',
        name: 'Trv Open',
        state: 'off',
        attributes: { friendly_name: 'TRV Open' },
      },
    ] as any)

    const addSpy = vi.spyOn(api, 'addTrvEntity').mockResolvedValue(undefined)
    const onRefresh = vi.fn()

    render(
      <TrvConfigDialog
        open={true}
        onClose={() => {}}
        areaId="a1"
        trvEntities={[]}
        onRefresh={onRefresh}
      />,
    )

    // Wait for candidates to load
    await waitFor(() => expect(screen.getByTestId('trv-entity-select')).toBeInTheDocument())

    // Set selected entity programmatically (MUI native select uses a hidden input in tests)
    const selectRoot = screen.getByTestId('trv-entity-select') as HTMLElement
    const nativeInput = selectRoot.querySelector('input') as HTMLInputElement
    expect(nativeInput).toBeTruthy()
    fireEvent.change(nativeInput, { target: { value: 'sensor.trv_position' } })

    // Set role to position
    const roleRoot = screen.getByTestId('trv-role-select') as HTMLElement
    const roleInput = roleRoot.querySelector('input') as HTMLInputElement
    expect(roleInput).toBeTruthy()
    fireEvent.change(roleInput, { target: { value: 'position' } })

    // Click Add
    fireEvent.click(screen.getByTestId('trv-add-button'))

    await waitFor(() =>
      expect(addSpy).toHaveBeenCalledWith('a1', {
        entity_id: 'sensor.trv_position',
        role: 'position',
        name: undefined,
      }),
    )
    await waitFor(() => expect(onRefresh).toHaveBeenCalled())
  })

  it('removes configured TRV when confirmed', async () => {
    const trvEntities = [{ entity_id: 'sensor.trv_position', role: 'position', name: 'TRV1' }]

    const removeSpy = vi.spyOn(api, 'removeTrvEntity').mockResolvedValue(undefined)
    const onRefresh = vi.fn()

    // Mock candidates (avoid network errors during loadCandidates)
    vi.spyOn(api, 'getTrvCandidates').mockResolvedValue([])

    // Mock confirm to accept the removal
    const confirmSpy = vi.spyOn(globalThis, 'confirm').mockImplementation(() => true)

    render(
      <TrvConfigDialog
        open={true}
        onClose={() => {}}
        areaId="a1"
        trvEntities={trvEntities as any}
        onRefresh={onRefresh}
      />,
    )

    // Remove button should be present
    await waitFor(() =>
      expect(screen.getByTestId('trv-remove-sensor.trv_position')).toBeInTheDocument(),
    )

    // Click remove
    fireEvent.click(screen.getByTestId('trv-remove-sensor.trv_position'))

    await waitFor(() => expect(confirmSpy).toHaveBeenCalled())
    await waitFor(() => expect(removeSpy).toHaveBeenCalledWith('a1', 'sensor.trv_position'))
    await waitFor(() => expect(onRefresh).toHaveBeenCalled())

    confirmSpy.mockRestore()
  })

  it('shows alert when add fails', async () => {
    vi.spyOn(api, 'getTrvCandidates').mockResolvedValue([
      {
        entity_id: 'sensor.trv_position',
        name: 'Trv Position',
        state: '50',
        attributes: { friendly_name: 'TRV Position' },
      },
    ] as any)

    const addSpy = vi.spyOn(api, 'addTrvEntity').mockRejectedValue(new Error('API Error'))
    const onRefresh = vi.fn()
    const alertSpy = vi.spyOn(globalThis, 'alert').mockImplementation(() => {})

    render(
      <TrvConfigDialog
        open={true}
        onClose={() => {}}
        areaId="a1"
        trvEntities={[]}
        onRefresh={onRefresh}
      />,
    )

    await waitFor(() => expect(screen.getByTestId('trv-entity-select')).toBeInTheDocument())

    const selectRoot = screen.getByTestId('trv-entity-select') as HTMLElement
    const nativeInput = selectRoot.querySelector('input') as HTMLInputElement
    fireEvent.change(nativeInput, { target: { value: 'sensor.trv_position' } })

    fireEvent.click(screen.getByTestId('trv-add-button'))

    await waitFor(() => expect(addSpy).toHaveBeenCalled())
    await waitFor(() => expect(alertSpy).toHaveBeenCalled())

    alertSpy.mockRestore()
  })

  it('limits initial candidates to 10 and supports search and show all', async () => {
    const many = Array.from({ length: 20 }).map((_, i) => ({
      entity_id: `sensor.trv_${i}`,
      state: String(i),
      attributes: { friendly_name: `TRV ${i}` },
    }))

    vi.spyOn(api, 'getTrvCandidates').mockResolvedValue(many as any)

    render(
      <TrvConfigDialog
        open={true}
        onClose={() => {}}
        areaId="a1"
        trvEntities={[]}
        onRefresh={() => {}}
      />,
    )

    // Wait for candidates
    await waitFor(() => expect(screen.getByTestId('trv-entity-select')).toBeInTheDocument())

    // Open the select to reveal menu items and assert first candidate is present
    const selectRoot = screen.getByTestId('trv-entity-select') as HTMLElement
    const combobox = selectRoot.querySelector('[role="combobox"]') || selectRoot
    fireEvent.mouseDown(combobox)

    await waitFor(() => expect(screen.getByText('TRV 0')).toBeInTheDocument())
    // 11th should not be visible initially
    expect(screen.queryByText('TRV 11')).not.toBeInTheDocument()

    // Close the menu (click away) and click show all
    fireEvent.keyDown(document.body, { key: 'Escape' })
    fireEvent.click(screen.getByTestId('trv-show-all'))

    // Re-open select and check 11th now appears
    fireEvent.mouseDown(combobox)
    await waitFor(() => expect(screen.getByText('TRV 11')).toBeInTheDocument())

    // Search for a specific later entity
    const searchRoot = screen.getByTestId('trv-search-input') as HTMLElement
    const searchInput = searchRoot.querySelector('input') as HTMLInputElement
    fireEvent.change(searchInput, { target: { value: 'trv_15' } })
    // Open select and assert
    fireEvent.keyDown(document.body, { key: 'Escape' })
    fireEvent.mouseDown(combobox)
    await waitFor(() => expect(screen.getByText('TRV 15')).toBeInTheDocument())
  })
})
