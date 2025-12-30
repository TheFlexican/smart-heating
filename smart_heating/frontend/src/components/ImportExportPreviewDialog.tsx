import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Typography,
  List,
  ListItem,
  ListItemText,
  Button,
  Alert,
  CircularProgress,
} from '@mui/material'

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

export const PreviewDialog = ({
  open,
  preview,
  onCancel,
  onConfirm,
  loading,
  t,
}: {
  open: boolean
  preview: ImportPreview | null
  onCancel: () => void
  onConfirm: () => void
  loading: boolean
  t: any
}) => (
  <Dialog open={open} onClose={onCancel} maxWidth="sm" fullWidth>
    <DialogTitle>{t('importExport.previewTitle')}</DialogTitle>
    <DialogContent>
      {preview?.valid ? (
        <>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            {t('importExport.previewDescription')}
          </Typography>
          <List dense>
            {preview.version && (
              <ListItem>
                <ListItemText primary={t('importExport.version')} secondary={preview.version} />
              </ListItem>
            )}
            {preview.export_date && (
              <ListItem>
                <ListItemText
                  primary={t('importExport.exportDate')}
                  secondary={new Date(preview.export_date).toLocaleString()}
                />
              </ListItem>
            )}
            {(preview.areas_to_create ?? 0) > 0 && (
              <ListItem>
                <ListItemText
                  primary={t('importExport.areasToCreate')}
                  secondary={preview.areas_to_create}
                />
              </ListItem>
            )}
            {(preview.areas_to_update ?? 0) > 0 && (
              <ListItem>
                <ListItemText
                  primary={t('importExport.areasToUpdate')}
                  secondary={preview.areas_to_update}
                />
              </ListItem>
            )}
            {preview.global_settings_included && (
              <ListItem>
                <ListItemText
                  primary={t('importExport.globalSettings')}
                  secondary={t('importExport.willBeUpdated')}
                />
              </ListItem>
            )}
            {preview.vacation_mode_included && (
              <ListItem>
                <ListItemText
                  primary={t('importExport.vacationMode')}
                  secondary={t('importExport.willBeUpdated')}
                />
              </ListItem>
            )}
          </List>
          <Alert severity="warning" sx={{ mt: 2 }}>
            {t('importExport.backupWarning')}
          </Alert>
        </>
      ) : (
        <Alert severity="error">{preview?.error || t('importExport.invalidConfig')}</Alert>
      )}
    </DialogContent>
    <DialogActions>
      <Button onClick={onCancel}>{t('common.cancel')}</Button>
      <Button onClick={onConfirm} variant="contained" disabled={!preview?.valid || loading}>
        {loading ? <CircularProgress size={20} /> : t('importExport.confirmImport')}
      </Button>
    </DialogActions>
  </Dialog>
)

export default PreviewDialog
