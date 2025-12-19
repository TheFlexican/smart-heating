import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  Typography,
  IconButton,
  Divider,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import ThermostatIcon from '@mui/icons-material/Thermostat'
import SensorsIcon from '@mui/icons-material/Sensors'
import BeachAccessIcon from '@mui/icons-material/BeachAccess'
import PeopleIcon from '@mui/icons-material/People'
import ShieldIcon from '@mui/icons-material/Shield'
import TuneIcon from '@mui/icons-material/Tune'
import ImportExportIcon from '@mui/icons-material/ImportExport'
import ArticleIcon from '@mui/icons-material/Article'
import FireplaceIcon from '@mui/icons-material/Fireplace'
import BugReportIcon from '@mui/icons-material/BugReport'
import ChevronRightIcon from '@mui/icons-material/ChevronRight'
import { useNavigate } from 'react-router-dom'

interface SettingItem {
  id: number
  title: string
  description: string
  icon: React.ReactNode
  path: string
  testId: string
}

export const settingsItems: SettingItem[] = [
  {
    id: 0,
    title: 'Temperature',
    description: 'Temperature ranges and thresholds',
    icon: <ThermostatIcon />,
    path: '/settings/temperature',
    testId: 'mobile-settings-temperature',
  },
  {
    id: 1,
    title: 'Sensors',
    description: 'Sensor configuration and mapping',
    icon: <SensorsIcon />,
    path: '/settings/sensors',
    testId: 'mobile-settings-sensors',
  },
  {
    id: 2,
    title: 'Vacation Mode',
    description: 'Away mode settings',
    icon: <BeachAccessIcon />,
    path: '/settings/vacation',
    testId: 'mobile-settings-vacation',
  },
  {
    id: 3,
    title: 'Users',
    description: 'User access management',
    icon: <PeopleIcon />,
    path: '/settings/users',
    testId: 'mobile-settings-users',
  },
  {
    id: 4,
    title: 'Safety',
    description: 'Safety sensor and alerts',
    icon: <ShieldIcon />,
    path: '/settings/safety',
    testId: 'mobile-settings-safety',
  },
  {
    id: 5,
    title: 'Advanced',
    description: 'Advanced system settings',
    icon: <TuneIcon />,
    path: '/settings/advanced',
    testId: 'mobile-settings-advanced',
  },
  {
    id: 6,
    title: 'Import/Export',
    description: 'Backup and restore configuration',
    icon: <ImportExportIcon />,
    path: '/settings/import-export',
    testId: 'mobile-settings-import-export',
  },
  {
    id: 7,
    title: 'Device Logs',
    description: 'View device activity logs',
    icon: <ArticleIcon />,
    path: '/settings/device-logs',
    testId: 'mobile-settings-device-logs',
  },
  {
    id: 8,
    title: 'OpenTherm',
    description: 'OpenTherm gateway settings',
    icon: <FireplaceIcon />,
    path: '/settings/opentherm',
    testId: 'mobile-settings-opentherm',
  },
  {
    id: 9,
    title: 'Debug',
    description: 'WebSocket diagnostics',
    icon: <BugReportIcon />,
    path: '/settings/debug',
    testId: 'mobile-settings-debug',
  },
]

/**
 * Mobile settings layout with list-based navigation
 * Shows a scrollable list of setting categories
 * When tapped, navigates to the specific setting page
 */
const MobileSettingsLayout = () => {
  const navigate = useNavigate()

  return (
    <Box
      sx={{
        minHeight: '100vh',
        bgcolor: 'background.default',
        pb: 8, // Account for bottom nav
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
        <IconButton
          onClick={() => navigate('/')}
          edge="start"
          data-testid="mobile-settings-home-button"
        >
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h6">Settings</Typography>
      </Paper>

      {/* Settings list */}
      <Box sx={{ p: 2 }}>
        <List sx={{ bgcolor: 'background.paper', borderRadius: 2 }}>
          {settingsItems.map((item, index) => (
            <Box key={item.id}>
              <ListItem disablePadding>
                <ListItemButton
                  onClick={() => navigate(item.path)}
                  data-testid={item.testId}
                  sx={{
                    minHeight: 72,
                    py: 2,
                  }}
                >
                  <ListItemIcon
                    sx={{
                      color: 'primary.main',
                      minWidth: 56,
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  <ListItemText
                    primary={item.title}
                    secondary={item.description}
                    primaryTypographyProps={{
                      variant: 'body1',
                      fontWeight: 500,
                    }}
                    secondaryTypographyProps={{
                      variant: 'body2',
                      color: 'text.secondary',
                    }}
                  />
                  <ChevronRightIcon sx={{ color: 'text.secondary' }} />
                </ListItemButton>
              </ListItem>
              {index < settingsItems.length - 1 && <Divider />}
            </Box>
          ))}
        </List>
      </Box>
    </Box>
  )
}

export default MobileSettingsLayout
