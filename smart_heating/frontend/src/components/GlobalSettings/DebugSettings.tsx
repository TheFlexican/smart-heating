import React from 'react'
import { Paper, Typography, Alert, Stack, Box, List, ListItem, ListItemText } from '@mui/material'
import { useTranslation } from 'react-i18next'

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

export const DebugSettings: React.FC<{ wsMetrics?: WebSocketMetrics }> = ({ wsMetrics }) => {
  const { t } = useTranslation()

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        {t('globalSettings.debug.title', 'WebSocket Connection Health')}
      </Typography>

      {wsMetrics ? (
        <Stack spacing={2}>
          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Device Information
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText primary="Platform" secondary={wsMetrics.deviceInfo.platform} />
              </ListItem>
              <ListItem>
                <ListItemText primary="Browser" secondary={wsMetrics.deviceInfo.browserName} />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Environment"
                  secondary={`${wsMetrics.deviceInfo.isIframe ? 'Iframe' : 'Standalone'} | iOS: ${wsMetrics.deviceInfo.isiOS ? 'Yes' : 'No'} | Android: ${wsMetrics.deviceInfo.isAndroid ? 'Yes' : 'No'}`}
                />
              </ListItem>
            </List>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Connection Statistics
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="Total Connection Attempts"
                  secondary={wsMetrics.totalConnectionAttempts}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Successful Connections"
                  secondary={`${wsMetrics.successfulConnections} (${wsMetrics.totalConnectionAttempts > 0 ? Math.round((wsMetrics.successfulConnections / wsMetrics.totalConnectionAttempts) * 100) : 0}%)`}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Failed Connections"
                  secondary={`${wsMetrics.failedConnections} (${wsMetrics.totalConnectionAttempts > 0 ? Math.round((wsMetrics.failedConnections / wsMetrics.totalConnectionAttempts) * 100) : 0}%)`}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Unexpected Disconnects"
                  secondary={wsMetrics.unexpectedDisconnects}
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Average Connection Duration"
                  secondary={`${(wsMetrics.averageConnectionDuration / 1000).toFixed(1)}s`}
                />
              </ListItem>
            </List>
          </Box>

          <Box>
            <Typography variant="subtitle2" color="text.secondary">
              Recent Activity
            </Typography>
            <List dense>
              <ListItem>
                <ListItemText
                  primary="Last Connected"
                  secondary={
                    wsMetrics.lastConnectedAt
                      ? new Date(wsMetrics.lastConnectedAt).toLocaleString()
                      : 'Never'
                  }
                />
              </ListItem>
              <ListItem>
                <ListItemText
                  primary="Last Disconnected"
                  secondary={
                    wsMetrics.lastDisconnectedAt
                      ? new Date(wsMetrics.lastDisconnectedAt).toLocaleString()
                      : 'Never'
                  }
                />
              </ListItem>
              {wsMetrics.lastFailureReason && (
                <ListItem>
                  <ListItemText
                    primary="Last Failure Reason"
                    secondary={wsMetrics.lastFailureReason}
                  />
                </ListItem>
              )}
            </List>
          </Box>

          {wsMetrics.connectionDurations.length > 0 && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary">
                {t(
                  'globalSettings.debug.recentDurations',
                  'Recent Connection Durations (last {{n}})',
                  { n: wsMetrics.connectionDurations.length },
                )}
              </Typography>
              <Typography variant="body2" sx={{ mt: 1 }}>
                {wsMetrics.connectionDurations
                  .map(duration => `${(duration / 1000).toFixed(1)}s`)
                  .join(', ')}
              </Typography>
            </Box>
          )}
        </Stack>
      ) : (
        <Alert severity="info" sx={{ mt: 2 }}>
          WebSocket metrics not available. Metrics are only available when connected.
        </Alert>
      )}
    </Paper>
  )
}
