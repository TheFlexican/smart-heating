import React from 'react'
import { Box } from '@mui/material'
import { Zone } from '../../types'
import ScheduleEditor from '../ScheduleEditor'

export interface AreaScheduleTabProps {
  area: Zone
  onUpdate: () => void
}

export const AreaScheduleTab: React.FC<AreaScheduleTabProps> = ({ area, onUpdate }) => {
  return (
    <Box sx={{ maxWidth: 1200, mx: 'auto' }}>
      <ScheduleEditor area={area} onUpdate={onUpdate} />
    </Box>
  )
}
