import React from 'react'
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Typography,
  Box,
  Alert,
  Stack,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  CircularProgress,
} from '@mui/material'
import ExpandMoreIcon from '@mui/icons-material/ExpandMore'
import { useTranslation } from 'react-i18next'
import OpenThermLogger from '../OpenThermLogger'

export const OpenThermSettings: React.FC<{
  openthermGateways: Array<{ gateway_id: string; title: string }>
  openthermGatewayId: string
  setOpenthermGatewayId: (id: string) => void
  openthermSaving: boolean
  handleSave: () => void
}> = ({
  openthermGateways,
  openthermGatewayId,
  setOpenthermGatewayId,
  openthermSaving,
  handleSave,
}) => {
  const { t } = useTranslation()

  return (
    <>
      <Accordion defaultExpanded={false}>
        <AccordionSummary expandIcon={<ExpandMoreIcon />}>
          <Typography variant="h6">
            {t('globalSettings.opentherm.title', 'OpenTherm Gateway Configuration')}
          </Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box
            sx={{ mb: 3, p: 2, bgcolor: 'info.main', color: 'info.contrastText', borderRadius: 1 }}
          >
            <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
              ⚠️ {t('globalSettings.opentherm.importantNote', 'Important: Use Numeric ID Only')}
            </Typography>
            <Typography variant="body2">
              {t(
                'globalSettings.opentherm.description',
                'Enter the numeric integration ID (e.g., 128937219831729813), NOT the entity ID (e.g., climate.opentherm_thermostaat).',
              )}
            </Typography>
            <Typography variant="body2" sx={{ mt: 1 }}>
              {t(
                'globalSettings.opentherm.findId',
                'Find this ID in: Settings → Devices & Services → OpenTherm Gateway → Click "Configure" → Look for "ID" field (numeric value).',
              )}
            </Typography>
          </Box>

          <Stack spacing={3}>
            {openthermGateways.length === 0 && (
              <Alert severity="warning">
                {t(
                  'globalSettings.opentherm.noGateways',
                  'No OpenTherm gateways found. Please add the OpenTherm Gateway integration in Home Assistant and configure its gateway ID.',
                )}{' '}
                <a href="/config/integrations" target="_blank" rel="noreferrer">
                  {t('globalSettings.openIntegrations', 'Open Integrations')}
                </a>
              </Alert>
            )}

            <FormControl fullWidth>
              <InputLabel id="opentherm-gateway-select-label">
                {t('globalSettings.opentherm.gatewayId', 'Gateway Integration ID (ID or slug)')}
              </InputLabel>
              <Select
                labelId="opentherm-gateway-select-label"
                value={openthermGatewayId}
                label={t(
                  'globalSettings.opentherm.gatewayId',
                  'Gateway Integration ID (ID or slug)',
                )}
                onChange={e => setOpenthermGatewayId(e.target.value)}
              >
                <MenuItem value="">None (Disabled)</MenuItem>
                {openthermGateways.map(g => (
                  <MenuItem key={g.gateway_id} value={g.gateway_id}>
                    {g.title}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <Button
              data-testid="save-opentherm-config"
              variant="contained"
              onClick={handleSave}
              disabled={openthermSaving || openthermGateways.length === 0}
            >
              {openthermSaving ? (
                <CircularProgress size={24} />
              ) : (
                t('globalSettings.opentherm.save', 'Save Configuration')
              )}
            </Button>
          </Stack>
        </AccordionDetails>
      </Accordion>

      <OpenThermLogger />
    </>
  )
}
