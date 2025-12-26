import React from 'react'
import { render, screen } from '@testing-library/react'
import { describe, it, expect, vi } from 'vitest'
import { GlobalSettingsHeader } from './GlobalSettingsHeader'

describe('GlobalSettingsHeader', () => {
  it('renders and calls onBack', () => {
    const onBack = vi.fn()
    render(<GlobalSettingsHeader onBack={onBack} />)

    expect(screen.getByTestId('global-back-button')).toBeInTheDocument()
    screen.getByTestId('global-back-button').click()
    expect(onBack).toHaveBeenCalled()
  })
})
