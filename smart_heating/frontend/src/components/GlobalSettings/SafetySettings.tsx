import React from 'react'
import {
  Paper,
  Typography,
  Alert,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Button,
} from '@mui/material'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import SecurityIcon from '@mui/icons-material/Security'
import { useTranslation } from 'react-i18next'

export const SafetySettings: React.FC<{
  safetySensor: any
  onRemove: (sensorId: string) => void
  onAddClick: () => void
}> = ({ safetySensor, onRemove, onAddClick }) => {
  const { t } = useTranslation()

  return (
    <Paper sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('globalSettings.safety.title', '🚨 Safety Sensors (Smoke/CO Detectors)')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t(
          'globalSettings.safety.description',
          'Configure smoke or carbon monoxide detectors that will automatically shut down all heating when danger is detected. All areas will be disabled immediately to prevent heating during a safety emergency.',
        )}
      </Typography>

      {safetySensor?.alert_active && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {t(
            'globalSettings.safety.alertActive',
            '⚠️ SAFETY ALERT ACTIVE! All heating has been shut down. Please resolve the safety issue and manually re-enable areas.',
          )}
        </Alert>
      )}

      {safetySensor?.sensors && safetySensor.sensors.length > 0 ? (
        <>
          <Alert severity="success" sx={{ mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 1 }}>
              {t('globalSettings.safety.configured', 'Safety Sensors Configured')} (
              {safetySensor.sensors.length})
            </Typography>
          </Alert>

          <List sx={{ mb: 2 }}>
            {safetySensor.sensors.map((sensor: any) => (
              <ListItem
                key={sensor.sensor_id}
                data-testid="safety-sensor-item"
                sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}
                secondaryAction={
                  <IconButton
                    edge="end"
                    aria-label="delete"
                    onClick={() => onRemove(sensor.sensor_id)}
                    color="error"
                  >
                    <RemoveCircleOutlineIcon />
                  </IconButton>
                }
              >
                <ListItemText
                  primary={sensor.sensor_id}
                  secondary={
                    <Typography component="span" variant="body2">
                      {t('globalSettings.safety.attribute', 'Attribute')}: {sensor.attribute} |{' '}
                      {t('globalSettings.safety.status', 'Status')}:{' '}
                      {sensor.enabled
                        ? t('globalSettings.safety.enabled', '✓ Enabled')
                        : t('globalSettings.safety.disabled', '✗ Disabled')}
                    </Typography>
                  }
                />
              </ListItem>
            ))}
          </List>

          <Button
            variant="outlined"
            fullWidth
            data-testid="global-add-safety-sensor"
            onClick={onAddClick}
            startIcon={<SecurityIcon />}
            sx={{ mb: 2 }}
          >
            {t('globalSettings.safety.addAnotherButton', 'Add Another Safety Sensor')}
          </Button>
        </>
      ) : (
        <>
          <Alert severity="warning" sx={{ mb: 2 }}>
            {t(
              'globalSettings.safety.notConfigured',
              'No safety sensors configured. It is highly recommended to configure smoke or CO detectors for emergency heating shutdown.',
            )}
          </Alert>

          <Button
            variant="outlined"
            fullWidth
            data-testid="global-add-safety-sensor"
            onClick={onAddClick}
            startIcon={<SecurityIcon />}
          >
            {t('globalSettings.safety.addButton', 'Add Safety Sensor')}
          </Button>
        </>
      )}

      <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
        💡{' '}
        {t(
          'globalSettings.safety.tip',
          'When any safety sensor detects smoke or carbon monoxide, all heating will be immediately stopped and all areas disabled. Areas must be manually re-enabled after the safety issue is resolved.',
        )}
      </Typography>
    </Paper>
  )
}
