import { useState } from 'react'
import { Box, Button, Typography, Alert, CircularProgress, IconButton } from '@mui/material'
import {
  Download as DownloadIcon,
  Upload as UploadIcon,
  Backup as BackupIcon,
  ArrowBack as ArrowBackIcon,
} from '@mui/icons-material'
import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import { importConfig, validateConfig } from '../api/import_export'
import PreviewDialog from './ImportExportPreviewDialog'
import SuccessAlert from './ImportExportSuccessAlert'

interface ImportPreview {
  valid: boolean
  version?: string
  export_date?: string
  areas_to_create?: number
  areas_to_update?: number
  global_settings_included?: boolean
  vacation_mode_included?: boolean
  error?: string
}

interface ImportResult {
  success: boolean
  message: string
  changes?: {
    areas_created: number
    areas_updated: number
    areas_deleted: number
    global_settings_updated: boolean
    vacation_mode_updated: boolean
  }
  error?: string
}

const formatImportMessage = (t: any, changes?: ImportResult['changes']) => {
  let message = t('importExport.importSuccess') + '\n'
  if (!changes) return message
  if (changes.areas_created > 0) {
    message += `\n• ${changes.areas_created} ${t('importExport.areasCreated')}`
  }
  if (changes.areas_updated > 0) {
    message += `\n• ${changes.areas_updated} ${t('importExport.areasUpdated')}`
  }
  if (changes.global_settings_updated) {
    message += `\n• ${t('importExport.globalSettingsUpdated')}`
  }
  if (changes.vacation_mode_updated) {
    message += `\n• ${t('importExport.vacationModeUpdated')}`
  }
  return message
}

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
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [importData, setImportData] = useState<any>(null)
  const [showPreviewDialog, setShowPreviewDialog] = useState(false)

  const handleExport = async () => {
    try {
      setLoading(true)
      setError(null)
      setSuccess(null)

      const response = await fetch('/api/smart_heating/export')
      if (!response.ok) {
        throw new Error('Failed to export configuration')
      }

      // Get filename from Content-Disposition header
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'smart_heating_backup.json'
      if (contentDisposition) {
        const m = /filename="(.+)"/.exec(contentDisposition)
        if (m) {
          filename = m[1]
        }
      }

      // Download the file
      const blob = await response.blob()
      const url = globalThis.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      globalThis.URL.revokeObjectURL(url)
      a.remove()

      setSuccess(t('importExport.exportSuccess'))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Export failed')
    } finally {
      setLoading(false)
    }
  }

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setLoading(true)
      setError(null)
      setSuccess(null)

      // Read file content
      const text = await file.text()
      const data = JSON.parse(text)
      setImportData(data)

      // Validate configuration
      const previewData = await validateConfig(data)
      setPreview(previewData)
      setShowPreviewDialog(true)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to read file')
    } finally {
      setLoading(false)
    }
  }

  const handleConfirmImport = async () => {
    if (!importData) return

    try {
      setLoading(true)
      setError(null)
      setSuccess(null)
      setShowPreviewDialog(false)

      const result: ImportResult = await importConfig(importData)

      if (result.success) {
        setSuccess(formatImportMessage(t, result.changes))

        // Reload page after 2 seconds to reflect changes
        setTimeout(() => {
          globalThis.location.reload()
        }, 2000)
      } else {
        setError(result.error || 'Import failed')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Import failed')
    } finally {
      setLoading(false)
      setImportData(null)
      setPreview(null)
    }
  }

  const handleCancelImport = () => {
    setShowPreviewDialog(false)
    setImportData(null)
    setPreview(null)
  }

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
