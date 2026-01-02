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
  alpha,
} from '@mui/material'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import WifiIcon from '@mui/icons-material/Wifi'
import WifiOffIcon from '@mui/icons-material/WifiOff'
import SettingsIcon from '@mui/icons-material/Settings'
import LanguageIcon from '@mui/icons-material/Language'
import AnalyticsIcon from '@mui/icons-material/Analytics'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'
import { useNavigate, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useState } from 'react'
import { thermalColors } from '../theme'

type AnalyticsMenuProps = {
  anchorEl: null | HTMLElement
  onClose: () => void
  onNavigate: (path: string) => void
  t: (key: string, opts?: any) => string
}

const AnalyticsMenu = ({ anchorEl, onClose, onNavigate, t }: AnalyticsMenuProps) => (
  <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={onClose}>
    <MenuItem
      data-testid="header-analytics-efficiency"
      onClick={() => onNavigate('/analytics/efficiency')}
    >
      <TrendingUpIcon sx={{ mr: 1.5, color: thermalColors.accent.emerald }} />
      {t('efficiency.title', 'Efficiency Reports')}
    </MenuItem>
    <MenuItem
      data-testid="header-analytics-comparison"
      onClick={() => onNavigate('/analytics/comparison')}
    >
      <CompareArrowsIcon sx={{ mr: 1.5, color: thermalColors.cool.primary }} />
      {t('comparison.title', 'Historical Comparisons')}
    </MenuItem>
  </Menu>
)

type LanguageMenuProps = {
  anchorEl: null | HTMLElement
  onClose: () => void
  onChange: (lang: string) => void
  i18n: any
}

