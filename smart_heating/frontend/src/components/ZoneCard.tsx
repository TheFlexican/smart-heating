import React, { useState, useEffect, useCallback } from 'react'
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
import { thermalColors } from '../theme'

interface ZoneCardProps {
  area: Zone
  onUpdate: () => void
  onPatchArea?: (areaId: string, patch: Partial<Zone>) => void
}

const ZoneCard = ({ area, onUpdate, onPatchArea }: ZoneCardProps) => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const isEnabledVal = (v: boolean | string | undefined | null) =>
    v === true || String(v) === 'true'
  const enabled = isEnabledVal(area.enabled)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: area.id,
  })

  const getDisplayTemperature = useCallback(() => {
    if (!enabled || area.state === 'off') return area.target_temperature
    if (!area.manual_override && area.effective_target_temperature != null) {
      if (Math.abs(area.effective_target_temperature - area.target_temperature) >= 0.1) {
        return area.effective_target_temperature
      }
    }
    return area.target_temperature
  }, [area, enabled])

  const normalizeTemperature = useCallback(
    (val: number | undefined | null) =>
      Number.isFinite(val as number) ? (val as number) : (area.target_temperature ?? 20),
    [area.target_temperature],
  )

  const [temperature, setTemperature] = useState(() =>
    normalizeTemperature(getDisplayTemperature()),
  )
  const [presenceState, setPresenceState] = useState<string | null>(null)

  useEffect(() => {
    const displayTemp = getDisplayTemperature()
    setTemperature(normalizeTemperature(displayTemp))
  }, [getDisplayTemperature, normalizeTemperature])

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

  const handleConfigureClick = (event: React.MouseEvent) => {
    event.stopPropagation()
    navigate(`/area/${area.id}`)
    handleMenuClose()
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
      onPatchArea?.(area.id, {
        target_temperature: value as number,
        manual_override: true,
        preset_mode: 'none',
      })
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

  // Thermal state styling
  const getStateGradient = () => {
    if (!enabled) return 'linear-gradient(135deg, #374151 0%, #1f2937 100%)'
    if (area.manual_override)
      return `linear-gradient(135deg, ${thermalColors.accent.amber} 0%, #d97706 100%)`

    switch (area.state) {
      case 'heating':
        return `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`
      case 'idle':
        return `linear-gradient(135deg, ${thermalColors.cool.primary} 0%, ${thermalColors.cool.secondary} 100%)`
      case 'off':
        return 'linear-gradient(135deg, #374151 0%, #1f2937 100%)'
      default:
        return 'linear-gradient(135deg, #374151 0%, #1f2937 100%)'
    }
  }

  const getStateGlow = () => {
    if (!enabled) return 'none'
    if (area.state === 'heating') {
      return `0 0 30px ${thermalColors.heat.glow}, 0 0 60px rgba(255, 107, 53, 0.2)`
    }
    return 'none'
  }

  const getStateIcon = () => {
    if (!enabled) return <AcUnitIcon />
    if (area.manual_override) return <TuneIcon />
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

  const getStateChipStyle = () => {
    if (!enabled) {
      return {
        background: alpha('#64748b', 0.2),
        border: `1px solid ${alpha('#64748b', 0.3)}`,
        color: '#94a3b8',
        '& .MuiChip-icon': { color: '#94a3b8' },
      }
    }
    if (area.manual_override) {
      return {
        background: `linear-gradient(135deg, ${alpha(thermalColors.accent.amber, 0.9)} 0%, ${alpha('#d97706', 0.9)} 100%)`,
        color: '#ffffff',
        '& .MuiChip-icon': { color: '#ffffff' },
      }
    }
    switch (area.state) {
      case 'heating':
        return {
          background: `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`,
          color: '#ffffff',
          boxShadow: `0 2px 8px ${thermalColors.heat.glow}`,
          '& .MuiChip-icon': { color: '#ffffff' },
        }
      case 'idle':
        return {
          background: `linear-gradient(135deg, ${thermalColors.cool.primary} 0%, ${thermalColors.cool.secondary} 100%)`,
          color: '#ffffff',
          '& .MuiChip-icon': { color: '#ffffff' },
        }
      case 'off':
      default:
        return {
          background: alpha('#64748b', 0.2),
          border: `1px solid ${alpha('#64748b', 0.3)}`,
          color: '#94a3b8',
          '& .MuiChip-icon': { color: '#94a3b8' },
        }
    }
  }

  const renderStateChip = () => {
    let stateLabel = t(`area.${area.state}`, { defaultValue: area.state }).toUpperCase()
    if (!enabled) stateLabel = t('area.off')
    else if (area.manual_override) stateLabel = t('area.manual')

    return (
      <Chip
        data-testid={`area-state-${area.id}`}
        icon={getStateIcon()}
        label={stateLabel}
        size="small"
        sx={{
          fontSize: { xs: '0.7rem', sm: '0.75rem' },
          fontWeight: 600,
          letterSpacing: '0.02em',
          ...getStateChipStyle(),
        }}
      />
    )
  }

  const formatTemperature = (temp: number | undefined | null): string | null => {
    if (temp === undefined || temp === null) return null
    return `${temp.toFixed(1)}°C`
  }

  const renderBadges = () => {
    const badges: React.ReactElement[] = []
    if (area.presence_sensors && area.presence_sensors.length > 0 && presenceState) {
      badges.push(
        <Chip
          key="presence"
          data-testid={`area-presence-${area.id}`}
          icon={<PersonIcon />}
          label={t(`presets.${presenceState}`, { defaultValue: presenceState }).toUpperCase()}
          size="small"
          sx={{
            fontSize: { xs: '0.7rem', sm: '0.75rem' },
            fontWeight: 600,
            ...(presenceState === 'home'
              ? {
                  background: `linear-gradient(135deg, ${alpha(thermalColors.accent.emerald, 0.9)} 0%, ${alpha('#059669', 0.9)} 100%)`,
                  color: '#ffffff',
                  '& .MuiChip-icon': { color: '#ffffff' },
                }
              : {
                  background: alpha('#64748b', 0.2),
                  border: `1px solid ${alpha('#64748b', 0.3)}`,
                  color: '#94a3b8',
                  '& .MuiChip-icon': { color: '#94a3b8' },
                }),
          }}
        />,
      )
    }
    if (area.boost_mode_active) {
      badges.push(
        <Chip
          key="boost"
          data-testid="boost-active-badge"
          icon={<RocketLaunchIcon />}
          label={t('presets.boost', { defaultValue: 'BOOST' }).toUpperCase()}
          size="small"
          sx={{
            fontSize: { xs: '0.7rem', sm: '0.75rem' },
            fontWeight: 600,
            animation: 'pulse-heat 2s infinite',
            background: `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`,
            color: '#ffffff',
            boxShadow: `0 2px 8px ${thermalColors.heat.glow}`,
            '& .MuiChip-icon': { color: '#ffffff' },
          }}
        />,
      )
    }

    // PID badge - show when PID is enabled and current mode is in active modes
    if (area.pid_enabled) {
      // Determine current mode: preset_mode or 'schedule' if schedule is active
      const currentMode = area.preset_mode || 'schedule'

      // Check if current mode is in active modes
      const activeModes = area.pid_active_modes || []
      if (activeModes.includes(currentMode)) {
        const pidMode = area.pid_automatic_gains ? 'Auto' : 'Manual'
        badges.push(
          <Chip
            key="pid"
            data-testid="pid-active-badge"
            label="PID"
            size="small"
            sx={{
              fontSize: { xs: '0.7rem', sm: '0.75rem' },
              fontWeight: 600,
              background: `linear-gradient(135deg, ${alpha(thermalColors.accent.amber, 0.9)} 0%, ${alpha('#d97706', 0.9)} 100%)`,
              color: '#ffffff',
              '& .MuiChip-icon': { color: '#ffffff' },
            }}
            title={t('settingsCards.pidBadgeTooltip', { mode: pidMode })}
          />,
        )
      }
    }

    return badges
  }

  const isValidState = (state: string | undefined): boolean => {
    return state !== undefined && state !== 'unavailable' && state !== 'unknown'
  }

  const getThermostatStatus = (device: any): string[] => {
    const parts = []
    if (device.hvac_action && device.hvac_action !== 'idle' && device.hvac_action !== 'off') {
      const key = `area.${device.hvac_action}`
      const translatedAction = t(key, { defaultValue: device.hvac_action })
      parts.push(`[${translatedAction}]`)
    }
    const currentTemp = formatTemperature(device.current_temperature)
    if (currentTemp) {
      parts.push(currentTemp)
    }
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
    <Card
      ref={setNodeRef}
      style={style}
      data-testid={`area-card-${area.name.toLowerCase().replaceAll(' ', '-')}`}
      elevation={isDragging ? 12 : 2}
      sx={{
        position: 'relative',
        borderRadius: '24px',
        cursor: isDragging ? 'grabbing' : 'default',
        opacity: isDragging ? 0.95 : 1,
        minHeight: { xs: 180, sm: 200 },
        overflow: 'hidden',
        // Thermal glow effect when heating
        boxShadow: isDragging
          ? `0 24px 48px rgba(0, 0, 0, 0.5), 0 0 0 2px ${alpha(thermalColors.heat.primary, 0.3)}`
          : getStateGlow(),
        transition: 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
        '&::before': {
          content: '""',
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 4,
          background: getStateGradient(),
          zIndex: 1,
        },
        '&:hover': {
          transform: isDragging ? undefined : 'translateY(-6px)',
          boxShadow: isDragging
            ? '0 24px 48px rgba(0, 0, 0, 0.5)'
            : area.state === 'heating'
              ? `0 20px 40px rgba(0, 0, 0, 0.4), ${getStateGlow()}`
              : '0 20px 40px rgba(0, 0, 0, 0.4)',
        },
      }}
    >
      <CardContent sx={{ p: { xs: 2.5, sm: 3 }, pt: { xs: 3, sm: 3.5 } }}>
        {/* Drag Handle */}
        <Box
          {...attributes}
          {...listeners}
          sx={{
            position: 'absolute',
            top: 12,
            left: 12,
            cursor: isDragging ? 'grabbing' : 'grab',
            color: isDragging ? 'primary.main' : 'text.secondary',
            opacity: isDragging ? 1 : 0.3,
            transition: 'all 0.2s',
            p: 0.5,
            borderRadius: 1,
            '&:hover': {
              opacity: 1,
              color: 'primary.main',
              bgcolor: alpha(thermalColors.heat.primary, 0.1),
            },
          }}
          onClick={e => e.stopPropagation()}
        >
          <DragIndicatorIcon fontSize="small" />
        </Box>

        {/* Header Section */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box flex={1} pl={3}>
            <Typography
              variant="h6"
              gutterBottom
              sx={{
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
                fontWeight: 600,
                letterSpacing: '-0.01em',
                mb: 1,
              }}
            >
              {area.name}
            </Typography>
            <Box display="flex" gap={1} flexWrap="wrap">
              {renderStateChip()}
              {renderBadges()}
            </Box>
          </Box>
          <Box onClick={e => e.stopPropagation()} display="flex" gap={0.5}>
            <Tooltip
              title={
                area.boost_mode_active ? t('boost.quickBoostActive') : t('boost.quickBoostInactive')
              }
            >
              <IconButton
                data-testid={`boost-toggle-${area.id}`}
                size="small"
                onClick={handleBoostToggle}
                sx={{
                  p: 1,
                  color: area.boost_mode_active ? '#fff' : 'text.secondary',
                  background: area.boost_mode_active
                    ? `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`
                    : 'transparent',
                  boxShadow: area.boost_mode_active
                    ? `0 4px 12px ${thermalColors.heat.glow}`
                    : 'none',
                  '&:hover': {
                    background: area.boost_mode_active
                      ? `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`
                      : alpha(thermalColors.heat.primary, 0.1),
                    transform: 'scale(1.1)',
                  },
                }}
              >
                <RocketLaunchIcon />
              </IconButton>
            </Tooltip>
            <IconButton
              data-testid={`zone-menu-button-${area.id}`}
              size="small"
              onClick={handleMenuOpen}
              sx={{ p: 1 }}
            >
              <MoreVertIcon />
            </IconButton>
          </Box>
        </Box>

        {/* HVAC Mode Selector for Airco */}
        {area.heating_type === 'airco' && (
          <Box mb={2} onClick={e => e.stopPropagation()}>
            <FormControl fullWidth size="small">
              <InputLabel id={`hvac-mode-label-${area.id}`}>
                {t('area.hvacMode', { defaultValue: 'Mode' })}
              </InputLabel>
              <Select
                labelId={`hvac-mode-label-${area.id}`}
                data-testid={`hvac-mode-select-${area.id}`}
                value={area.hvac_mode || 'auto'}
                label={t('area.hvacMode', { defaultValue: 'Mode' })}
                onChange={handleHvacModeChange}
                disabled={!enabled || area.devices.length === 0}
              >
                <MenuItem value="heat" data-testid="hvac-mode-heat">
                  <Box display="flex" alignItems="center" gap={1}>
                    <LocalFireDepartmentIcon
                      fontSize="small"
                      sx={{ color: thermalColors.heat.primary }}
                    />
                    <span>{t('area.hvacModeHeat', { defaultValue: 'Heat' })}</span>
                  </Box>
                </MenuItem>
                <MenuItem value="cool" data-testid="hvac-mode-cool">
                  <Box display="flex" alignItems="center" gap={1}>
                    <AcUnitIcon fontSize="small" sx={{ color: thermalColors.cool.primary }} />
                    <span>{t('area.hvacModeCool', { defaultValue: 'Cool' })}</span>
                  </Box>
                </MenuItem>
                <MenuItem value="off" data-testid="hvac-mode-off">
                  <Box display="flex" alignItems="center" gap={1}>
                    <RemoveCircleOutlineIcon fontSize="small" />
                    <span>{t('area.hvacModeOff', { defaultValue: 'Off' })}</span>
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>
          </Box>
        )}

        {/* Temperature Section - Hero Element */}
        <Box
          my={{ xs: 2.5, sm: 3 }}
          onClick={handleSliderClick}
          sx={{
            p: 2,
            borderRadius: 3,
            background: theme =>
              theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)',
          }}
        >
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1.5}>
            <Box display="flex" alignItems="center" gap={1}>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
              >
                {t('area.targetTemperature')}
              </Typography>
              {enabled &&
                area.state !== 'off' &&
                area.preset_mode &&
                area.preset_mode !== 'none' && (
                  <Chip
                    data-testid="preset-mode-badge"
                    label={t(`presets.${area.preset_mode}`).toUpperCase()}
                    size="small"
                    sx={{
                      fontSize: '0.65rem',
                      height: 20,
                      fontWeight: 600,
                      background: `linear-gradient(135deg, ${alpha(thermalColors.accent.violet, 0.8)} 0%, ${alpha('#6366f1', 0.8)} 100%)`,
                      color: '#fff',
                    }}
                  />
                )}
            </Box>
            <Typography
              className="temperature-display"
              data-testid="target-temperature-display"
              sx={{
                fontSize: { xs: '2rem', sm: '2.5rem' },
                fontWeight: 600,
                fontFamily: '"JetBrains Mono", monospace',
                background:
                  area.state === 'heating'
                    ? `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`
                    : area.state === 'idle'
                      ? `linear-gradient(135deg, ${thermalColors.cool.primary} 0%, ${thermalColors.cool.secondary} 100%)`
                      : 'linear-gradient(135deg, #94a3b8 0%, #64748b 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
                letterSpacing: '-0.02em',
              }}
            >
              {Number.isFinite(temperature)
                ? `${temperature}°`
                : (formatTemperature(area.target_temperature) ?? '-')}
            </Typography>
          </Box>
          <Slider
            data-testid="temperature-slider"
            value={Number.isFinite(temperature) ? temperature : (area.target_temperature ?? 20)}
            onChange={handleTemperatureChange}
            onChangeCommitted={handleTemperatureCommit}
            min={5}
            max={30}
            step={0.1}
            marks={[
              { value: 5, label: '5°' },
              { value: 30, label: '30°' },
            ]}
            valueLabelDisplay="auto"
            disabled={!enabled || area.devices.length === 0 || !area.manual_override}
          />
          {area.devices.length === 0 && (
            <Box
              display="flex"
              alignItems="center"
              gap={1}
              mt={1.5}
              sx={{
                color: 'warning.main',
                p: 1,
                borderRadius: 2,
                bgcolor: alpha(thermalColors.accent.amber, 0.1),
              }}
            >
              <InfoOutlinedIcon fontSize="small" />
              <Typography variant="caption" sx={{ fontSize: '0.75rem' }}>
                {t('area.addDevicesPrompt')}
              </Typography>
            </Box>
          )}
        </Box>

        {/* Current Temperature */}
        {area.current_temperature !== undefined && area.current_temperature !== null && (
          <Box
            display="flex"
            justifyContent="space-between"
            alignItems="center"
            mb={2}
            sx={{
              p: 1.5,
              borderRadius: 2,
              background: theme =>
                theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.01)',
            }}
          >
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
            >
              {t('area.currentTemperature')}
            </Typography>
            <Typography
              className="temperature-display"
              data-testid="current-temperature-display"
              sx={{
                fontSize: { xs: '1.1rem', sm: '1.25rem' },
                fontWeight: 500,
                fontFamily: '"JetBrains Mono", monospace',
              }}
            >
              {area.current_temperature.toFixed(1)}°C
            </Typography>
          </Box>
        )}

        {/* Manual Override Toggle */}
        <Box mb={2} onClick={e => e.stopPropagation()}>
          <FormControlLabel
            control={
              <Switch
                data-testid="area-enable-toggle"
                checked={!area.manual_override}
                disabled={!enabled}
                onChange={async e => {
                  if (!enabled) return
                  try {
                    await setManualOverride(area.id, !e.target.checked)
                    onUpdate()
                  } catch (error) {
                    console.error('Failed to toggle manual override:', error)
                  }
                }}
                size="small"
              />
            }
            label={
              <Box display="flex" alignItems="center" gap={1}>
                <BookmarkIcon fontSize="small" sx={{ opacity: 0.7 }} />
                <Typography variant="body2" sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}>
                  {area.manual_override ? t('area.usePresetMode') : t('area.usingPresetMode')}
                </Typography>
              </Box>
            }
          />
        </Box>

        {/* Device Count */}
        <Box
          display="flex"
          alignItems="center"
          gap={1}
          mb={area.devices.length > 0 ? 2 : 0}
          sx={{ opacity: 0.8 }}
        >
          <SensorsIcon fontSize="small" sx={{ opacity: 0.7 }} />
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ fontSize: { xs: '0.8rem', sm: '0.875rem' } }}
          >
            {t('area.deviceCount', { count: area.devices.length })}
          </Typography>
        </Box>

        {/* Devices List */}
        {area.devices.length > 0 && (
          <List
            dense
            sx={{
              mt: 1,
              p: 1,
              bgcolor: theme =>
                theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.01)',
              borderRadius: 2,
            }}
          >
            {area.devices.map(device => (
              <ListItem
                key={device.id}
                secondaryAction={
                  <IconButton
                    edge="end"
                    size="small"
                    onClick={e => {
                      e.stopPropagation()
                      handleRemoveDevice(device.id)
                    }}
                    sx={{
                      color: 'text.secondary',
                      opacity: 0.6,
                      p: 0.5,
                      '&:hover': {
                        opacity: 1,
                        color: 'error.main',
                      },
                    }}
                  >
                    <RemoveCircleOutlineIcon fontSize="small" />
                  </IconButton>
                }
                sx={{
                  py: 0.75,
                  pr: 5,
                  borderRadius: 1.5,
                  '&:hover': {
                    bgcolor: theme =>
                      theme.palette.mode === 'dark'
                        ? 'rgba(255, 255, 255, 0.04)'
                        : 'rgba(0, 0, 0, 0.02)',
                  },
                }}
              >
                <ListItemText
                  primary={
                    <Typography
                      variant="body2"
                      color="text.primary"
                      sx={{
                        fontSize: { xs: '0.8rem', sm: '0.875rem' },
                        wordBreak: 'break-word',
                        fontWeight: 500,
                      }}
                    >
                      {device.name || device.id}
                    </Typography>
                  }
                  secondary={getDeviceStatusText(device)}
                  slotProps={{
                    secondary: {
                      variant: 'caption',
                      color: 'text.secondary',
                      sx: {
                        fontSize: { xs: '0.7rem', sm: '0.75rem' },
                        fontFamily: '"JetBrains Mono", monospace',
                      },
                    },
                  }}
                />
              </ListItem>
            ))}
          </List>
        )}
      </CardContent>

      {/* Context Menu */}
      <Menu
        data-testid={`zone-menu-${area.id}`}
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={handleMenuClose}
      >
        <MenuItem data-testid={`zone-menu-configure-${area.id}`} onClick={handleConfigureClick}>
          <ListItemIcon>
            <TuneIcon />
          </ListItemIcon>
          <ListItemText primary={t('area.settings', 'Settings')} />
        </MenuItem>
        <MenuItem data-testid={`zone-menu-hide-${area.id}`} onClick={handleToggleHidden}>
          <ListItemIcon>{area.hidden ? <VisibilityIcon /> : <VisibilityOffIcon />}</ListItemIcon>
          <ListItemText primary={area.hidden ? t('area.unhideArea') : t('area.hideArea')} />
        </MenuItem>
      </Menu>
    </Card>
  )
}

export default ZoneCard
