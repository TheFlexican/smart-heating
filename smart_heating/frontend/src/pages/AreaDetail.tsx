import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Paper, Typography, Tabs, Tab, CircularProgress, Button, Alert } from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import TuneIcon from '@mui/icons-material/Tune'
// EditIcon removed - TRV editing moved to component
import ArticleIcon from '@mui/icons-material/Article'
import { useTranslation } from 'react-i18next'
import { Zone, Device, GlobalPresets } from '../types'
import {
  getZones,
  setZoneTemperature,
  enableZone,
  disableZone,
  addDeviceToZone,
  removeDeviceFromZone,
} from '../api/areas'

import { getAreaLogs, AreaLogEntry } from '../api/logs'
import { getHistoryConfig, getDatabaseStats } from '../api/history'
import { getDevices } from '../api/devices'
import { getGlobalPresets } from '../api/presets'
import { getEntityState } from '../api/config'
import ScheduleEditor from '../components/area/ScheduleEditor'
import PrimaryTemperatureSensor from '../components/area/PrimaryTemperatureSensor'
import TrvConfigDialog from '../components/area/TrvConfigDialog'
import LearningStats from '../components/area/LearningStats'
import DevicesPanel from '../components/common/DevicesPanel'
import TemperatureControl from '../components/area/TemperatureControl'
import QuickStats from '../components/area/QuickStats'
import DraggableSettings from '../components/common/DraggableSettings'
import buildAreaSettingsSections from './area/common/AreaSettingsSections'
import { HistoryTabContent, LogsTabContent } from './area/common/AreaHistoryAndLogs'
import { useWebSocket } from '../hooks/useWebSocket'
import AreaHeader from '../components/area/AreaHeader'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

