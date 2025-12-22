import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import TuneIcon from '@mui/icons-material/Tune'
import SensorsIcon from '@mui/icons-material/Sensors'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import { Zone } from '../../../types'

export const getDeviceStatusIcon = (area: Zone | null, device: any) => {
  if (device.type === 'thermostat') {
    const shouldHeat =
      area?.target_temperature !== undefined &&
      device.current_temperature !== undefined &&
      area.target_temperature > device.current_temperature

    if (shouldHeat) {
      return <LocalFireDepartmentIcon fontSize="small" sx={{ color: 'error.main' }} />
    } else if (device.state === 'heat') {
      return <ThermostatIcon fontSize="small" sx={{ color: 'primary.main' }} />
    } else {
      return <AcUnitIcon fontSize="small" sx={{ color: 'info.main' }} />
    }
  } else if (device.type === 'valve') {
    return (
      <TuneIcon
        fontSize="small"
        sx={{ color: device.position > 0 ? 'warning.main' : 'text.secondary' }}
      />
    )
  } else if (device.type === 'temperature_sensor') {
    return <SensorsIcon fontSize="small" sx={{ color: 'success.main' }} />
  } else {
    return (
      <PowerSettingsNewIcon
        fontSize="small"
        sx={{ color: device.state === 'on' ? 'success.main' : 'text.secondary' }}
      />
    )
  }
}

export const getDeviceStatus = (area: Zone | null, device: any) => {
  if (device.type === 'thermostat') {
    const parts: string[] = []
    if (device.current_temperature !== undefined && device.current_temperature !== null) {
      parts.push(`${device.current_temperature.toFixed(1)}°C`)
    }
    if (
      area?.target_temperature !== undefined &&
      area.target_temperature !== null &&
      device.current_temperature !== undefined &&
      device.current_temperature !== null &&
      area.target_temperature > device.current_temperature
    ) {
      parts.push(`→ ${area.target_temperature.toFixed(1)}°C`)
    }
    return parts.length > 0 ? parts.join(' · ') : device.state || 'unknown'
  } else if (device.type === 'temperature_sensor') {
    if (device.temperature !== undefined && device.temperature !== null) {
      return `${device.temperature.toFixed(1)}°C`
    }
    return device.state || 'unknown'
  } else if (device.type === 'valve') {
    const parts: string[] = []
    if (device.position !== undefined) {
      parts.push(`${device.position}%`)
    }
    if (device.state) {
      parts.push(device.state)
    }
    return parts.length > 0 ? parts.join(' · ') : 'unknown'
  } else {
    return device.state || 'unknown'
  }
}

export default { getDeviceStatusIcon, getDeviceStatus }
