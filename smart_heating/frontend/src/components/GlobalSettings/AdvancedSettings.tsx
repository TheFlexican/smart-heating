import React from 'react'
import {
  Paper,
  Typography,
  Box,
  Switch,
  Alert,
  Slider,
  Stack,
  Button,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  IconButton,
  CircularProgress,
} from '@mui/material'
import HelpOutlineIcon from '@mui/icons-material/HelpOutline'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { useTranslation } from 'react-i18next'

export const AdvancedSettings: React.FC<{
  themeMode: 'light' | 'dark'
  onThemeChange: (mode: 'light' | 'dark') => void
  hysteresis: number
  saving: boolean
  onHysteresisChange: (e: Event | React.SyntheticEvent, v: number | number[]) => void
  onHysteresisCommit: (e: Event | React.SyntheticEvent, v: number | number[]) => void
  onOpenHysteresisHelp: () => void
  hideDevicesPanel: boolean
  onToggleHideDevicesPanel: (hide: boolean) => void
  advancedControlEnabled: boolean
  heatingCurveEnabled: boolean
  pwmEnabled: boolean
  pidEnabled: boolean
  overshootProtectionEnabled: boolean
  defaultCoefficient: number
  onToggleAdvancedControl: (field: string, value: boolean | number) => void
  onResetAdvancedControl: () => void
  onRunCalibration: () => void
  calibrating: boolean
  calibrationResult: number | null
}> = ({
  themeMode,
  onThemeChange,
  hysteresis,
  saving,
  onHysteresisChange,
  onHysteresisCommit,
  onOpenHysteresisHelp,
  hideDevicesPanel,
  onToggleHideDevicesPanel,
  advancedControlEnabled,
  heatingCurveEnabled,
  pwmEnabled,
  pidEnabled,
  overshootProtectionEnabled,
  defaultCoefficient,
  onToggleAdvancedControl,
  onResetAdvancedControl,
  onRunCalibration,
  calibrating,
  calibrationResult,
}) => {
  const { t } = useTranslation()

  return (
    <>
      {/* Theme Settings */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('globalSettings.theme.title', 'Theme')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t(
            'globalSettings.theme.description',
            'Choose the color theme for the application interface.',
          )}
        </Typography>

        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography variant="subtitle1">
              {t('globalSettings.theme.mode', 'Appearance')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {themeMode === 'dark'
                ? t('globalSettings.theme.darkMode', 'Dark mode is active')
                : t('globalSettings.theme.lightMode', 'Light mode is active')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              variant="body2"
              color={themeMode === 'light' ? 'primary' : 'text.secondary'}
            >
              {t('globalSettings.theme.light', 'Light')}
            </Typography>
            <Switch
              checked={themeMode === 'dark'}
              onChange={e => onThemeChange(e.target.checked ? 'dark' : 'light')}
              color="primary"
            />
            <Typography variant="body2" color={themeMode === 'dark' ? 'primary' : 'text.secondary'}>
              {t('globalSettings.theme.dark', 'Dark')}
            </Typography>
          </Box>
        </Box>
      </Paper>

      {/* Temperature Hysteresis */}
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Typography variant="h6">
            {t('globalSettings.hysteresis.title', 'Temperature Hysteresis')}
          </Typography>
          <IconButton onClick={onOpenHysteresisHelp} color="primary" size="small">
            <HelpOutlineIcon />
          </IconButton>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          {t(
            'globalSettings.hysteresis.description',
            'Controls the temperature buffer to prevent rapid on/off cycling of your heating system.',
          )}
        </Typography>

        <Alert severity="info" sx={{ mb: 3 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>{t('globalSettings.hysteresis.what', 'What is hysteresis?')}</strong>
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {t(
              'globalSettings.hysteresis.explanation',
              'Hysteresis prevents your heating system from constantly turning on and off (short cycling), which can damage equipment like boilers, relays, and valves.',
            )}
          </Typography>
          <Typography variant="body2" sx={{ mb: 1 }}>
            <strong>{t('globalSettings.hysteresis.howItWorks', 'How it works:')}</strong>{' '}
            {t(
              'globalSettings.hysteresis.example',
              'If your target is 19.2°C and hysteresis is 0.5°C, heating starts at 18.7°C and stops at 19.2°C.',
            )}
          </Typography>
          <Typography variant="body2">
            <strong>{t('globalSettings.hysteresis.recommendations', 'Recommendations:')}</strong>
          </Typography>
          <ul style={{ margin: '4px 0 0 0', paddingLeft: '20px' }}>
            <li>
              {t(
                'globalSettings.hysteresis.rec1',
                '0.1°C - Minimal delay, more frequent cycling (use only if needed)',
              )}
            </li>
            <li>
              {t(
                'globalSettings.hysteresis.rec2',
                '0.5°C - Balanced (default, recommended for most systems)',
              )}
            </li>
            <li>
              {t(
                'globalSettings.hysteresis.rec3',
                '1.0°C - Energy efficient, less wear on equipment',
              )}
            </li>
          </ul>
          <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
            💡{' '}
            {t(
              'globalSettings.hysteresis.tip',
              'Tip: For immediate heating, use Boost Mode instead of reducing hysteresis.',
            )}
          </Typography>
        </Alert>

        <Box>
          <Typography variant="subtitle1" sx={{ mb: 0.5 }}>
            {t('globalSettings.hysteresis.current', 'Current')}: {hysteresis.toFixed(1)}°C
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t('globalSettings.hysteresis.heatingStarts', 'Heating starts when temperature drops')}{' '}
            {hysteresis.toFixed(1)}°C {t('globalSettings.hysteresis.belowTarget', 'below target')}
          </Typography>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, px: 1 }}>
            <Slider
              data-testid="global-hysteresis-slider"
              value={hysteresis}
              onChange={onHysteresisChange}
              onChangeCommitted={onHysteresisCommit}
              min={0.1}
              max={2}
              step={0.1}
              marks={[
                { value: 0.1, label: '0.1°C' },
                { value: 0.5, label: '0.5°C' },
                { value: 1, label: '1°C' },
                { value: 2, label: '2°C' },
              ]}
              valueLabelDisplay="auto"
              valueLabelFormat={v => `${(v as number).toFixed(1)}°C`}
              disabled={saving}
              sx={{ maxWidth: 600 }}
            />
          </Box>
        </Box>
      </Paper>

      {/* UI Settings */}
      <Paper sx={{ p: 3, mt: 3 }}>
        <Typography variant="h6" sx={{ mb: 1 }}>
          {t('globalSettings.ui.title', 'User Interface')}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          {t('globalSettings.ui.description', 'Customize the user interface to your preferences.')}
        </Typography>

        <Stack spacing={2}>
          <Box
            sx={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              p: 2,
              border: 1,
              borderColor: 'divider',
              borderRadius: 1,
            }}
          >
            <Box>
              <Typography variant="subtitle1">
                {t('globalSettings.ui.hideDevicesPanel', 'Hide Available Devices Panel')}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t(
                  'globalSettings.ui.hideDevicesPanelDescription',
                  "Hide the sidebar with available devices when you're done setting up zones.",
                )}
              </Typography>
            </Box>
            <Switch
              checked={hideDevicesPanel}
              onChange={e => onToggleHideDevicesPanel(e.target.checked)}
              color="primary"
            />
          </Box>
        </Stack>
      </Paper>

      {/* Advanced Control Accordion */}
      <Accordion sx={{ mt: 3 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            {t('globalSettings.advanced.title', 'Advanced Boiler & Control')}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {t(
              'globalSettings.advanced.description',
              'Advanced features for optimizing setpoints, boiler cycling and energy efficiency. These are disabled by default. Enable to use advanced control algorithms (heating curves, PWM for on/off boilers, PID auto-gains, and calibration routines).',
            )}
          </Typography>
          <Stack spacing={2}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography>
                {t('globalSettings.advanced.enableAll', 'Enable advanced control')}
              </Typography>
              <Switch
                data-testid="global-advanced-control-switch"
                checked={advancedControlEnabled}
                onChange={e =>
                  onToggleAdvancedControl('advanced_control_enabled', e.target.checked)
                }
              />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography>{t('globalSettings.advanced.heatingCurve', 'Heating curve')}</Typography>
              <Switch
                data-testid="global-heating-curve-switch"
                checked={heatingCurveEnabled}
                onChange={e => onToggleAdvancedControl('heating_curve_enabled', e.target.checked)}
                disabled={!advancedControlEnabled}
              />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography>{t('globalSettings.advanced.pwm', 'PWM for on/off boilers')}</Typography>
              <Switch
                data-testid="global-pwm-switch"
                checked={pwmEnabled}
                onChange={e => onToggleAdvancedControl('pwm_enabled', e.target.checked)}
                disabled={!advancedControlEnabled}
              />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography>{t('globalSettings.advanced.pid', 'PID Automatic Gains')}</Typography>
              <Switch
                data-testid="global-pid-switch"
                checked={pidEnabled}
                onChange={e => onToggleAdvancedControl('pid_enabled', e.target.checked)}
                disabled={!advancedControlEnabled}
              />
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography>
                {t('globalSettings.advanced.overshoot', 'Overshoot Protection (OPV) calibration')}
              </Typography>
              <Switch
                data-testid="global-opv-switch"
                checked={overshootProtectionEnabled}
                onChange={e =>
                  onToggleAdvancedControl('overshoot_protection_enabled', e.target.checked)
                }
                disabled={!advancedControlEnabled}
              />
            </Box>

            <Box
              sx={{ display: 'flex', alignItems: 'center', gap: 2 }}
              data-testid="heating-curve-control"
            >
              <Typography>
                {t(
                  'globalSettings.advanced.defaultCoefficient',
                  'Default heating curve coefficient',
                )}
              </Typography>
              <input
                data-testid="global-settings-default-coefficient"
                type="number"
                value={defaultCoefficient}
                onChange={e =>
                  onToggleAdvancedControl(
                    'default_heating_curve_coefficient',
                    Number(e.target.value),
                  )
                }
                step={0.1}
                disabled={!advancedControlEnabled}
              />
              <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                {t(
                  'globalSettings.advanced.defaultCoefficientHelper',
                  'Default coefficient used when Heating Curve is enabled',
                )}
              </Typography>
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2 }}>
              <Button
                data-testid="run-opv-calibration"
                variant="contained"
                onClick={onRunCalibration}
                disabled={!advancedControlEnabled || calibrating}
              >
                {calibrating ? (
                  <CircularProgress size={20} />
                ) : (
                  t('globalSettings.advanced.runCalibration', 'Run OPV calibration')
                )}
              </Button>
              <Button
                data-testid="reset-advanced-control"
                variant="outlined"
                onClick={onResetAdvancedControl}
              >
                {t('globalSettings.advanced.resetDefaults', 'Reset to defaults')}
              </Button>
              {calibrationResult !== null && (
                <Typography variant="body2" sx={{ ml: 2 }}>
                  {t('globalSettings.advanced.calibrationResult', 'OPV: {{value}} °C', {
                    value: calibrationResult,
                  })}
                </Typography>
              )}
            </Box>
          </Stack>
        </AccordionDetails>
      </Accordion>
    </>
  )
}
