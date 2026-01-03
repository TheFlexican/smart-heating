import React from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  CircularProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { AreaLogEntry } from '../../api/logs'

export interface AreaLogsTabProps {
  logs: AreaLogEntry[]
  logsLoading: boolean
  logFilter: string
  onFilterChange: (filter: string) => void
  onRefresh: () => void
}

const getEventStyle = (type: string) => {
  switch (type) {
    case 'heating':
      return {
        background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(255, 107, 53, 0.3)',
        border: 'none',
      }
    case 'temperature':
      return {
        background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(6, 182, 212, 0.3)',
        border: 'none',
      }
    case 'schedule':
      return {
        background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
        border: 'none',
      }
    case 'smart_boost':
    case 'proactive_maintenance':
      return {
        background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(139, 92, 246, 0.3)',
        border: 'none',
      }
    case 'sensor':
      return {
        background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(245, 158, 11, 0.3)',
        border: 'none',
      }
    case 'mode':
      return {
        background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
        border: 'none',
      }
    default:
      return {
        background: 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
        color: '#ffffff',
        fontWeight: 600,
        boxShadow: '0 2px 6px rgba(0, 0, 0, 0.15)',
        border: 'none',
      }
  }
}

export const AreaLogsTab: React.FC<AreaLogsTabProps> = ({
  logs,
  logsLoading,
  logFilter,
  onFilterChange,
  onRefresh,
}) => {
  const { t } = useTranslation()

  const filterOptions = [
    { key: 'all', label: t('areaDetail.allEvents'), color: 'primary' as const },
    { key: 'temperature', label: t('areaDetail.temperature'), color: 'info' as const },
    { key: 'heating', label: t('areaDetail.heating'), color: 'error' as const },
    { key: 'schedule', label: t('areaDetail.schedule'), color: 'success' as const },
    { key: 'smart_boost', label: t('areaDetail.smartBoost'), color: 'secondary' as const },
    {
      key: 'proactive_maintenance',
      label: t('areaDetail.proactiveMaintenance'),
      color: 'secondary' as const,
    },
    { key: 'sensor', label: t('areaDetail.sensors'), color: 'warning' as const },
    { key: 'mode', label: t('areaDetail.mode'), color: 'primary' as const },
  ]

  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" color="text.primary">
            {t('areaDetail.heatingStrategyLogs')}
          </Typography>
          <Button variant="outlined" size="small" onClick={onRefresh} disabled={logsLoading}>
            {logsLoading ? 'Loading...' : t('areaDetail.refresh')}
          </Button>
        </Box>

        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('areaDetail.logsDescription')}
        </Typography>

        <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
          {filterOptions.map(({ key, label }) => {
            const isActive = logFilter === key
            const getFilterStyle = () => {
              if (!isActive) {
                return {
                  background: 'transparent',
                  color: 'text.secondary',
                  border: (theme: any) =>
                    `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)'}`,
                  fontWeight: 500,
                  '&:hover': {
                    background: (theme: any) =>
                      theme.palette.mode === 'dark'
                        ? 'rgba(255, 255, 255, 0.05)'
                        : 'rgba(0, 0, 0, 0.03)',
                    borderColor: (theme: any) =>
                      theme.palette.mode === 'dark'
                        ? 'rgba(255, 255, 255, 0.3)'
                        : 'rgba(0, 0, 0, 0.3)',
                  },
                }
              }
              // Active state gradients based on filter type
              switch (key) {
                case 'all':
                case 'heating':
                  return {
                    background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    boxShadow: '0 2px 8px rgba(255, 107, 53, 0.3)',
                    border: 'none',
                  }
                case 'temperature':
                  return {
                    background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    boxShadow: '0 2px 8px rgba(6, 182, 212, 0.3)',
                    border: 'none',
                  }
                case 'schedule':
                  return {
                    background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
                    border: 'none',
                  }
                case 'smart_boost':
                case 'proactive_maintenance':
                  return {
                    background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    boxShadow: '0 2px 8px rgba(139, 92, 246, 0.3)',
                    border: 'none',
                  }
                case 'sensor':
                  return {
                    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    boxShadow: '0 2px 8px rgba(245, 158, 11, 0.3)',
                    border: 'none',
                  }
                case 'mode':
                  return {
                    background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                    color: '#ffffff',
                    fontWeight: 700,
                    boxShadow: '0 2px 8px rgba(59, 130, 246, 0.3)',
                    border: 'none',
                  }
                default:
                  return {
                    background: 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
                    color: '#ffffff',
                    fontWeight: 600,
                    border: 'none',
                  }
              }
            }
            return (
              <Chip
                key={key}
                label={label}
                onClick={() => onFilterChange(key)}
                sx={{
                  cursor: 'pointer',
                  fontSize: '0.8125rem',
                  transition: 'all 0.2s ease',
                  ...getFilterStyle(),
                }}
              />
            )
          })}
        </Box>

        {(() => {
          if (logsLoading) {
            return (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                <CircularProgress />
              </Box>
            )
          }

          if (logs.length === 0) {
            return (
              <Box data-testid="area-logs-empty" sx={{ textAlign: 'center', py: 4 }}>
                <Typography variant="body2" color="text.secondary">
                  {t('settingsCards.noLogsYet')}
                </Typography>
              </Box>
            )
          }

          return (
            <List sx={{ bgcolor: 'background.paper' }}>
              {logs.map((log, index) => {
                const timestamp = new Date(log.timestamp)
                const timeStr = timestamp.toLocaleTimeString('nl-NL', {
                  hour: '2-digit',
                  minute: '2-digit',
                  second: '2-digit',
                })
                const dateStr = timestamp.toLocaleDateString('nl-NL')

                return (
                  <Box key={`${log.timestamp}-${log.type}`}>
                    {index > 0 && <Divider />}
                    <ListItem alignItems="flex-start" sx={{ py: 2 }}>
                      <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
                        <Chip
                          label={log.type}
                          size="small"
                          sx={{
                            fontSize: '0.7rem',
                            height: 22,
                            letterSpacing: '0.03em',
                            ...getEventStyle(log.type),
                          }}
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box
                            sx={{
                              display: 'flex',
                              justifyContent: 'space-between',
                              alignItems: 'center',
                            }}
                          >
                            <Typography variant="body2" color="text.primary">
                              {log.message}
                            </Typography>
                            <Typography variant="caption" color="text.secondary" sx={{ ml: 2 }}>
                              {dateStr} {timeStr}
                            </Typography>
                          </Box>
                        }
                        secondary={
                          log.details &&
                          Object.keys(log.details).length > 0 && (
                            <Box sx={{ mt: 0.5 }}>
                              <Box
                                component="pre"
                                sx={{
                                  mt: 1,
                                  p: 1,
                                  bgcolor: 'action.hover',
                                  borderRadius: 1,
                                  fontSize: '0.75rem',
                                  overflow: 'auto',
                                  fontFamily: 'monospace',
                                  m: 0,
                                }}
                              >
                                {JSON.stringify(log.details, null, 2)}
                              </Box>
                            </Box>
                          )
                        }
                        slotProps={{ secondary: { component: 'div' } }}
                      />
                    </ListItem>
                  </Box>
                )
              })}
            </List>
          )
        })()}
      </Paper>
    </Box>
  )
}
