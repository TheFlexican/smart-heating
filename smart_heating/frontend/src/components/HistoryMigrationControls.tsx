import React from 'react'
import { Box, Button } from '@mui/material'

interface Props {
  storageBackend: 'json' | 'database'
  migrating: boolean
  onMigrateToDatabase: () => Promise<void>
  onMigrateToJson: () => Promise<void>
}

const HistoryMigrationControls: React.FC<Props> = ({
  storageBackend,
  migrating,
  onMigrateToDatabase,
  onMigrateToJson,
}) => {
  return (
    <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
      {storageBackend === 'json' && (
        <Button variant="outlined" size="small" disabled={migrating} onClick={onMigrateToDatabase}>
          {migrating ? 'Migrating...' : 'Migrate to Database'}
        </Button>
      )}
      {storageBackend === 'database' && (
        <Button variant="outlined" size="small" disabled={migrating} onClick={onMigrateToJson}>
          {migrating ? 'Migrating...' : 'Migrate to JSON'}
        </Button>
      )}
    </Box>
  )
}

export default HistoryMigrationControls
