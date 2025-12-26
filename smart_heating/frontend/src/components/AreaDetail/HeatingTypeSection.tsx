import { Box, Typography, RadioGroup, FormControlLabel, Radio, Alert } from '@mui/material'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import { TFunction } from 'i18next'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setHeatingType } from '../../api/areas'
import { HeatingCurveControl } from './HeatingCurveControl'

export interface HeatingTypeSectionProps {
  area: Zone
  onUpdate: () => void
  t: TFunction
}

export const HeatingTypeSection = ({
  area,
  onUpdate,
  t,
}: HeatingTypeSectionProps): SettingSection => {
  return {
    id: 'heating-type',
    title: t('settingsCards.heatingTypeTitle', 'Heating Type'),
    description: t(
      'settingsCards.heatingTypeDescription',
      'Select radiator or floor heating to optimize temperature control',
    ),
    icon: <LocalFireDepartmentIcon />,
    badge:
      area.heating_type === 'floor_heating'
        ? t('settingsCards.floorHeating', 'Floor Heating')
        : area.heating_type === 'airco'
          ? t('settingsCards.airConditioner', 'Air Conditioner')
          : t('settingsCards.radiator', 'Radiator'),
    defaultExpanded: false,
    content: (
      <Box>
        <RadioGroup
          data-testid="heating-type-control"
          aria-label={t('settingsCards.heatingTypeTitle', 'Heating Type')}
          value={area.heating_type || 'radiator'}
          onChange={async e => {
            try {
              await setHeatingType(
                area.id,
                e.target.value as 'radiator' | 'floor_heating' | 'airco',
              )
              onUpdate()
            } catch (error) {
              console.error('Failed to update heating type:', error)
            }
          }}
        >
          <FormControlLabel
            value="radiator"
            control={<Radio />}
            label={
              <Box>
                <Typography variant="body1">{t('settingsCards.radiator', 'Radiator')}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {t(
                    'settingsCards.radiatorDescription',
                    'Fast response, higher overhead temperature (default: +20°C)',
                  )}
                </Typography>
              </Box>
            }
          />
          <FormControlLabel
            value="floor_heating"
            control={<Radio />}
            label={
              <Box>
                <Typography variant="body1">
                  {t('settingsCards.floorHeating', 'Floor Heating')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t(
                    'settingsCards.floorHeatingDescription',
                    'Slow response, lower overhead temperature (default: +5°C)',
                  )}
                </Typography>
              </Box>
            }
          />
          <FormControlLabel
            value="airco"
            control={<Radio />}
            label={
              <Box>
                <Typography variant="body1">
                  {t('settingsCards.airConditioner', 'Air Conditioner')}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {t(
                    'settingsCards.aircoDescription',
                    'Use air conditioner (cooling/heating). Radiator/floor-specific settings are disabled.',
                  )}
                </Typography>
              </Box>
            }
          />
        </RadioGroup>

        <Alert severity="info" sx={{ mt: 2 }}>
          {t(
            'settingsCards.heatingTypeInfo',
            'Heating type affects the boiler setpoint temperature. Radiators use higher temperature for faster heating, floor heating uses lower temperature for gradual heating.',
          )}
        </Alert>

        {/* Per-area heating curve coefficient */}
        <HeatingCurveControl area={area} onUpdate={onUpdate} />
      </Box>
    ),
  }
}
