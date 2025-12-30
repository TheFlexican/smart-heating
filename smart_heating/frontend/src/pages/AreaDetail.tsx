import { useState, useEffect, useCallback } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { Box, Paper, Tabs, Tab, CircularProgress, Button, Alert } from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import TuneIcon from '@mui/icons-material/Tune'
import ArticleIcon from '@mui/icons-material/Article'
import { useTranslation } from 'react-i18next'
import {
  Zone,
  WindowSensorConfig,
  PresenceSensorConfig,
  Device,
  GlobalPresets,
  HassEntity,
} from '../types'
import {
  getZones,
  setZoneTemperature,
  enableZone,
  disableZone,
  setPrimaryTemperatureSensor,
  addDeviceToZone,
  removeDeviceFromZone,
  getLearningStatsDetailed,
} from '../api/areas'
import { addTrvEntity, addWindowSensor, addPresenceSensor, removeTrvEntity } from '../api/sensors'
import { getAreaLogs, AreaLogEntry } from '../api/logs'
import { getHistoryConfig, getDatabaseStats } from '../api/history'
import { getDevices } from '../api/devices'
import { getGlobalPresets } from '../api/presets'
import { getEntityState, getWeatherEntities } from '../api/config'
import SensorConfigDialog from '../components/SensorConfigDialog'
import TrvConfigDialog from '../components/TrvConfigDialog'
import { SettingSection } from '../components/DraggableSettings'
import { useWebSocket } from '../hooks/useWebSocket'
import { TabPanel } from '../components/common/TabPanel'
import { isEnabledVal, getDisplayTemperature } from '../utils/areaHelpers'
import { AreaDetailHeader } from '../components/AreaDetail/AreaDetailHeader'
import { AreaOverviewTab } from '../components/AreaDetail/AreaOverviewTab'
import { AreaDevicesTab } from '../components/AreaDetail/AreaDevicesTab'
import { AreaScheduleTab } from '../components/AreaDetail/AreaScheduleTab'
import { AreaHistoryTab } from '../components/AreaDetail/AreaHistoryTab'
import { AreaLearningTab } from '../components/AreaDetail/AreaLearningTab'
import { AreaLogsTab } from '../components/AreaDetail/AreaLogsTab'
import { AreaSettingsTab } from '../components/AreaDetail/AreaSettingsTab'
import { PresetModesSection } from '../components/AreaDetail/PresetModesSection'
import { PresetConfigSection } from '../components/AreaDetail/PresetConfigSection'
import { BoostModeSection } from '../components/AreaDetail/BoostModeSection'
import { HvacModeSection } from '../components/AreaDetail/HvacModeSection'
import { HeatingTypeSection } from '../components/AreaDetail/HeatingTypeSection'
import { SwitchControlSection } from '../components/AreaDetail/SwitchControlSection'
import { WindowSensorsSection } from '../components/AreaDetail/WindowSensorsSection'
import { PresenceConfigSection } from '../components/AreaDetail/PresenceConfigSection'
import { PresenceSensorsSection } from '../components/AreaDetail/PresenceSensorsSection'
import { AutoPresetSection } from '../components/AreaDetail/AutoPresetSection'
import { NightBoostSection } from '../components/AreaDetail/NightBoostSection'
import { SmartNightBoostSection } from '../components/AreaDetail/SmartNightBoostSection'
import { HeatingControlSection } from '../components/AreaDetail/HeatingControlSection'
import { HistoryManagementSection } from '../components/AreaDetail/HistoryManagementSection'

