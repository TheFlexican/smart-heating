import {
  Box,
  Typography,
  Paper,
  Card,
  CardContent,
  CardActionArea,
  IconButton,
  useMediaQuery,
  useTheme,
} from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import TrendingUpIcon from '@mui/icons-material/TrendingUp'
import CompareArrowsIcon from '@mui/icons-material/CompareArrows'
import FireplaceIcon from '@mui/icons-material/Fireplace'
import { useNavigate } from 'react-router-dom'

const AnalyticsMenu = () => {
  const navigate = useNavigate()
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))

  const analyticsOptions = [
    {
      title: 'Efficiency Reports',
      description: 'View system efficiency metrics and performance data',
      icon: <TrendingUpIcon sx={{ fontSize: 48, color: 'primary.main' }} />,
      path: '/analytics/efficiency',
      testId: 'analytics-efficiency-card',
    },
    {
      title: 'Historical Comparisons',
      description: 'Compare heating patterns across different time periods',
      icon: <CompareArrowsIcon sx={{ fontSize: 48, color: 'secondary.main' }} />,
      path: '/analytics/comparison',
      testId: 'analytics-comparison-card',
    },
    {
      title: 'OpenTherm Metrics',
      description: 'Advanced OpenTherm gateway metrics and diagnostics',
      icon: <FireplaceIcon sx={{ fontSize: 48, color: 'warning.main' }} />,
      path: '/opentherm/metrics',
      testId: 'analytics-opentherm-card',
    },
  ]

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
          mb: 3,
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
          <IconButton
            onClick={() => navigate('/')}
            edge="start"
            data-testid="analytics-back-button"
          >
            <ArrowBackIcon />
          </IconButton>
        )}
        <Typography variant="h6">Analytics</Typography>
      </Paper>

      {/* Content */}
      <Box sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
          Choose an analytics view to explore your heating system's performance
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(2, 1fr)',
              md: 'repeat(3, 1fr)',
            },
            gap: 3,
          }}
        >
          {analyticsOptions.map(option => (
            <Card
              key={option.path}
              elevation={2}
              sx={{
                height: '100%',
                transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 4,
                },
              }}
            >
              <CardActionArea
                onClick={() => navigate(option.path)}
                data-testid={option.testId}
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  p: 3,
                }}
              >
                <Box sx={{ mb: 2 }}>{option.icon}</Box>
                <CardContent sx={{ p: 0, '&:last-child': { pb: 0 } }}>
                  <Typography variant="h6" gutterBottom>
                    {option.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {option.description}
                  </Typography>
                </CardContent>
              </CardActionArea>
            </Card>
          ))}
        </Box>
      </Box>
    </Box>
  )
}

export default AnalyticsMenu
