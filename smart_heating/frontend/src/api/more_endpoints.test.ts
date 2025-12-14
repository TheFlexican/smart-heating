import axios from 'axios'
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

vi.mock('axios')
const mockedAxios = axios as unknown as jest.Mocked<typeof axios>

describe('API additional endpoints', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('set frost protection and presence config', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await cfg.setFrostProtection(true, 3)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/frost_protection', { enabled: true, temperature: 3 })
  })

  it('copy schedule builds data with optional arrays', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await areas.copySchedule('a1', 'a2')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/copy_schedule', { source_area_id: 'a1', target_area_id: 'a2' })
    await areas.copySchedule('a1', 'a2', ['Monday'], ['Tuesday'])
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/copy_schedule', { source_area_id: 'a1', target_area_id: 'a2', source_days: ['Monday'], target_days: ['Tuesday'] })
  })

  it('setHeatingType with optional customOverheadTemp', async () => {
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await areas.setHeatingType('a1', 'radiator')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/areas/a1/heating_type', { heating_type: 'radiator' })
    await areas.setHeatingType('a1', 'floor_heating', 42)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/areas/a1/heating_type', { heating_type: 'floor_heating', custom_overhead_temp: 42 })
  })

  it('get and set history and db endpoints', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { retention_days: 30 } }) as any
    const cfgResp = await history.getHistoryConfig()
    expect(cfgResp.retention_days).toBe(30)
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await history.setHistoryRetention(10)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/history/config', { retention_days: 10 })
  })

  it('get area logs with optional params', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { logs: [] } }) as any
    await log.getAreaLogs('a1')
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/areas/a1/logs?')
    await log.getAreaLogs('a1', { limit: 10, type: 'info' })
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/areas/a1/logs?limit=10&type=info')
  })

  it('safety sensor CRUD', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { sensors: [] } }) as any
    await safety.getSafetySensor()
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/safety_sensor')
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await safety.setSafetySensor({ sensor_id: 's1', enabled: true })
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/safety_sensor', { sensor_id: 's1', enabled: true })
    mockedAxios.delete = vi.fn().mockResolvedValue({ data: {} }) as any
    await safety.removeSafetySensor('s1')
    expect(mockedAxios.delete).toHaveBeenCalledWith('/api/smart_heating/safety_sensor?sensor_id=s1')
  })

  it('import/export/validate and backups', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: new Blob(['ok']) }) as any
    const blob = await importExport.exportConfig()
    expect(blob).toBeTruthy()
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { success: true } }) as any
    await importExport.importConfig({})
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/import', {})
    await importExport.validateConfig({})
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/validate', {})
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { backups: [] } }) as any
    await importExport.listBackups()
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/backups')
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { success: true } }) as any
    await importExport.restoreBackup('file.json')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/backups/file.json/restore')
  })

  it('user CRUD and presence', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { users: [] } }) as any
    await users.getUsers()
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/users')
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { user: { user_id: 'u1' } } }) as any
    await users.createUser({ user_id: 'u1', name: 'U' } as any)
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/users', { user_id: 'u1', name: 'U' })
    mockedAxios.post = vi.fn().mockResolvedValue({ data: { settings: {} } }) as any
    await users.updateUserSettings({})
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/users/settings', {})
  })

  it('get efficiency and comparison endpoints', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: { report: true } }) as any
    await efficiency.getEfficiencyReport('a1')
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/efficiency/report/a1?period=week')
    await efficiency.getAllAreasEfficiency('day')
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/efficiency/all_areas?period=day')
    await efficiency.getComparison('month')
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/comparison/month')
    mockedAxios.post = vi.fn().mockResolvedValue({ data: {} }) as any
    await efficiency.getCustomComparison('2020-01-01', '2020-01-02', '2021-01-01', '2021-01-02')
    expect(mockedAxios.post).toHaveBeenCalledWith('/api/smart_heating/comparison/custom', { start_a: '2020-01-01', end_a: '2020-01-02', start_b: '2021-01-01', end_b: '2021-01-02' })
  })

  it('advanced metrics builds params', async () => {
    mockedAxios.get = vi.fn().mockResolvedValue({ data: {} }) as any
    await metrics.getAdvancedMetrics(7)
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/metrics/advanced?days=7')
    await metrics.getAdvancedMetrics(1, 'a1')
    expect(mockedAxios.get).toHaveBeenCalledWith('/api/smart_heating/metrics/advanced?days=1&area_id=a1')
  })
})
