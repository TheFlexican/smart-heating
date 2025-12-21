import React from 'react'
import { Box, Paper, IconButton, Chip, Typography, Switch } from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { Zone } from '../types'

interface Props {
  area: Zone
  enabled: boolean
  onBack: () => void
  onToggle: (e: any) => void
  getStateColor: (state: string) => string
}

const AreaHeader: React.FC<Props> = ({ area, enabled, onBack, onToggle, getStateColor }) => {
  return (
    <Paper
      elevation={0}
      sx={{
        p: { xs: 1.5, sm: 2 },
        borderBottom: 1,
        borderColor: 'divider',
        bgcolor: 'background.paper',
      }}
    >
      <Box
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: 1,
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, sm: 2 } }}>
          <IconButton
            data-testid="area-top-back-button"
            onClick={onBack}
            edge="start"
            sx={{ p: { xs: 0.5, sm: 1 } }}
          >
            <ArrowBackIcon />
          </IconButton>
          <Box>
            <Typography
              variant="h5"
              color="text.primary"
              sx={{ fontSize: { xs: '1.25rem', sm: '1.5rem' } }}
            >
              {area.name}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
              <Chip
                label={area.state.toUpperCase()}
                color={getStateColor(area.state) as any}
                size="small"
                sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
              />
              <Chip
                label={enabled ? 'ENABLED' : 'DISABLED'}
                color={enabled ? 'success' : 'default'}
                size="small"
                sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
              />
            </Box>
          </Box>
        </Box>

        <Box
          sx={{
            display: 'flex',
            gap: { xs: 1, sm: 2 },
            alignItems: 'center',
            mr: { xs: 0, sm: 2 },
          }}
        >
          <Box sx={{ textAlign: 'right', display: { xs: 'none', sm: 'block' } }}>
            <Typography variant="body2" color="text.primary">
              {enabled ? 'Heating Active' : 'Heating Disabled'}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {enabled ? 'Area is being controlled' : 'No temperature control'}
            </Typography>
          </Box>
          <Switch
            data-testid="area-enable-switch"
            checked={enabled}
            onChange={onToggle}
            color="primary"
          />
        </Box>
      </Box>
    </Paper>
  )
}

export default AreaHeader
