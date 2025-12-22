import React from 'react'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'
import HistoryMigrationControls from './HistoryMigrationControls'

describe('HistoryMigrationControls', () => {
  it('renders migrate to database button when backend is json and calls handler', async () => {
    const migrate = vi.fn().mockResolvedValue(undefined)
    render(
      <HistoryMigrationControls
        storageBackend="json"
        migrating={false}
        onMigrateToDatabase={migrate}
        onMigrateToJson={vi.fn()}
      />,
    )

    const btn = screen.getByRole('button', { name: /Migrate to Database/i })
    await userEvent.click(btn)
    expect(migrate).toHaveBeenCalled()
  })

  it('renders migrate to JSON when backend is database', () => {
    render(
      <HistoryMigrationControls
        storageBackend="database"
        migrating={false}
        onMigrateToDatabase={vi.fn()}
        onMigrateToJson={vi.fn()}
      />,
    )

    expect(screen.getByRole('button', { name: /Migrate to JSON/i })).toBeInTheDocument()
  })
})
