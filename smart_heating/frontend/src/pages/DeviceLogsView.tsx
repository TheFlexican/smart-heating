import { Box, Paper } from '@mui/material'
import DeviceLogsPanel from '../components/DeviceLogsPanel'

const DeviceLogsView = () => {
  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'background.default', p: { xs: 2, sm: 3 } }}>
      <Paper elevation={0} sx={{ borderRadius: 0, p: 0 }}>
        <DeviceLogsPanel />
      </Paper>
    </Box>
  )
}

export default DeviceLogsView
