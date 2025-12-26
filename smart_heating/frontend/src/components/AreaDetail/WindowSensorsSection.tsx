import { List, ListItem, ListItemText, IconButton, Alert, Button } from '@mui/material'
import WindowIcon from '@mui/icons-material/Window'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { removeWindowSensor } from '../../api/sensors'

export interface WindowSensorsSectionProps {
  area: Zone
  onUpdate: () => void
  onOpenAddDialog: () => void
  t: TFunction
}

export const WindowSensorsSection = ({
  area,
  onUpdate,
  onOpenAddDialog,
  t,
}: WindowSensorsSectionProps): SettingSection => {
  return {
    id: 'window-sensors',
    title: t('settingsCards.windowSensorsTitle'),
    description: t('settingsCards.windowSensorsDescription'),
    icon: <WindowIcon />,
    badge: area.window_sensors?.length || undefined,
    defaultExpanded: false,
    content: (
      <>
        {area.window_sensors && area.window_sensors.length > 0 ? (
          <List dense>
            {area.window_sensors.map(sensor => {
              const sensorConfig =
                typeof sensor === 'string'
                  ? { entity_id: sensor, action_when_open: 'reduce_temperature', temp_drop: 5 }
                  : sensor

              let secondaryText = ''
              if (sensorConfig.action_when_open === 'turn_off') {
                secondaryText = 'Turn off heating when open'
              } else if (sensorConfig.action_when_open === 'reduce_temperature') {
                secondaryText = `Reduce temperature by ${sensorConfig.temp_drop}°C when open`
              } else {
                secondaryText = 'No action when open'
              }

              return (
                <ListItem
                  key={sensorConfig.entity_id}
                  data-testid="window-sensor-item"
                  secondaryAction={
                    <IconButton
                      edge="end"
                      onClick={async () => {
                        try {
                          await removeWindowSensor(area.id, sensorConfig.entity_id)
                          onUpdate()
                        } catch (error) {
                          console.error('Failed to remove window sensor:', error)
                        }
                      }}
                    >
                      <RemoveCircleOutlineIcon />
                    </IconButton>
                  }
                >
                  <ListItemText primary={sensorConfig.entity_id} secondary={secondaryText} />
                </ListItem>
              )
            })}
          </List>
        ) : (
          <Alert severity="info" sx={{ mb: 2 }}>
            No window sensors configured. Add binary sensors to enable window detection.
          </Alert>
        )}

        <Button
          variant="outlined"
          fullWidth
          onClick={onOpenAddDialog}
          data-testid="add-window-sensor-button"
        >
          Add Window Sensor
        </Button>
      </>
    ),
  }
}
