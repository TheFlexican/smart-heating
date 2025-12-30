import { Button, CircularProgress } from '@mui/material'
import { Download as DownloadIcon } from '@mui/icons-material'

const ExportButton = ({
  loading,
  onExport,
  t,
}: {
  loading: boolean
  onExport: () => void
  t: any
}) => (
  <Button
    data-testid="import-export-button"
    variant="contained"
    startIcon={loading ? <CircularProgress size={20} /> : <DownloadIcon />}
    onClick={onExport}
    disabled={loading}
  >
    {t('importExport.exportButton')}
  </Button>
)

export default ExportButton
