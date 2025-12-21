import React, { useState } from 'react'
import { Box, List, ListItem, ListItemText, IconButton, Alert, Button } from '@mui/material'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { Zone, WindowSensorConfig, PresenceSensorConfig } from '../types'
import SensorConfigDialog from './SensorConfigDialog'
import {
  addWindowSensor,
  addPresenceSensor,
  removeWindowSensor,
  removePresenceSensor,
} from '../api/sensors'
import { useTranslation } from 'react-i18next'

interface Props {
  area: Zone
  entityStates: Record<string, any>
  loadData: () => Promise<void>
}

const SensorConfigControls: React.FC<Props> = ({ area, entityStates, loadData }) => {
  const { t } = useTranslation()
  const [sensorDialogOpen, setSensorDialogOpen] = useState(false)
  const [sensorDialogType, setSensorDialogType] = useState<'window' | 'presence'>('window')

  return (
    <>
      {/* Window sensors */}
      <>
        {area.window_sensors && area.window_sensors.length > 0 ? (
          <List dense>
            {area.window_sensors.map(sensor => {
              const sensorConfig: WindowSensorConfig =
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
                          await loadData()
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
          onClick={() => {
            setSensorDialogType('window')
            setSensorDialogOpen(true)
          }}
          data-testid="add-window-sensor-button"
        >
          Add Window Sensor
        </Button>
      </>

      {/* Presence sensors */}
      <Box sx={{ mt: 2 }}>
        {area.presence_sensors && area.presence_sensors.length > 0 ? (
          <List dense>
            {area.presence_sensors.map(sensor => {
              const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
              return (
                <ListItem
                  key={entity_id}
                  data-testid="presence-sensor-item"
                  secondaryAction={
                    <IconButton
                      edge="end"
                      onClick={async () => {
                        try {
                          await removePresenceSensor(area.id, entity_id)
                          await loadData()
                        } catch (error) {
                          console.error('Failed to remove presence sensor:', error)
                        }
                      }}
                    >
                      <RemoveCircleOutlineIcon />
                    </IconButton>
                  }
                >
                  <ListItemText
                    primary={entity_id}
                    secondary={entityStates[entity_id]?.name || ''}
                  />
                </ListItem>
              )
            })}
          </List>
        ) : (
          <Alert severity="info" sx={{ mb: 2 }}>
            {t('settingsCards.noPresenceSensors')}
          </Alert>
        )}

        <Button
          variant="outlined"
          fullWidth
          onClick={() => {
            setSensorDialogType('presence')
            setSensorDialogOpen(true)
          }}
          data-testid="add-presence-sensor-button"
        >
          {t('settingsCards.addPresenceSensor')}
        </Button>
      </Box>

      {/* Sensor Dialog */}
      <SensorConfigDialog
        open={sensorDialogOpen}
        onClose={() => setSensorDialogOpen(false)}
        onAdd={async config => {
          try {
            if (sensorDialogType === 'window') {
              await addWindowSensor(area.id, config as WindowSensorConfig)
            } else {
              await addPresenceSensor(area.id, config as PresenceSensorConfig)
            }
            setSensorDialogOpen(false)
            await loadData()
          } catch (error) {
            console.error('Failed to add sensor:', error)
            alert(`Failed to add sensor: ${error}`)
          }
        }}
        sensorType={sensorDialogType}
      />
    </>
  )
}

export default SensorConfigControls
