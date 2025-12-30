import { useState } from 'react'
import { importConfig, validateConfig } from '../api/import_export'

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

export const useImportExport = (t: any) => {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [preview, setPreview] = useState<ImportPreview | null>(null)
  const [importData, setImportData] = useState<any>(null)
  const [showPreviewDialog, setShowPreviewDialog] = useState(false)

  const formatImportMessage = (changes?: ImportResult['changes']) => {
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
        setSuccess(formatImportMessage(result.changes))

        // Reload page after 2 seconds to reflect changes
        setTimeout(() => globalThis.location.reload(), 2000)
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

  return {
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
  }
}

export default useImportExport
