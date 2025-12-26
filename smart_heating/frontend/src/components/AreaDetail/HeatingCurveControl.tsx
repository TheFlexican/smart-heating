import React from 'react'
import { Box, Typography, FormControlLabel, Switch, TextField, Button } from '@mui/material'
import { useTranslation } from 'react-i18next'
import { Zone } from '../../types'
import { setAreaHeatingCurve } from '../../api/areas'

export interface HeatingCurveControlProps {
  area: Zone
  onUpdate: () => void
}

export const HeatingCurveControl: React.FC<HeatingCurveControlProps> = ({ area, onUpdate }) => {
  const { t } = useTranslation()
  const [areaHeatingCurveCoefficient, setAreaHeatingCurveCoefficient] = React.useState<
    number | null
  >(
    area.heating_curve_coefficient !== undefined && area.heating_curve_coefficient !== null
      ? area.heating_curve_coefficient
      : null,
  )
  const [useGlobalHeatingCurve, setUseGlobalHeatingCurve] = React.useState<boolean>(
    area.heating_curve_coefficient === undefined || area.heating_curve_coefficient === null,
  )

  // Update state when area changes
  React.useEffect(() => {
    if (area.heating_curve_coefficient !== undefined && area.heating_curve_coefficient !== null) {
      setAreaHeatingCurveCoefficient(area.heating_curve_coefficient)
      setUseGlobalHeatingCurve(false)
    } else {
      setAreaHeatingCurveCoefficient(null)
      setUseGlobalHeatingCurve(true)
    }
  }, [area.heating_curve_coefficient])

  return (
    <Box sx={{ mt: 2 }} data-testid="heating-curve-control">
      <Typography variant="subtitle1">
        {t('settingsCards.heatingCurveTitle', 'Heating Curve Coefficient')}
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
        {t(
          'settingsCards.heatingCurveDescription',
          'Optional per-area coefficient used in heating curve calculations. Leave blank to use the global coefficient.',
        )}
      </Typography>
      <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
        <FormControlLabel
          control={
            <Switch
              data-testid="heating-curve-override-switch"
              checked={!useGlobalHeatingCurve}
              onChange={e => setUseGlobalHeatingCurve(!e.target.checked)}
            />
          }
          label={t('settingsCards.heatingCurveUseArea', 'Use area-specific coefficient')}
        />
        <TextField
          label="Coefficient"
          type="number"
          value={areaHeatingCurveCoefficient ?? ''}
          onChange={e =>
            setAreaHeatingCurveCoefficient(e.target.value ? Number(e.target.value) : null)
          }
          disabled={useGlobalHeatingCurve || area.heating_type === 'airco'}
          slotProps={{ htmlInput: { step: 0.1, min: 0.1, max: 10 } }}
          inputProps={{ 'data-testid': 'heating-curve-control' }}
          helperText={
            area.heating_type === 'airco'
              ? t('settingsCards.disabledForAirco', 'Disabled for Air Conditioner')
              : useGlobalHeatingCurve
                ? t('settingsCards.heatingCurveHelper.usingGlobal', 'Using global coefficient')
                : t('settingsCards.heatingCurveHelper.overrideActive', 'Per-area override active')
          }
        />
        <Button
          variant="contained"
          onClick={async () => {
            try {
              await setAreaHeatingCurve(
                area.id,
                useGlobalHeatingCurve,
                areaHeatingCurveCoefficient ?? undefined,
              )
              await onUpdate()
            } catch (err) {
              console.error('Failed to save heating curve coefficient', err)
            }
          }}
        >
          {t('common.save', 'Save')}
        </Button>
      </Box>
    </Box>
  )
}
