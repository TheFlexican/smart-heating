import {} from 'react'
import { Box, Button, Typography, Alert, CircularProgress, IconButton } from '@mui/material'
import {
  Download as DownloadIcon,
  Upload as UploadIcon,
  Backup as BackupIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
// importConfig/validateConfig moved into hook
import PreviewDialog from './ImportExportPreviewDialog'
import SuccessAlert from './ImportExportSuccessAlert'
import useImportExport from '../hooks/useImportExport'

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

const ImportExport = () => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const {
    loading,
    error,
    success,
    preview,
    showPreviewDialog,
    handleExport,
    handleFileSelect,
    handleConfirmImport,
    handleCancelImport,
    setSuccess,
    setError,
  } = useImportExport(t)

  // Handlers and state are managed by the `useImportExport` hook

  return (
    <Box>
      <Box display="flex" alignItems="center" gap={2} mb={2}>
        <IconButton
          data-testid="import-export-back"
          onClick={() => navigate('/')}
          size="large"
          color="primary"
        >
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="body2" color="text.secondary">
          {t('importExport.description')}
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {success && <SuccessAlert message={success} onClose={() => setSuccess(null)} />}

      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        <ExportButton loading={loading} onExport={handleExport} t={t} />
        <ImportButton loading={loading} onFileSelect={handleFileSelect} t={t} />
      </Box>

      <Alert severity="info" sx={{ mt: 3 }}>
        <Typography variant="body2">
          <BackupIcon sx={{ fontSize: 16, mr: 1, verticalAlign: 'middle' }} />
          {t('importExport.backupInfo')}
        </Typography>
      </Alert>

      <PreviewDialog
        open={showPreviewDialog}
        preview={preview}
        onCancel={handleCancelImport}
        onConfirm={handleConfirmImport}
        loading={loading}
        t={t}
      />
    </Box>
  )
}

export default ImportExport
