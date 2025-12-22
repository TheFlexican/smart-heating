import React, { useState } from 'react'
import {
  Paper,
  Box,
  Typography,
  FormControlLabel,
  Switch,
  TextField,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  IconButton,
  Button,
  Chip,
  Alert,
} from '@mui/material'
import SensorsIcon from '@mui/icons-material/Sensors'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { useTranslation } from 'react-i18next'
import { Zone, Device } from '../../types'

interface Props {
  area: Zone
  availableDevices: Device[]
  loadData: () => Promise<void>
  addDeviceToZone: (areaId: string, payload: any) => Promise<void>
  removeDeviceFromZone: (areaId: string, deviceId: string) => Promise<void>
  getDeviceStatusIcon: (device: any) => React.ReactNode
  getDeviceStatus: (device: any) => string
}

const DevicesPanel: React.FC<Props> = ({
  area,
  availableDevices,
  loadData,
  addDeviceToZone,
  removeDeviceFromZone,
  getDeviceStatusIcon,
  getDeviceStatus,
}) => {
  const { t } = useTranslation()
  const [showOnlyHeating, setShowOnlyHeating] = useState(true)
  const [deviceSearch, setDeviceSearch] = useState('')

  return (
    <>
      {/* Assigned Devices */}
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
                sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}
                secondaryAction={
                  <IconButton
                    edge="end"
                    aria-label="remove"
                    data-testid={`remove-device-${(device.entity_id || device.id).toLowerCase().replaceAll(' ', '-')}`}
                    onClick={async () => {
                      try {
                        await removeDeviceFromZone(area.id, device.entity_id || device.id)
                        await loadData()
                      } catch (error) {
                        console.error('Failed to remove device:', error)
                      }
                    }}
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
                            color="error"
                            sx={{ height: 20, fontSize: '0.7rem' }}
                          />
                        )}
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" color="text.secondary" display="block">
                        {String(device.type).replaceAll('_', ' ')}
                      </Typography>
                      <Typography variant="body2" color="text.primary" sx={{ mt: 0.5 }}>
                        {getDeviceStatus(device)}
                      </Typography>
                      {device.type === 'valve' && area?.heating_type === 'airco' && (
                        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
                          {t('areaDetail.disabledForAirco', 'Disabled for Air Conditioner')}
                        </Typography>
                      )}
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        )}
      </Paper>

      {/* Available Devices */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" color="text.primary">
            {t('areaDetail.availableDevices', {
              count: availableDevices.filter(device => {
                const typeMatch =
                  !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
                if (!deviceSearch) return typeMatch
                const searchLower = deviceSearch.toLowerCase()
                const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
                const entityMatch = (device.entity_id || device.id || '')
                  .toLowerCase()
                  .includes(searchLower)
                const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
                return typeMatch && (nameMatch || entityMatch || areaMatch)
              }).length,
            })}
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={showOnlyHeating}
                onChange={e => setShowOnlyHeating(e.target.checked)}
                color="primary"
              />
            }
            label={t('areaDetail.showOnlyClimate')}
          />
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('areaDetail.availableDevicesDescription', { area: area.name })}
        </Typography>

        <TextField
          fullWidth
          size="small"
          placeholder={t('areaDetail.searchPlaceholder')}
          value={deviceSearch}
          onChange={e => setDeviceSearch(e.target.value)}
          sx={{ mb: 2 }}
        />

        {availableDevices.filter(device => {
          const typeMatch =
            !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
          if (!deviceSearch) return typeMatch
          const searchLower = deviceSearch.toLowerCase()
          const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
          const entityMatch = (device.entity_id || device.id || '')
            .toLowerCase()
            .includes(searchLower)
          const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
          return typeMatch && (nameMatch || entityMatch || areaMatch)
        }).length === 0 ? (
          <Alert severity="info">
            {(() => {
              if (deviceSearch) return t('areaDetail.noDevicesMatch', { search: deviceSearch })
              if (showOnlyHeating) return t('areaDetail.noClimateDevices')
              return t('areaDetail.noAdditionalDevices')
            })()}
          </Alert>
        ) : (
          <List>
            {availableDevices
              .filter(device => {
                const typeMatch =
                  !showOnlyHeating || ['climate', 'temperature'].includes(device.subtype || '')
                if (!deviceSearch) return typeMatch
                const searchLower = deviceSearch.toLowerCase()
                const nameMatch = (device.name || '').toLowerCase().includes(searchLower)
                const entityMatch = (device.entity_id || device.id || '')
                  .toLowerCase()
                  .includes(searchLower)
                const areaMatch = (device.ha_area_name || '').toLowerCase().includes(searchLower)
                return typeMatch && (nameMatch || entityMatch || areaMatch)
              })
              .map(device => (
                <ListItem
                  key={device.entity_id || device.id}
                  sx={{ border: 1, borderColor: 'divider', borderRadius: 1, mb: 1 }}
                  secondaryAction={
                    <Button
                      data-testid={`add-available-device-${(device.entity_id || device.id).toLowerCase().replaceAll(' ', '-')}`}
                      variant="contained"
                      size="small"
                      disabled={device.type === 'valve' && area?.heating_type === 'airco'}
                      title={
                        device.type === 'valve' && area?.heating_type === 'airco'
                          ? t('areaDetail.disabledForAirco', 'Disabled for Air Conditioner')
                          : undefined
                      }
                      onClick={async () => {
                        try {
                          await addDeviceToZone(area.id, {
                            device_id: device.entity_id || device.id,
                            device_type: device.type,
                            mqtt_topic: (device as any).mqtt_topic,
                          })
                          await loadData()
                        } catch (error) {
                          console.error('Failed to add device:', error)
                        }
                      }}
                    >
                      {t('areaDetail.add') || 'Add'}
                    </Button>
                  }
                >
                  <ListItemIcon>{getDeviceStatusIcon(device)}</ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body1">
                        {device.name || device.entity_id || device.id}
                      </Typography>
                    }
                  />
                </ListItem>
              ))}
          </List>
        )}
      </Paper>
    </>
  )
}

export default DevicesPanel
