import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import LogsPanel from './LogsPanel'

// Mock i18n
vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (s: string) => s }) }))

test('shows empty logs message when no logs', () => {
  render(
    <LogsPanel
      logs={[]}
      logsLoading={false}
      logFilter={'all'}
      setLogFilter={() => {}}
      loadLogs={() => {}}
    />,
  )
  expect(screen.getByTestId('area-logs-empty')).toBeInTheDocument()
})

test('shows loading when logsLoading is true', () => {
  render(
    <LogsPanel
      logs={[]}
      logsLoading={true}
      logFilter={'all'}
      setLogFilter={() => {}}
      loadLogs={() => {}}
    />,
  )
  expect(screen.getByRole('progressbar')).toBeInTheDocument()
})
