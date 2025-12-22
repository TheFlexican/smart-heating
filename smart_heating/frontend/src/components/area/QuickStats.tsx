import { Box, Paper, Typography } from '@mui/material'
import SpeedIcon from '@mui/icons-material/Speed'
import { useTranslation } from 'react-i18next'
import { Zone } from '../../types'

interface Props {
  readonly area: Zone
}

export default function QuickStats({ area }: Props) {
  const { t } = useTranslation()

  return (
    <Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <SpeedIcon sx={{ fontSize: 32, color: 'primary.main' }} />
        <Typography variant="h5" color="text.primary" sx={{ fontWeight: 600 }}>
          {t('areaDetail.quickStats')}
        </Typography>
      </Box>
      <Box
        sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(3, 1fr)' }, gap: 3 }}
      >
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {t('areaDetail.devices')}
          </Typography>
          <Typography variant="h6" color="text.primary">
            {area.devices.length}
          </Typography>
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {t('areaDetail.status')}
          </Typography>
          <Typography variant="h6" color="text.primary" sx={{ textTransform: 'capitalize' }}>
            {area.state}
          </Typography>
        </Box>
        <Box>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {t('areaDetail.zoneId')}
          </Typography>
          <Typography variant="h6" color="text.primary" sx={{ fontSize: '1rem' }}>
            {area.id}
          </Typography>
        </Box>
      </Box>
    </Paper>
  )
}
