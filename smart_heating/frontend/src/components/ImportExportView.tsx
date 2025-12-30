import React from 'react'
import { Box } from '@mui/material'
import ImportExportActions from './ImportExportActions'
import ImportExportNotifications from './ImportExportNotifications'
import ImportExportHeader from './ImportExportHeader'
import ImportExportInfo from './ImportExportInfo'
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
    <ImportExportHeader t={t} navigate={navigate} />

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

    <ImportExportInfo t={t} />

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
