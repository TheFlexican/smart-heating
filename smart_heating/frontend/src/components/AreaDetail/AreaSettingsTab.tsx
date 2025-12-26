import React from 'react'
import { Box } from '@mui/material'
import DraggableSettings, { SettingSection } from '../DraggableSettings'

export interface AreaSettingsTabProps {
  areaId: string
  sections: SettingSection[]
  expandedCard: string | null
  onExpandedChange: (card: string | null) => void
  presenceSensorsCount?: number
  windowSensorsCount?: number
}

export const AreaSettingsTab: React.FC<AreaSettingsTabProps> = ({
  areaId,
  sections,
  expandedCard,
  onExpandedChange,
  presenceSensorsCount = 0,
  windowSensorsCount = 0,
}) => {
  return (
    <Box sx={{ maxWidth: 1600, mx: 'auto', px: 2 }}>
      <DraggableSettings
        key={`settings-${areaId}-${presenceSensorsCount}-${windowSensorsCount}`}
        sections={sections}
        storageKey={`area-settings-order-${areaId}`}
        expandedCard={expandedCard}
        onExpandedChange={onExpandedChange}
      />
    </Box>
  )
}
