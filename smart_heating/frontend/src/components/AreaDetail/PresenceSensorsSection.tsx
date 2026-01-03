import {
  Box,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Alert,
  Button,
  Typography,
  Chip,
} from '@mui/material'
import SensorOccupiedIcon from '@mui/icons-material/SensorOccupied'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { removePresenceSensor } from '../../api/sensors'

export interface PresenceSensorsSectionProps {
  area: Zone
  entityStates: Record<string, any>
  onUpdate: () => void
  onOpenAddDialog: () => void
  t: TFunction
}

export const PresenceSensorsSection = ({
  area,
  entityStates,
  onUpdate,
  onOpenAddDialog,
  t,
}: PresenceSensorsSectionProps): SettingSection => {
  return {
    id: 'presence-sensors',
    title: t('settingsCards.presenceSensorsTitle'),
    description: t('settingsCards.presenceSensorsDescription'),
    icon: <SensorOccupiedIcon />,
    badge: area.presence_sensors?.length || undefined,
    defaultExpanded: false,
    content: (
      <>
        {area.presence_sensors && area.presence_sensors.length > 0 ? (
          <List dense>
            {area.presence_sensors.map(sensor => {
              const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id

              const entityState = entityStates[entity_id]
              const friendlyName = entityState?.attributes?.friendly_name || entity_id
              const state = entityState?.state || 'unknown'
              const isAway = state === 'not_home' || state === 'off' || state === 'away'
              const isActive = isAway || state === 'home' || state === 'on'

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
                          onUpdate()
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
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography>{friendlyName}</Typography>
                        {isActive && (
                          <Chip
                            label={
                              isAway ? t('settingsCards.awayChip') : t('settingsCards.homeChip')
                            }
                            size="small"
                            sx={{
                              height: '22px',
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              letterSpacing: '0.03em',
                              background: isAway
                                ? 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
                                : 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                              color: '#ffffff',
                              boxShadow: isAway
                                ? '0 2px 8px rgba(245, 158, 11, 0.3)'
                                : '0 2px 8px rgba(16, 185, 129, 0.3)',
                              border: 'none',
                              transition: 'all 0.2s ease',
                              '&:hover': {
                                transform: 'scale(1.05)',
                                boxShadow: isAway
                                  ? '0 4px 12px rgba(245, 158, 11, 0.4)'
                                  : '0 4px 12px rgba(16, 185, 129, 0.4)',
                              },
                            }}
                          />
                        )}
                      </Box>
                    }
                    secondary={
                      <Typography component="span" variant="body2" color="text.secondary">
                        {t('settingsCards.presenceSensorDescription')}
                      </Typography>
                    }
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
          onClick={onOpenAddDialog}
          data-testid="add-presence-sensor-button"
        >
          {t('settingsCards.addPresenceSensor')}
        </Button>
      </>
    ),
  }
}
