import {
  AppBar,
  Toolbar,
  Typography,
  Chip,
  Box,
  Tooltip,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import WifiIcon from '@mui/icons-material/Wifi'
import WifiOffIcon from '@mui/icons-material/WifiOff'
import SettingsIcon from '@mui/icons-material/Settings'
import LanguageIcon from '@mui/icons-material/Language'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'
import DevicesIcon from '@mui/icons-material/Devices'
import FireplaceIcon from '@mui/icons-material/Fireplace'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useState } from 'react'

interface HeaderProps {
  wsConnected?: boolean
  transportMode?: 'websocket' | 'polling'
}

const Header = ({ wsConnected = false, transportMode = 'websocket' }: HeaderProps) => {
  const { t, i18n } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [langMenuAnchor, setLangMenuAnchor] = useState<null | HTMLElement>(null)
  const [analyticsMenuAnchor, setAnalyticsMenuAnchor] = useState<null | HTMLElement>(null)

  // Determine active section for highlighting
  const isDevices = location.pathname.startsWith('/devices')
  const isAnalytics =
    location.pathname.startsWith('/analytics') || location.pathname.startsWith('/opentherm')
  const isSettings = location.pathname.startsWith('/settings')

  const handleLanguageMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setLangMenuAnchor(event.currentTarget)
  }

  const handleLanguageMenuClose = () => {
    setLangMenuAnchor(null)
  }

  const handleLanguageChange = (language: string) => {
    i18n.changeLanguage(language)
    handleLanguageMenuClose()
  }

  const handleSettingsClick = () => {
    navigate('/settings/global')
  }

  const handleAnalyticsMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnalyticsMenuAnchor(event.currentTarget)
  }

  const handleAnalyticsMenuClose = () => {
    setAnalyticsMenuAnchor(null)
  }

  const handleNavigateAnalytics = (path: string) => {
    navigate(path)
    handleAnalyticsMenuClose()
  }

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: 'background.paper',
        borderBottom: 1,
        borderColor: 'divider',
      }}
    >
      <Toolbar sx={{ gap: { xs: 1, sm: 2 } }}>
        <ThermostatIcon sx={{ color: 'primary.main', fontSize: { xs: 28, sm: 32 } }} />
        <Typography
          variant="h6"
          component="div"
          sx={{
            flexGrow: 1,
            fontWeight: 600,
            fontSize: { xs: '1rem', sm: '1.25rem' },
            cursor: 'pointer',
          }}
          onClick={() => navigate('/')}
        >
          {t('header.title')}
        </Typography>
        <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1, alignItems: 'center' }}>
          <Tooltip title={t('header.devices', 'Devices')}>
            <IconButton
              data-testid="header-devices-button"
              onClick={() => navigate('/devices')}
              sx={{
                color: isDevices ? 'primary.main' : 'text.secondary',
                bgcolor: isDevices ? 'action.selected' : 'transparent',
                p: 1,
                '&:hover': {
                  bgcolor: isDevices ? 'action.selected' : 'action.hover',
                },
              }}
            >
              <DevicesIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('header.analytics', 'Analytics')}>
            <IconButton
              data-testid="header-analytics-button"
              onClick={handleAnalyticsMenuOpen}
              sx={{
                color: isAnalytics ? 'primary.main' : 'text.secondary',
                bgcolor: isAnalytics ? 'action.selected' : 'transparent',
                p: 1,
                '&:hover': {
                  bgcolor: isAnalytics ? 'action.selected' : 'action.hover',
                },
              }}
            >
              <AnalyticsIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title={t('header.settings', 'Settings')}>
            <IconButton
              data-testid="header-settings-button"
              aria-label={t('header.settings', 'Settings')}
              onClick={handleSettingsClick}
              sx={{
                color: isSettings ? 'primary.main' : 'text.secondary',
                bgcolor: isSettings ? 'action.selected' : 'transparent',
                p: 1,
                '&:hover': {
                  bgcolor: isSettings ? 'action.selected' : 'action.hover',
                },
              }}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
        </Box>
        <Menu
          anchorEl={analyticsMenuAnchor}
          open={Boolean(analyticsMenuAnchor)}
          onClose={handleAnalyticsMenuClose}
        >
          <MenuItem
            data-testid="header-analytics-efficiency"
            onClick={() => handleNavigateAnalytics('/analytics/efficiency')}
          >
            <TrendingUpIcon sx={{ mr: 1 }} />
            {t('efficiency.title', 'Efficiency Reports')}
          </MenuItem>
          <MenuItem
            data-testid="header-analytics-comparison"
            onClick={() => handleNavigateAnalytics('/analytics/comparison')}
          >
            <CompareArrowsIcon sx={{ mr: 1 }} />
            {t('comparison.title', 'Historical Comparisons')}
          </MenuItem>
          <MenuItem
            data-testid="header-analytics-opentherm"
            onClick={() => handleNavigateAnalytics('/opentherm/metrics')}
          >
            <FireplaceIcon sx={{ mr: 1 }} />
            {t('opentherm.title', 'OpenTherm Metrics')}
          </MenuItem>
        </Menu>
        <Box sx={{ display: 'flex', gap: { xs: 0.5, sm: 1 }, alignItems: 'center' }}>
          <Tooltip title={t('header.changeLanguage')}>
            <IconButton
              data-testid="header-language-button"
              onClick={handleLanguageMenuOpen}
              sx={{
                color: 'text.secondary',
                p: { xs: 0.5, sm: 1 },
              }}
            >
              <LanguageIcon />
            </IconButton>
          </Tooltip>
          <Menu
            anchorEl={langMenuAnchor}
            open={Boolean(langMenuAnchor)}
            onClose={handleLanguageMenuClose}
          >
            <MenuItem
              data-testid="header-language-en"
              onClick={() => handleLanguageChange('en')}
              selected={i18n.language === 'en'}
            >
              English
            </MenuItem>
            <MenuItem
              data-testid="header-language-nl"
              onClick={() => handleLanguageChange('nl')}
              selected={i18n.language === 'nl'}
            >
              Nederlands
            </MenuItem>
          </Menu>
          <Tooltip title={wsConnected ? t('header.realtimeActive') : t('header.realtimeInactive')}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Chip
                icon={wsConnected ? <WifiIcon /> : <WifiOffIcon />}
                label={wsConnected ? t('header.connected') : t('header.disconnected')}
                size="small"
                color={wsConnected ? 'success' : 'default'}
                variant="outlined"
                sx={{
                  borderColor: wsConnected ? 'success.main' : 'divider',
                  color: wsConnected ? 'success.main' : 'text.secondary',
                  display: { xs: 'none', sm: 'flex' },
                }}
              />
              <Box sx={{ display: { xs: 'flex', sm: 'none' } }}>
                {wsConnected ? <WifiIcon color="success" /> : <WifiOffIcon color="disabled" />}
              </Box>
            </Box>
          </Tooltip>
          {transportMode === 'polling' && (
            <Tooltip title="Using polling mode (limited connectivity). WebSocket failed 3 times, falling back to periodic polling.">
              <Chip
                label="Polling"
                size="small"
                color="warning"
                variant="filled"
                sx={{
                  display: { xs: 'none', sm: 'flex' },
                }}
              />
            </Tooltip>
          )}
          <Chip
            label="v1.0.0"
            size="small"
            variant="outlined"
            sx={{
              borderColor: 'divider',
              color: 'text.secondary',
              display: { xs: 'none', sm: 'flex' },
            }}
          />
        </Box>
      </Toolbar>
    </AppBar>
  )
}

export default Header
