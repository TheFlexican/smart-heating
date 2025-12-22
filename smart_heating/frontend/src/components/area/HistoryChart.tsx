import { useState, useEffect, useCallback } from 'react'

// Helper moved outside component for lint rules and testability
function legendFormatter(value: any, entry: any) {
  let id = 'history-legend-item-unknown'
  const val = String(value || '')
  if (entry?.dataKey) {
    id = `history-legend-item-${entry.dataKey}`
  } else if (val.includes('currentTempLine') || val.toLowerCase().includes('current')) {
    id = 'history-legend-item-current'
  } else if (val.includes('targetTempLine') || val.toLowerCase().includes('target')) {
    id = 'history-legend-item-target'
  } else if (val.toLowerCase().includes('heating')) {
    id = 'history-legend-item-heating'
  } else if (val.toLowerCase().includes('cooling')) {
    id = 'history-legend-item-cooling'
  }
  return <span data-testid={id}>{value}</span>
}
import { useTranslation } from 'react-i18next'
import {
  Box,
  CircularProgress,
  Alert,
  ToggleButtonGroup,
  ToggleButton,
  TextField,
  Button,
  FormControlLabel,
  Checkbox,
  Stack,
} from '@mui/material'
import { TrvHistoryEntry } from '../../types'
import CustomTooltip from '../common/CustomTooltip'

import {
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Scatter,
  ComposedChart,
} from 'recharts'
import { getHistory } from '../../api/history'

interface HistoryEntry {
  timestamp: string
  current_temperature: number
  target_temperature: number
  state: string
  trvs?: TrvHistoryEntry[]
}

interface HistoryChartProps {
  areaId: string
}

