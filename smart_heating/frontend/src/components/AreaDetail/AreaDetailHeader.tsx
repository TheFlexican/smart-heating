import React from 'react'
import { Box, Paper, IconButton, Typography, Chip, Switch } from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'

export interface AreaDetailHeaderProps {
  areaName: string
  state: string
  enabled: boolean
  onBack: () => void
  onToggle: () => Promise<void>
}

const getStateColor = (state: string) => {
  switch (state) {
    case 'heating':
      return 'error'
    case 'idle':
      return 'info'
    case 'off':
      return 'default'
    default:
      return 'default'
  }
}

export const AreaDetailHeader: React.FC<AreaDetailHeaderProps> = ({
  areaName,
  state,
  enabled,
  onBack,
  onToggle,
}) => {
  return (
    <Paper
      elevation={0}
      sx={{
        p: { xs: 2, sm: 3 },
        borderBottom: 1,
        borderColor: 'divider',
        borderRadius: 0,
      }}
    >
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
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
              {areaName}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 0.5, flexWrap: 'wrap' }}>
              <Chip
                label={state.toUpperCase()}
                color={getStateColor(state)}
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
            onChange={() => onToggle()}
            color="primary"
          />
        </Box>
      </Box>
    </Paper>
  )
}
