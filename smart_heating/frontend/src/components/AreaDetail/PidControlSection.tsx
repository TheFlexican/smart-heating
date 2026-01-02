import React, { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  FormControlLabel,
  Switch,
  FormGroup,
  Checkbox,
  Alert,
  Button,
} from '@mui/material'
import TuneIcon from '@mui/icons-material/Tune'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setAreaPid } from '../../api/areas'

export interface PidControlSectionProps {
  area: Zone
  onUpdate: () => void
  t: (key: string, options?: any) => string
}

const AVAILABLE_MODES = ['schedule', 'home', 'away', 'sleep', 'comfort', 'eco', 'boost']

const DEFAULT_ACTIVE_MODES = ['schedule', 'home', 'comfort']

// Separate React component for the content that can use hooks
const PidControlContent: React.FC<{
  area: Zone
  onUpdate: () => void
  t: (key: string, options?: any) => string
}> = ({ area, onUpdate, t }) => {
  const [pidEnabled, setPidEnabled] = useState(area.pid_enabled ?? false)
  const [automaticGains, setAutomaticGains] = useState(area.pid_automatic_gains ?? true)
  const [activeModes, setActiveModes] = useState<string[]>(
    area.pid_active_modes ?? DEFAULT_ACTIVE_MODES,
  )
  const [saving, setSaving] = useState(false)

  // Update state when area changes
  useEffect(() => {
    setPidEnabled(area.pid_enabled ?? false)
    setAutomaticGains(area.pid_automatic_gains ?? true)
    setActiveModes(area.pid_active_modes ?? DEFAULT_ACTIVE_MODES)
  }, [area.pid_enabled, area.pid_automatic_gains, area.pid_active_modes])

  const handleSave = async () => {
    try {
      setSaving(true)
      await setAreaPid(area.id, pidEnabled, automaticGains, activeModes)
      onUpdate()
    } catch (err) {
      console.error('Failed to save PID configuration:', err)
      alert('Failed to save PID configuration')
    } finally {
      setSaving(false)
    }
  }

  const handleModeToggle = (mode: string) => {
    setActiveModes(prev => {
      if (prev.includes(mode)) {
        return prev.filter(m => m !== mode)
      } else {
        return [...prev, mode]
      }
    })
  }

  return (
    <Box data-testid="pid-control-section">
      {/* Enable PID Control */}
      <FormControlLabel
        control={
          <Switch
            data-testid="pid-enabled-switch"
            checked={pidEnabled}
            onChange={e => setPidEnabled(e.target.checked)}
          />
        }
        label={t('settingsCards.enablePid')}
        sx={{ mb: 2 }}
      />

      {/* Automatic Gains */}
      <FormControlLabel
        control={
          <Switch
            data-testid="pid-automatic-gains-switch"
            checked={automaticGains}
            onChange={e => setAutomaticGains(e.target.checked)}
            disabled={!pidEnabled}
          />
        }
        label={t('settingsCards.automaticGains')}
        sx={{ mb: 2 }}
      />

      {/* Active Modes */}
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {t('settingsCards.pidActiveModes')}
      </Typography>
      <FormGroup sx={{ mb: 2, ml: 2 }}>
        {AVAILABLE_MODES.map(mode => (
          <FormControlLabel
            key={mode}
            control={
              <Checkbox
                data-testid={`pid-mode-${mode}`}
                checked={activeModes.includes(mode)}
                onChange={() => handleModeToggle(mode)}
                disabled={!pidEnabled}
              />
            }
            label={t(`settingsCards.modeLabels.${mode}`, { defaultValue: mode })}
          />
        ))}
      </FormGroup>

      {/* Warning for floor heating */}
      <Alert severity="warning" sx={{ mb: 2 }} data-testid="pid-floor-heating-warning">
        {t('settingsCards.pidFloorHeatingWarning')}
      </Alert>

      {/* Save Button */}
      <Button
        variant="contained"
        onClick={handleSave}
        disabled={saving}
        data-testid="pid-save-button"
      >
        {saving ? t('common.saving', { defaultValue: 'Saving...' }) : t('common.save')}
      </Button>
    </Box>
  )
}

export const PidControlSection = ({
  area,
  onUpdate,
  t,
}: PidControlSectionProps): SettingSection => {
  return {
    id: 'pid-control',
    title: t('settingsCards.pidControlTitle'),
    description: t('settingsCards.pidControlDescription'),
    icon: <TuneIcon />,
    defaultExpanded: false,
    content: <PidControlContent area={area} onUpdate={onUpdate} t={t} />,
  }
}
