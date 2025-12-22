import { Box, Paper, Typography } from '@mui/material'
import HistoryIcon from '@mui/icons-material/History'
import HistoryChart from '../../../components/area/HistoryChart'
import LogsPanel from '../../../components/area/LogsPanel'
import { Zone } from '../../../types'

type HistoryProps = {
  area: Zone | null
}

export const HistoryTabContent = ({ area }: HistoryProps) => {
  return (
    <Box sx={{ maxWidth: { xs: 800, lg: 1200 }, mx: 'auto' }}>
      <Paper sx={{ p: { xs: 2, sm: 3, md: 4 } }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
          <HistoryIcon sx={{ fontSize: 32, color: 'primary.main' }} />
          <Typography variant="h5" color="text.primary" sx={{ fontWeight: 600 }}>
            Temperature History
          </Typography>
        </Box>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          Historical temperature data for this area
        </Typography>

        {area?.id && <HistoryChart areaId={area.id} />}
      </Paper>
    </Box>
  )
}

type LogsProps = {
  logs: any[]
  logsLoading: boolean
  logFilter: string
  setLogFilter: (v: string) => void
  loadLogs: () => Promise<void>
}

export const LogsTabContent = ({
  logs,
  logsLoading,
  logFilter,
  setLogFilter,
  loadLogs,
}: LogsProps) => {
  return (
    <Box sx={{ maxWidth: 1000, mx: 'auto' }}>
      <LogsPanel
        logs={logs}
        logsLoading={logsLoading}
        logFilter={logFilter}
        setLogFilter={setLogFilter}
        loadLogs={loadLogs}
      />
    </Box>
  )
}

export default null as any
