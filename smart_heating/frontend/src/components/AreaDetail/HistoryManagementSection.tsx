import { Alert, Box, Button, Chip, Slider, Typography } from '@mui/material'
import HistoryIcon from '@mui/icons-material/History'
import { SettingSection } from '../DraggableSettings'
import {
  setHistoryRetention as updateHistoryRetention,
  migrateHistoryStorage,
} from '../../api/history'

export interface HistoryManagementSectionProps {
  historyRetention: number
  setHistoryRetention: (value: number) => void
  storageBackend: string
  databaseStats: any
  migrating: boolean
  setMigrating: (value: boolean) => void
  recordInterval: number
  loadHistoryConfig: () => Promise<void>
  t: (key: string, options?: any) => string
}

export const HistoryManagementSection = ({
  historyRetention,
  setHistoryRetention,
  storageBackend,
  databaseStats,
  migrating,
  setMigrating,
  recordInterval,
  loadHistoryConfig,
  t,
}: HistoryManagementSectionProps): SettingSection => {
  return {
    id: 'history-management',
    title: t('settingsCards.historyManagementTitle'),
    description: t('settingsCards.historyManagementDescription'),
    icon: <HistoryIcon />,
    defaultExpanded: false,
    content: (
      <>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t('settingsCards.dataRetentionDescription', { interval: recordInterval })}
        </Typography>

        {/* Storage Backend Display */}
        <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
          <Typography variant="subtitle2" gutterBottom>
            Storage Backend
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <Chip
              label={
                storageBackend === 'database' ? 'Database (MariaDB/PostgreSQL)' : 'JSON (File)'
              }
              color={storageBackend === 'database' ? 'primary' : 'default'}
              size="small"
            />
            {storageBackend === 'database' && databaseStats?.total_entries !== undefined && (
              <Typography variant="caption" color="text.secondary">
                {databaseStats.total_entries.toLocaleString()} entries stored
              </Typography>
            )}
          </Box>

          {/* Migration Buttons */}
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            {storageBackend === 'json' && (
              <Button
                variant="outlined"
                size="small"
                disabled={migrating}
                onClick={async () => {
                  if (
                    !confirm(
                      'Migrate history data to database? This requires MariaDB, MySQL, or PostgreSQL. SQLite is not supported.',
                    )
                  )
                    return
                  setMigrating(true)
                  try {
                    const result = await migrateHistoryStorage('database')
                    if (result.success) {
                      alert(`Successfully migrated ${result.migrated_entries} entries to database!`)
                      await loadHistoryConfig()
                    } else {
                      alert(`Migration failed: ${result.message}`)
                    }
                  } catch (error: any) {
                    alert(`Migration error: ${error.message}`)
                  } finally {
                    setMigrating(false)
                  }
                }}
              >
                {migrating ? 'Migrating...' : 'Migrate to Database'}
              </Button>
            )}
            {storageBackend === 'database' && (
              <Button
                variant="outlined"
                size="small"
                disabled={migrating}
                onClick={async () => {
                  if (!confirm('Migrate history data back to JSON file storage?')) return
                  setMigrating(true)
                  try {
                    const result = await migrateHistoryStorage('json')
                    if (result.success) {
                      alert(`Successfully migrated ${result.migrated_entries} entries to JSON!`)
                      await loadHistoryConfig()
                    } else {
                      alert(`Migration failed: ${result.message}`)
                    }
                  } catch (error: any) {
                    alert(`Migration error: ${error.message}`)
                  } finally {
                    setMigrating(false)
                  }
                }}
              >
                {migrating ? 'Migrating...' : 'Migrate to JSON'}
              </Button>
            )}
          </Box>

          <Alert severity="info" sx={{ mt: 2 }} icon={false}>
            <Typography variant="caption">
              <strong>Database storage</strong> requires MariaDB ≥10.3, MySQL ≥8.0, or PostgreSQL
              ≥12. SQLite is not supported and will automatically fall back to JSON storage.
            </Typography>
          </Alert>
        </Box>

        {/* Retention Period Slider */}
        <Typography variant="body2" color="text.secondary" gutterBottom>
          {t('settingsCards.dataRetentionPeriod', { days: historyRetention })}
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', mt: 2, mb: 3 }}>
          <Slider
            value={historyRetention}
            onChange={(_, value) => setHistoryRetention(value as number)}
            min={1}
            max={365}
            step={1}
            marks={[
              { value: 1, label: '1d' },
              { value: 30, label: '30d' },
              { value: 90, label: '90d' },
              { value: 180, label: '180d' },
              { value: 365, label: '365d' },
            ]}
            valueLabelDisplay="auto"
            valueLabelFormat={value => `${value}d`}
            sx={{ flexGrow: 1 }}
          />
          <Button
            variant="contained"
            size="small"
            onClick={async () => {
              try {
                await updateHistoryRetention(historyRetention)
                await loadHistoryConfig()
              } catch (error) {
                console.error('Failed to update history retention:', error)
              }
            }}
          >
            {t('common.save')}
          </Button>
        </Box>

        <Alert severity="info" sx={{ mt: 2 }}>
          <strong>Note:</strong> {t('settingsCards.historyNote', { interval: recordInterval })}
        </Alert>
      </>
    ),
  }
}
