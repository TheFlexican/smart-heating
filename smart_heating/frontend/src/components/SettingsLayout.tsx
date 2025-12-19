import { useMediaQuery, useTheme } from '@mui/material'
import { useLocation } from 'react-router-dom'
import MobileSettingsLayout from './MobileSettingsLayout'
import GlobalSettings from '../pages/GlobalSettings'
import { settingsItems } from './MobileSettingsLayout'

interface SettingsLayoutProps {
  themeMode: 'light' | 'dark'
  onThemeChange: (mode: 'light' | 'dark') => void
  wsMetrics?: {
    totalConnectionAttempts: number
    successfulConnections: number
    failedConnections: number
    unexpectedDisconnects: number
    averageConnectionDuration: number
    lastFailureReason: string
    lastConnectedAt: string | null
    lastDisconnectedAt: string | null
    connectionDurations: number[]
    deviceInfo: {
      userAgent: string
      platform: string
      isIframe: boolean
      isiOS: boolean
      isAndroid: boolean
      browserName: string
    }
  }
}

/**
 * Responsive settings layout component
 * - Mobile (xs/sm): List-based navigation with separate pages for each setting
 * - Desktop (md+): Tab-based navigation with all settings in one view
 */
const SettingsLayout = ({ themeMode, onThemeChange, wsMetrics }: SettingsLayoutProps) => {
  const theme = useTheme()
  const location = useLocation()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  // On mobile, check if we're on a specific setting page
  if (isMobile) {
    // If on /settings (no subpath), show menu
    if (location.pathname === '/settings') {
      return <MobileSettingsLayout />
    }

    // If on a specific setting page, render GlobalSettings with that tab
    const settingItem = settingsItems.find(item => item.path === location.pathname)
    if (settingItem) {
      return (
        <GlobalSettings
          themeMode={themeMode}
          onThemeChange={onThemeChange}
          wsMetrics={wsMetrics}
          initialTab={settingItem.id}
        />
      )
    }

    // Fallback to menu if route not found
    return <MobileSettingsLayout />
  }

  // Desktop: always show full GlobalSettings with tabs
  return (
    <GlobalSettings themeMode={themeMode} onThemeChange={onThemeChange} wsMetrics={wsMetrics} />
  )
}

export default SettingsLayout
