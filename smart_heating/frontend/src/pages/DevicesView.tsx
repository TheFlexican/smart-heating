import { useState, useEffect } from 'react'
import {
  Box,
  Typography,
  Paper,
  CircularProgress,
  Alert,
  IconButton,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { useNavigate } from 'react-router-dom'
import DevicePanel from '../components/DevicePanel'
import { getDevices } from '../api/devices'
import { getZones } from '../api/areas'
import { Device } from '../types'

const DevicesView = () => {
  const navigate = useNavigate()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const [devices, setDevices] = useState<Device[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadDevices = async () => {
    try {
      setLoading(true)
      setError(null)

      const [devicesData, areasData] = await Promise.all([getDevices(), getZones()])

      // Filter out devices already assigned to areas
      const assignedDeviceIds = new Set(areasData.flatMap(area => area.devices.map(d => d.id)))
      const availableDevices = devicesData.filter(device => !assignedDeviceIds.has(device.id))

      setDevices(availableDevices)
    } catch (err) {
      console.error('Failed to load devices:', err)
      setError('Failed to load devices')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDevices()
  }, [])

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          pb: { xs: 8, md: 0 }, // Account for bottom nav on mobile
        }}
      >
        <CircularProgress />
      </Box>
    )
  }

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        pb: { xs: 8, md: 0 }, // Account for bottom nav on mobile
      }}
    >
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
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}
      >
        {isMobile && (
          <IconButton onClick={() => navigate('/')} edge="start" data-testid="devices-back-button">
            <ArrowBackIcon />
          </IconButton>
        )}
        <Typography variant="h6">Devices</Typography>
      </Paper>

      {/* Content */}
      <Box sx={{ p: { xs: 2, sm: 3 } }}>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        <DevicePanel devices={devices} onUpdate={loadDevices} />
      </Box>
    </Box>
  )
}

export default DevicesView
