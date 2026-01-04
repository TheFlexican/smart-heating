import { useState, useEffect, useCallback, lazy, Suspense, useRef } from 'react'
import mergeZones from './utils/areaOrder'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { ThemeProvider, CssBaseline, Box, Snackbar, Alert, CircularProgress } from '@mui/material'
import Header from './components/Header'
import ZoneList from './components/ZoneList'
import MobileBottomNav from './components/MobileBottomNav'
import { VacationModeBanner } from './components/VacationModeBanner'
import { Zone } from './types'
import { getZones } from './api/areas'
import { getSafetySensor } from './api/safety'
import { useWebSocket } from './hooks/useWebSocket'
import { createHATheme } from './theme'

// Lazy load heavy components for better performance
const ZoneDetail = lazy(() => import('./pages/AreaDetail'))
const SettingsLayout = lazy(() => import('./components/SettingsLayout'))
const DevicesView = lazy(() => import('./pages/DevicesView'))
const AnalyticsMenu = lazy(() => import('./pages/AnalyticsMenu'))
const EfficiencyReports = lazy(() => import('./components/EfficiencyReports'))
const HistoricalComparisons = lazy(() => import('./components/HistoricalComparisons'))
const DeviceLogsView = lazy(() => import('./pages/DeviceLogsView'))

// Loading component
const PageLoader = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '60vh',
    }}
  >
    <CircularProgress />
  </Box>
)

interface ZonesOverviewProps {
  wsConnected: boolean
  safetyAlertActive: boolean
  areas: Zone[]
  loading: boolean
  showHidden: boolean
  handleZonesUpdate: () => void
  setShowHidden: (value: boolean) => void
  onAreasReorder: (areas: Zone[]) => void
  listContainerRef?: React.RefObject<HTMLDivElement | null>
  onPatchArea?: (areaId: string, patch: Partial<Zone>) => void
}

const ZonesOverview = ({
  wsConnected,
  safetyAlertActive,
  areas,
  loading,
  showHidden,
  handleZonesUpdate,
  setShowHidden,
  onAreasReorder,
  transportMode,
  listContainerRef,
  onPatchArea,
}: ZonesOverviewProps & { transportMode: 'websocket' | 'polling' }) => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      bgcolor: 'background.default',
    }}
  >
    <Header wsConnected={wsConnected} transportMode={transportMode} />
    <Box
      sx={{
        display: 'flex',
        flex: 1,
        overflow: 'hidden',
        flexDirection: { xs: 'column', md: 'row' },
      }}
    >
      <Box
        sx={{
          flex: 1,
          overflow: 'auto',
          p: { xs: 1.5, sm: 2, md: 3 },
          bgcolor: 'background.default',
        }}
        data-testid="zones-scroll-container"
        ref={listContainerRef}
      >
        {safetyAlertActive && (
          <Alert
            severity="error"
            sx={{ mb: 2 }}
            icon={<span style={{ fontSize: '24px' }}>🚨</span>}
          >
            <strong>SAFETY ALERT ACTIVE!</strong> All heating has been shut down due to a safety
            sensor alert. Please resolve the safety issue and manually re-enable areas in Settings.
          </Alert>
        )}
        <VacationModeBanner />
        <ZoneList
          areas={areas}
          loading={loading}
          onUpdate={handleZonesUpdate}
          showHidden={showHidden}
          onToggleShowHidden={() => setShowHidden(!showHidden)}
          onAreasReorder={onAreasReorder}
          onPatchArea={onPatchArea}
        />
      </Box>
    </Box>
  </Box>
)

