import React from 'react'
import {
  Box,
  Paper,
  Typography,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Alert,
  Chip,
} from '@mui/material'
import SensorsIcon from '@mui/icons-material/Sensors'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { useTranslation } from 'react-i18next'
import { Zone } from '../../types'

export interface AssignedDevicesListProps {
  area: Zone
  onRemoveDevice: (deviceId: string) => Promise<void>
  getDeviceStatusIcon: (device: any) => React.ReactNode
  getDeviceStatus: (device: any) => string
}

export const AssignedDevicesList: React.FC<AssignedDevicesListProps> = ({
  area,
  onRemoveDevice,
  getDeviceStatusIcon,
  getDeviceStatus,
}) => {
  const { t } = useTranslation()

  const handleRemove = async (deviceId: string) => {
    try {
      await onRemoveDevice(deviceId)
    } catch (error) {
      console.error('Failed to remove device:', error)
    }
  }

  return (
    <Paper sx={{ p: { xs: 2, sm: 3, md: 4 }, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
        <SensorsIcon sx={{ fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h5" color="text.primary" sx={{ fontWeight: 600 }}>
          {t('areaDetail.assignedDevices', { count: area.devices.length })}
        </Typography>
      </Box>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t('areaDetail.devicesDescription')}
      </Typography>

      {area.devices.length === 0 ? (
        <Alert severity="info">{t('areaDetail.noDevicesAssigned')}</Alert>
      ) : (
        <List>
          {area.devices.map(device => (
            <ListItem
              data-testid={`assigned-device-${device.id}`}
              key={device.id}
              sx={{
                border: 1,
                borderColor: 'divider',
                borderRadius: 1,
                mb: 1,
              }}
              secondaryAction={
                <IconButton
                  edge="end"
                  aria-label="remove"
                  data-testid={`remove-device-${(device.entity_id || device.id).toLowerCase().replaceAll(' ', '-')}`}
                  onClick={() => handleRemove(device.entity_id || device.id)}
                >
                  <RemoveCircleOutlineIcon />
                </IconButton>
              }
            >
              <ListItemIcon>{getDeviceStatusIcon(device)}</ListItemIcon>
              <ListItemText
                primary={
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography variant="body1" color="text.primary">
                      {device.name || device.id}
                    </Typography>
                    {device.type === 'thermostat' &&
                      area?.target_temperature !== undefined &&
                      device.current_temperature !== undefined &&
                      area.target_temperature > device.current_temperature && (
                        <Chip
                          data-testid={`device-heating-chip-${device.id}`}
                          label="heating"
                          size="small"
                          sx={{
                            height: 22,
                            fontSize: '0.7rem',
                            fontWeight: 700,
                            background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
                            color: '#ffffff',
                            boxShadow: '0 2px 8px rgba(255, 107, 53, 0.3)',
                            border: 'none',
                          }}
                        />
                      )}
                  </Box>
                }
                secondary={
                  <Box>
                    <Typography
                      variant="caption"
                      color="text.secondary"
                      display="block"
                      component="span"
                    >
                      {String(device.type).replaceAll('_', ' ')}
                    </Typography>
                    <Typography
                      variant="body2"
                      color="text.primary"
                      sx={{ mt: 0.5 }}
                      component="div"
                    >
                      {getDeviceStatus(device)}
                    </Typography>
                    {device.type === 'valve' && area?.heating_type === 'airco' && (
                      <Typography
                        data-testid={`device-disabled-airco-${device.id}`}
                        variant="caption"
                        color="text.secondary"
                        sx={{ mt: 0.5 }}
                        component="span"
                      >
                        {t('areaDetail.disabledForAirco', 'Disabled for Air Conditioner')}
                      </Typography>
                    )}
                  </Box>
                }
                slotProps={{ secondary: { component: 'div' } }}
              />
            </ListItem>
          ))}
        </List>
      )}
    </Paper>
  )
}
