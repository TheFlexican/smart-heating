import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Alert,
  Snackbar,
  CircularProgress,
  Tabs,
  Tab,
  // TextField no longer used in this file
} from '@mui/material'

import ThermostatIcon from '@mui/icons-material/Thermostat'
import PeopleIcon from '@mui/icons-material/People'
import BeachAccessIcon from '@mui/icons-material/BeachAccess'
import TuneIcon from '@mui/icons-material/Tune'
import SecurityIcon from '@mui/icons-material/Security'
import BackupIcon from '@mui/icons-material/Backup'
import FireplaceIcon from '@mui/icons-material/Fireplace'
import ListAltIcon from '@mui/icons-material/ListAlt'

import BugReportIcon from '@mui/icons-material/BugReport'

import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { getGlobalPresets, setGlobalPresets } from '../api/presets'
import { GlobalSettingsHeader } from '../components/GlobalSettings/GlobalSettingsHeader'
import { TabPanel } from '../components/common/TabPanel'
import { getGlobalPresence, setGlobalPresence } from '../api/sensors'
import { getHysteresis, setHysteresis as setHysteresisApi } from '../api/logs'
import {
  getSafetySensor,
  setSafetySensor as setSafetySensorApi,
  removeSafetySensor,
  type SafetySensorResponse,
} from '../api/safety'
import { setHideDevicesPanel as setHideDevicesPanelApi } from '../api/devices'
import { getConfig, getAdvancedControlConfig, setAdvancedControlConfig } from '../api/config'
import { setOpenthermGateway, getOpenthermGateways, calibrateOpentherm } from '../api/opentherm'
import { PresenceSensorConfig, WindowSensorConfig, SafetySensorConfig } from '../types'
import SensorConfigDialog from '../components/SensorConfigDialog'
import SafetySensorConfigDialog from '../components/SafetySensorConfigDialog'
import { VacationModeSettings } from '../components/VacationModeSettings'
import HysteresisHelpModal from '../components/HysteresisHelpModal'
import ImportExport from '../components/ImportExport'
import { UserManagement } from '../components/UserManagement'
import DeviceLogsPanel from '../components/DeviceLogsPanel'
import { PresetsSettings } from '../components/GlobalSettings/PresetsSettings'
import { SensorsSettings } from '../components/GlobalSettings/SensorsSettings'
import { SafetySettings } from '../components/GlobalSettings/SafetySettings'
import { AdvancedSettings } from '../components/GlobalSettings/AdvancedSettings'
import { OpenThermSettings } from '../components/GlobalSettings/OpenThermSettings'
import { DebugSettings } from '../components/GlobalSettings/DebugSettings'
// additional advanced control apis already imported above

interface GlobalPresetsData {
  away_temp: number
  eco_temp: number
  comfort_temp: number
  home_temp: number
  sleep_temp: number
  activity_temp: number
}

interface WebSocketMetrics {
  totalConnectionAttempts: number
  successfulConnections: number
  failedConnections: number
  unexpectedDisconnects: number
  averageConnectionDuration: number
  lastFailureReason: string
  lastConnectedAt: string | null
  lastDisconnectedAt: string | null
  connectionDurations: number[]
  deviceInfo: {
    userAgent: string
    platform: string
    isIframe: boolean
    isiOS: boolean
    isAndroid: boolean
    browserName: string
  }
}

type GlobalSettingsProps = Readonly<{
  themeMode: 'light' | 'dark'
  onThemeChange: (mode: 'light' | 'dark') => void
  wsMetrics?: WebSocketMetrics
  initialTab?: number
}>

