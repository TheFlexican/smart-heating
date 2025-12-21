import { useState, useEffect } from 'react'
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Box,
  Typography,
  Alert,
  CircularProgress,
  List,
  ListItem,
  ListItemText,
  IconButton,
} from '@mui/material'
import DeleteIcon from '@mui/icons-material/Delete'
import { HassEntity, TrvEntityConfig } from '../types'
import { getTrvCandidates, addTrvEntity, removeTrvEntity } from '../api/sensors'

interface TrvConfigDialogProps {
  open: boolean
  onClose: () => void
  areaId: string
  trvEntities: TrvEntityConfig[]
  onRefresh: () => void
}

const TrvConfigDialog = ({
  open,
  onClose,
  areaId,
  trvEntities,
  onRefresh,
}: TrvConfigDialogProps) => {
  const [entities, setEntities] = useState<HassEntity[]>([])
  const [loading, setLoading] = useState(false)
  const [selectedEntity, setSelectedEntity] = useState('')
  const [role, setRole] = useState<'position' | 'open' | 'both'>('both')
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (open) {
      loadCandidates()
    }
  }, [open])

  const loadCandidates = async () => {
    setLoading(true)
    try {
      const data = await getTrvCandidates()
      setEntities(data)
    } catch (err) {
      console.error('Failed to load TRV candidates:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = async () => {
    if (!selectedEntity) return
    setBusy(true)
    try {
      await addTrvEntity(areaId, { entity_id: selectedEntity, role, name: name || undefined })
      setSelectedEntity('')
      setName('')
      setRole('both')
      onRefresh()
    } catch (err) {
      console.error('Failed to add TRV entity:', err)
      alert(`Failed to add TRV: ${err}`)
    } finally {
      setBusy(false)
    }
  }

  const handleRemove = async (entityId: string) => {
    if (!confirm(`Remove ${entityId} from area?`)) return
    setBusy(true)
    try {
      await removeTrvEntity(areaId, entityId)
      onRefresh()
    } catch (err) {
      console.error('Failed to remove TRV entity:', err)
      alert(`Failed to remove TRV: ${err}`)
    } finally {
      setBusy(false)
    }
  }

  const handleClose = () => {
    setSelectedEntity('')
    setName('')
    setRole('both')
    onClose()
  }

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle data-testid="trv-dialog-title">Configure TRVs</DialogTitle>
      <DialogContent>
        <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <FormControl fullWidth>
                <InputLabel>Entity</InputLabel>
                <Select
                  data-testid="trv-entity-select"
                  value={selectedEntity}
                  label="Entity"
                  onChange={e => setSelectedEntity(e.target.value)}
                >
                  {entities.length > 0 ? (
                    entities.map(e => (
                      <MenuItem
                        key={e.entity_id}
                        value={e.entity_id}
                        data-testid={`trv-candidate-${e.entity_id}`}
                      >
                        {e.attributes.friendly_name || e.entity_id}
                      </MenuItem>
                    ))
                  ) : (
                    <MenuItem disabled>No TRV-related entities found</MenuItem>
                  )}
                </Select>
              </FormControl>

              <FormControl fullWidth>
                <InputLabel>Role</InputLabel>
                <Select value={role} label="Role" onChange={e => setRole(e.target.value as any)}>
                  <MenuItem value="position">Position</MenuItem>
                  <MenuItem value="open">Open/Closed</MenuItem>
                  <MenuItem value="both">Both</MenuItem>
                </Select>
              </FormControl>

              <TextField
                label="Friendly name (optional)"
                value={name}
                onChange={e => setName(e.target.value)}
                data-testid="trv-name-input"
                fullWidth
              />

              <Alert severity="info">
                Select which entity corresponds to the TRV. Sensors reporting a numeric valve
                position and/or a binary open state are supported.
              </Alert>

              <Box>
                <Typography variant="subtitle1" sx={{ mt: 2 }}>
                  Configured TRVs
                </Typography>
                <List dense>
                  {trvEntities && trvEntities.length > 0 ? (
                    trvEntities.map(entity => (
                      <ListItem
                        key={entity.entity_id}
                        secondaryAction={
                          <IconButton
                            edge="end"
                            aria-label={`remove-${entity.entity_id}`}
                            onClick={() => handleRemove(entity.entity_id)}
                            data-testid={`trv-remove-${entity.entity_id}`}
                          >
                            <DeleteIcon />
                          </IconButton>
                        }
                      >
                        <ListItemText
                          primary={entity.name || entity.entity_id}
                          secondary={`role: ${entity.role || 'both'}`}
                        />
                      </ListItem>
                    ))
                  ) : (
                    <Typography variant="caption">No TRVs configured for this area.</Typography>
                  )}
                </List>
              </Box>
            </>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button data-testid="trv-cancel" onClick={handleClose} disabled={busy}>
          Cancel
        </Button>
        <Button
          data-testid="trv-add-button"
          onClick={handleAdd}
          variant="contained"
          disabled={!selectedEntity || busy}
        >
          Add TRV
        </Button>
      </DialogActions>
    </Dialog>
  )
}

export default TrvConfigDialog
