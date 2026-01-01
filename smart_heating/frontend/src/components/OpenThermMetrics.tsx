import { useState, useEffect, useCallback } from 'react'
import {
  Box,
  Paper,
  Typography,
  Card,
  CardContent,
  Stack,
  ToggleButtonGroup,
  ToggleButton,
  Switch,
  FormControlLabel,
  CircularProgress,
  Alert,
} from '@mui/material'

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
import { AdvancedMetricPoint } from '../types'

export default function OpenThermMetrics() {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [metrics, setMetrics] = useState<AdvancedMetricPoint[]>([])
  const [timeRange, setTimeRange] = useState<1 | 3 | 7 | 30>(7)
  const [autoRefresh, setAutoRefresh] = useState(true)
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date())

  const loadData = useCallback(async () => {
    try {
      setError(null)
      const metricsData = await getAdvancedMetrics(timeRange)
      setMetrics(metricsData.metrics || [])
      setLastUpdate(new Date())
    } catch (err) {
      console.error('Failed to load advanced metrics:', err)
      setError(t('advancedMetrics.loadError', 'Failed to load metrics'))
    } finally {
      setLoading(false)
    }
  }, [timeRange, t])

  useEffect(() => {
    setLoading(true)
    loadData()
  }, [loadData])

  useEffect(() => {
    if (!autoRefresh) return
    const iv = setInterval(() => loadData(), 30000)
    return () => clearInterval(iv)
  }, [autoRefresh, loadData])

  const heatingCurveData = metrics.map(m => ({
    time: new Date(m.timestamp).toLocaleTimeString(),
    outdoor: m.outdoor_temp,
    flow: m.boiler_flow_temp,
    return: m.boiler_return_temp,
    setpoint: m.boiler_setpoint,
  }))

  const modulationData = metrics.map(m => ({
    time: new Date(m.timestamp).toLocaleTimeString(),
    modulation: m.modulation_level,
    flame: m.flame_on ? 100 : 0,
  }))

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
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h6">{t('opentherm.metricsTitle', 'OpenTherm Metrics')}</Typography>
          <Typography variant="body2" color="text.secondary">
            {t('opentherm.metricsSubtitle', 'Historical OpenTherm performance and boiler metrics')}
          </Typography>
        </Box>

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
            onChange={(_, v) => v && setTimeRange(v)}
            size="small"
          >
            <ToggleButton value={1}>1d</ToggleButton>
            <ToggleButton value={3}>3d</ToggleButton>
            <ToggleButton value={7}>7d</ToggleButton>
            <ToggleButton value={30}>30d</ToggleButton>
          </ToggleButtonGroup>
        </Stack>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
        {t('advancedMetrics.lastUpdate', 'Last updated')}: {lastUpdate.toLocaleTimeString()}
      </Typography>

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t('advancedMetrics.heatingCurve.title', 'Heating Curve Performance')}
        </Typography>
        <ResponsiveContainer width="100%" height={260}>
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

      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          {t('advancedMetrics.efficiency.title', 'Boiler Efficiency')}
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2,1fr)', md: 'repeat(5,1fr)' },
            gap: 2,
            mb: 3,
          }}
        >
          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                {t('advancedMetrics.avgModulation', 'Avg Modulation')}
              </Typography>
              <Typography variant="h6">{stats.avgModulation}%</Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                {t('advancedMetrics.flameOn', 'Flame Active')}
              </Typography>
              <Typography variant="h6">{stats.flameOnPercent}%</Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                {t('advancedMetrics.avgFlow', 'Avg Flow Temp')}
              </Typography>
              <Typography variant="h6">{stats.avgFlowTemp}°C</Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                {t('advancedMetrics.avgReturn', 'Avg Return Temp')}
              </Typography>
              <Typography variant="h6">{stats.avgReturnTemp}°C</Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="caption" color="text.secondary">
                {t('advancedMetrics.tempDelta', 'Temp Delta')}
              </Typography>
              <Typography variant="h6">{stats.tempDelta}°C</Typography>
            </CardContent>
          </Card>
        </Box>

        <ResponsiveContainer width="100%" height={240}>
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
      </Paper>
    </Box>
  )
}