function TabPanel(props: Readonly<TabPanelProps>) {
  const { children, value, index, ...other } = props

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`area-tabpanel-${index}`}
      aria-labelledby={`area-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: { xs: 2, sm: 3 } }}>{children}</Box>}
    </div>
  )
}

const ZoneDetail = () => {
  const { t } = useTranslation()
  const { areaId } = useParams<{ areaId: string }>()
  const navigate = useNavigate()
  // Helper: accepts boolean or string forms of enabled and returns boolean true only
  const isEnabledVal = useCallback(
    (v: boolean | string | undefined | null) => v === true || String(v) === 'true',
    [],
  )

  // Small helper to compute display temperature for a zone without nested ternaries
  const getDisplayTempForZone = useCallback(
    (z: Zone | null) => {
      if (!z) return 0
      if (!isEnabledVal(z.enabled) || z.state === 'off') return z.target_temperature
      if (z.preset_mode && z.preset_mode !== 'none' && z.effective_target_temperature != null)
        return z.effective_target_temperature
      return z.target_temperature
    },
    [isEnabledVal],
  )

  const loadEntityStates = useCallback(async (currentZone: Zone) => {
    try {
      const states: Record<string, any> = {}

      const loadPresence = async () => {
        if (!currentZone.presence_sensors) return
        for (const sensor of currentZone.presence_sensors) {
          const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
          try {
            const s = await getEntityState(entity_id)
            states[entity_id] = { state: s?.state, name: s?.attributes?.friendly_name }
          } catch {
            // ignore
          }
        }
      }

      const loadWindow = async () => {
        if (!currentZone.window_sensors) return
        for (const sensor of currentZone.window_sensors) {
          const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
          try {
            const state = await getEntityState(entity_id)
            states[entity_id] = state
          } catch (err) {
            console.error(`Failed to load state for ${entity_id}:`, err)
          }
        }
      }

      await loadPresence()
      await loadWindow()

      setEntityStates(states)
    } catch (err) {
      console.error('Failed to load entity states:', err)
    }
  }, [])
  const [area, setArea] = useState<Zone | null>(null)
  const [availableDevices, setAvailableDevices] = useState<Device[]>([])
  const [entityStates, setEntityStates] = useState<Record<string, any>>({})
  const [globalPresets, setGlobalPresets] = useState<GlobalPresets | null>(null)
  const [loading, setLoading] = useState(true)
  const [tabValue, setTabValue] = useState(0)
  const [temperature, setTemperature] = useState(21)
  const [historyRetention, setHistoryRetention] = useState(30)
  const [storageBackend, setStorageBackend] = useState<string>('json')
  const [databaseStats, setDatabaseStats] = useState<any>(null)
  const [migrating, setMigrating] = useState(false)
  const [recordInterval, setRecordInterval] = useState(5)

  const [trvDialogOpen, setTrvDialogOpen] = useState(false)
  const [expandedCard, setExpandedCard] = useState<string | null>(null) // Accordion state
  const [logs, setLogs] = useState<AreaLogEntry[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logFilter, setLogFilter] = useState<string>('all')
  const [learningStats, setLearningStats] = useState<any>(null)
  const [learningStatsLoading, setLearningStatsLoading] = useState(false)
  // TRV dialog state (editing moved to TrvList)

  const [areaHeatingCurveCoefficient, setAreaHeatingCurveCoefficient] = useState<number | null>(
    null,
  )
  const [useGlobalHeatingCurve, setUseGlobalHeatingCurve] = useState<boolean>(true)

  // WebSocket for real-time updates
  useWebSocket({
    onZoneUpdate: updatedZone => {
      if (updatedZone.id === areaId) {
        setArea(updatedZone)
        setTemperature(getDisplayTempForZone(updatedZone))
      }
    },
    onZonesUpdate: areas => {
      const currentZone = areas.find(z => z.id === areaId)
      if (currentZone) {
        setArea(currentZone)
        setTemperature(getDisplayTempForZone(currentZone))
      }
    },
  })

  // Ensure the currently-selected weather entity state is fetched even when the
  // full weather entities list isn't loaded (keeps behavior for tests).
  useEffect(() => {
    const ensureSelected = async () => {
      if (!area?.weather_entity_id) return
      try {
        await getEntityState(area.weather_entity_id)
      } catch {
        // Ignore errors; this is best-effort to surface selected entity
      }
    }

    ensureSelected()
  }, [area])

  const loadData = useCallback(async () => {
    if (!areaId) return

    try {
      setLoading(true)
      const areasData = await getZones()

      const currentZone = areasData.find(z => z.id === areaId)
      if (!currentZone) {
        navigate('/')
        return
      }

      setArea(currentZone)
      setTemperature(getDisplayTempForZone(currentZone))
      // Load global presets for preset configuration section
      try {
        const presets = await getGlobalPresets()
        setGlobalPresets(presets)
      } catch (error) {
        console.error('Failed to load global presets:', error)
      }

      // Set area heating curve coefficient state if present
      if (
        currentZone.heating_curve_coefficient !== undefined &&
        currentZone.heating_curve_coefficient !== null
      ) {
        setAreaHeatingCurveCoefficient(currentZone.heating_curve_coefficient)
        setUseGlobalHeatingCurve(false)
      } else {
        setAreaHeatingCurveCoefficient(null)
        setUseGlobalHeatingCurve(true)
      }

      // Load entity states for presence/window sensors
      await loadEntityStates(currentZone)

      // Load available devices
      await loadAvailableDevices(currentZone)
    } catch (error) {
      console.error('Failed to load area data:', error)
    } finally {
      setLoading(false)
    }
  }, [areaId, navigate, getDisplayTempForZone, loadEntityStates])

  // TRV editing logic moved to TrvList component

  const loadHistoryConfig = useCallback(async () => {
    try {
      const config = await getHistoryConfig()
      if (config) {
        setHistoryRetention(config.retention_days)
        setStorageBackend(config.storage_backend || 'json')
        setRecordInterval(config.record_interval_minutes)

        // Load database stats if using database backend
        if (config.storage_backend === 'database') {
          try {
            const stats = await getDatabaseStats()
            setDatabaseStats(stats)
          } catch (error) {
            console.error('Failed to load database stats:', error)
          }
        }
      }
    } catch (error) {
      console.error('Failed to load history config:', error)
    }
  }, [])

  useEffect(() => {
    loadData()
    loadHistoryConfig()
  }, [areaId, loadData, loadHistoryConfig])

  const loadAvailableDevices = async (currentZone: Zone) => {
    try {
      const allDevices = await getDevices()

      // Filter devices:
      // 1. Must be assigned to the same HA area as this zone (by area_id OR name matching)
      // 2. Must NOT already be assigned to this zone
      const available = allDevices.filter(device => {
        // Check if already assigned
        const alreadyAssigned = currentZone.devices.some(
          d => (d.entity_id || d.id) === (device.entity_id || device.id),
        )
        if (alreadyAssigned) return false

        // Method 1: Direct HA area match
        if (device.ha_area_id === currentZone.id) {
          return true
        }

        // Method 2: Name-based matching (for MQTT devices without HA area assignment)
        // Check if device name contains the zone name
        const zoneName = currentZone.name.toLowerCase()
        const deviceName = (device.name || device.entity_id || device.id || '').toLowerCase()
        if (deviceName.includes(zoneName)) {
          return true
        }

        return false
      })

      setAvailableDevices(available)
    } catch (error) {
      console.error('Failed to load available devices:', error)
    }
  }

  const loadLearningStats = useCallback(async () => {
    if (!areaId) return

    try {
      setLearningStatsLoading(true)
      const response = await fetch(`/api/smart_heating/areas/${areaId}/learning/stats`)
      if (response.ok) {
        const data = await response.json()
        setLearningStats(data.stats)
      }
    } catch (error) {
      console.error('Failed to load learning stats:', error)
    } finally {
      setLearningStatsLoading(false)
    }
  }, [areaId])

  // Load learning stats when tab is switched to Learning tab
  useEffect(() => {
    if (tabValue === 5) {
      // Learning tab index
      loadLearningStats()
    }
  }, [tabValue, loadLearningStats])

  const loadLogs = useCallback(async () => {
    if (!areaId) return

    try {
      setLogsLoading(true)
      const options: any = { limit: 100 }
      if (logFilter !== 'all') {
        options.type = logFilter
      }
      const logsData = await getAreaLogs(areaId, options)
      setLogs(logsData)
    } catch (error) {
      console.error('Failed to load logs:', error)
    } finally {
      setLogsLoading(false)
    }
  }, [areaId, logFilter])

  // Load logs when tab is switched to Logs tab
  useEffect(() => {
    if (tabValue === 6) {
      // Logs tab index
      loadLogs()
    }
  }, [tabValue, loadLogs])

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue)
  }

  const handleToggle = async () => {
    if (!area) return

    try {
      const currentlyEnabled = area.enabled === true || String(area.enabled) === 'true'
      if (currentlyEnabled) {
        await disableZone(area.id)
      } else {
        await enableZone(area.id)
      }
      await loadData()
    } catch (error) {
      console.error('Failed to toggle area:', error)
    }
  }

  const handleTemperatureChange = (_event: Event, value: number | number[]) => {
    setTemperature(value as number)
  }

  const handleTemperatureCommit = async (
    _event: Event | React.SyntheticEvent,
    value: number | number[],
  ) => {
    if (!area) return

    try {
      await setZoneTemperature(area.id, value as number)
      await loadData()
    } catch (error) {
      console.error('Failed to set temperature:', error)
    }
  }

  const getDeviceStatusIcon = (device: any) => {
    if (device.type === 'thermostat') {
      // Check if should be heating based on area target temperature (not device's stale target)
      const shouldHeat =
        area?.target_temperature !== undefined &&
        device.current_temperature !== undefined &&
        area.target_temperature > device.current_temperature

      if (shouldHeat) {
        return <LocalFireDepartmentIcon fontSize="small" sx={{ color: 'error.main' }} />
      } else if (device.state === 'heat') {
        return <ThermostatIcon fontSize="small" sx={{ color: 'primary.main' }} />
      } else {
        return <AcUnitIcon fontSize="small" sx={{ color: 'info.main' }} />
      }
    } else if (device.type === 'valve') {
      return (
        <TuneIcon
          fontSize="small"
          sx={{ color: device.position > 0 ? 'warning.main' : 'text.secondary' }}
        />
      )
    } else if (device.type === 'temperature_sensor') {
      return <SensorsIcon fontSize="small" sx={{ color: 'success.main' }} />
    } else {
      return (
        <PowerSettingsNewIcon
          fontSize="small"
          sx={{ color: device.state === 'on' ? 'success.main' : 'text.secondary' }}
        />
      )
    }
  }

  const getThermostatStatus = (area: Zone | null, device: any) => {
    const parts: string[] = []
    if (device.current_temperature !== undefined && device.current_temperature !== null) {
      parts.push(`${device.current_temperature.toFixed(1)}°C`)
    }

    if (
      area?.target_temperature !== undefined &&
      area.target_temperature !== null &&
      device.current_temperature !== undefined &&
      device.current_temperature !== null &&
      area.target_temperature > device.current_temperature
    ) {
      parts.push(`→ ${area.target_temperature.toFixed(1)}°C`)
    }

    return parts.length > 0 ? parts.join(' · ') : device.state || 'unknown'
  }

  const getTemperatureSensorStatus = (device: any) => {
    if (device.temperature !== undefined && device.temperature !== null) {
      return `${device.temperature.toFixed(1)}°C`
    }
    return device.state || 'unknown'
  }

  const getValveStatus = (device: any) => {
    const parts: string[] = []
    if (device.position !== undefined) parts.push(`${device.position}%`)
    if (device.state) parts.push(device.state)
    return parts.length > 0 ? parts.join(' · ') : 'unknown'
  }

  const getDeviceStatus = (device: any) => {
    if (device.type === 'thermostat') return getThermostatStatus(area, device)
    if (device.type === 'temperature_sensor') return getTemperatureSensorStatus(device)
    if (device.type === 'valve') return getValveStatus(device)
    return device.state || 'unknown'
  }

  const getStateColor = (state: string) => {
    switch (state) {
      case 'heating':
        return 'error'
      case 'idle':
        return 'info'
      case 'off':
        return 'default'
      default:
        return 'default'
    }
  }

  // Helper function to get effective preset temperature (global or custom)
  const getPresetTemp = (
    presetKey: string,
    customTemp: number | undefined,
    fallback: number,
  ): string => {
    if (!area) return `${fallback}°C`

    const useGlobalKey = `use_global_${presetKey}` as keyof Zone
    const useGlobal = (area[useGlobalKey] as boolean | undefined) ?? true

    if (useGlobal && globalPresets) {
      const globalKey = `${presetKey}_temp` as keyof GlobalPresets
      return `${globalPresets[globalKey]}°C (global)`
    }
    return `${customTemp ?? fallback}°C (custom)`
  }

  // Settings builder is used directly in the JSX below

  if (loading) {
    return (
      <Box
        sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}
      >
        <CircularProgress />
      </Box>
    )
  }

  if (!area) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">Zone not found</Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/')}
          sx={{ mt: 2 }}
          data-testid="area-back-button"
        >
          Back to Zones
        </Button>
      </Box>
    )
  }

  // Normalize enabled - accept boolean true or string 'true'
  const enabled = isEnabledVal(area.enabled)

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: 'background.default',
      }}
    >
      <AreaHeader
        area={area}
        enabled={enabled}
        onToggle={handleToggle}
        onBack={() => navigate('/')}
        getStateColor={getStateColor}
      />

      {/* Tabs */}
      <Paper
        elevation={0}
        sx={{
          borderBottom: 1,
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              fontSize: { xs: '0.75rem', sm: '0.875rem' },
              minWidth: { xs: 'auto', sm: 160 },
              px: { xs: 1, sm: 2 },
            },
          }}
        >
          <Tab data-testid="area-detail-tab-overview" label={t('tabs.overview')} />
          <Tab data-testid="area-detail-tab-devices" label={t('tabs.devices')} />
          <Tab data-testid="area-detail-tab-schedule" label={t('tabs.schedule')} />
          <Tab data-testid="area-detail-tab-history" label={t('tabs.history')} />
          <Tab data-testid="area-detail-tab-settings" label={t('tabs.settings')} />
          <Tab data-testid="area-detail-tab-learning" label={t('tabs.learning')} />
          <Tab
            data-testid="tab-logs"
            label={t('tabs.logs')}
            icon={<ArticleIcon />}
            iconPosition="start"
          />
        </Tabs>
      </Paper>

      {/* Tab Panels */}
      <Box sx={{ flex: 1, overflow: 'auto' }}>
        {/* Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ maxWidth: { xs: 800, lg: 1200 }, mx: 'auto', px: { xs: 0, sm: 0 } }}>
            <TemperatureControl
              area={area}
              temperature={temperature}
              enabled={enabled}
              onTemperatureChange={handleTemperatureChange}
              onTemperatureCommit={handleTemperatureCommit}
              onOpenTrvDialog={() => setTrvDialogOpen(true)}
              trvs={area.trvs}
              loadData={loadData}
            />

            <QuickStats area={area} />
          </Box>
        </TabPanel>

        {/* Devices Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box sx={{ maxWidth: { xs: 800, lg: 1200 }, mx: 'auto' }}>
            <PrimaryTemperatureSensor area={area} loadData={loadData} />

            <DevicesPanel
              area={area}
              availableDevices={availableDevices}
              loadData={loadData}
              addDeviceToZone={addDeviceToZone}
              removeDeviceFromZone={removeDeviceFromZone}
              getDeviceStatusIcon={getDeviceStatusIcon}
              getDeviceStatus={getDeviceStatus}
            />
          </Box>
        </TabPanel>

        {/* Schedule Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
            <ScheduleEditor area={area} onUpdate={loadData} />
          </Box>
        </TabPanel>

        {/* History Tab */}
        <TabPanel value={tabValue} index={3}>
          <HistoryTabContent area={area} />
        </TabPanel>

        {/* Settings Tab */}
        <TabPanel value={tabValue} index={4}>
          <Box sx={{ maxWidth: 1600, mx: 'auto', px: 2 }}>
            <DraggableSettings
              key={`settings-${area.id}-${area.presence_sensors?.length || 0}-${area.window_sensors?.length || 0}`}
              sections={buildAreaSettingsSections({
                t,
                area: area,
                globalPresets,
                getPresetTemp,
                loadData,
                useGlobalHeatingCurve,
                setUseGlobalHeatingCurve,
                areaHeatingCurveCoefficient,
                setAreaHeatingCurveCoefficient,
                entityStates,
                historyRetention,
                setHistoryRetention,
                storageBackend,
                databaseStats,
                migrating,
                setMigrating,
                recordInterval,
                loadHistoryConfig,
              } as any)}
              storageKey={`area-settings-order-${area.id}`}
              expandedCard={expandedCard}
              onExpandedChange={setExpandedCard}
            />
          </Box>
        </TabPanel>

        {/* TRV Configuration Dialog */}
        <TrvConfigDialog
          open={trvDialogOpen}
          onClose={() => setTrvDialogOpen(false)}
          areaId={area?.id || ''}
          trvEntities={area?.trv_entities || []}
          onRefresh={async () => {
            await loadData()
            setTrvDialogOpen(false)
          }}
        />

        {/* Learning Tab */}
        <TabPanel value={tabValue} index={5}>
          <Box sx={{ maxWidth: 800, mx: 'auto' }}>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom color="text.primary">
                {t('areaDetail.adaptiveLearning')}
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t('areaDetail.learningDescription')}
              </Typography>

              {area.smart_boost_enabled ? (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" color="success.main" gutterBottom>
                    ✓ {t('areaDetail.smartNightBoostActive')}
                  </Typography>
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    display="block"
                    sx={{ mb: 3 }}
                  >
                    {t('areaDetail.learningSystemText')}
                  </Typography>

                  <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1, mb: 3 }}>
                    <Typography variant="body2" color="info.dark">
                      <strong>Note:</strong> {t('areaDetail.learningNote')}
                    </Typography>
                  </Box>

                  <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
                    {t('areaDetail.configuration')}
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        {t('areaDetail.targetWakeupTime')}
                      </Typography>
                      <Typography variant="body2" color="text.primary">
                        <strong>{area.smart_boost_target_time ?? '06:00'}</strong>
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2" color="text.secondary">
                        {t('areaDetail.weatherSensor')}
                      </Typography>
                      <Typography variant="body2" color="text.primary">
                        {area.weather_entity_id ? (
                          <strong>{area.weather_entity_id}</strong>
                        ) : (
                          <em>{t('areaDetail.notConfigured')}</em>
                        )}
                      </Typography>
                    </Box>
                  </Box>

                  <LearningStats learningStats={learningStats} loading={learningStatsLoading} />
                </Box>
              ) : (
                <Box sx={{ mt: 3, textAlign: 'center', py: 4 }}>
                  <Typography variant="body1" color="text.secondary" gutterBottom>
                    {t('settingsCards.smartNightBoostNotEnabled')}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                    {t('settingsCards.enableSmartNightBoostInfo')}
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="caption" color="text.secondary">
                      {t('settingsCards.adaptiveLearningInfo')}
                    </Typography>
                  </Box>
                </Box>
              )}
            </Paper>
          </Box>
        </TabPanel>

        {/* Logs Tab */}
        <TabPanel value={tabValue} index={6}>
          <LogsTabContent
            logs={logs}
            logsLoading={logsLoading}
            logFilter={logFilter}
            setLogFilter={setLogFilter}
            loadLogs={loadLogs}
          />
        </TabPanel>
      </Box>
    </Box>
  )
}

export default ZoneDetail
