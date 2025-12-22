import { SettingSection } from '../../../components/common/DraggableSettings'
import * as areasApi from '../../../api/areas'
import PresetControls from '../../../components/common/PresetControls'
import AutoPresetControls from '../../../components/global/AutoPresetControls'
import { Box, Switch, FormControlLabel, RadioGroup, Radio } from '@mui/material'
import BookmarkIcon from '@mui/icons-material/Bookmark'
import LocalFireDepartmentIcon from '@mui/icons-material/LocalFireDepartment'
import PowerSettingsNewIcon from '@mui/icons-material/PowerSettingsNew'
import PersonIcon from '@mui/icons-material/Person'
import HistoryIcon from '@mui/icons-material/History'

export default function buildAreaSettingsSections(p: any): SettingSection[] {
  if (!p?.area) return []
  const area = p.area

  const presetSection: SettingSection = {
    id: 'preset-modes',
    title: p.t?.('settingsCards.presetModesTitle') ?? 'Presets',
    icon: <BookmarkIcon />,
    content: (
      <PresetControls
        area={area}
        areaEnabled={!!area.enabled}
        globalPresets={p.globalPresets}
        getPresetTemp={p.getPresetTemp}
        loadData={p.loadData}
      />
    ),
  }

  const heatingTypeSection: SettingSection = {
    id: 'heating-type',
    title: p.t?.('settingsCards.heatingType') ?? 'Heating Type',
    icon: <LocalFireDepartmentIcon />,
    badge:
      area.heating_type === 'airco'
        ? p.t?.('settingsCards.airConditioner')
        : area.heating_type === 'floor_heating'
          ? p.t?.('settingsCards.floorHeating')
          : p.t?.('settingsCards.radiator'),
    content: (
      <Box>
        <RadioGroup
          data-testid="heating-type-control"
          value={(area.heating_type as 'airco' | 'floor_heating' | 'radiator') || 'radiator'}
          onChange={async e => {
            try {
              await areasApi.setHeatingType(
                area.id,
                e.target.value as 'airco' | 'floor_heating' | 'radiator',
              )
              await p.loadData?.()
            } catch (err) {
              console.error(err)
            }
          }}
        >
          <FormControlLabel
            value="radiator"
            control={<Radio />}
            label={p.t?.('settingsCards.radiator') ?? 'Radiator'}
          />
          <FormControlLabel
            value="floor_heating"
            control={<Radio />}
            label={p.t?.('settingsCards.floorHeating') ?? 'Floor Heating'}
          />
          <FormControlLabel
            value="airco"
            control={<Radio />}
            label={p.t?.('settingsCards.airConditioner') ?? 'Air Conditioner'}
          />
        </RadioGroup>
      </Box>
    ),
  }

  const autoPresetSection: SettingSection = {
    id: 'auto-preset',
    title: p.t?.('settingsCards.autoPreset') ?? 'Auto Preset',
    icon: <PersonIcon />,
    content: (
      <Box>
        <Switch
          data-testid="auto-preset-toggle"
          checked={!!area.auto_preset_enabled}
          onChange={async e => {
            try {
              await areasApi.setAreaAutoPreset(area.id, e.target.checked)
              await p.loadData?.()
            } catch (err) {
              console.error(err)
            }
          }}
        />
        <AutoPresetControls area={area} loadData={p.loadData} />
      </Box>
    ),
  }

  const switchControlSection: SettingSection = {
    id: 'switch-control',
    title: p.t?.('settingsCards.switchPumpControlTitle') ?? 'Switch Control',
    icon: <PowerSettingsNewIcon />,
    content: (
      <Box>
        <FormControlLabel
          control={
            <Switch
              data-testid="shutdown-switches-input"
              checked={!!area.shutdown_switches_when_idle}
              disabled={area.heating_type === 'airco'}
              onChange={async e => {
                try {
                  await areasApi.setSwitchShutdown(area.id, e.target.checked)
                  await p.loadData?.()
                } catch (err) {
                  console.error(err)
                }
              }}
            />
          }
          label={p.t?.('settingsCards.shutdownSwitchesPumps') ?? 'Shutdown switches'}
        />
      </Box>
    ),
  }

  const historySection: SettingSection = {
    id: 'history-management',
    title: p.t?.('settingsCards.historyManagementTitle') ?? 'History',
    icon: <HistoryIcon />,
    content: null as any,
  }

  return [
    presetSection,
    heatingTypeSection,
    autoPresetSection,
    switchControlSection,
    historySection,
  ]
}
