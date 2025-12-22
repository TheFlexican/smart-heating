import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
} from '@mui/material'
import { useTranslation } from 'react-i18next'
import { HassEntity, SafetySensorConfig } from '../../types'
import { getBinarySensorEntities } from '../../api/config'

interface SafetySensorConfigDialogProps {
  open: boolean
  onClose: () => void
  onAdd: (config: SafetySensorConfig) => Promise<void>
  configuredSensors?: string[] // List of already-configured sensor IDs to exclude
}

const SafetySensorConfigDialog = ({
  open,
  onClose,
  onAdd,
  configuredSensors = [],
}: SafetySensorConfigDialogProps) => {
  const { t } = useTranslation()
  const [entities, setEntities] = useState<HassEntity[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedEntity, setSelectedEntity] = useState('')
  const [attribute, setAttribute] = useState('state')
  const [alertValue, setAlertValue] = useState('true')
  const [enabled, setEnabled] = useState(true)

  useEffect(() => {
    if (open) {
      loadEntities()
    }
  }, [open])

  const loadEntities = async () => {
    setLoading(true)
    try {
      const data = await getBinarySensorEntities()
      setEntities(data)
    } catch (error) {
      console.error('Failed to load entities:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async () => {
    if (!selectedEntity) {
      return
    }

    try {
      const config: SafetySensorConfig = {
        sensor_id: selectedEntity,
        attribute: attribute,
        alert_value: alertValue === 'true' ? true : alertValue === 'false' ? false : alertValue,
        enabled: enabled,
      }
      await onAdd(config)
    } catch (error) {
      console.error('Failed to add safety sensor:', error)
      alert(`Failed to add safety sensor: ${error}`)
    }
  }

  const handleClose = () => {
    setSelectedEntity('')
    setAttribute('state')
    setAlertValue('true')
    setEnabled(true)
    onClose()
  }

  // Filter to show only safety-related binary sensors that aren't already configured
  const filteredEntities = entities.filter(e => {
    // Exclude already-configured sensors
    if (configuredSensors.includes(e.entity_id)) {
      return false
    }

    const deviceClass = e.attributes.device_class
    return (
      deviceClass === 'smoke' ||
      deviceClass === 'gas' ||
      deviceClass === 'carbon_monoxide' ||
      deviceClass === 'safety' ||
      deviceClass === 'problem' ||
      e.entity_id.includes('smoke') ||
      e.entity_id.includes('co_') ||
      e.entity_id.includes('gas') ||
      e.entity_id.includes('safety')
    )
  })

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle data-testid="safety-dialog-title">
        {t('globalSettings.safety.addSensorTitle', 'Configure Safety Sensor')}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3, pt: 2 }}>
          <Alert severity="info" data-testid="safety-info">
            {t(
              'globalSettings.safety.sensorDescription',
              'Configure a smoke or carbon monoxide detector that will automatically shut down all heating when danger is detected.',
            )}
          </Alert>

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <FormControl fullWidth>
                <InputLabel>{t('globalSettings.safety.sensorLabel', 'Safety Sensor')}</InputLabel>
                <Select
                  data-testid="safety-entity-select"
                  value={selectedEntity}
                  onChange={e => setSelectedEntity(e.target.value)}
                  label={t('globalSettings.safety.sensorLabel', 'Safety Sensor')}
                >
                  {filteredEntities.length === 0 ? (
                    <MenuItem disabled data-testid="safety-no-entities">
                      {t('globalSettings.safety.noSensors', 'No safety sensors found')}
                    </MenuItem>
                  ) : (
                    filteredEntities.map(entity => (
                      <MenuItem
                        data-testid={`safety-entity-${entity.entity_id}`}
                        key={entity.entity_id}
                        value={entity.entity_id}
                      >
                        <Box>
                          <Typography variant="body2">{entity.name}</Typography>
                          <Typography variant="caption" color="text.secondary">
                            {entity.entity_id}
                            {entity.attributes.device_class &&
                              ` • ${entity.attributes.device_class}`}
                          </Typography>
                        </Box>
                      </MenuItem>
                    ))
                  )}
                </Select>

                {/*
                  Hidden native select for testing purposes only: some MUI Select
                  variants render via portal and are hard to interact with in tests.
                  This native select mirrors the available entities and allows tests
                  to programmatically set the selected value.
                */}
                <select
                  data-testid="safety-entity-native"
                  value={selectedEntity}
                  onChange={e => setSelectedEntity(e.target.value)}
                  aria-hidden="true"
                  style={{ display: 'none' }}
                >
                  {filteredEntities.length === 0 ? (
                    <option data-testid="safety-no-entities-hidden" value="">
                      {t('globalSettings.safety.noSensors', 'No safety sensors found')}
                    </option>
                  ) : (
                    filteredEntities.map(entity => (
                      <option
                        key={entity.entity_id}
                        value={entity.entity_id}
                        data-testid={`safety-entity-${entity.entity_id}`}
                      >
                        {entity.name}
                      </option>
                    ))
                  )}
                </select>
              </FormControl>

              <TextField
                data-testid="safety-attribute-input"
                fullWidth
                label={t('globalSettings.safety.attributeLabel', 'Attribute to Monitor')}
                value={attribute}
                onChange={e => setAttribute(e.target.value)}
                helperText={t(
                  'globalSettings.safety.attributeHelp',
                  'The sensor attribute to monitor (e.g., "state", "smoke", "carbon_monoxide")',
                )}
              />

              <TextField
                data-testid="safety-alert-value"
                fullWidth
                label={t('globalSettings.safety.alertValueLabel', 'Alert Value')}
                value={alertValue}
                onChange={e => setAlertValue(e.target.value)}
                helperText={t(
                  'globalSettings.safety.alertValueHelp',
                  'The value that indicates danger (e.g., "true", "on", "detected")',
                )}
              />

              <FormControl fullWidth>
                <InputLabel>
                  {t('globalSettings.safety.enabledLabel', 'Enable Monitoring')}
                </InputLabel>
                <Select
                  data-testid="safety-enabled-select"
                  value={enabled ? 'true' : 'false'}
                  onChange={e => setEnabled(e.target.value === 'true')}
                  label={t('globalSettings.safety.enabledLabel', 'Enable Monitoring')}
                >
                  <MenuItem data-testid="safety-enabled-true" value="true">
                    {t('globalSettings.safety.enabled', 'Enabled')}
                  </MenuItem>
                  <MenuItem data-testid="safety-enabled-false" value="false">
                    {t('globalSettings.safety.disabled', 'Disabled (for testing)')}
                  </MenuItem>
                </Select>
              </FormControl>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button data-testid="safety-cancel" onClick={handleClose} color="inherit">
          {t('common.cancel', 'Cancel')}
        </Button>
        <Button
          data-testid="safety-add-button"
          onClick={handleAdd}
          variant="contained"
          disabled={!selectedEntity || loading}
        >
          {t('globalSettings.safety.addButton', 'Add Safety Sensor')}
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default SafetySensorConfigDialog
