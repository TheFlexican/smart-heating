import React from 'react'
import { Box, Paper, Typography } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Zone } from '../../types'

interface StatRowProps {
  label: string
  value: string | React.ReactNode
  color?: string
}

const StatRow: React.FC<StatRowProps> = ({ label, value, color }) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
    <Typography variant="body2" color="text.secondary">
      {label}
    </Typography>
    <Typography variant="body2" color={color || 'text.primary'}>
      {typeof value === 'string' ? <strong>{value}</strong> : value}
    </Typography>
  </Box>
)

// Helper: Render recent events list
const RecentEventsList: React.FC<{ events: any[] }> = ({ events }) => (
  <Box sx={{ mt: 2 }}>
    <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
      Recent Events (Last 10):
    </Typography>
    <Box sx={{ maxHeight: 200, overflow: 'auto' }}>
      {events.map((event: any) => (
        <Box
          key={`${event.timestamp}-${event.heating_rate}`}
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
)

// Helper: Render learning statistics
interface LearningStatsDisplayProps {
  learningStats: any
  learningStatsLoading: boolean
}

const LearningStatsDisplay: React.FC<LearningStatsDisplayProps> = ({
  learningStats,
  learningStatsLoading,
}) => {
  if (learningStatsLoading) {
    return (
      <Box sx={{ textAlign: 'center', py: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Loading statistics...
        </Typography>
      </Box>
    )
  }

  if (!learningStats) {
    return (
      <Box sx={{ textAlign: 'center', py: 2 }}>
        <Typography variant="body2" color="text.secondary">
          No learning data available yet. Start heating cycles to collect data.
        </Typography>
      </Box>
    )
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
      <StatRow label="Total Events" value={String(learningStats.total_events_all_time || 0)} />
      <StatRow label="Data Points (Last 30 Days)" value={String(learningStats.data_points || 0)} />
      {learningStats.avg_heating_rate > 0 && (
        <StatRow
          label="Average Heating Rate"
          value={`${learningStats.avg_heating_rate.toFixed(4)}°C/min`}
        />
      )}
      <StatRow
        label="Ready for Predictions"
        value={
          <strong>{learningStats.ready_for_predictions ? 'Yes' : 'No (need 20+ events)'}</strong>
        }
        color={learningStats.ready_for_predictions ? 'success.main' : 'warning.main'}
      />
      {learningStats.first_event_time && (
        <StatRow
          label="First Event"
          value={new Date(learningStats.first_event_time).toLocaleString()}
        />
      )}
      {learningStats.last_event_time && (
        <StatRow
          label="Last Event"
          value={new Date(learningStats.last_event_time).toLocaleString()}
        />
      )}
      {learningStats.recent_events?.length > 0 && (
        <RecentEventsList events={learningStats.recent_events} />
      )}
    </Box>
  )
}

export interface AreaLearningTabProps {
  area: Zone
  learningStats: any | null
  learningStatsLoading: boolean
}

export const AreaLearningTab: React.FC<AreaLearningTabProps> = ({
  area,
  learningStats,
  learningStatsLoading,
}) => {
  const { t } = useTranslation()

  return (
    <Box sx={{ maxWidth: 800, mx: 'auto' }}>
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom color="text.primary">
          {t('areaDetail.adaptiveLearning')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('areaDetail.learningDescription')}
        </Typography>

        {area.smart_boost_enabled ? (
          <Box sx={{ mt: 3 }}>
            <Typography variant="body2" color="success.main" gutterBottom>
              ✓ {t('areaDetail.smartNightBoostActive')}
            </Typography>
            <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 3 }}>
              {t('areaDetail.learningSystemText')}
            </Typography>
            <Box sx={{ p: 2, bgcolor: 'info.light', borderRadius: 1, mb: 3 }}>
              <Typography variant="body2" color="info.dark">
                <strong>Note:</strong> {t('areaDetail.learningNote')}
              </Typography>
            </Box>

            <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
              {t('areaDetail.configuration')}
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1, mb: 3 }}>
              <StatRow
                label={t('areaDetail.targetWakeupTime')}
                value={area.smart_boost_target_time ?? '06:00'}
              />
              <StatRow
                label={t('areaDetail.weatherSensor')}
                value={
                  area.weather_entity_id ? (
                    <strong>{area.weather_entity_id}</strong>
                  ) : (
                    <em>{t('areaDetail.notConfigured')}</em>
                  )
                }
              />
            </Box>

            {/* Learning Statistics */}
            <Typography variant="subtitle2" color="text.primary" gutterBottom sx={{ mt: 3 }}>
              Learning Data
            </Typography>
            <LearningStatsDisplay
              learningStats={learningStats}
              learningStatsLoading={learningStatsLoading}
            />
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
          </Box>
        ) : (
          <Box sx={{ mt: 3, textAlign: 'center', py: 4 }}>
            <Typography variant="body1" color="text.secondary" gutterBottom>
              {t('settingsCards.smartNightBoostNotEnabled')}
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              {t('settingsCards.enableSmartNightBoostInfo')}
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              {t('settingsCards.adaptiveLearningInfo')}
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  )
}
