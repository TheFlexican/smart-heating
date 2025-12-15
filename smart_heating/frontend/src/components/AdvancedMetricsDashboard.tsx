import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Grid,
  Card,
  CardContent,
  ToggleButtonGroup,
  ToggleButton,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert,
  Chip,
  Stack,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SpeedIcon from '@mui/icons-material/Speed'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import OpacityIcon from '@mui/icons-material/Opacity'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Area as RechartsArea,
  AreaChart,
} from 'recharts'
import { useTranslation } from 'react-i18next'
import { getAdvancedMetrics } from '../api/metrics'
import { getZones } from '../api/areas'
import { AdvancedMetricPoint, Zone } from '../types'
import { useWebSocket } from '../hooks/useWebSocket'

export default function AdvancedMetricsDashboard() {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<AdvancedMetricPoint[]>([])
  const [areas, setAreas] = useState<Zone[]>([])
  const [timeRange, setTimeRange] = useState<1 | 3 | 7 | 30>(7)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())
  const [mounted, setMounted] = useState(true)

  // WebSocket for real-time updates
  useWebSocket({
    onZonesUpdate: () => {
      // Only reload if component is still mounted and auto-refresh is enabled
      if (mounted && autoRefresh) {
        loadData()
      }
    },
  })

  const loadData = async () => {
    try {
      setError(null)
      const [metricsData, areasData] = await Promise.all([
        getAdvancedMetrics(timeRange),
        getZones(),
      ])

      // Only update state if component is still mounted
      if (mounted) {
        setMetrics(metricsData.metrics)
        setAreas(areasData)
        setLastUpdate(new Date())
      }
    } catch (err) {
      console.error('Failed to load advanced metrics:', err)
      if (mounted) {
        setError('Failed to load metrics data')
      }
    } finally {
      if (mounted) {
        setLoading(false)
      }
    }
  }

  useEffect(() => {
    setMounted(true)
    loadData()

    return () => {
      setMounted(false)
    }
  }, [timeRange])

  useEffect(() => {
    if (!autoRefresh || !mounted) return

    const interval = setInterval(() => {
      if (mounted) {
        loadData()
      }
    }, 30000) // 30 seconds

    return () => clearInterval(interval)
  }, [autoRefresh, timeRange, mounted])

  // Transform metrics for charts
  const heatingCurveData = metrics.map(m => ({
    time: new Date(m.timestamp).toLocaleTimeString('nl-NL', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    timestamp: m.timestamp,
    outdoor: m.outdoor_temp,
    flow: m.boiler_flow_temp,
    return: m.boiler_return_temp,
    setpoint: m.boiler_setpoint,
  }))

  const modulationData = metrics.map(m => ({
    time: new Date(m.timestamp).toLocaleTimeString('nl-NL', {
      hour: '2-digit',
      minute: '2-digit',
    }),
    timestamp: m.timestamp,
    modulation: m.modulation_level,
    flame: m.flame_on ? 100 : 0,
  }))

  // Calculate statistics
  const stats = {
    avgModulation:
      metrics.length > 0
        ? (metrics.reduce((acc, m) => acc + (m.modulation_level || 0), 0) / metrics.length).toFixed(
            1,
          )
        : '0',
    avgFlowTemp:
      metrics.length > 0
        ? (metrics.reduce((acc, m) => acc + (m.boiler_flow_temp || 0), 0) / metrics.length).toFixed(
            1,
          )
        : '0',
    avgReturnTemp:
      metrics.length > 0
        ? (
            metrics.reduce((acc, m) => acc + (m.boiler_return_temp || 0), 0) / metrics.length
          ).toFixed(1)
        : '0',
    flameOnPercent:
      metrics.length > 0
        ? ((metrics.filter(m => m.flame_on).length / metrics.length) * 100).toFixed(1)
        : '0',
    tempDelta:
      metrics.length > 0
        ? (
            metrics.reduce(
              (acc, m) => acc + ((m.boiler_flow_temp || 0) - (m.boiler_return_temp || 0)),
              0,
            ) / metrics.length
          ).toFixed(1)
        : '0',
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <IconButton onClick={() => navigate('/settings/global')} size="large" color="primary">
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography variant="h4" gutterBottom>
              {t('advancedMetrics.title', 'Advanced Metrics & Performance')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {t('advancedMetrics.subtitle', 'Real-time heating system analysis')}
            </Typography>
          </Box>
        </Box>

        {/* Controls */}
        <Stack direction="row" spacing={2} alignItems="center">
          <FormControlLabel
            control={
              <Switch checked={autoRefresh} onChange={e => setAutoRefresh(e.target.checked)} />
            }
            label={t('advancedMetrics.autoRefresh', 'Auto-refresh (30s)')}
          />
          <ToggleButtonGroup
            value={timeRange}
            exclusive
            onChange={(_, value) => value && setTimeRange(value)}
            size="small"
          >
            <ToggleButton value={1}>1{t('advancedMetrics.day', 'd')}</ToggleButton>
            <ToggleButton value={3}>3{t('advancedMetrics.day', 'd')}</ToggleButton>
            <ToggleButton value={7}>7{t('advancedMetrics.day', 'd')}</ToggleButton>
            <ToggleButton value={30}>30{t('advancedMetrics.day', 'd')}</ToggleButton>
          </ToggleButtonGroup>
        </Stack>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {metrics.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t(
            'advancedMetrics.noData',
            'No metrics data yet. Data is collected every 5 minutes. Check back soon!',
          )}
        </Alert>
      )}

      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
        {t('advancedMetrics.lastUpdate', 'Last updated')}: {lastUpdate.toLocaleTimeString()}
      </Typography>

      {/* Section 1: Heating Curve Performance */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {t('advancedMetrics.heatingCurve.title', 'Heating Curve Performance')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t(
            'advancedMetrics.heatingCurve.description',
            'Shows how the system proactively adjusts flow temperature based on outdoor conditions',
          )}
        </Typography>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={heatingCurveData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis label={{ value: '°C', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="outdoor"
              stroke="#8884d8"
              name={t('advancedMetrics.outdoorTemp', 'Outdoor')}
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="setpoint"
              stroke="#ff7300"
              name={t('advancedMetrics.setpoint', 'Setpoint')}
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="flow"
              stroke="#82ca9d"
              name={t('advancedMetrics.flowTemp', 'Flow')}
              strokeWidth={2}
            />
            <Line
              type="monotone"
              dataKey="return"
              stroke="#ffc658"
              name={t('advancedMetrics.returnTemp', 'Return')}
              strokeWidth={1}
            />
          </LineChart>
        </ResponsiveContainer>
      </Paper>

      {/* Section 2: Boiler Efficiency Metrics */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom>
          {t('advancedMetrics.efficiency.title', 'Boiler Efficiency')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t(
            'advancedMetrics.efficiency.description',
            'Modulation stability and thermal performance indicators',
          )}
        </Typography>

        {/* Statistics Cards */}
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={1} alignItems="center">
                  <SpeedIcon color="primary" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {t('advancedMetrics.avgModulation', 'Avg Modulation')}
                    </Typography>
                    <Typography variant="h6">{stats.avgModulation}%</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={1} alignItems="center">
                  <LocalFireDepartmentIcon color="error" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {t('advancedMetrics.flameOn', 'Flame Active')}
                    </Typography>
                    <Typography variant="h6">{stats.flameOnPercent}%</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={1} alignItems="center">
                  <ThermostatIcon color="success" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {t('advancedMetrics.avgFlow', 'Avg Flow Temp')}
                    </Typography>
                    <Typography variant="h6">{stats.avgFlowTemp}°C</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={1} alignItems="center">
                  <OpacityIcon color="info" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {t('advancedMetrics.avgReturn', 'Avg Return Temp')}
                    </Typography>
                    <Typography variant="h6">{stats.avgReturnTemp}°C</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={1} alignItems="center">
                  <TrendingUpIcon color="warning" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      {t('advancedMetrics.tempDelta', 'Temp Delta')}
                    </Typography>
                    <Typography variant="h6">{stats.tempDelta}°C</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>

        {/* Modulation Chart */}
        <ResponsiveContainer width="100%" height={250}>
          <AreaChart data={modulationData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" />
            <YAxis label={{ value: '%', angle: -90, position: 'insideLeft' }} />
            <Tooltip />
            <Legend />
            <RechartsArea
              type="monotone"
              dataKey="modulation"
              stroke="#8884d8"
              fill="#8884d8"
              name={t('advancedMetrics.modulation', 'Modulation Level')}
            />
          </AreaChart>
        </ResponsiveContainer>

        <Alert severity="info" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>{t('advancedMetrics.efficiency.tip', 'Tip')}:</strong>{' '}
            {t(
              'advancedMetrics.efficiency.tipText',
              'Stable modulation between 30-60% indicates efficient operation. Large fluctuations suggest the system is cycling on/off frequently.',
            )}
          </Typography>
        </Alert>
      </Paper>

      {/* Section 3: Per-Area Features */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h5" gutterBottom>
          {t('advancedMetrics.areas.title', 'Active Area Features')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t(
            'advancedMetrics.areas.description',
            'Current advanced feature configuration per heating area',
          )}
        </Typography>

        <Grid container spacing={2}>
          {areas
            .filter(area => area.enabled)
            .map(area => {
              const latestMetric = metrics[metrics.length - 1]
              const areaData = latestMetric?.area_metrics?.[area.id]

              return (
                <Grid size={{ xs: 12, sm: 6, md: 4 }} key={area.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" gutterBottom>
                        {area.name}
                      </Typography>

                      <Stack spacing={1}>
                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">
                            {t('advancedMetrics.heatingType', 'Heating Type')}:
                          </Typography>
                          <Chip
                            size="small"
                            label={(() => {
                              if (areaData?.heating_type === 'floor_heating')
                                return t('advancedMetrics.floorHeating', 'Floor')
                              if (areaData?.heating_type === 'airco')
                                return t('advancedMetrics.airConditioner', 'Air Conditioner')
                              return t('advancedMetrics.radiator', 'Radiator')
                            })()}
                            color={
                              areaData?.heating_type === 'floor_heating' ? 'primary' : 'default'
                            }
                          />
                        </Box>

                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">
                            {t('advancedMetrics.currentTemp', 'Current')}:
                          </Typography>
                          <Typography variant="body2">
                            {areaData?.current_temp?.toFixed(1) || '--'}°C
                          </Typography>
                        </Box>

                        <Box display="flex" justifyContent="space-between">
                          <Typography variant="body2" color="text.secondary">
                            {t('advancedMetrics.targetTemp', 'Target')}:
                          </Typography>
                          <Typography variant="body2">
                            {areaData?.target_temp?.toFixed(1) || '--'}°C
                          </Typography>
                        </Box>

                        {areaData?.heating_curve_coefficient && (
                          <Box display="flex" justifyContent="space-between">
                            <Typography variant="body2" color="text.secondary">
                              {t('advancedMetrics.coefficient', 'Coefficient')}:
                            </Typography>
                            <Chip
                              size="small"
                              label={areaData.heating_curve_coefficient.toFixed(2)}
                              color="secondary"
                            />
                          </Box>
                        )}

                        {areaData?.hysteresis_override && (
                          <Box display="flex" justifyContent="space-between">
                            <Typography variant="body2" color="text.secondary">
                              {t('advancedMetrics.hysteresis', 'Hysteresis')}:
                            </Typography>
                            <Typography variant="body2">
                              {areaData.hysteresis_override.toFixed(1)}°C
                            </Typography>
                          </Box>
                        )}

                        <Chip
                          size="small"
                          label={areaData?.state || 'unknown'}
                          color={areaData?.state === 'heating' ? 'success' : 'default'}
                        />
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              )
            })}
        </Grid>
      </Paper>
    </Box>
  )
}
