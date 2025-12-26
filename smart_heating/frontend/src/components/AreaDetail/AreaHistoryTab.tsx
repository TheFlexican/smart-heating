import React from 'react'
import { Box, Paper, Typography } from '@mui/material'
import HistoryIcon from '@mui/icons-material/History'
import { useTranslation } from 'react-i18next'
import HistoryChart from '../HistoryChart'

export interface AreaHistoryTabProps {
  areaId: string
}

export const AreaHistoryTab: React.FC<AreaHistoryTabProps> = ({ areaId }) => {
  const { t } = useTranslation()

  return (
    <Box sx={{ maxWidth: { xs: 800, lg: 1200 }, mx: 'auto' }}>
      <Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <HistoryIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" color="text.primary" sx={{ fontWeight: 600 }}>
            {t('areaDetail.temperatureHistory')}
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('areaDetail.historyDescription')}
        </Typography>

        {areaId && <HistoryChart areaId={areaId} />}
      </Paper>
    </Box>
  )
}
