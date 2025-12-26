import React from 'react'
import {
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Alert,
  Button,
} from '@mui/material'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { useTranslation } from 'react-i18next'
import { PresenceSensorConfig } from '../../types'

export const SensorsSettings: React.FC<{
  presenceSensors: PresenceSensorConfig[]
  onRemove: (entityId: string) => void
  onAddClick: () => void
}> = ({ presenceSensors, onRemove, onAddClick }) => {
  const { t } = useTranslation()

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" sx={{ mb: 1 }}>
        {t('globalSettings.sensors.title', 'Global Presence Sensors')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        {t(
          'globalSettings.sensors.description',
          'Configure presence sensors that can be used across all areas. Areas can choose to use these global sensors or configure their own.',
        )}
      </Typography>

      {presenceSensors.length > 0 ? (
        <List dense>
          {presenceSensors.map(sensor => (
            <ListItem
              key={sensor.entity_id}
              data-testid="presence-sensor-item"
              secondaryAction={
                <IconButton
                  data-testid={`presence-remove-${sensor.entity_id}`}
                  edge="end"
                  onClick={() => onRemove(sensor.entity_id)}
                >
                  <RemoveCircleOutlineIcon />
                </IconButton>
              }
            >
              <ListItemText
                primary={sensor.entity_id}
                secondary={t(
                  'globalSettings.sensors.switchText',
                  "Switches heating to 'away' when nobody is home",
                )}
              />
            </ListItem>
          ))}
        </List>
      ) : (
        <Alert severity="info" sx={{ mb: 2 }}>
          {t(
            'globalSettings.sensors.noSensors',
            'No global presence sensors configured. Add sensors that will be available to all areas.',
          )}
        </Alert>
      )}

      <Button
        variant="outlined"
        fullWidth
        data-testid="global-add-presence-sensor"
        onClick={onAddClick}
        sx={{ mt: 2 }}
      >
        {t('globalSettings.sensors.addButton', 'Add Presence Sensor')}
      </Button>

      <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
        💡{' '}
        {t(
          'globalSettings.sensors.tip',
          'Tip: Areas can enable "Use global presence" in their settings to use these sensors instead of configuring their own.',
        )}
      </Typography>
    </Paper>
  )
}
