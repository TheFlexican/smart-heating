import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  Slider,
  IconButton,
  Alert,
  CircularProgress,
  Stack,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { useNavigate } from 'react-router-dom'
import { getGlobalPresets, setGlobalPresets } from '../api'

interface GlobalPresetsData {
  away_temp: number
  eco_temp: number
  comfort_temp: number
  home_temp: number
  sleep_temp: number
  activity_temp: number
}

const presetLabels = {
  away_temp: 'Away',
  eco_temp: 'Eco',
  comfort_temp: 'Comfort',
  home_temp: 'Home',
  sleep_temp: 'Sleep',
  activity_temp: 'Activity',
}

const presetDescriptions = {
  away_temp: 'Used when nobody is home',
  eco_temp: 'Energy-saving temperature',
  comfort_temp: 'Comfortable temperature for relaxing',
  home_temp: 'Standard temperature when home',
  sleep_temp: 'Nighttime sleeping temperature',
  activity_temp: 'Active daytime temperature',
}

export default function GlobalSettings() {
  const navigate = useNavigate()
  const [presets, setPresets] = useState<GlobalPresetsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const [saveSuccess, setSaveSuccess] = useState(false)
  const [saveTimeout, setSaveTimeout] = useState<number | null>(null)

  useEffect(() => {
    loadPresets()
  }, [])

  const loadPresets = async () => {
    try {
      setLoading(true)
      const data = await getGlobalPresets()
      setPresets(data)
      setError(null)
    } catch (err) {
      setError('Failed to load global presets')
      console.error('Error loading global presets:', err)
    } finally {
      setLoading(false)
    }
  }

  const handlePresetChange = (key: keyof GlobalPresetsData, value: number) => {
    if (!presets) return

    const newPresets = { ...presets, [key]: value }
    setPresets(newPresets)

    // Clear any existing timeout
    if (saveTimeout) {
      clearTimeout(saveTimeout)
    }

    // Set a new timeout to save after 500ms of no changes
    const timeout = setTimeout(async () => {
      try {
        setSaving(true)
        setSaveSuccess(false)
        await setGlobalPresets({ [key]: value })
        setSaveSuccess(true)
        setTimeout(() => setSaveSuccess(false), 2000)
      } catch (err) {
        setError('Failed to save preset')
        console.error('Error saving preset:', err)
        // Revert on error
        await loadPresets()
      } finally {
        setSaving(false)
      }
    }, 500)

    setSaveTimeout(timeout)
  }

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <CircularProgress />
      </Box>
    )
  }

  if (error && !presets) {
    return (
      <Box sx={{ p: 2 }}>
        <Alert severity="error">{error}</Alert>
      </Box>
    )
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', pb: 4 }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 2,
          mb: 2,
          borderRadius: 0,
          display: 'flex',
          alignItems: 'center',
          gap: 1,
        }}
      >
        <IconButton onClick={() => navigate('/')} edge="start">
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6">Global Preset Temperatures</Typography>
      </Paper>

      <Box sx={{ px: 2 }}>
        {saveSuccess && (
          <Alert severity="success" sx={{ mb: 2 }}>
            Preset saved successfully
          </Alert>
        )}

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <Paper sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" sx={{ mb: 1 }}>
            Preset Temperatures
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            These are the default temperatures for each preset mode. Areas can choose to use these global settings or define their own custom temperatures.
          </Typography>

          <Stack spacing={3}>
            {presets && Object.entries(presetLabels).map(([key, label]) => {
              const presetKey = key as keyof GlobalPresetsData
              const value = presets[presetKey]

              return (
                <Box key={key}>
                  <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
                    {label}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {presetDescriptions[presetKey]}
                  </Typography>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, px: 1 }}>
                    <Slider
                      value={value}
                      onChange={(_, newValue) => handlePresetChange(presetKey, newValue as number)}
                      min={5}
                      max={30}
                      step={0.1}
                      marks={[
                        { value: 5, label: '5°C' },
                        { value: 15, label: '15°C' },
                        { value: 20, label: '20°C' },
                        { value: 25, label: '25°C' },
                        { value: 30, label: '30°C' },
                      ]}
                      valueLabelDisplay="on"
                      valueLabelFormat={(v) => `${v}°C`}
                      disabled={saving}
                      sx={{ maxWidth: 600 }}
                    />
                  </Box>
                </Box>
              )
            })}
          </Stack>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 3, fontStyle: 'italic' }}>
            💡 Tip: To customize temperatures for a specific area, go to that area's settings and toggle off "Use global preset" for individual preset modes.
          </Typography>
        </Paper>
      </Box>
    </Box>
  )
}
