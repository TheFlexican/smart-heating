import { FormControl, InputLabel, Select, MenuItem } from '@mui/material'
import TuneIcon from '@mui/icons-material/Tune'
import { Zone } from '../../types'
import { SettingSection } from '../DraggableSettings'
import { setHvacMode } from '../../api/areas'

export interface HvacModeSectionProps {
  area: Zone
  onUpdate: () => void
}

export const HvacModeSection = ({ area, onUpdate }: HvacModeSectionProps): SettingSection => {
  return {
    id: 'hvac-mode',
    title: 'HVAC Mode',
    description: 'Control the heating/cooling mode for this area',
    icon: <TuneIcon />,
    badge: area.hvac_mode || 'heat',
    defaultExpanded: false,
    content: (
      <FormControl fullWidth>
        <InputLabel>HVAC Mode</InputLabel>
        <Select
          data-testid="hvac-mode-select"
          value={area.hvac_mode || 'heat'}
          label="HVAC Mode"
          onChange={async e => {
            try {
              await setHvacMode(area.id, e.target.value)
              onUpdate()
            } catch (error) {
              console.error('Failed to set HVAC mode:', error)
            }
          }}
        >
          <MenuItem value="heat">Heat</MenuItem>
          <MenuItem value="cool">Cool</MenuItem>
          <MenuItem value="auto">Auto</MenuItem>
          <MenuItem value="off">Off</MenuItem>
        </Select>
      </FormControl>
    ),
  }
}
