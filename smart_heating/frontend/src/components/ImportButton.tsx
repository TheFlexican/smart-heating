import { Button, CircularProgress } from '@mui/material'
import { Upload as UploadIcon } from '@mui/icons-material'

const ImportButton = ({
  loading,
  onFileSelect,
  t,
}: {
  loading: boolean
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  t: any
}) => (
  <Button
    data-testid="import-file-button"
    variant="outlined"
    component="label"
    startIcon={loading ? <CircularProgress size={20} /> : <UploadIcon />}
    disabled={loading}
  >
    {t('importExport.importButton')}
    <input type="file" accept=".json" hidden onChange={onFileSelect} />
  </Button>
)

export default ImportButton
