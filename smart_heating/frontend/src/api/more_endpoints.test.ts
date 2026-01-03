import { apiClient } from './client'
import * as areas from './areas'
import * as cfg from './config'
import * as history from './history'
import * as log from './logs'
import * as safety from './safety'
import * as importExport from './import_export'
import * as users from './users'
import * as efficiency from './efficiency'
import * as metrics from './metrics'
import { vi, describe, it, expect, beforeEach } from 'vitest'

vi.mock('./client')
const mockedClient = vi.mocked(apiClient)

describe('API additional endpoints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('set frost protection and presence config', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await cfg.setFrostProtection(true, 3)
    expect(mockedClient.post).toHaveBeenCalledWith('/frost_protection', {
      enabled: true,
      temperature: 3,
    })
  })

  it('copy schedule builds data with optional arrays', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await areas.copySchedule('a1', 'a2')
    expect(mockedClient.post).toHaveBeenCalledWith('/copy_schedule', {
      source_area_id: 'a1',
      target_area_id: 'a2',
    })
    await areas.copySchedule('a1', 'a2', ['Monday'], ['Tuesday'])
    expect(mockedClient.post).toHaveBeenCalledWith('/copy_schedule', {
      source_area_id: 'a1',
      target_area_id: 'a2',
      source_days: ['Monday'],
      target_days: ['Tuesday'],
    })
  })

  it('setHeatingType with optional customOverheadTemp', async () => {
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await areas.setHeatingType('a1', 'radiator')
    expect(mockedClient.post).toHaveBeenCalledWith('/areas/a1/heating_type', {
      heating_type: 'radiator',
    })
    await areas.setHeatingType('a1', 'airco')
    expect(mockedClient.post).toHaveBeenCalledWith('/areas/a1/heating_type', {
      heating_type: 'airco',
    })
    await areas.setHeatingType('a1', 'floor_heating', 42)
    expect(mockedClient.post).toHaveBeenCalledWith('/areas/a1/heating_type', {
      heating_type: 'floor_heating',
      custom_overhead_temp: 42,
    })
  })

  it('get and set history and db endpoints', async () => {
    mockedClient.get.mockResolvedValue({ data: { retention_days: 30 } } as any)
    const cfgResp = await history.getHistoryConfig()
    expect(cfgResp.retention_days).toBe(30)
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await history.setHistoryRetention(10)
    expect(mockedClient.post).toHaveBeenCalledWith('/history/config', {
      retention_days: 10,
    })
  })

  it('get area logs with optional params', async () => {
    mockedClient.get.mockResolvedValue({ data: { logs: [] } } as any)
    await log.getAreaLogs('a1')
    expect(mockedClient.get).toHaveBeenCalledWith('/areas/a1/logs?')
    await log.getAreaLogs('a1', { limit: 10, type: 'info' })
    expect(mockedClient.get).toHaveBeenCalledWith('/areas/a1/logs?limit=10&type=info')
  })

  it('safety sensor CRUD', async () => {
    mockedClient.get.mockResolvedValue({ data: { sensors: [] } } as any)
    await safety.getSafetySensor()
    expect(mockedClient.get).toHaveBeenCalledWith('/safety_sensor')
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await safety.setSafetySensor({ sensor_id: 's1', enabled: true })
    expect(mockedClient.post).toHaveBeenCalledWith('/safety_sensor', {
      sensor_id: 's1',
      enabled: true,
    })
    mockedClient.delete.mockResolvedValue({ data: {} } as any)
    await safety.removeSafetySensor('s1')
    expect(mockedClient.delete).toHaveBeenCalledWith('/safety_sensor?sensor_id=s1')
  })

  it('import/export/validate and backups', async () => {
    mockedClient.get.mockResolvedValue({ data: new Blob(['ok']) } as any)
    const blob = await importExport.exportConfig()
    expect(blob).toBeTruthy()
    mockedClient.post.mockResolvedValue({ data: { success: true } } as any)
    await importExport.importConfig({})
    expect(mockedClient.post).toHaveBeenCalledWith('/import', {})
    await importExport.validateConfig({})
    expect(mockedClient.post).toHaveBeenCalledWith('/validate', {})
    mockedClient.get.mockResolvedValue({ data: { backups: [] } } as any)
    await importExport.listBackups()
    expect(mockedClient.get).toHaveBeenCalledWith('/backups')
    mockedClient.post.mockResolvedValue({ data: { success: true } } as any)
    await importExport.restoreBackup('file.json')
    expect(mockedClient.post).toHaveBeenCalledWith('/backups/file.json/restore')
  })

  it('user CRUD and presence', async () => {
    mockedClient.get.mockResolvedValue({ data: { users: [] } } as any)
    await users.getUsers()
    expect(mockedClient.get).toHaveBeenCalledWith('/users')
    mockedClient.post.mockResolvedValue({ data: { user: { user_id: 'u1' } } } as any)
    await users.createUser({ user_id: 'u1', name: 'U' } as any)
    expect(mockedClient.post).toHaveBeenCalledWith('/users', {
      user_id: 'u1',
      name: 'U',
    })
    mockedClient.post.mockResolvedValue({ data: { settings: {} } } as any)
    await users.updateUserSettings({})
    expect(mockedClient.post).toHaveBeenCalledWith('/users/settings', {})
  })

  it('get efficiency and comparison endpoints', async () => {
    mockedClient.get.mockResolvedValue({ data: { report: true } } as any)
    await efficiency.getEfficiencyReport('a1')
    expect(mockedClient.get).toHaveBeenCalledWith('/efficiency/report/a1?period=week')
    await efficiency.getAllAreasEfficiency('day')
    expect(mockedClient.get).toHaveBeenCalledWith('/efficiency/all_areas?period=day')
    await efficiency.getComparison('month')
    expect(mockedClient.get).toHaveBeenCalledWith('/comparison/month')
    mockedClient.post.mockResolvedValue({ data: {} } as any)
    await efficiency.getCustomComparison('2020-01-01', '2020-01-02', '2021-01-01', '2021-01-02')
    expect(mockedClient.post).toHaveBeenCalledWith('/comparison/custom', {
      start_a: '2020-01-01',
      end_a: '2020-01-02',
      start_b: '2021-01-01',
      end_b: '2021-01-02',
    })
  })

  it('advanced metrics builds params', async () => {
    mockedClient.get.mockResolvedValue({ data: {} } as any)
    await metrics.getAdvancedMetrics(7)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?days=7')
    await metrics.getAdvancedMetrics(1, 'a1')
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?minutes=1&area_id=a1')
    await metrics.getAdvancedMetrics(1, undefined, true)
    expect(mockedClient.get).toHaveBeenCalledWith('/metrics/advanced?days=1')
  })
})