const HistoryChart = ({ areaId }: HistoryChartProps) => {
  const { t } = useTranslation()
  const [data, setData] = useState<HistoryEntry[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [timeRange, setTimeRange] = useState<number>(4)
  const [customRange, setCustomRange] = useState(false)
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [showHeating, setShowHeating] = useState(true)
  const [showCooling, setShowCooling] = useState(true)
  const [showTrvs, setShowTrvs] = useState(true)

  const loadHistory = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      let result
      if (customRange && startTime && endTime) {
        // Custom time range
        result = await getHistory(areaId, {
          startTime: new Date(startTime).toISOString(),
          endTime: new Date(endTime).toISOString(),
        })
      } else {
        // Preset time range
        result = await getHistory(areaId, { hours: timeRange })
      }

      setData(result.entries || [])
    } catch (err) {
      console.error('Failed to load history:', err)
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }, [areaId, timeRange, customRange, startTime, endTime])

  useEffect(() => {
    loadHistory()

    // Refresh every 5 minutes
    const interval = setInterval(loadHistory, 5 * 60 * 1000)
    return () => clearInterval(interval)
  }, [loadHistory])

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>
  }

  if (!data || data.length === 0) {
    return (
      <Alert severity="info">
        No history data available yet. Temperature readings will be recorded every 5 minutes.
      </Alert>
    )
  }

  // Sort data oldest -> newest so current time appears on the right of the chart
  const sortedData = data.slice().sort((a, b) => {
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
  })

  // Derive TRV entity ids present in history entries
  const trvIds = Array.from(new Set(sortedData.flatMap(e => (e.trvs || []).map(t => t.entity_id))))

  // Format data for chart and include TRV fields dynamically
  const chartData = sortedData.map(entry => {
    const base: any = {
      time: new Date(entry.timestamp).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }),
      current: entry.current_temperature,
      target: entry.target_temperature,
      // For heating/cooling indicator scatter plot
      heatingDot: entry.state === 'heating' ? entry.current_temperature : null,
      coolingDot: entry.state === 'cooling' ? entry.current_temperature : null,
      // Store state for custom tooltip
      heatingState: entry.state,
    }

    // Add TRV series fields
    for (const id of trvIds) {
      const trv = (entry.trvs || []).find(t => t.entity_id === id)
      const sanitized = id
        .replaceAll('.', '_')
        .replaceAll('/', '_')
        .replaceAll(':', '_')
        .replaceAll('-', '_')
        .replaceAll(' ', '_')
      base[`trv_${sanitized}_position`] = trv?.position ?? null
      // For open markers, use position when available, else a fixed 100 marker
      base[`trv_${sanitized}_open`] = trv?.open ? (trv.position ?? 100) : null
    }

    return base
  })

  const hasCooling = chartData.some(d => d.coolingDot !== null && d.coolingDot !== undefined)

  // Custom tooltip moved outside to satisfy lint rules; t passed in as prop

  // Calculate average target temperature for reference line
  const avgTarget =
    data.length > 0
      ? data.reduce((sum, entry) => sum + entry.target_temperature, 0) / data.length
      : null

  return (
    <Box>
      <Stack spacing={2} sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <ToggleButtonGroup
            value={customRange ? 'custom' : timeRange}
            exclusive
            onChange={(_e, value) => {
              if (value === 'custom') {
                setCustomRange(true)
              } else if (value) {
                setCustomRange(false)
                setTimeRange(value)
              }
            }}
            size="small"
          >
            <ToggleButton data-testid="history-range-1h" value={1}>
              1h
            </ToggleButton>
            <ToggleButton data-testid="history-range-2h" value={2}>
              2h
            </ToggleButton>
            <ToggleButton data-testid="history-range-4h" value={4}>
              4h
            </ToggleButton>
            <ToggleButton data-testid="history-range-8h" value={8}>
              8h
            </ToggleButton>
            <ToggleButton data-testid="history-range-24h" value={24}>
              24h
            </ToggleButton>
            <ToggleButton data-testid="history-range-custom" value="custom">
              Custom
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {customRange && (
          <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
            <TextField
              label="Start Date & Time"
              type="datetime-local"
              value={startTime}
              onChange={e => setStartTime(e.target.value)}
              data-testid="history-start-datetime"
              slotProps={{ inputLabel: { shrink: true } }}
              size="small"
              sx={{ flex: 1 }}
            />
            <TextField
              label="End Date & Time"
              type="datetime-local"
              value={endTime}
              onChange={e => setEndTime(e.target.value)}
              data-testid="history-end-datetime"
              slotProps={{ inputLabel: { shrink: true } }}
              size="small"
              sx={{ flex: 1 }}
            />
            <Button
              data-testid="history-apply-button"
              variant="contained"
              onClick={loadHistory}
              disabled={!startTime || !endTime}
            >
              Apply
            </Button>
          </Box>
        )}
      </Stack>
      <div data-testid="history-chart">
        <ResponsiveContainer width="100%" height={400}>
          <ComposedChart data={chartData}>
            <CartesianGrid
              horizontal={true}
              vertical={false}
              stroke="#2c2c2c"
              strokeOpacity={0.18}
            />
            {/* Reduce label clutter: show up to 6 evenly spaced ticks */}
            <XAxis
              dataKey="time"
              stroke="#9e9e9e"
              tick={{ fill: '#9e9e9e', fontSize: 11 }}
              angle={-45}
              textAnchor="end"
              height={60}
              ticks={(() => {
                const maxTicks = 6
                const len = chartData.length
                if (len <= maxTicks) return chartData.map(d => d.time)
                const step = Math.ceil(len / maxTicks)
                return chartData.filter((_, i) => i % step === 0).map(d => d.time)
              })()}
            />
            <YAxis
              stroke="#9e9e9e"
              tick={{ fill: '#9e9e9e' }}
              domain={['dataMin - 2', 'dataMax + 2']}
              label={{
                value: 'Temperature (°C)',
                angle: -90,
                position: 'insideLeft',
                fill: '#9e9e9e',
              }}
            />

            {trvIds.length > 0 && (
              <YAxis
                yAxisId="right"
                orientation="right"
                stroke="#9e9e9e"
                tick={{ fill: '#9e9e9e' }}
                domain={[0, 100]}
                label={{
                  value: 'Position (%)',
                  angle: 90,
                  position: 'insideRight',
                  fill: '#9e9e9e',
                }}
              />
            )}
            <Tooltip content={<CustomTooltip />} />
            <Legend wrapperStyle={{ color: '#e1e1e1' }} formatter={legendFormatter} />
            {avgTarget && (
              <ReferenceLine
                y={avgTarget}
                stroke="#4caf50"
                strokeWidth={1}
                label={{
                  value: `Avg: ${avgTarget.toFixed(1)}°C`,
                  position: 'right',
                  fill: '#4caf50',
                  fontSize: 12,
                }}
              />
            )}
            <Line
              type="monotone"
              dataKey="current"
              stroke="#03a9f4"
              strokeWidth={2}
              dot={false}
              name={t('areaDetail.currentTempLine')}
            />
            <Line
              type="stepAfter"
              dataKey="target"
              stroke="#ffc107"
              strokeWidth={2}
              dot={false}
              name={t('areaDetail.targetTempLine')}
            />

            {/* TRV series (position line + optional open markers) */}
            {trvIds.map((id, idx) => {
              const sanitized = id
                .replaceAll('.', '_')
                .replaceAll('/', '_')
                .replaceAll(':', '_')
                .replaceAll('-', '_')
              const colors = ['#8bc34a', '#9c27b0', '#ff5722', '#607d8b', '#795548']
              const color = colors[idx % colors.length]
              return (
                <span key={`trv-series-${id}`}>
                  <Line
                    dataKey={`trv_${sanitized}_position`}
                    yAxisId="right"
                    stroke={color}
                    strokeWidth={2}
                    dot={false}
                    name={`TRV ${id} position`}
                  />
                  {showTrvs && (
                    <Scatter
                      dataKey={`trv_${sanitized}_open`}
                      yAxisId="right"
                      fill={color}
                      shape="triangle"
                      name={`TRV ${id} open`}
                    />
                  )}
                </span>
              )
            })}
            {/** Render heating/cooling activity only if present in history entries */}
            {(() => {
              const hasHeating = chartData.some(
                d => d.heatingDot !== null && d.heatingDot !== undefined,
              )
              const hasCooling = chartData.some(
                d => d.coolingDot !== null && d.coolingDot !== undefined,
              )
              return (
                <>
                  {hasHeating && showHeating && (
                    <Scatter
                      dataKey="heatingDot"
                      fill="#f44336"
                      shape="circle"
                      name={t('areaDetail.heatingActiveLine')}
                    />
                  )}
                  {hasCooling && showCooling && (
                    <Scatter
                      dataKey="coolingDot"
                      fill="#03a9f4"
                      shape="circle"
                      name={t('areaDetail.coolingActiveLine')}
                    />
                  )}
                </>
              )
            })()}
          </ComposedChart>
        </ResponsiveContainer>
      </div>

      {/* test-only flag to indicate cooling series present */}
      <div data-testid="history-has-cooling" style={{ display: 'none' }}>
        {hasCooling ? '1' : '0'}
      </div>

      {/* test-only list of TRV ids detected in the history entries */}
      <div data-testid="history-trv-ids" style={{ display: 'none' }}>
        {trvIds.join(',')}
      </div>

      <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
        {chartData.some(d => d.heatingDot !== null && d.heatingDot !== undefined) && (
          <FormControlLabel
            control={
              <Checkbox
                data-testid="history-toggle-heating"
                checked={showHeating}
                onChange={e => setShowHeating(e.target.checked)}
              />
            }
            label={t('areaDetail.heatingActiveLineShort', 'Heating')}
          />
        )}

        {hasCooling && (
          <FormControlLabel
            control={
              <Checkbox
                data-testid="history-toggle-cooling"
                checked={showCooling}
                onChange={e => setShowCooling(e.target.checked)}
              />
            }
            label={t('areaDetail.coolingActiveLineShort', 'Cooling')}
          />
        )}

        {trvIds.length > 0 && (
          <FormControlLabel
            control={
              <Checkbox
                data-testid="history-toggle-trvs"
                checked={showTrvs}
                onChange={e => setShowTrvs(e.target.checked)}
              />
            }
            label={t('areaDetail.trvs', 'TRVs')}
          />
        )}
      </Box>

      <Box sx={{ mt: 2 }}>
        <Alert severity="info" variant="outlined">
          <strong>{t('areaDetail.chartLegend')}</strong>
          <ul style={{ margin: '8px 0', paddingLeft: '20px' }}>
            <li>
              <strong data-testid="history-legend-item-temp" style={{ color: '#03a9f4' }}>
                {t('areaDetail.blueLine')}
              </strong>{' '}
              {t('areaDetail.blueLineDesc')}
            </li>
            <li>
              <strong data-testid="history-legend-item-target" style={{ color: '#ffc107' }}>
                {t('areaDetail.yellowDashed')}
              </strong>{' '}
              {t('areaDetail.yellowDashedDesc')}
            </li>
            {chartData.some(d => d.heatingDot !== null && d.heatingDot !== undefined) && (
              <li>
                <strong data-testid="history-legend-item-redDots" style={{ color: '#f44336' }}>
                  {t('areaDetail.redDots')}
                </strong>{' '}
                {t('areaDetail.redDotsDesc')}
              </li>
            )}
            {hasCooling && (
              <li>
                <strong data-testid="history-legend-item-blueDots" style={{ color: '#03a9f4' }}>
                  {t('areaDetail.blueDots')}
                </strong>{' '}
                {t('areaDetail.blueDotsDesc')}
              </li>
            )}
            <li>
              <strong data-testid="history-legend-item-greenDashed" style={{ color: '#4caf50' }}>
                {t('areaDetail.greenDashed')}
              </strong>{' '}
              {t('areaDetail.greenDashedDesc')}
            </li>
          </ul>
        </Alert>
      </Box>
    </Box>
  )
}

export default HistoryChart