function App() {
  const [areas, setAreas] = useState<Zone[]>([])
  const [loading, setLoading] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)
  const [showConnectionAlert, setShowConnectionAlert] = useState(false)
  const [showHidden, setShowHidden] = useState(false)
  const [safetyAlertActive, setSafetyAlertActive] = useState(false)
  const [themeMode, setThemeMode] = useState<'light' | 'dark'>(() => {
    // Load theme preference from localStorage
    const saved = localStorage.getItem('appThemeMode')
    return saved === 'light' || saved === 'dark' ? saved : 'dark'
  })

  // Ref to the main scrolling container so we can preserve viewport on updates
  const listContainerRef = useRef<HTMLDivElement | null>(null)

  const loadData = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true)
      const [areasData, safetySensorData] = await Promise.all([
        getZones(),
        getSafetySensor().catch(() => null),
      ])

      // Apply saved area order from localStorage
      const savedOrder = localStorage.getItem('areasOrder')
      let orderedAreas = areasData
      if (savedOrder) {
        try {
          const orderIds = JSON.parse(savedOrder)
          const areaMap = new Map(areasData.map(a => [a.id, a]))
          orderedAreas = orderIds
            .map((id: string) => areaMap.get(id))
            .filter((a: Zone | undefined): a is Zone => a !== undefined)
          // Add any new areas that weren't in the saved order
          const orderedIds = new Set(orderIds)
          const newAreas = areasData.filter(a => !orderedIds.has(a.id))
          orderedAreas = [...orderedAreas, ...newAreas]
        } catch {
          // If parsing fails, use default order
        }
      }

      // Preserve scroll position to avoid viewport jumps when replacing areas
      const prevScroll = listContainerRef.current?.scrollTop ?? 0
      setAreas(orderedAreas)
      requestAnimationFrame(() => {
        if (listContainerRef.current) listContainerRef.current.scrollTop = prevScroll
      })

      // Check if safety alert is active
      if (safetySensorData?.alert_active) {
        setSafetyAlertActive(true)
      } else {
        setSafetyAlertActive(false)
      }
    } catch (error) {
      console.error('Failed to load data:', error)
    } finally {
      if (showLoading) setLoading(false)
    }
  }, [])

  // WebSocket connection for real-time updates
  const { metrics: wsMetrics, transportMode } = useWebSocket({
    onConnect: () => {
      setWsConnected(true)
      setShowConnectionAlert(false)
      // Reload safety sensor status when reconnecting
      getSafetySensor()
        .then(data => setSafetyAlertActive(data?.alert_active || false))
        .catch(() => setSafetyAlertActive(false))
    },
    onDisconnect: () => {
      setWsConnected(false)
      setShowConnectionAlert(true)
    },
    onZonesUpdate: updatedZones => {
      const savedOrder = localStorage.getItem('areasOrder')

      // Preserve scroll position of the main list container to avoid viewport jumps
      const prevScroll = listContainerRef.current?.scrollTop ?? 0

      // Merge updated list with saved order or previous client order
      setAreas(prev => mergeZones(prev, updatedZones, savedOrder))

      // Also refresh safety sensor status
      getSafetySensor()
        .then(data => setSafetyAlertActive(data?.alert_active || false))
        .catch(() => setSafetyAlertActive(false))

      // Restore scroll on next paint to keep viewport stable
      requestAnimationFrame(() => {
        if (listContainerRef.current) listContainerRef.current.scrollTop = prevScroll
      })
    },
    onZoneUpdate: updatedZone => {
      const prevScroll = listContainerRef.current?.scrollTop ?? 0
      setAreas(prevAreas => prevAreas.map(z => (z.id === updatedZone.id ? updatedZone : z)))
      requestAnimationFrame(() => {
        if (listContainerRef.current) listContainerRef.current.scrollTop = prevScroll
      })
    },
    onZoneDelete: areaId => {
      const prevScroll = listContainerRef.current?.scrollTop ?? 0
      setAreas(prevAreas => prevAreas.filter(z => z.id !== areaId))
      // Reload data to update available devices (background refresh)
      loadData(false)
      requestAnimationFrame(() => {
        if (listContainerRef.current) listContainerRef.current.scrollTop = prevScroll
      })
    },
    onError: error => {
      console.error('WebSocket error:', error)
    },
  })

  // Save theme preference to localStorage when changed
  useEffect(() => {
    localStorage.setItem('appThemeMode', themeMode)
  }, [themeMode])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleZonesUpdate = () => {
    // Perform a background refresh so UI doesn't show full-page loader
    loadData(false)
  }

  const handlePatchArea = (areaId: string, patch: Partial<Zone>) => {
    setAreas((prev: Zone[]) => prev.map((a: Zone) => (a.id === areaId ? { ...a, ...patch } : a)))
  }

  // Device drag-drop temporarily disabled - will be re-implemented with @dnd-kit

  return (
    <ThemeProvider theme={createHATheme(themeMode)}>
      <CssBaseline />
      <Router basename="/smart_heating_ui">
        <Suspense fallback={<PageLoader />}>
          <Routes>
            <Route
              path="/"
              element={
                <ZonesOverview
                  wsConnected={wsConnected}
                  safetyAlertActive={safetyAlertActive}
                  areas={areas}
                  loading={loading}
                  showHidden={showHidden}
                  handleZonesUpdate={handleZonesUpdate}
                  setShowHidden={setShowHidden}
                  transportMode={transportMode}
                  listContainerRef={listContainerRef}
                  onPatchArea={handlePatchArea}
                  onAreasReorder={reorderedAreas => {
                    setAreas(reorderedAreas)
                    // Persist to localStorage
                    const orderIds = reorderedAreas.map(a => a.id)
                    localStorage.setItem('areasOrder', JSON.stringify(orderIds))
                  }}
                />
              }
            />
            <Route path="/area/:areaId" element={<ZoneDetail />} />

            {/* Devices View */}
            <Route path="/devices" element={<DevicesView />} />

            {/* Analytics */}
            <Route path="/analytics" element={<AnalyticsMenu />} />
            <Route path="/analytics/efficiency" element={<EfficiencyReports />} />
            <Route path="/analytics/comparison" element={<HistoricalComparisons />} />

            {/* Device logs (live) */}
            <Route path="/devices/logs" element={<DeviceLogsView />} />

            {/* Settings */}
            <Route
              path="/settings"
              element={
                <SettingsLayout
                  themeMode={themeMode}
                  onThemeChange={setThemeMode}
                  wsMetrics={wsMetrics}
                />
              }
            />
            <Route
              path="/settings/*"
              element={
                <SettingsLayout
                  themeMode={themeMode}
                  onThemeChange={setThemeMode}
                  wsMetrics={wsMetrics}
                />
              }
            />
          </Routes>
        </Suspense>

        {/* Mobile Bottom Navigation */}
        <MobileBottomNav />
      </Router>

      {/* Connection status notification */}
      <Snackbar
        open={showConnectionAlert}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
        autoHideDuration={null}
      >
        <Alert
          severity="warning"
          onClose={() => setShowConnectionAlert(false)}
          sx={{ width: '100%' }}
        >
          WebSocket disconnected. Real-time updates disabled.
        </Alert>
      </Snackbar>
    </ThemeProvider>
  )
}

export default App
