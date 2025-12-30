import { Alert } from '@mui/material'

export const SuccessAlert = ({ message, onClose }: { message: string; onClose: () => void }) => (
  <Alert severity="success" sx={{ mb: 2 }} onClose={onClose}>
    {message.split('\n').map((line, i) => (
      <div key={`${line}-${i}`}>{line}</div>
    ))}
  </Alert>
)

export default SuccessAlert
