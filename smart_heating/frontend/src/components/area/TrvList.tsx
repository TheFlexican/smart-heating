import { useState } from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Chip,
  TextField,
  FormControl,
  Select,
  MenuItem,
  Alert,
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { useTranslation } from 'react-i18next'
import { Zone, TrvRuntimeState } from '../../types'
import { addTrvEntity, removeTrvEntity } from '../../api/sensors'

interface Props {
  area: Zone
  trvs?: TrvRuntimeState[]
  onOpenAdd: () => void
  loadData: () => Promise<void>
}

export default function TrvList(props: Props) {
  const { area, trvs, onOpenAdd, loadData } = props
  const { t } = useTranslation()

  const [editingTrvId, setEditingTrvId] = useState<string | null>(null)
  const [editingTrvName, setEditingTrvName] = useState<string | null>(null)
  const [editingTrvRole, setEditingTrvRole] = useState<'position' | 'open' | 'both' | null>(null)

  const startEditingTrv = (trv: any) => {
    setEditingTrvId(trv.entity_id)
    setEditingTrvName(trv.name ?? '')
    setEditingTrvRole((trv.role as any) ?? 'both')
  }

  const cancelEditingTrv = () => {
    setEditingTrvId(null)
    setEditingTrvName(null)
    setEditingTrvRole(null)
  }

  const handleSaveTrv = async (trv: any) => {
    try {
      await addTrvEntity(area.id, {
        entity_id: trv.entity_id,
        role: editingTrvRole ?? trv.role,
        name: editingTrvName ?? undefined,
      })
      await loadData()
      cancelEditingTrv()
    } catch (err) {
      console.error('Failed to save TRV edit:', err)
      alert(`Failed to save TRV: ${err}`)
    }
  }

  const handleDeleteTrv = async (entityId: string) => {
    if (!globalThis.confirm(`Remove ${entityId} from area?`)) return
    try {
      await removeTrvEntity(area.id, entityId)
      await loadData()
    } catch (err) {
      console.error('Failed to delete TRV:', err)
      alert(`Failed to delete TRV: ${err}`)
    }
  }

  return (
    <Box sx={{ mt: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="subtitle1">{t('areaDetail.trvs')}</Typography>
        <Button
          data-testid="trv-add-button-overview"
          variant="outlined"
          size="small"
          onClick={onOpenAdd}
        >
          {t('common.add') || 'Add TRV'}
        </Button>
      </Box>

      {area.trv_entities && area.trv_entities.length > 0 ? (
        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)' },
            gap: 2,
            mt: 1,
          }}
        >
          {area.trv_entities.map((trv: any) => {
            const runtime = (trvs || []).find(t => t.entity_id === trv.entity_id) as
              | TrvRuntimeState
              | undefined
            const name = trv.name || runtime?.name || trv.entity_id
            const open = runtime?.open
            const position = runtime?.position

            const isEditing = editingTrvId === trv.entity_id

            return (
              <Paper
                key={trv.entity_id}
                sx={{
                  p: 2,
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                }}
              >
                <Box sx={{ flex: 1 }}>
                  {!isEditing ? (
                    <>
                      <Typography variant="body1">{name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {trv.role || 'both'}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {open !== undefined && (
                          <Chip
                            label={open ? t('areaDetail.trvOpen') : t('areaDetail.trvClosed')}
                            color={open ? 'success' : 'default'}
                            size="small"
                            data-testid={`trv-open-${trv.entity_id}`}
                          />
                        )}
                        <Typography
                          variant="caption"
                          sx={{ ml: 1 }}
                          data-testid={`trv-position-${trv.entity_id}`}
                        >
                          {position !== undefined && position !== null ? `${position}%` : '—'}
                        </Typography>
                      </Box>
                    </>
                  ) : (
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <TextField
                        size="small"
                        value={editingTrvName ?? ''}
                        onChange={e => setEditingTrvName(e.target.value)}
                        data-testid={`trv-edit-name-${trv.entity_id}`}
                      />
                      <FormControl size="small">
                        <Select
                          value={editingTrvRole ?? trv.role ?? 'both'}
                          onChange={e => setEditingTrvRole(e.target.value as any)}
                          data-testid={`trv-edit-role-${trv.entity_id}`}
                        >
                          <MenuItem value="position">Position</MenuItem>
                          <MenuItem value="open">Open/Closed</MenuItem>
                          <MenuItem value="both">Both</MenuItem>
                        </Select>
                      </FormControl>
                    </Box>
                  )}
                </Box>

                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  {!isEditing ? (
                    <>
                      <IconButton
                        aria-label={`edit-${trv.entity_id}`}
                        data-testid={`trv-edit-${trv.entity_id}`}
                        size="small"
                        onClick={() => startEditingTrv(trv)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        aria-label={`delete-${trv.entity_id}`}
                        data-testid={`trv-delete-${trv.entity_id}`}
                        size="small"
                        onClick={() => handleDeleteTrv(trv.entity_id)}
                      >
                        <RemoveCircleOutlineIcon />
                      </IconButton>
                    </>
                  ) : (
                    <>
                      <Button
                        size="small"
                        variant="contained"
                        data-testid={`trv-save-${trv.entity_id}`}
                        onClick={() => handleSaveTrv(trv)}
                      >
                        Save
                      </Button>
                      <Button
                        size="small"
                        data-testid={`trv-cancel-edit-${trv.entity_id}`}
                        onClick={() => cancelEditingTrv()}
                      >
                        Cancel
                      </Button>
                    </>
                  )}
                </Box>
              </Paper>
            )
          })}
        </Box>
      ) : (
        <Alert severity="info">No TRVs configured for this area. Click Add TRV to add one.</Alert>
      )}
    </Box>
  )
}
