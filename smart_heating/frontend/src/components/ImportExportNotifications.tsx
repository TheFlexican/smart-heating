import { Alert } from '@mui/material'
import SuccessAlert from './ImportExportSuccessAlert'

const ImportExportNotifications = ({
  error,
  success,
  setError,
  setSuccess,
}: {
  error: string | null
  success: string | null
  setError: (v: string | null) => void
  setSuccess: (v: string | null) => void
}) => (
  <>
    {error && (
      <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
        {error}
      </Alert>
    )}

    {success && <SuccessAlert message={success} onClose={() => setSuccess(null)} />}
  </>
)

export default ImportExportNotifications
