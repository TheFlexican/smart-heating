import React, { useState, useEffect } from 'react'
import {
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Typography,
  CircularProgress,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Zone, HassEntity } from '../types'
import { getWeatherEntities, getEntityState } from '../api/config'

interface Props {
  area: Zone
  loadData: () => Promise<void>
}

const OutdoorSensorControls: React.FC<Props> = ({ area, loadData }) => {
  const { t } = useTranslation()
  const [weatherEntities, setWeatherEntities] = useState<HassEntity[]>([])
  const [weatherEntitiesLoading, setWeatherEntitiesLoading] = useState(false)

  const loadWeatherEntities = async () => {
    setWeatherEntitiesLoading(true)
    try {
      const entities = await getWeatherEntities()
      setWeatherEntities(entities)
    } catch (error) {
      console.error('Failed to load weather entities:', error)
    } finally {
      setWeatherEntitiesLoading(false)
    }
  }

  useEffect(() => {
    const ensureSelected = async () => {
      if (!area || !area.weather_entity_id) return
      if (weatherEntities.find(e => e.entity_id === area.weather_entity_id)) return

      try {
        const state = await getEntityState(area.weather_entity_id)
        const entity: HassEntity = {
          entity_id: area.weather_entity_id,
          name: state.attributes?.friendly_name || area.weather_entity_id,
          state: state.state || 'unknown',
          attributes: state.attributes || {},
        }
        setWeatherEntities(prev => [entity, ...prev])
      } catch (err) {
        console.error('Failed to load selected weather entity state:', err)
      }
    }

    ensureSelected()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [area])

  return (
    <FormControl fullWidth sx={{ mb: 3 }} disabled={!area.smart_boost_enabled}>
      <InputLabel>{t('settingsCards.outdoorTemperatureSensor')}</InputLabel>
      <Select
        value={area.weather_entity_id || ''}
        onChange={async e => {
          const newValue = e.target.value || null
          try {
            const serviceCallBody = {
              service: 'set_night_boost',
              area_id: area.id,
              weather_entity_id: newValue,
            }

            const response = await fetch('/api/smart_heating/call_service', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(serviceCallBody),
            })
            await response.json()

            // Wait a bit for the backend to save
            await new Promise(resolve => setTimeout(resolve, 500))

            await loadData()
          } catch (error) {
            console.error('Weather sensor onChange - Failed to update:', error)
          }
        }}
        onOpen={() => {
          if (weatherEntities.length === 0) loadWeatherEntities()
        }}
        label={t('settingsCards.outdoorTemperatureSensor')}
      >
        <MenuItem value="">
          <em>{t('settingsCards.outdoorTemperatureSensorPlaceholder')}</em>
        </MenuItem>
        {weatherEntitiesLoading ? (
          <MenuItem disabled>
            <CircularProgress size={20} sx={{ mr: 1 }} />
            Loading...
          </MenuItem>
        ) : (
          weatherEntities.map(entity => (
            <MenuItem key={entity.entity_id} value={entity.entity_id}>
              {entity.attributes?.friendly_name || entity.entity_id}
            </MenuItem>
          ))
        )}
      </Select>
      <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5 }}>
        {t('settingsCards.outdoorTemperatureSensorHelper')}
      </Typography>
    </FormControl>
  )
}

export default OutdoorSensorControls
