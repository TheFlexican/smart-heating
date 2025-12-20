import { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Paper,
  Typography,
  ToggleButtonGroup,
  ToggleButton,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Chip,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { getAdvancedMetrics } from '../api/metrics'
import { useWebSocket } from '../hooks/useWebSocket'

export default function DeviceLogsPanel() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<any[]>([])
  // minutes picker: 1,2,3,5 minute options
  const [timeRange, setTimeRange] = useState<1 | 2 | 3 | 5>(1)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [mounted, setMounted] = useState(true)
  const [deviceEvents, setDeviceEvents] = useState<any[]>([])

  const { send } = useWebSocket()

  const loadData = useCallback(async () => {
    try {
      setError(null)
      const data = await getAdvancedMetrics(timeRange)
      if (mounted) {
        setMetrics(data.metrics)
      }
    } catch (err) {
      console.error('Failed to load device logs:', err)
      if (mounted) setError('Failed to load device logs')
    } finally {
      if (mounted) setLoading(false)
    }
  }, [timeRange, mounted])

  useEffect(() => {
    setMounted(true)
    loadData()
    return () => setMounted(false)
  }, [loadData])

  // Subscribe to live device events and request backend subscription via WS
  useEffect(() => {
    if (!mounted) return

    // Request backend to start sending device events over websocket
    try {
      send({ type: 'smart_heating/subscribe_device_logs' })
    } catch {
      // ignore
    }

    const handler = (e: any) => {
      try {
        const evt = e?.detail || e
        setDeviceEvents(prev => [evt, ...prev].slice(0, 200))
      } catch {
        // ignore
      }
    }

    globalThis.addEventListener('smart_heating.device_event', handler as EventListener)
    return () =>
      globalThis.removeEventListener('smart_heating.device_event', handler as EventListener)
  }, [send, mounted])

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h6">{t('deviceLogs.title', 'Device Logs')}</Typography>
        <Box>
          <FormControlLabel
            control={
              <Switch checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
            }
            label={t('deviceLogs.autoRefresh', 'Auto-refresh')}
          />
          <ToggleButtonGroup
            value={timeRange}
            exclusive
            onChange={(_, value) => value && setTimeRange(value)}
            size="small"
          >
            <ToggleButton value={1}>1m</ToggleButton>
            <ToggleButton value={2}>2m</ToggleButton>
            <ToggleButton value={3}>3m</ToggleButton>
            <ToggleButton value={5}>5m</ToggleButton>
          </ToggleButtonGroup>
        </Box>
      </Box>

      {error && <Alert severity="error">{error}</Alert>}

      {/* Show latest metric's thermostat failures grouped by area */}
      {metrics.length === 0 ? (
        <Alert severity="info">{t('deviceLogs.noData', 'No logs available yet')}</Alert>
      ) : (
        <Paper sx={{ p: 2 }}>
          <Typography variant="subtitle1" sx={{ mb: 2 }}>
            {t('deviceLogs.latest', 'Latest device failure/backoff entries')}
          </Typography>

          {/* Use the latest metrics entry */}
          {(() => {
            const latest = metrics[metrics.length - 1]
            const areaMetrics = latest?.area_metrics || {}
            const rows: Array<{ areaId: string; tid: string; info: any }> = []
            Object.entries(areaMetrics).forEach(([areaId, info]: any) => {
              if (info?.thermostat_failures) {
                Object.entries(info.thermostat_failures).forEach(([tid, st]: any) => {
                  rows.push({ areaId, tid, info: st })
                })
              }
            })

            if (rows.length === 0) {
              return (
                <Alert severity="info">
                  {t('deviceLogs.noFailures', 'No device failures recorded')}
                </Alert>
              )
            }

            return (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Area</TableCell>
                    <TableCell>Thermostat</TableCell>
                    <TableCell>Failures</TableCell>
                    <TableCell>Last Failure</TableCell>
                    <TableCell>Backoff (s)</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rows.map(r => (
                    <TableRow key={`${r.areaId}-${r.tid}`}>
                      <TableCell>{r.areaId}</TableCell>
                      <TableCell>{r.tid}</TableCell>
                      <TableCell>
                        <Chip
                          label={String(r.info.count)}
                          color={r.info.count > 0 ? 'warning' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        {new Date((r.info.last_failure || 0) * 1000).toLocaleString()}
                      </TableCell>
                      <TableCell>{String(r.info.retry_seconds || '')}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            )
          })()}

          {/* Live device events (recent) */}
          <Box sx={{ mt: 3 }}>
            <Typography variant="subtitle1" sx={{ mb: 1 }}>
              {t('deviceLogs.liveEvents', 'Live device events')}
            </Typography>
            {deviceEvents.length === 0 ? (
              <Alert severity="info">{t('deviceLogs.noLiveEvents', 'No live events yet')}</Alert>
            ) : (
              <Paper sx={{ p: 1, maxHeight: 300, overflow: 'auto' }}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Time</TableCell>
                      <TableCell>Area</TableCell>
                      <TableCell>Device</TableCell>
                      <TableCell>Direction</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell>Details</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {deviceEvents
                      .slice()
                      .sort((a, b) => (b.timestamp || Date.now()) - (a.timestamp || Date.now()))
                      .map((ev: any, idx: number) => (
                        <TableRow
                          key={`${ev.timestamp || idx}-${ev.device_id || ev.deviceId || ev.id || idx}`}
                        >
                          <TableCell>
                            {new Date(ev.timestamp || Date.now()).toLocaleString()}
                          </TableCell>
                          <TableCell>{ev.area_id || ev.areaId || ''}</TableCell>
                          <TableCell>{ev.device_id || ev.deviceId || ev.id || ''}</TableCell>
                          <TableCell>{ev.direction || ev.dir || ''}</TableCell>
                          <TableCell>{ev.action || ev.service || ''}</TableCell>
                          <TableCell>
                            <Typography variant="caption">
                              {JSON.stringify(ev.payload || ev.data || ev.details || {})}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                  </TableBody>
                </Table>
              </Paper>
            )}
          </Box>
        </Paper>
      )}
    </Box>
  )
}
