import React from 'react'
import { Box, Alert, FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import { Zone } from '../../types'
import { useTranslation } from 'react-i18next'

interface Props {
  area: Zone
  loadData: () => Promise<void>
}

const AutoPresetControls: React.FC<Props> = ({ area, loadData }) => {
  const { t } = useTranslation()

  return (
    <>
      {area.auto_preset_enabled && (
        <>
          <Alert severity="info" sx={{ mb: 3 }}>
            {t('settingsCards.autoPresetExplanation')}
          </Alert>

          <Box sx={{ mb: 3 }}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>{t('settingsCards.presetWhenHome')}</InputLabel>
              <Select
                value={area.auto_preset_home || 'home'}
                label={t('settingsCards.presetWhenHome')}
                onChange={async e => {
                  try {
                    await fetch(`/api/smart_heating/areas/${area.id}/auto_preset`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ auto_preset_home: e.target.value }),
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update home preset:', error)
                  }
                }}
              >
                <MenuItem value="home">{t('settingsCards.presetHome')}</MenuItem>
                <MenuItem value="comfort">{t('settingsCards.presetComfort')}</MenuItem>
                <MenuItem value="activity">{t('settingsCards.presetActivity')}</MenuItem>
              </Select>
            </FormControl>

            <FormControl fullWidth>
              <InputLabel>{t('settingsCards.presetWhenAway')}</InputLabel>
              <Select
                value={area.auto_preset_away || 'away'}
                label={t('settingsCards.presetWhenAway')}
                onChange={async e => {
                  try {
                    await fetch(`/api/smart_heating/areas/${area.id}/auto_preset`, {
                      method: 'POST',
                      headers: { 'Content-Type': 'application/json' },
                      body: JSON.stringify({ auto_preset_away: e.target.value }),
                    })
                    loadData()
                  } catch (error) {
                    console.error('Failed to update away preset:', error)
                  }
                }}
              >
                <MenuItem value="away">{t('settingsCards.presetAway')}</MenuItem>
                <MenuItem value="eco">{t('settingsCards.presetEco')}</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </>
      )}

      {!area.auto_preset_enabled && (
        <Alert severity="warning">{t('settingsCards.autoPresetDisabled')}</Alert>
      )}

      {(!area.presence_sensors || area.presence_sensors.length === 0) &&
        !area.use_global_presence && (
          <Alert severity="warning" sx={{ mt: 2 }}>
            {t('settingsCards.autoPresetNeedsSensors')}
          </Alert>
        )}
    </>
  )
}

export default AutoPresetControls