export default function GlobalSettings({
  themeMode,
  onThemeChange,
  wsMetrics,
  initialTab = 0,
}: GlobalSettingsProps) {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState(initialTab)
  const [presets, setPresets] = useState<GlobalPresetsData | null>(null)
  const [hysteresis, setHysteresis] = useState<number>(0.5)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [presenceSensors, setPresenceSensors] = useState<PresenceSensorConfig[]>([])
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false)
  const [hysteresisHelpOpen, setHysteresisHelpOpen] = useState(false)
  const [safetySensor, setSafetySensor] = useState<SafetySensorResponse | null>(null)
  const [safetySensorDialogOpen, setSafetySensorDialogOpen] = useState(false)
  const [hideDevicesPanel, setHideDevicesPanel] = useState(false)
  // Advanced control state
  const [advancedControlEnabled, setAdvancedControlEnabled] = useState(false)
  const [heatingCurveEnabled, setHeatingCurveEnabled] = useState(false)
  const [pwmEnabled, setPwmEnabled] = useState(false)
  const [pidEnabled, setPidEnabled] = useState(false)
  const [overshootProtectionEnabled, setOvershootProtectionEnabled] = useState(false)
  const [defaultCoefficient, setDefaultCoefficient] = useState<number>(1)

  // OpenTherm Gateway Configuration
  const [openthermGatewayId, setOpenthermGatewayId] = useState<string>('')
  const [openthermSaving, setOpenthermSaving] = useState(false)
  const [openthermGateways, setOpenthermGateways] = useState<
    Array<{ gateway_id: string; title: string }>
  >([])

  useEffect(() => {
    loadPresets()
    loadHysteresis()
    loadPresenceSensors()
    loadSafetySensor()
    loadConfig()
    loadOpenthermGateways()
    loadAdvancedControlConfig()
  }, [])

  const loadConfig = async () => {
    try {
      const config = await getConfig()
      setHideDevicesPanel(config.hide_devices_panel || false)

      // Load OpenTherm configuration
      setOpenthermGatewayId(config.opentherm_gateway_id || '')
    } catch (err) {
      console.error('Error loading config:', err)
    }
  }

  const loadAdvancedControlConfig = async () => {
    try {
      const cfg = await getAdvancedControlConfig()
      // cfg is a config block; it includes advanced control keys
      setAdvancedControlEnabled(!!cfg.advanced_control_enabled)
      setHeatingCurveEnabled(!!cfg.heating_curve_enabled)
      setPwmEnabled(!!cfg.pwm_enabled)
      setPidEnabled(!!cfg.pid_enabled)
      setOvershootProtectionEnabled(!!cfg.overshoot_protection_enabled)
      setDefaultCoefficient(Number(cfg.default_heating_curve_coefficient || 1))
    } catch (err) {
      console.error('Error loading advanced control config', err)
    }
  }

  const loadOpenthermGateways = async () => {
    try {
      const gateways = await getOpenthermGateways()
      setOpenthermGateways(gateways)
    } catch (err) {
      console.error('Error loading OpenTherm gateways:', err)
    }
  }

  const loadPresets = async () => {
    try {
      setLoading(true)
      const data = await getGlobalPresets()
      setPresets(data)
      setError(null)
    } catch (err) {
      setError('Failed to load global presets')
      console.error('Error loading global presets:', err)
    } finally {
      setLoading(false)
    }
  }

  const loadPresenceSensors = async () => {
    try {
      const data = await getGlobalPresence()
      setPresenceSensors(data.sensors || [])
    } catch (err) {
      console.error('Error loading global presence sensors:', err)
    }
  }

  const loadHysteresis = async () => {
    try {
      const value = await getHysteresis()
      setHysteresis(value)
    } catch (err) {
      console.error('Error loading hysteresis:', err)
    }
  }

  const loadSafetySensor = async () => {
    try {
      const data = await getSafetySensor()
      setSafetySensor(data)
    } catch (err) {
      console.error('Error loading safety sensor:', err)
    } finally {
      setLoading(false)
    }
  }

  // Update local value while dragging; commit on release via onChangeCommitted
  const handlePresetChange = (key: keyof GlobalPresetsData, value: number) => {
    if (!presets) return
    const newPresets = { ...presets, [key]: value }
    setPresets(newPresets)
  }

  // Called when user finishes interacting with the slider
  const handlePresetCommit = async (key: keyof GlobalPresetsData, value: number) => {
    try {
      setSaving(true)
      setSaveSuccess(false)
      await setGlobalPresets({ [key]: value })
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      setError('Failed to save preset')
      console.error('Error saving preset:', err)
      await loadPresets()
    } finally {
      setSaving(false)
    }
  }

  const handleHysteresisChange = (
    _event: Event | React.SyntheticEvent,
    value: number | number[],
  ) => {
    const newValue = Array.isArray(value) ? value[0] : value
    setHysteresis(newValue)
  }

  const handleHysteresisCommit = async (
    _event: Event | React.SyntheticEvent,
    value: number | number[],
  ) => {
    const newValue = Array.isArray(value) ? value[0] : value
    try {
      setSaving(true)
      setSaveSuccess(false)
      await setHysteresisApi(newValue)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      setError('Failed to save hysteresis')
      console.error('Error saving hysteresis:', err)
      await loadHysteresis()
    } finally {
      setSaving(false)
    }
  }

  const handleToggleHideDevicesPanel = async (hide: boolean) => {
    try {
      setHideDevicesPanel(hide)
      await setHideDevicesPanelApi(hide)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
      // Reload to apply changes
      setTimeout(() => globalThis.location.reload(), 500)
    } catch (err) {
      setError('Failed to save setting')
      console.error('Error saving hide devices panel:', err)
      setHideDevicesPanel(!hide)
    }
  }

  const handleToggleAdvancedControl = async (field: string, value: boolean | number) => {
    const payload: Record<string, boolean | number> = {}
    payload[field] = value
    try {
      await setAdvancedControlConfig(payload)
      // Push local state update
      switch (field) {
        case 'advanced_control_enabled':
          setAdvancedControlEnabled(Boolean(value))
          break
        case 'heating_curve_enabled':
          setHeatingCurveEnabled(Boolean(value))
          break
        case 'pwm_enabled':
          setPwmEnabled(Boolean(value))
          break
        case 'pid_enabled':
          setPidEnabled(Boolean(value))
          break
        case 'overshoot_protection_enabled':
          setOvershootProtectionEnabled(Boolean(value))
          break
        case 'default_heating_curve_coefficient':
          setDefaultCoefficient(Number(value))
          break
      }
    } catch (err) {
      setError('Failed to save advanced control setting')
      console.error('Error saving advanced control setting:', err)
    }
  }

  const handleResetAdvancedControl = async () => {
    try {
      setSaving(true)
      // Reset to sensible defaults
      await setAdvancedControlConfig({
        advanced_control_enabled: false,
        heating_curve_enabled: false,
        pwm_enabled: false,
        pid_enabled: false,
        overshoot_protection_enabled: false,
        default_heating_curve_coefficient: 1,
      })
      // reload values immediately
      await loadAdvancedControlConfig()
    } catch (err) {
      setError('Failed to reset advanced control settings')
      console.error('Error resetting advanced control:', err)
    } finally {
      setSaving(false)
    }
  }

  const handleSaveOpenthermConfig = async () => {
    try {
      setOpenthermSaving(true)
      // Only send gateway id; control is automatic when a gateway is configured
      await setOpenthermGateway(openthermGatewayId)
      // Reload config to confirm saved values
      await loadConfig()
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      setError('Failed to save OpenTherm configuration')
      console.error('Error saving OpenTherm config:', err)
    } finally {
      setOpenthermSaving(false)
    }
  }
  const [calibrating, setCalibrating] = useState(false)
  const [calibrationResult, setCalibrationResult] = useState<number | null>(null)

  const handleRunCalibration = async () => {
    setCalibrating(true)
    try {
      const res = await calibrateOpentherm()
      if (res?.opv != null) {
        setCalibrationResult(res.opv)
      }
    } catch (err) {
      setError('Calibration failed')
      console.error('Calibration error:', err)
    } finally {
      setCalibrating(false)
    }
  }

  const handleAddPresenceSensor = async (config: WindowSensorConfig | PresenceSensorConfig) => {
    try {
      const newSensors = [...presenceSensors, config as PresenceSensorConfig]
      await setGlobalPresence(newSensors)
      await loadPresenceSensors()
      setSensorDialogOpen(false)
    } catch (err) {
      console.error('Error adding presence sensor:', err)
      setError('Failed to add presence sensor')
    }
  }

  const handleRemovePresenceSensor = async (entityId: string) => {
    try {
      const newSensors = presenceSensors.filter(s => s.entity_id !== entityId)
      await setGlobalPresence(newSensors)
      await loadPresenceSensors()
    } catch (err) {
      console.error('Error removing presence sensor:', err)
      setError('Failed to remove presence sensor')
    }
  }

  const handleAddSafetySensor = async (config: SafetySensorConfig) => {
    try {
      await setSafetySensorApi(config)
      await loadSafetySensor()
      setSafetySensorDialogOpen(false)
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      console.error('Error adding safety sensor:', err)
      setError('Failed to add safety sensor')
    }
  }

  const handleRemoveSafetySensor = async (sensorId: string) => {
    try {
      await removeSafetySensor(sensorId)
      await loadSafetySensor()
      setSaveSuccess(true)
      setTimeout(() => setSaveSuccess(false), 2000)
    } catch (err) {
      console.error('Error removing safety sensor:', err)
      setError('Failed to remove safety sensor')
    }
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

  if (error && !presets) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        pb: 0,
        display: 'flex',
        flexDirection: 'column',
        height: '100vh',
      }}
    >
      {/* Header */}
      <GlobalSettingsHeader onBack={() => navigate('/')} />

      <Box sx={{ borderBottom: 1, borderColor: 'divider', px: 2 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          aria-label="global settings tabs"
        >
          {/* Removed duplicate Advanced Control tab to keep tabs in the correct order */}
          <Tab
            icon={<ThermostatIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.temperature', 'Temperature')}
          />
          <Tab
            icon={<PeopleIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.sensors', 'Sensors')}
          />
          <Tab
            icon={<BeachAccessIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.vacation', 'Vacation')}
          />
          <Tab
            icon={<PeopleIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.users', 'User Management')}
          />
          <Tab
            icon={<SecurityIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.safety', 'Safety')}
          />
          <Tab
            icon={<TuneIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.advanced', 'Advanced')}
          />
          <Tab
            icon={<BackupIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.importExport', 'Import/Export')}
          />
          <Tab
            icon={<ListAltIcon />}
            iconPosition="start"
            label={t('globalSettings.tabs.deviceLogs', 'Device Logs')}
          />
          <Tab
            icon={<FireplaceIcon />}
            iconPosition="start"
            data-testid="opentherm-tab"
            label={t('globalSettings.tabs.opentherm', 'OpenTherm')}
          />
          <Tab
            icon={<BugReportIcon />}
            iconPosition="start"
            data-testid="debug-tab"
            label="Debug"
          />
        </Tabs>
      </Box>

      {/* Content area: on mobile allow scrolling inside the viewport */}
      <Box
        sx={{
          px: 2,
          overflowY: { xs: 'auto', sm: 'visible' },
          maxHeight: { xs: 'calc(100vh - 120px)', sm: 'none' },
          py: 2,
        }}
      >
        {/* Use a Snackbar for success messages so layout is not pushed while interacting with sliders */}
        <Snackbar
          open={saveSuccess}
          autoHideDuration={2000}
          onClose={() => setSaveSuccess(false)}
          anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        >
          <Alert severity="success" sx={{ width: '100%' }}>
            {t('globalSettings.saveSuccess', 'Settings saved successfully')}
          </Alert>
        </Snackbar>

        {error && (
          <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Temperature Tab */}
        <TabPanel value={activeTab} index={0}>
          {presets ? (
            <PresetsSettings
              presets={presets}
              saving={saving}
              onChange={handlePresetChange}
              onCommit={handlePresetCommit}
            />
          ) : null}
        </TabPanel>

        {/* Sensors Tab */}
        <TabPanel value={activeTab} index={1}>
          <SensorsSettings
            presenceSensors={presenceSensors}
            onRemove={handleRemovePresenceSensor}
            onAddClick={() => setSensorDialogOpen(true)}
          />
        </TabPanel>

        {/* Vacation Tab */}
        <TabPanel value={activeTab} index={2}>
          <VacationModeSettings />
        </TabPanel>

        {/* User Management Tab */}
        <TabPanel value={activeTab} index={3}>
          <UserManagement embedded={true} />
        </TabPanel>

        {/* Safety Tab */}
        <TabPanel value={activeTab} index={4}>
          <SafetySettings
            safetySensor={safetySensor}
            onRemove={handleRemoveSafetySensor}
            onAddClick={() => setSafetySensorDialogOpen(true)}
          />
        </TabPanel>

        {/* Advanced Tab */}
        <TabPanel value={activeTab} index={5}>
          <AdvancedSettings
            themeMode={themeMode}
            onThemeChange={onThemeChange}
            hysteresis={hysteresis}
            saving={saving}
            onHysteresisChange={handleHysteresisChange}
            onHysteresisCommit={handleHysteresisCommit}
            onOpenHysteresisHelp={() => setHysteresisHelpOpen(true)}
            hideDevicesPanel={hideDevicesPanel}
            onToggleHideDevicesPanel={handleToggleHideDevicesPanel}
            advancedControlEnabled={advancedControlEnabled}
            heatingCurveEnabled={heatingCurveEnabled}
            pwmEnabled={pwmEnabled}
            pidEnabled={pidEnabled}
            overshootProtectionEnabled={overshootProtectionEnabled}
            defaultCoefficient={defaultCoefficient}
            onToggleAdvancedControl={handleToggleAdvancedControl}
            onResetAdvancedControl={handleResetAdvancedControl}
            onRunCalibration={handleRunCalibration}
            calibrating={calibrating}
            calibrationResult={calibrationResult}
          />
        </TabPanel>

        {/* Import/Export Tab */}
        <TabPanel value={activeTab} index={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" sx={{ mb: 1 }}>
              {t('importExport.title', 'Import/Export Configuration')}
            </Typography>
            <ImportExport />
          </Paper>
        </TabPanel>

        {/* Device Logs Tab */}
        <TabPanel value={activeTab} index={7}>
          <DeviceLogsPanel />
        </TabPanel>

        {/* OpenTherm Tab */}
        <TabPanel value={activeTab} index={8}>
          <OpenThermSettings
            openthermGateways={openthermGateways}
            openthermGatewayId={openthermGatewayId}
            setOpenthermGatewayId={setOpenthermGatewayId}
            openthermSaving={openthermSaving}
            handleSave={handleSaveOpenthermConfig}
          />
        </TabPanel>

        {/* Debug Tab */}
        <TabPanel value={activeTab} index={9}>
          <DebugSettings wsMetrics={wsMetrics} />
        </TabPanel>
      </Box>

      {/* Sensor Dialog */}
      <SensorConfigDialog
        open={sensorDialogOpen}
        onClose={() => setSensorDialogOpen(false)}
        onAdd={handleAddPresenceSensor}
        sensorType="presence"
      />

      {/* Safety Sensor Dialog */}
      <SafetySensorConfigDialog
        open={safetySensorDialogOpen}
        onClose={() => setSafetySensorDialogOpen(false)}
        onAdd={handleAddSafetySensor}
        configuredSensors={safetySensor?.sensors?.map(s => s.sensor_id) || []}
      />

      {/* Hysteresis Help Modal */}
      <HysteresisHelpModal open={hysteresisHelpOpen} onClose={() => setHysteresisHelpOpen(false)} />
    </Box>
  )
}
