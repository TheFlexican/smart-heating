import React from 'react'
import { Box } from '@mui/material'

interface TabPanelProps {
  children?: React.ReactNode
  index: number
  value: number
}

export const TabPanel: React.FC<TabPanelProps> = ({ children, value, index, ...other }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3, px: { xs: 2, sm: 3 }, maxWidth: { xs: 800, lg: 1200 }, mx: 'auto' }}>
          {children}
        </Box>
      )}
    </div>
  )
}
