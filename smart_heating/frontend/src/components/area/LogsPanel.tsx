import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  CircularProgress,
  List,
  Divider,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material'
import { AreaLogEntry } from '../../api/logs'
import { useTranslation } from 'react-i18next'

interface Props {
  logs: AreaLogEntry[]
  logsLoading: boolean
  logFilter: string
  setLogFilter: (f: string) => void
  loadLogs: () => void
}

export default function LogsPanel({ logs, logsLoading, logFilter, setLogFilter, loadLogs }: Props) {
  const { t } = useTranslation()

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
    <Paper sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6" color="text.primary">
          {t('areaDetail.heatingStrategyLogs')}
        </Typography>
        <Button variant="outlined" size="small" onClick={loadLogs} disabled={logsLoading}>
          {logsLoading ? 'Loading...' : t('areaDetail.refresh')}
        </Button>
      </Box>

      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('areaDetail.logsDescription')}
      </Typography>

      <Box sx={{ mb: 3, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
        <Chip
          label={t('areaDetail.allEvents')}
          onClick={() => setLogFilter('all')}
          color={logFilter === 'all' ? 'primary' : 'default'}
          variant={logFilter === 'all' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer' }}
        />
        <Chip
          label={t('areaDetail.temperature')}
          onClick={() => setLogFilter('temperature')}
          color={logFilter === 'temperature' ? 'info' : 'default'}
          variant={logFilter === 'temperature' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer' }}
        />
        <Chip
          label={t('areaDetail.heating')}
          onClick={() => setLogFilter('heating')}
          color={logFilter === 'heating' ? 'error' : 'default'}
          variant={logFilter === 'heating' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer' }}
        />
        <Chip
          label={t('areaDetail.schedule')}
          onClick={() => setLogFilter('schedule')}
          color={logFilter === 'schedule' ? 'success' : 'default'}
          variant={logFilter === 'schedule' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer' }}
        />
        <Chip
          label={t('areaDetail.smartBoost')}
          onClick={() => setLogFilter('smart_boost')}
          color={logFilter === 'smart_boost' ? 'secondary' : 'default'}
          variant={logFilter === 'smart_boost' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer' }}
        />
        <Chip
          label={t('areaDetail.sensors')}
          onClick={() => setLogFilter('sensor')}
          color={logFilter === 'sensor' ? 'warning' : 'default'}
          variant={logFilter === 'sensor' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer' }}
        />
        <Chip
          label={t('areaDetail.mode')}
          onClick={() => setLogFilter('mode')}
          color={logFilter === 'mode' ? 'primary' : 'default'}
          variant={logFilter === 'mode' ? 'filled' : 'outlined'}
          sx={{ cursor: 'pointer' }}
        />
      </Box>

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
                        }}
                      >
                        {JSON.stringify(log.details, null, 2)}
                      </Box>
                    )
                  }
                />
              </ListItem>
            </Box>
          )
        })}
      </List>
    </Paper>
  )
}
