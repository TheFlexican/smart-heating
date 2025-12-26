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

const getEventColor = (type: string) => {
  switch (type) {
    case 'heating':
      return 'error'
    case 'temperature':
      return 'info'
    case 'schedule':
      return 'success'
    case 'smart_boost':
      return 'secondary'
    case 'sensor':
      return 'warning'
    case 'mode':
      return 'primary'
    default:
      return 'default'
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
          {filterOptions.map(({ key, label, color }) => (
            <Chip
              key={key}
              label={label}
              onClick={() => onFilterChange(key)}
              color={logFilter === key ? color : 'default'}
              variant={logFilter === key ? 'filled' : 'outlined'}
              sx={{ cursor: 'pointer' }}
            />
          ))}
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
                  <Box key={`${log.timestamp}-${index}`}>
                    {index > 0 && <Divider />}
                    <ListItem alignItems="flex-start" sx={{ py: 2 }}>
                      <ListItemIcon sx={{ minWidth: 40, mt: 0.5 }}>
                        <Chip
                          label={log.type}
                          color={getEventColor(log.type)}
                          size="small"
                          sx={{ fontSize: '0.7rem', height: 20 }}
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
                        secondaryTypographyProps={{ component: 'div' }}
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
