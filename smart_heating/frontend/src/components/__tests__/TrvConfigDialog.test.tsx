import React from 'react'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import TrvConfigDialog from '../TrvConfigDialog'
import * as api from '../../api/sensors'
import { vi } from 'vitest'

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

    // Click Add
    fireEvent.click(screen.getByTestId('trv-add-button'))

    await waitFor(() => expect(addSpy).toHaveBeenCalled())
    await waitFor(() => expect(onRefresh).toHaveBeenCalled())
  })
})
