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

const getStateStyle = (state: string) => {
  switch (state) {
    case 'heating':
      return {
        background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(255, 107, 53, 0.3)',
        border: 'none',
      }
    case 'idle':
      return {
        background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
        color: '#ffffff',
        fontWeight: 700,
        boxShadow: '0 2px 8px rgba(6, 182, 212, 0.3)',
        border: 'none',
      }
    case 'off':
      return {
        background: 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
        color: '#ffffff',
        fontWeight: 600,
        boxShadow: '0 2px 6px rgba(0, 0, 0, 0.15)',
        border: 'none',
      }
    default:
      return {
        background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
        color: '#ffffff',
        fontWeight: 600,
        boxShadow: '0 2px 6px rgba(139, 92, 246, 0.3)',
        border: 'none',
      }
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
                size="small"
                sx={{
                  fontSize: { xs: '0.7rem', sm: '0.8125rem' },
                  ...getStateStyle(state),
                }}
              />
              <Chip
                label={enabled ? 'ENABLED' : 'DISABLED'}
                size="small"
                sx={{
                  fontSize: { xs: '0.7rem', sm: '0.8125rem' },
                  fontWeight: 700,
                  background: enabled
                    ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                    : 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
                  color: '#ffffff',
                  boxShadow: enabled
                    ? '0 2px 8px rgba(16, 185, 129, 0.3)'
                    : '0 2px 6px rgba(0, 0, 0, 0.15)',
                  border: 'none',
                }}
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
