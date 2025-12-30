import { Alert, Typography } from '@mui/material'
import { Backup as BackupIcon } from '@mui/icons-material'

const ImportExportInfo = ({ t }: { t: any }) => (
  <Alert severity="info" sx={{ mt: 3 }}>
    <Typography variant="body2">
      <BackupIcon sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
      {t('importExport.backupInfo')}
    </Typography>
  </Alert>
)

export default ImportExportInfo
