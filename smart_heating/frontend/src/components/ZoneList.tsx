import {
  Box,
  Grid,
  Typography,
  CircularProgress,
  Alert,
  Button,
  Chip,
} from '@mui/material'
import { DragDropContext, Droppable, DropResult, DragUpdate, DragStart } from 'react-beautiful-dnd'
import VisibilityIcon from '@mui/icons-material/Visibility'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import { useTranslation } from 'react-i18next'
import ZoneCard from './ZoneCard'
import { Zone } from '../types'
import { useState } from 'react'

interface ZoneListProps {
  areas: Zone[]
  loading: boolean
  onUpdate: () => void
  showHidden: boolean
  onToggleShowHidden: () => void
  onAreasReorder: (areas: Zone[]) => void
}

const ZoneList = ({ areas, loading, onUpdate, showHidden, onToggleShowHidden, onAreasReorder }: ZoneListProps) => {
  const { t } = useTranslation()
  const [isDragging, setIsDragging] = useState(false)
    const [draggingId, setDraggingId] = useState<string | null>(null)
    const [dragDestinationIndex, setDragDestinationIndex] = useState<number | null>(null)

  const handleDragStart = (start?: DragStart) => {
    setIsDragging(true)
    const id = start?.draggableId ? start.draggableId.replace(/^area-card-/, '') : null
    setDraggingId(id)
  }

  const handleDragUpdate = (update: DragUpdate) => {
    const dest = update.destination ? update.destination.index : null
    if (dest == null) return
    setDragDestinationIndex(dest)
  }

  const handleDragEnd = (result: DropResult) => {
    setIsDragging(false)
    setDragDestinationIndex(null)
    setDraggingId(null)
    if (!result.destination) return

    const items = Array.from(visibleAreas)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    // Merge reordered visible areas with hidden areas
    const hiddenAreas = areas.filter(a => a.hidden && !showHidden)
    const newOrder = [...items, ...hiddenAreas]
    onAreasReorder(newOrder)
  }

  // placeholder height logic removed; we now reflow items during drag instead of using placeholders

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="400px">
        <CircularProgress />
      </Box>
    )
  }

  const hiddenCount = areas.filter(a => a.hidden).length
  const visibleAreas = areas
    .filter(area => showHidden || !area.hidden)

  return (
    <DragDropContext onDragEnd={handleDragEnd} onDragStart={handleDragStart} onDragUpdate={handleDragUpdate}>
      <Box>
        <Box
          mb={{ xs: 2, sm: 3 }}
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={1}
        >
          <Box display="flex" alignItems="center" gap={{ xs: 1, sm: 2 }} flexWrap="wrap">
            <Typography variant="h4" sx={{ fontSize: { xs: '1.5rem', sm: '2rem' } }}>
              {t('dashboard.zones')}
            </Typography>
            {hiddenCount > 0 && !showHidden && (
              <Chip
                label={t('dashboard.hiddenCount', { count: hiddenCount })}
                size="small"
                color="default"
                variant="outlined"
                sx={{ fontSize: { xs: '0.7rem', sm: '0.8125rem' } }}
              />
            )}
          </Box>
          {hiddenCount > 0 && (
            <Button
              startIcon={showHidden ? <VisibilityOffIcon /> : <VisibilityIcon />}
              onClick={onToggleShowHidden}
              variant="outlined"
              size="small"
              sx={{ fontSize: { xs: '0.75rem', sm: '0.875rem' } }}
            >
              {showHidden ? t('dashboard.hideHiddenAreas') : t('dashboard.showHiddenAreas')}
            </Button>
          )}
        </Box>

        {visibleAreas.length === 0 ? (
          <Alert severity="info">
            {t('dashboard.noAreasFound')}
          </Alert>
        ) : (
          <Droppable droppableId="areas-list" type="AREA">
            {(provided) => (
              <Grid
                container
                spacing={{ xs: 2, sm: 2, md: 3 }}
                ref={provided.innerRef}
                {...provided.droppableProps}
              >
                {(() => {
                  if (isDragging && draggingId) {
                    const list = visibleAreas.filter(a => a.id !== draggingId)
                    const nodes = [] as JSX.Element[]
                    for (let i = 0; i < list.length; i++) {
                      if (dragDestinationIndex === i) {
                        nodes.push(
                          <Grid item xs={12} sm={6} md={4} lg={3} key={`placeholder-${i}`}>
                            <Box sx={{ minHeight: 140, borderRadius: 2, border: '2px dashed', borderColor: 'primary.main', bgcolor: 'action.hover', mb: 1 }} />
                          </Grid>
                        )
                      }
                      const area = list[i]
                      nodes.push(
                        <Grid item xs={12} sm={6} md={4} lg={3} key={area.id}>
                          <ZoneCard area={area} onUpdate={onUpdate} index={i} />
                        </Grid>
                      )
                    }
                    // placeholder at the end
                    if (dragDestinationIndex === list.length) {
                      nodes.push(
                        <Grid item xs={12} sm={6} md={4} lg={3} key={`placeholder-end`}>
                          <Box sx={{ minHeight: 140, borderRadius: 2, border: '2px dashed', borderColor: 'primary.main', bgcolor: 'action.hover', mb: 1 }} />
                        </Grid>
                      )
                    }
                    return nodes
                  }

                  return visibleAreas.map((area, index) => (
                    <Grid item xs={12} sm={6} md={4} lg={3} key={area.id}>
                      <ZoneCard area={area} onUpdate={onUpdate} index={index} />
                    </Grid>
                  ))
                })()}
                {provided.placeholder}
              </Grid>
            )}
          </Droppable>
        )}
      </Box>
    </DragDropContext>
  )
}

export default ZoneList
