import React from 'react'
import { Paper, IconButton, Typography } from '@mui/material'
import ArrowBackIcon from '@mui/icons-material/ArrowBack'
import { useTranslation } from 'react-i18next'

export const GlobalSettingsHeader: React.FC<{ onBack: () => void }> = ({ onBack }) => {
  const { t } = useTranslation()

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2,
        mb: 2,
        borderRadius: 0,
        display: 'flex',
        alignItems: 'center',
        gap: 1,
      }}
    >
      <IconButton data-testid="global-back-button" onClick={onBack} edge="start">
        <ArrowBackIcon />
      </IconButton>
      <Typography variant="h6">{t('globalSettings.title', 'Global Settings')}</Typography>
    </Paper>
  )
}
