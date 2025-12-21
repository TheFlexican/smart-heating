import React from 'react'
import { Box, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'

interface Props {
  learningStats: any
  loading: boolean
}

const LearningStats: React.FC<Props> = ({ learningStats, loading }) => {
  const { t } = useTranslation()

  if (loading) {
    return (
      <>
        <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
          Learning Data
        </Typography>
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Typography variant="body2" color="text.secondary">
            Loading statistics...
          </Typography>
        </Box>
      </>
    )
  }

  return (
    <>
      <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
        Learning Data
      </Typography>
      {learningStats ? (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Total Events
            </Typography>
            <Typography variant="body2" color="text.primary">
              <strong>{learningStats.total_events_all_time || 0}</strong>
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Data Points (Last 30 Days)
            </Typography>
            <Typography variant="body2" color="text.primary">
              <strong>{learningStats.data_points || 0}</strong>
            </Typography>
          </Box>
          {learningStats.avg_heating_rate > 0 && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Average Heating Rate
              </Typography>
              <Typography variant="body2" color="text.primary">
                <strong>{learningStats.avg_heating_rate.toFixed(4)}°C/min</strong>
              </Typography>
            </Box>
          )}
          <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <Typography variant="body2" color="text.secondary">
              Ready for Predictions
            </Typography>
            <Typography
              variant="body2"
              color={learningStats.ready_for_predictions ? 'success.main' : 'warning.main'}
            >
              <strong>
                {learningStats.ready_for_predictions ? 'Yes' : 'No (need 20+ events)'}
              </strong>
            </Typography>
          </Box>
          {learningStats.first_event_time && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                First Event
              </Typography>
              <Typography variant="body2" color="text.primary">
                {new Date(learningStats.first_event_time).toLocaleString()}
              </Typography>
            </Box>
          )}
          {learningStats.last_event_time && (
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2" color="text.secondary">
                Last Event
              </Typography>
              <Typography variant="body2" color="text.primary">
                {new Date(learningStats.last_event_time).toLocaleString()}
              </Typography>
            </Box>
          )}
          {learningStats.recent_events && learningStats.recent_events.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                Recent Events (Last 10):
              </Typography>
              <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
                {learningStats.recent_events.map((event: any) => (
                  <Box
                    key={event.timestamp}
                    sx={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      py: 0.5,
                      borderBottom: '1px solid',
                      borderColor: 'divider',
                    }}
                  >
                    <Typography variant="caption" color="text.secondary">
                      {new Date(event.timestamp).toLocaleString()}
                    </Typography>
                    <Typography variant="caption" color="text.primary">
                      {event.heating_rate.toFixed(4)}°C/min
                    </Typography>
                  </Box>
                ))}
              </Box>
            </Box>
          )}
        </Box>
      ) : (
        <Box sx={{ textAlign: 'center', py: 2 }}>
          <Typography variant="body2" color="text.secondary">
            No learning data available yet. Start heating cycles to collect data.
          </Typography>
        </Box>
      )}

      <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
        {t('areaDetail.learningProcessTitle')}
      </Typography>
      <Box component="ol" sx={{ pl: 2, mt: 1 }}>
        <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('settingsCards.learningStep1')}
        </Typography>
        <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('settingsCards.learningStep2')}
        </Typography>
        <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('settingsCards.learningStep3')}
        </Typography>
        <Typography component="li" variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('settingsCards.learningStep4')}
        </Typography>
        <Typography component="li" variant="body2" color="text.secondary">
          {t('settingsCards.learningStep5')}
        </Typography>
      </Box>
    </>
  )
}

export default LearningStats
