import React from 'react'
import { Box, Alert, Typography, IconButton } from '@mui/material'
import { Backup as BackupIcon, ArrowBack as ArrowBackIcon } from '@mui/icons-material'
import ImportExportActions from './ImportExportActions'
import ImportExportNotifications from './ImportExportNotifications'
import PreviewDialog from './ImportExportPreviewDialog'

type Props = {
  t: any
  navigate: (path: string) => void
  loading: boolean
  error: string | null
  success: string | null
  preview: any
  showPreviewDialog: boolean
  handleExport: () => void
  handleFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  handleConfirmImport: () => void
  handleCancelImport: () => void
  setError: (v: string | null) => void
  setSuccess: (v: string | null) => void
}

const ImportExportView = ({
  t,
  navigate,
  loading,
  error,
  success,
  preview,
  showPreviewDialog,
  handleExport,
  handleFileSelect,
  handleConfirmImport,
  handleCancelImport,
  setError,
  setSuccess,
}: Props) => (
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

    <ImportExportNotifications
      error={error}
      success={success}
      setError={setError}
      setSuccess={setSuccess}
    />

    <ImportExportActions
      loading={loading}
      onExport={handleExport}
      onFileSelect={handleFileSelect}
      t={t}
    />

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

export default ImportExportView