const LanguageMenu = ({ anchorEl, onClose, onChange, i18n }: LanguageMenuProps) => (
  <Menu anchorEl={anchorEl} open={Boolean(anchorEl)} onClose={onClose}>
    <MenuItem
      data-testid="header-language-en"
      onClick={() => onChange('en')}
      selected={i18n.language === 'en'}
    >
      English
    </MenuItem>
    <MenuItem
      data-testid="header-language-nl"
      onClick={() => onChange('nl')}
      selected={i18n.language === 'nl'}
    >
      Nederlands
    </MenuItem>
  </Menu>
)

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

  const isAnalytics = location.pathname.startsWith('/analytics')
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

  const renderRightActions = () => (
    <Box sx={{ display: 'flex', gap: { xs: 0.75, sm: 1 }, alignItems: 'center' }}>
      <Tooltip title={t('header.changeLanguage')}>
        <IconButton
          data-testid="header-language-button"
          onClick={handleLanguageMenuOpen}
          sx={{
            color: 'text.secondary',
            p: { xs: 0.75, sm: 1 },
            '&:hover': {
              color: 'primary.main',
            },
          }}
        >
          <LanguageIcon sx={{ fontSize: { xs: 20, sm: 24 } }} />
        </IconButton>
      </Tooltip>
      <LanguageMenu
        anchorEl={langMenuAnchor}
        onClose={handleLanguageMenuClose}
        onChange={handleLanguageChange}
        i18n={i18n}
      />

      {/* Connection Status */}
      <Tooltip title={wsConnected ? t('header.realtimeActive') : t('header.realtimeInactive')}>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Chip
            icon={wsConnected ? <WifiIcon /> : <WifiOffIcon />}
            label={wsConnected ? t('header.connected') : t('header.disconnected')}
            size="small"
            sx={{
              display: { xs: 'none', sm: 'flex' },
              fontWeight: 500,
              background: wsConnected
                ? `linear-gradient(135deg, ${alpha(thermalColors.accent.emerald, 0.15)} 0%, ${alpha('#059669', 0.15)} 100%)`
                : alpha('#64748b', 0.15),
              border: `1px solid ${wsConnected ? alpha(thermalColors.accent.emerald, 0.3) : alpha('#64748b', 0.2)}`,
              color: wsConnected ? thermalColors.accent.emerald : 'text.secondary',
              '& .MuiChip-icon': {
                color: wsConnected ? thermalColors.accent.emerald : 'text.secondary',
              },
            }}
          />
          <Box
            sx={{
              display: { xs: 'flex', sm: 'none' },
              p: 0.75,
              borderRadius: 2,
              bgcolor: wsConnected
                ? alpha(thermalColors.accent.emerald, 0.15)
                : alpha('#64748b', 0.15),
            }}
          >
            {wsConnected ? (
              <WifiIcon sx={{ fontSize: 20, color: thermalColors.accent.emerald }} />
            ) : (
              <WifiOffIcon sx={{ fontSize: 20, color: 'text.secondary' }} />
            )}
          </Box>
        </Box>
      </Tooltip>

      {transportMode === 'polling' && (
        <Tooltip title="Using polling mode (limited connectivity). WebSocket failed 3 times, falling back to periodic polling.">
          <Chip
            label="Polling"
            size="small"
            sx={{
              display: { xs: 'none', sm: 'flex' },
              fontWeight: 500,
              background: alpha(thermalColors.accent.amber, 0.15),
              border: `1px solid ${alpha(thermalColors.accent.amber, 0.3)}`,
              color: thermalColors.accent.amber,
            }}
          />
        </Tooltip>
      )}

      <Chip
        label="v1.0.0"
        size="small"
        sx={{
          display: { xs: 'none', md: 'flex' },
          fontWeight: 500,
          background: alpha('#64748b', 0.1),
          border: '1px solid rgba(255, 255, 255, 0.06)',
          color: 'text.secondary',
        }}
      />
    </Box>
  )

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        bgcolor: 'transparent',
        background: theme =>
          theme.palette.mode === 'dark'
            ? `linear-gradient(180deg, ${alpha('#0a0a0f', 0.95)} 0%, ${alpha('#12121a', 0.9)} 100%)`
            : `linear-gradient(180deg, ${alpha('#ffffff', 0.98)} 0%, ${alpha('#f8fafc', 0.95)} 100%)`,
        backdropFilter: 'blur(20px)',
        borderBottom: theme =>
          `1px solid ${theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)'}`,
      }}
    >
      <Toolbar
        sx={{ gap: { xs: 1, sm: 1.5, md: 2 }, py: { xs: 0.75, sm: 1 }, px: { xs: 1.5, sm: 2 } }}
      >
        {/* Logo / Brand */}
        <Box
          onClick={() => navigate('/')}
          sx={{
            display: 'flex',
            alignItems: 'center',
            gap: { xs: 1, sm: 1.5 },
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            '&:hover': {
              opacity: 0.85,
            },
          }}
        >
          <Box
            sx={{
              p: { xs: 0.75, sm: 1 },
              borderRadius: 2.5,
              background: `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`,
              boxShadow: `0 4px 12px ${thermalColors.heat.glow}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ThermostatIcon sx={{ color: '#ffffff', fontSize: { xs: 20, sm: 26 } }} />
          </Box>
          <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
            <Typography
              variant="h6"
              sx={{
                fontFamily: '"Outfit", sans-serif',
                fontWeight: 700,
                fontSize: { xs: '1rem', sm: '1.2rem' },
                letterSpacing: '-0.02em',
                background: `linear-gradient(135deg, ${thermalColors.heat.primary} 0%, ${thermalColors.heat.secondary} 100%)`,
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                backgroundClip: 'text',
              }}
            >
              {t('header.title')}
            </Typography>
          </Box>
        </Box>

        {/* Spacer */}
        <Box sx={{ flexGrow: 1 }} />

        {/* Navigation Actions */}
        <Box sx={{ display: { xs: 'none', md: 'flex' }, gap: 1, alignItems: 'center' }}>
          <Tooltip title={t('header.analytics', 'Analytics')}>
            <IconButton
              data-testid="header-analytics-button"
              onClick={handleAnalyticsMenuOpen}
              sx={{
                p: 1.25,
                borderRadius: 2,
                color: isAnalytics ? thermalColors.heat.primary : 'text.secondary',
                background: isAnalytics ? alpha(thermalColors.heat.primary, 0.1) : 'transparent',
                '&:hover': {
                  background: isAnalytics
                    ? alpha(thermalColors.heat.primary, 0.15)
                    : alpha('#ffffff', 0.05),
                  color: isAnalytics ? thermalColors.heat.primary : 'text.primary',
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
                p: 1.25,
                borderRadius: 2,
                color: isSettings ? thermalColors.heat.primary : 'text.secondary',
                background: isSettings ? alpha(thermalColors.heat.primary, 0.1) : 'transparent',
                '&:hover': {
                  background: isSettings
                    ? alpha(thermalColors.heat.primary, 0.15)
                    : alpha('#ffffff', 0.05),
                  color: isSettings ? thermalColors.heat.primary : 'text.primary',
                },
              }}
            >
              <SettingsIcon />
            </IconButton>
          </Tooltip>
          <AnalyticsMenu
            anchorEl={analyticsMenuAnchor}
            onClose={handleAnalyticsMenuClose}
            onNavigate={handleNavigateAnalytics}
            t={t}
          />
        </Box>

        {renderRightActions()}
      </Toolbar>
    </AppBar>
  )
}

export default Header
