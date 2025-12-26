import { describe, it, expect, vi, beforeEach } from 'vitest'
import { HistoryManagementSection } from './HistoryManagementSection'

// Mock the API functions
vi.mock('../../api/history', () => ({
  setHistoryRetention: vi.fn(),
  migrateHistoryStorage: vi.fn(),
}))

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: any) => {
      if (params) {
        return `${key}:${JSON.stringify(params)}`
      }
      return key
    },
  }),
}))

describe('HistoryManagementSection', () => {
  const mockSetHistoryRetention = vi.fn()
  const mockSetMigrating = vi.fn()
  const mockLoadHistoryConfig = vi.fn()
  const mockT = (key: string, params?: any) => {
    if (params) {
      return `${key}:${JSON.stringify(params)}`
    }
    return key
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('returns a SettingSection with correct id', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.id).toBe('history-management')
  })

  it('returns a SettingSection with correct title', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.title).toBe('settingsCards.historyManagementTitle')
  })

  it('returns a SettingSection with correct description', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.description).toBe('settingsCards.historyManagementDescription')
  })

  it('sets defaultExpanded to false', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.defaultExpanded).toBe(false)
  })

  it('includes content', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })

  it('handles json storage backend', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })

  it('handles database storage backend with stats', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'database',
      databaseStats: { total_entries: 1000 },
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })

  it('handles migrating state', () => {
    const section = HistoryManagementSection({
      historyRetention: 30,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: true,
      setMigrating: mockSetMigrating,
      recordInterval: 5,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })

  it('handles different record intervals', () => {
    const section = HistoryManagementSection({
      historyRetention: 90,
      setHistoryRetention: mockSetHistoryRetention,
      storageBackend: 'json',
      databaseStats: null,
      migrating: false,
      setMigrating: mockSetMigrating,
      recordInterval: 10,
      loadHistoryConfig: mockLoadHistoryConfig,
      t: mockT,
    })

    expect(section.content).toBeDefined()
  })
})
