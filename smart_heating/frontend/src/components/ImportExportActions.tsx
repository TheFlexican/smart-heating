import ExportButton from './ExportButton'
import ImportButton from './ImportButton'
import { Box } from '@mui/material'

const ImportExportActions = ({
  loading,
  onExport,
  onFileSelect,
  t,
}: {
  loading: boolean
  onExport: () => void
  onFileSelect: (e: React.ChangeEvent<HTMLInputElement>) => void
  t: any
}) => (
  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
    <ExportButton loading={loading} onExport={onExport} t={t} />
    <ImportButton loading={loading} onFileSelect={onFileSelect} t={t} />
  </Box>
)

export default ImportExportActions