const ZoneDetail = () => {
  const { t } = useTranslation()
  const { areaId } = useParams<{ areaId: string }>()
  const navigate = useNavigate()
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
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false)
  const [sensorDialogType, setSensorDialogType] = useState<'window' | 'presence'>('window')
  const [trvDialogOpen, setTrvDialogOpen] = useState(false)
  const [expandedCard, setExpandedCard] = useState<string | null>(null) // Accordion state
  const [logs, setLogs] = useState<AreaLogEntry[]>([])
  const [logsLoading, setLogsLoading] = useState(false)
  const [logFilter, setLogFilter] = useState<string>('all')
  const [learningStats, setLearningStats] = useState<any>(null)
  const [learningStatsLoading, setLearningStatsLoading] = useState(false)
  // TRV inline edit state
  const [editingTrvId, setEditingTrvId] = useState<string | null>(null)
  const [editingTrvName, setEditingTrvName] = useState<string | null>(null)
  const [editingTrvRole, setEditingTrvRole] = useState<'position' | 'open' | 'both' | null>(null)
  const [weatherEntities, setWeatherEntities] = useState<HassEntity[]>([])
  const [weatherEntitiesLoading, setWeatherEntitiesLoading] = useState(false)

  // WebSocket for real-time updates
  useWebSocket({
    onZoneUpdate: updatedZone => {
      if (updatedZone.id === areaId) {
        setArea(updatedZone)
        const displayTemp = getDisplayTemperature(updatedZone)
        setTemperature(displayTemp)
      }
    },
    onZonesUpdate: areas => {
      const currentZone = areas.find(z => z.id === areaId)
      if (currentZone) {
        setArea(currentZone)
        const displayTemp = getDisplayTemperature(currentZone)
        setTemperature(displayTemp)
      }
    },
  })

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
      setTemperature(getDisplayTemperature(currentZone))
      // Load global presets for preset configuration section
      try {
        const presets = await getGlobalPresets()
        setGlobalPresets(presets)
      } catch (error) {
        console.error('Failed to load global presets:', error)
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
  }, [areaId, navigate])

  // Void-returning wrapper for loadData to avoid promise misuse in callbacks
  const handleDataUpdate = useCallback(() => {
    loadData().catch(console.error)
  }, [loadData])

  const startEditingTrv = (trv: any) => {
    setEditingTrvId(trv.entity_id)
    setEditingTrvName(trv.name ?? '')
    setEditingTrvRole((trv.role ?? 'both') as 'position' | 'open' | 'both')
  }

  const cancelEditingTrv = () => {
    setEditingTrvId(null)
    setEditingTrvName(null)
    setEditingTrvRole(null)
  }

  const handleSaveTrv = async (trv: any) => {
    try {
      await addTrvEntity(areaId as string, {
        entity_id: trv.entity_id,
        role: editingTrvRole ?? trv.role,
        name: editingTrvName ?? undefined,
      })
      await loadData()
      cancelEditingTrv()
    } catch (err) {
      console.error('Failed to save TRV edit:', err)
      alert(`Failed to save TRV: ${err}`)
    }
  }

  const handleDeleteTrv = async (entityId: string) => {
    if (!confirm(`Remove ${entityId} from area?`)) return
    try {
      await removeTrvEntity(areaId as string, entityId)
      await loadData()
    } catch (err) {
      console.error('Failed to delete TRV:', err)
      alert(`Failed to delete TRV: ${err}`)
    }
  }

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
    loadData().catch(console.error)
    loadHistoryConfig().catch(console.error)
  }, [areaId, loadData, loadHistoryConfig])

  const getEntityId = (sensor: string | WindowSensorConfig | PresenceSensorConfig): string =>
    typeof sensor === 'string' ? sensor : sensor.entity_id

  const loadStatesForSensors = async (
    sensors: (string | WindowSensorConfig | PresenceSensorConfig)[] | undefined,
    states: Record<string, any>,
  ): Promise<void> => {
    if (!sensors) return
    for (const sensor of sensors) {
      const entity_id = getEntityId(sensor)
      try {
        const state = await getEntityState(entity_id)
        states[entity_id] = state
      } catch (error) {
        console.error(`Failed to load state for ${entity_id}:`, error)
      }
    }
  }

  const loadEntityStates = useCallback(async (currentZone: Zone) => {
    try {
      const states: Record<string, any> = {}

      // Load presence and window sensor states
      await loadStatesForSensors(currentZone.presence_sensors, states)
      await loadStatesForSensors(currentZone.window_sensors, states)

      setEntityStates(states)
    } catch (error) {
      console.error('Failed to load entity states:', error)
    }
  }, [])

  const loadWeatherEntities = async () => {
    setWeatherEntitiesLoading(true)
    try {
      const entities = await getWeatherEntities()
      setWeatherEntities(entities)
    } catch (error) {
      console.error('Failed to load weather entities:', error)
    } finally {
      setWeatherEntitiesLoading(false)
    }
  }

  // Ensure the currently-selected weather entity is visible even when the
  // full weather entity list hasn't been loaded yet. This makes the selected
  // outdoor sensor persistently visible across page reloads.
  useEffect(() => {
    const ensureSelectedWeatherEntityVisible = async () => {
      if (!area?.weather_entity_id) return
      // If we already have the full list or the selected entity is present, nothing to do
      if (weatherEntities.some(e => e.entity_id === area.weather_entity_id)) return

      try {
        const state = await getEntityState(area.weather_entity_id)
        // Create a HassEntity object matching the full interface
        const entity: HassEntity = {
          entity_id: area.weather_entity_id,
          name: state.attributes?.friendly_name || area.weather_entity_id,
          state: state.state || 'unknown',
          attributes: state.attributes || {},
        }
        setWeatherEntities(prev => [entity, ...prev])
      } catch (err) {
        // Ignore - it's okay if the entity can't be fetched
        console.error('Failed to load selected weather entity state:', err)
      }
    }

    ensureSelectedWeatherEntityVisible()
    // Only re-run when area changes (specifically when weather_entity_id changes)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [area])

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
      const stats = await getLearningStatsDetailed(areaId)
      setLearningStats(stats)
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

  const getThermostatStatus = (device: Device): string => {
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

  const getTemperatureSensorStatus = (device: Device): string => {
    if (device.temperature !== undefined && device.temperature !== null) {
      return `${(device.temperature as number).toFixed(1)}°C`
    }
    return device.state || 'unknown'
  }

  const getValveStatus = (device: Device): string => {
    const parts: string[] = []
    if (device.position !== undefined && device.position !== null) {
      parts.push(`${device.position}%`)
    }
    if (device.state) {
      parts.push(device.state)
    }
    return parts.length > 0 ? parts.join(' · ') : 'unknown'
  }

  const getDeviceStatus = (device: Device): string => {
    switch (device.type) {
      case 'thermostat':
        return getThermostatStatus(device)
      case 'temperature_sensor':
        return getTemperatureSensorStatus(device)
      case 'valve':
        return getValveStatus(device)
      default:
        return device.state || 'unknown'
    }
  }

  // Generate settings sections for draggable layout
  const getSettingsSections = (): SettingSection[] => {
    if (!area) return []

    return [
      PresetModesSection({ area, globalPresets, onUpdate: handleDataUpdate, t }),
      PresetConfigSection({ area, globalPresets, onUpdate: handleDataUpdate, t }),
      BoostModeSection({ area, onUpdate: handleDataUpdate, t }),
      HvacModeSection({ area, onUpdate: handleDataUpdate }),
      HeatingTypeSection({ area, onUpdate: handleDataUpdate, t }),
      SwitchControlSection({ area, onUpdate: handleDataUpdate, t }),
      WindowSensorsSection({
        area,
        onUpdate: handleDataUpdate,
        onOpenAddDialog: () => {
          setSensorDialogType('window')
          setSensorDialogOpen(true)
        },
        t,
      }),
      PresenceConfigSection({ area, onUpdate: handleDataUpdate, t }),
      PresenceSensorsSection({
        area,
        entityStates,
        onUpdate: handleDataUpdate,
        onOpenAddDialog: () => {
          setSensorDialogType('presence')
          setSensorDialogOpen(true)
        },
        t,
      }),
      AutoPresetSection({ area, onUpdate: handleDataUpdate, t }),
      NightBoostSection({ area, onUpdate: handleDataUpdate, t }),
      SmartNightBoostSection({
        area,
        onUpdate: handleDataUpdate,
        t,
        weatherEntities,
        weatherEntitiesLoading,
        onLoadWeatherEntities: () => {
          loadWeatherEntities().catch(console.error)
        },
      }),
      HeatingControlSection({ area, onUpdate: handleDataUpdate, t }),
      HistoryManagementSection({
        historyRetention,
        setHistoryRetention,
        storageBackend,
        databaseStats,
        migrating,
        setMigrating,
        recordInterval,
        loadHistoryConfig,
        t,
      }),
    ]
  }

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
      {/* Header */}
      <AreaDetailHeader
        areaName={area.name}
        state={area.state}
        enabled={enabled}
        onBack={() => navigate('/')}
        onToggle={handleToggle}
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
          <AreaOverviewTab
            area={area}
            temperature={temperature}
            enabled={enabled}
            editingTrvId={editingTrvId}
            editingTrvName={editingTrvName}
            editingTrvRole={editingTrvRole}
            onTemperatureChange={handleTemperatureChange}
            onTemperatureCommit={handleTemperatureCommit}
            onTrvDialogOpen={() => setTrvDialogOpen(true)}
            onStartEditingTrv={startEditingTrv}
            onEditingTrvNameChange={setEditingTrvName}
            onEditingTrvRoleChange={setEditingTrvRole}
            onSaveTrv={handleSaveTrv}
            onCancelEditingTrv={cancelEditingTrv}
            onDeleteTrv={handleDeleteTrv}
          />
        </TabPanel>
        {/* Devices Tab */}
        <TabPanel value={tabValue} index={1}>
          <AreaDevicesTab
            area={area}
            availableDevices={availableDevices}
            onPrimarySensorChange={async sensorId => {
              await setPrimaryTemperatureSensor(area.id, sensorId)
              await loadData()
            }}
            onRemoveDevice={async deviceId => {
              await removeDeviceFromZone(area.id, deviceId)
              await loadData()
            }}
            onAddDevice={async device => {
              await addDeviceToZone(area.id, {
                device_id: device.entity_id || device.id,
                device_type: device.type,
                mqtt_topic: device.mqtt_topic,
              })
              await loadData()
            }}
            getDeviceStatusIcon={getDeviceStatusIcon}
            getDeviceStatus={getDeviceStatus}
          />
        </TabPanel>

        {/* Schedule Tab */}
        <TabPanel value={tabValue} index={2}>
          <AreaScheduleTab area={area} onUpdate={handleDataUpdate} />
        </TabPanel>

        {/* History Tab */}
        <TabPanel value={tabValue} index={3}>
          {area.id && <AreaHistoryTab areaId={area.id} />}
        </TabPanel>

        {/* Settings Tab */}
        <TabPanel value={tabValue} index={4}>
          <AreaSettingsTab
            areaId={area.id}
            sections={getSettingsSections()}
            expandedCard={expandedCard}
            onExpandedChange={setExpandedCard}
            presenceSensorsCount={area.presence_sensors?.length || 0}
            windowSensorsCount={area.window_sensors?.length || 0}
          />
        </TabPanel>

        {/* Sensor Configuration Dialog */}
        <SensorConfigDialog
          open={sensorDialogOpen}
          onClose={() => setSensorDialogOpen(false)}
          onAdd={async config => {
            if (!area) return
            try {
              if (sensorDialogType === 'window') {
                await addWindowSensor(area.id, config as WindowSensorConfig)
              } else {
                await addPresenceSensor(area.id, config as PresenceSensorConfig)
              }
              setSensorDialogOpen(false)
              await loadData()
            } catch (error) {
              console.error('Failed to add sensor:', error)
              alert(`Failed to add sensor: ${error}`)
            }
          }}
          sensorType={sensorDialogType}
        />

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
          <AreaLearningTab
            area={area}
            learningStats={learningStats}
            learningStatsLoading={learningStatsLoading}
          />
        </TabPanel>

        {/* Logs Tab */}
        <TabPanel value={tabValue} index={6}>
          <AreaLogsTab
            logs={logs}
            logsLoading={logsLoading}
            logFilter={logFilter}
            onFilterChange={setLogFilter}
            onRefresh={loadLogs}
          />
        </TabPanel>
      </Box>
    </Box>
  )
}

export default ZoneDetail
