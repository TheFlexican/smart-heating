import React, { useState } from 'react'
import { Box } from '@mui/material'
import { Zone, Device } from '../../types'
import { PrimarySensorSelector } from './PrimarySensorSelector'
import { AssignedDevicesList } from './AssignedDevicesList'
import { AvailableDevicesList } from './AvailableDevicesList'

export interface AreaDevicesTabProps {
  area: Zone
  availableDevices: Device[]
  onPrimarySensorChange: (sensorId: string | null) => Promise<void>
  onRemoveDevice: (deviceId: string) => Promise<void>
  onAddDevice: (device: Device) => Promise<void>
  getDeviceStatusIcon: (device: any) => React.ReactNode
  getDeviceStatus: (device: any) => string
}

export const AreaDevicesTab: React.FC<AreaDevicesTabProps> = ({
  area,
  availableDevices,
  onPrimarySensorChange,
  onRemoveDevice,
  onAddDevice,
  getDeviceStatusIcon,
  getDeviceStatus,
}) => {
  const [showOnlyHeating, setShowOnlyHeating] = useState(true)
  const [deviceSearch, setDeviceSearch] = useState('')

  return (
    <Box sx={{ maxWidth: { xs: 800, lg: 1200 }, mx: 'auto' }}>
      <PrimarySensorSelector area={area} onPrimarySensorChange={onPrimarySensorChange} />

      <AssignedDevicesList
        area={area}
        onRemoveDevice={onRemoveDevice}
        getDeviceStatusIcon={getDeviceStatusIcon}
        getDeviceStatus={getDeviceStatus}
      />

      <AvailableDevicesList
        area={area}
        availableDevices={availableDevices}
        showOnlyHeating={showOnlyHeating}
        deviceSearch={deviceSearch}
        onShowOnlyHeatingChange={setShowOnlyHeating}
        onDeviceSearchChange={setDeviceSearch}
        onAddDevice={onAddDevice}
      />
    </Box>
  )
}
