import { Box, IconButton, Typography } from '@mui/material'
import { ArrowBack as ArrowBackIcon } from '@mui/icons-material'

const ImportExportHeader = ({ t, navigate }: { t: any; navigate: (path: string) => void }) => (
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
)

export default ImportExportHeader
