import { useTranslation } from 'react-i18next'
import { useNavigate } from 'react-router-dom'
import useImportExport from '../hooks/useImportExport'
import ImportExportView from './ImportExportView'

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
    setError,
    setSuccess,
  } = useImportExport(t)

  return (
    <ImportExportView
      t={t}
      navigate={navigate}
      loading={loading}
      error={error}
      success={success}
      preview={preview}
      showPreviewDialog={showPreviewDialog}
      handleExport={handleExport}
      handleFileSelect={handleFileSelect}
      handleConfirmImport={handleConfirmImport}
      handleCancelImport={handleCancelImport}
      setError={setError}
      setSuccess={setSuccess}
    />
  )
}

export default ImportExport
