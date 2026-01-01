import { BottomNavigation, BottomNavigationAction, Paper } from '@mui/material'
import HomeIcon from '@mui/icons-material/Home'
import DevicesIcon from '@mui/icons-material/Devices'
import BarChartIcon from '@mui/icons-material/BarChart'
import SettingsIcon from '@mui/icons-material/Settings'
import { useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'

const MobileBottomNav = () => {
  const navigate = useNavigate()
  const location = useLocation()
  const [value, setValue] = useState(0)

  // Determine active tab based on current route
  useEffect(() => {
    const path = location.pathname
    if (path === '/' || path.startsWith('/area/')) {
      setValue(0) // Zones
    } else if (path.startsWith('/devices')) {
      setValue(1) // Devices
    } else if (path.startsWith('/analytics')) {
      setValue(2) // Analytics
    } else if (path.startsWith('/settings')) {
      setValue(3) // Settings
    }
  }, [location.pathname])

  const handleChange = (_event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue)

    switch (newValue) {
      case 0:
        navigate('/')
        break
      case 1:
        navigate('/devices')
        break
      case 2:
        navigate('/analytics')
        break
      case 3:
        navigate('/settings')
        break
    }
  }

  return (
    <Paper
      sx={{
        position: 'fixed',
        bottom: 0,
        left: 0,
        right: 0,
        zIndex: 1000,
        display: { xs: 'block', md: 'none' }, // Only show on mobile/tablet
        // Safe area insets for iPhone notch
        paddingBottom: 'env(safe-area-inset-bottom)',
      }}
      elevation={8}
    >
      <BottomNavigation
        value={value}
        onChange={handleChange}
        showLabels
        sx={{
          height: 56,
          '& .MuiBottomNavigationAction-root': {
            minWidth: 'auto',
            padding: '6px 12px',
            '&.Mui-selected': {
              color: 'primary.main',
            },
          },
          '& .MuiBottomNavigationAction-label': {
            fontSize: '0.75rem',
            '&.Mui-selected': {
              fontSize: '0.75rem',
            },
          },
        }}
      >
        <BottomNavigationAction label="Zones" icon={<HomeIcon />} data-testid="mobile-nav-zones" />
        <BottomNavigationAction
          label="Devices"
          icon={<DevicesIcon />}
          data-testid="mobile-nav-devices"
        />
        <BottomNavigationAction
          label="Analytics"
          icon={<BarChartIcon />}
          data-testid="mobile-nav-analytics"
        />
        <BottomNavigationAction
          label="Settings"
          icon={<SettingsIcon />}
          data-testid="mobile-nav-settings"
        />
      </BottomNavigation>
    </Paper>
  )
}

export default MobileBottomNav
