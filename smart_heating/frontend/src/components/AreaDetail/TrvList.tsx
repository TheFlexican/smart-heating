import React from 'react'
import {
  Box,
  Paper,
  Typography,
  Button,
  Chip,
  Alert,
  TextField,
  Select,
  MenuItem,
  FormControl,
  IconButton,
} from '@mui/material'
import EditIcon from '@mui/icons-material/Edit'
import RemoveCircleOutlineIcon from '@mui/icons-material/RemoveCircleOutline'
import { useTranslation } from 'react-i18next'
import { Zone } from '../../types'

export interface TrvListProps {
  area: Zone
  editingTrvId: string | null
  editingTrvName: string | null
  editingTrvRole: 'position' | 'open' | 'both' | null
  onTrvDialogOpen: () => void
  onStartEditingTrv: (trv: any) => void
  onEditingTrvNameChange: (name: string) => void
  onEditingTrvRoleChange: (role: 'position' | 'open' | 'both') => void
  onSaveTrv: (trv: any) => void
  onCancelEditingTrv: () => void
  onDeleteTrv: (entityId: string) => void
}

export const TrvList: React.FC<TrvListProps> = ({
  area,
  editingTrvId,
  editingTrvName,
  editingTrvRole,
  onTrvDialogOpen,
  onStartEditingTrv,
  onEditingTrvNameChange,
  onEditingTrvRoleChange,
  onSaveTrv,
  onCancelEditingTrv,
  onDeleteTrv,
}) => {
  const { t } = useTranslation()

  return (
    <Box sx={{ mt: 3 }}>
      <Box
        sx={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <Typography variant="subtitle1">{t('areaDetail.trvs')}</Typography>
        <Button
          data-testid="trv-add-button-overview"
          variant="outlined"
          size="small"
          onClick={onTrvDialogOpen}
        >
          Add TRV
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
          {area.trv_entities.map(trv => {
            const runtime = (area.trvs || []).find(t => t.entity_id === trv.entity_id)
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
                  {isEditing ? (
                    <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                      <TextField
                        size="small"
                        value={editingTrvName ?? ''}
                        onChange={e => onEditingTrvNameChange(e.target.value)}
                        data-testid={`trv-edit-name-${trv.entity_id}`}
                      />
                      <FormControl size="small">
                        <Select
                          value={editingTrvRole ?? trv.role ?? 'both'}
                          onChange={e => onEditingTrvRoleChange(e.target.value)}
                          data-testid={`trv-edit-role-${trv.entity_id}`}
                        >
                          <MenuItem value="position">Position</MenuItem>
                          <MenuItem value="open">Open/Closed</MenuItem>
                          <MenuItem value="both">Both</MenuItem>
                        </Select>
                      </FormControl>
                    </Box>
                  ) : (
                    <>
                      <Typography variant="body1">{name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {trv.role || 'both'}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        {open !== undefined && (
                          <Chip
                            label={open ? t('areaDetail.trvOpen') : t('areaDetail.trvClosed')}
                            size="small"
                            data-testid={`trv-open-${trv.entity_id}`}
                            sx={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              background: open
                                ? 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
                                : 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
                              color: '#ffffff',
                              boxShadow: open
                                ? '0 2px 8px rgba(16, 185, 129, 0.3)'
                                : '0 2px 6px rgba(0, 0, 0, 0.15)',
                              border: 'none',
                            }}
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
                  )}
                </Box>

                <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
                  {isEditing ? (
                    <>
                      <Button
                        size="small"
                        variant="contained"
                        data-testid={`trv-save-${trv.entity_id}`}
                        onClick={() => onSaveTrv(trv)}
                      >
                        Save
                      </Button>
                      <Button
                        size="small"
                        data-testid={`trv-cancel-edit-${trv.entity_id}`}
                        onClick={onCancelEditingTrv}
                      >
                        Cancel
                      </Button>
                    </>
                  ) : (
                    <>
                      <IconButton
                        aria-label={`edit-${trv.entity_id}`}
                        data-testid={`trv-edit-${trv.entity_id}`}
                        size="small"
                        onClick={() => onStartEditingTrv(trv)}
                      >
                        <EditIcon />
                      </IconButton>
                      <IconButton
                        aria-label={`delete-${trv.entity_id}`}
                        data-testid={`trv-delete-${trv.entity_id}`}
                        size="small"
                        onClick={() => onDeleteTrv(trv.entity_id)}
                      >
                        <RemoveCircleOutlineIcon />
                      </IconButton>
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

export default TrvList
