import React from 'react'
import { Box, Chip, Typography } from '@mui/material'

interface Props {
  storageBackend: string
  databaseStats?: { total_entries?: number } | null
}

const StorageBackendInfo: React.FC<Props> = ({ storageBackend, databaseStats }) => {
  return (
    <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
      <Typography variant="subtitle2" gutterBottom>
        Storage Backend
      </Typography>
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
        <Chip
          label={storageBackend === 'database' ? 'Database (MariaDB/PostgreSQL)' : 'JSON (File)'}
          color={storageBackend === 'database' ? 'primary' : 'default'}
          size="small"
        />
        {storageBackend === 'database' && databaseStats?.total_entries !== undefined && (
          <Typography variant="caption" color="text.secondary">
            {databaseStats.total_entries.toLocaleString()} entries stored
          </Typography>
        )}
      </Box>
    </Box>
  )
}

export default StorageBackendInfo
