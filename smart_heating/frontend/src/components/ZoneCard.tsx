import { useState, useEffect, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import {
  Card,
  CardContent,
  Typography,
  IconButton,
  Box,
  Chip,
  Slider,
  Menu,
  ListItemText,
  List,
  ListItem,
  ListItemIcon,
  MenuItem,
  FormControlLabel,
  Switch,
  Tooltip,
  alpha,
  Select,
  FormControl,
  InputLabel,
  SelectChangeEvent,
} from '@mui/material'
import { useSortable } from '@dnd-kit/sortable'
import { CSS } from '@dnd-kit/utilities'
import MoreVertIcon from '@mui/icons-material/MoreVert'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import AcUnitIcon from '@mui/icons-material/AcUnit'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import TuneIcon from '@mui/icons-material/Tune'
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import VisibilityIcon from '@mui/icons-material/Visibility'
import PersonIcon from '@mui/icons-material/Person'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import RocketLaunchIcon from '@mui/icons-material/RocketLaunch'
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'
import { Zone } from '../types'
import {
  setZoneTemperature,
  removeDeviceFromZone,
  hideZone,
  unhideZone,
  setManualOverride,
  setBoostMode,
  cancelBoost,
  setZoneHvacMode,
} from '../api/areas'
import { getEntityState } from '../api/config'

interface ZoneCardProps {
  area: Zone
  onUpdate: () => void
}

const ZoneCard = ({ area, onUpdate }: ZoneCardProps) => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const enabled = Boolean(area.enabled)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: area.id,
  })

  // Get displayed temperature: use effective temperature when in preset mode, otherwise use target
  const getDisplayTemperature = useCallback(() => {
    // If the area is off/disabled, always show the area target temperature
    if (!enabled || area.state === 'off') return area.target_temperature

    // When using preset mode (not manual override), show effective temperature
    if (
      !area.manual_override &&
      area.preset_mode &&
      area.preset_mode !== 'none' &&
      area.effective_target_temperature != null
    ) {
      return area.effective_target_temperature
    }
    // Otherwise show the base target temperature
    return area.target_temperature
  }, [area])

  const [temperature, setTemperature] = useState(getDisplayTemperature())
  const [presenceState, setPresenceState] = useState<string | null>(null)

  // Sync local temperature state when area or devices change
  useEffect(() => {
    const displayTemp = getDisplayTemperature()
    setTemperature(displayTemp)
  }, [getDisplayTemperature])

  useEffect(() => {
    const loadPresenceState = async () => {
      if (area.presence_sensors && area.presence_sensors.length > 0) {
        try {
          const firstSensor = area.presence_sensors[0]
          const state = await getEntityState(firstSensor.entity_id)
          setPresenceState(state.state)
        } catch (error) {
          console.error('Failed to load presence state:', error)
        }
      }
    }
    loadPresenceState()
  }, [area.presence_sensors])

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    event.stopPropagation()
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleCardClick = () => {
    navigate(`/area/${area.id}`)
  }

  const handleTemperatureChange = async (event: Event, value: number | number[]) => {
    event.stopPropagation()
    const newTemp = value as number
    setTemperature(newTemp)
  }

  const handleTemperatureCommit = async (
    event: Event | React.SyntheticEvent,
    value: number | number[],
  ) => {
    event.stopPropagation()
    try {
      await setZoneTemperature(area.id, value as number)
      onUpdate()
    } catch (error) {
      console.error('Failed to set temperature:', error)
    }
  }

  const handleRemoveDevice = async (deviceId: string) => {
    try {
      await removeDeviceFromZone(area.id, deviceId)
      onUpdate()
    } catch (error) {
      console.error('Failed to remove device:', error)
    }
  }

  const handleToggleHidden = async (event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      if (area.hidden) {
        await unhideZone(area.id)
      } else {
        await hideZone(area.id)
      }
      handleMenuClose()
      onUpdate()
    } catch (error) {
      console.error('Failed to toggle hidden:', error)
    }
  }

  const handleSliderClick = (event: React.MouseEvent) => {
    event.stopPropagation()
  }

  const handleBoostToggle = async (event: React.MouseEvent) => {
    event.stopPropagation()
    try {
      if (area.boost_mode_active) {
        await cancelBoost(area.id)
      } else {
        // Use area's boost settings or defaults
        const boostTemp = area.boost_temp || 25
        const boostDuration = area.boost_duration || 60
        await setBoostMode(area.id, boostDuration, boostTemp)
      }
      onUpdate()
    } catch (error) {
      console.error('Failed to toggle boost mode:', error)
    }
  }

  const handleHvacModeChange = async (event: SelectChangeEvent) => {
    event.stopPropagation()
    try {
      const newMode = event.target.value
      await setZoneHvacMode(area.id, newMode)
      onUpdate()
    } catch (error) {
      console.error('Failed to set HVAC mode:', error)
    }
  }

  const getStateColor = () => {
    if (area.manual_override) {
      return 'warning'
    }
    switch (area.state) {
      case 'heating':
        return 'error'
      case 'idle':
        return 'info'
      case 'off':
        return 'default'
      default:
        return 'default'
    }
  }

  const getStateIcon = () => {
    if (area.manual_override) {
      return <TuneIcon />
    }
    switch (area.state) {
      case 'heating':
        return <LocalFireDepartmentIcon />
      case 'idle':
        return <ThermostatIcon />
      case 'off':
        return <AcUnitIcon />
      default:
        return <ThermostatIcon />
    }
  }

  const formatTemperature = (temp: number | undefined | null): string | null => {
    if (temp === undefined || temp === null) return null
    return `${temp.toFixed(1)}°C`
  }

  const isValidState = (state: string | undefined): boolean => {
    return state !== undefined && state !== 'unavailable' && state !== 'unknown'
  }

  const getThermostatStatus = (device: any): string[] => {
    const parts = []

    // Add hvac_action if available (heating, cooling, idle, etc.)
    if (device.hvac_action && device.hvac_action !== 'idle' && device.hvac_action !== 'off') {
      const key = `area.${device.hvac_action}`
      const translatedAction = t(key, { defaultValue: device.hvac_action })
      parts.push(`[${translatedAction}]`)
    }

    const currentTemp = formatTemperature(device.current_temperature)
    if (currentTemp) {
      parts.push(currentTemp)
    }

    // Use area's target temperature instead of device's stale target
    const areaTarget = area.target_temperature
    if (
      areaTarget !== undefined &&
      areaTarget !== null &&
      device.current_temperature !== undefined &&
      device.current_temperature !== null &&
      areaTarget > device.current_temperature
    ) {
      const targetTemp = formatTemperature(areaTarget)
      if (targetTemp) parts.push(`→ ${targetTemp}`)
    }

    if (parts.length === 0 && device.state) {
      // Translate common states
      const key = `area.${device.state}`
      const translatedState = t(key, { defaultValue: device.state })
      parts.push(translatedState)
    }

    return parts
  }

  const getTemperatureSensorStatus = (device: any): string[] => {
    const parts = []

    const temp = formatTemperature(device.temperature)
    if (temp) {
      parts.push(temp)
    } else if (isValidState(device.state)) {
      parts.push(`${device.state}°C`)
    }

    return parts
  }

  const getValveStatus = (device: any): string[] => {
    const parts = []

    if (device.position !== undefined && device.position !== null) {
      parts.push(`${device.position}%`)
    } else if (isValidState(device.state)) {
      parts.push(`${device.state}%`)
    }

    return parts
  }

  const getGenericDeviceStatus = (device: any): string[] => {
    const parts = []

    if (isValidState(device.state)) {
      // Translate common states (on, off, etc.)
      const key = `area.${device.state}`
      const translatedState = t(key, { defaultValue: device.state })
      parts.push(translatedState)
    }

    return parts
  }

  const getDeviceStatusText = (device: any): string => {
    let parts: string[] = []

    if (device.type === 'thermostat') {
      parts = getThermostatStatus(device)
    } else if (device.type === 'temperature_sensor') {
      parts = getTemperatureSensorStatus(device)
    } else if (device.type === 'valve') {
      parts = getValveStatus(device)
    } else {
      parts = getGenericDeviceStatus(device)
    }

    return parts.length > 0 ? parts.join(' · ') : 'unavailable'
  }

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
  }

  return (
{