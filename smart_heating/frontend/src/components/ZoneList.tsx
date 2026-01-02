import { Box, Typography, CircularProgress, Button, Chip, alpha } from '@mui/material'
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core'
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  rectSortingStrategy,
} from '@dnd-kit/sortable'
import VisibilityIcon from '@mui/icons-material/Visibility'
import VisibilityOffIcon from '@mui/icons-material/VisibilityOff'
import GridViewIcon from '@mui/icons-material/GridView'
import { useTranslation } from 'react-i18next'
import ZoneCard from './ZoneCard'
import { Zone } from '../types'
import { thermalColors } from '../theme'

interface ZoneListProps {
  areas: Zone[]
  loading: boolean
  onUpdate: () => void
  showHidden: boolean
  onToggleShowHidden: () => void
  onAreasReorder: (areas: Zone[]) => void
  onPatchArea?: (areaId: string, patch: Partial<Zone>) => void
}

const ZoneList = ({
  areas,
  loading,
  onUpdate,
  showHidden,
  onToggleShowHidden,
  onAreasReorder,
  onPatchArea,
}: ZoneListProps) => {
  const { t } = useTranslation()

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    }),
  )

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event

    if (over && active.id !== over.id) {
      const oldIndex = visibleAreas.findIndex(area => area.id === active.id)
      const newIndex = visibleAreas.findIndex(area => area.id === over.id)

      const reorderedAreas = arrayMove(visibleAreas, oldIndex, newIndex)

      const hiddenAreas = areas.filter(a => a.hidden && !showHidden)
      const newOrder = [...reorderedAreas, ...hiddenAreas]
      onAreasReorder(newOrder)
    }
  }

  if (loading) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        height="400px"
        gap={2}
      >
        <Box
          sx={{
            p: 3,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${alpha(thermalColors.heat.primary, 0.1)} 0%, ${alpha(thermalColors.heat.secondary, 0.1)} 100%)`,
          }}
        >
          <CircularProgress
            size={48}
            thickness={3}
            sx={{
              color: thermalColors.heat.primary,
            }}
          />
        </Box>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ fontWeight: 500, letterSpacing: '0.02em' }}
        >
          Loading zones...
        </Typography>
      </Box>
    )
  }

  const hiddenCount = areas.filter(a => a.hidden).length
  const visibleAreas = areas.filter(area => showHidden || !area.hidden)
  const heatingCount = visibleAreas.filter(a => a.state === 'heating').length

  return (
    <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <Box>
        {/* Header Section */}
        <Box
          mb={{ xs: 3, sm: 4 }}
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={2}
        >
          <Box display="flex" alignItems="center" gap={{ xs: 1.5, sm: 2 }} flexWrap="wrap">
            <Box
              sx={{
                p: 1,
                borderRadius: 2,
                background: alpha(thermalColors.heat.primary, 0.1),
                display: { xs: 'none', sm: 'flex' },
              }}
            >
              <GridViewIcon sx={{ color: thermalColors.heat.primary }} />
            </Box>
            <Typography
              variant="h4"
              sx={{
                fontSize: { xs: '1.75rem', sm: '2.25rem' },
                fontFamily: '"Outfit", sans-serif',
                fontWeight: 700,
                letterSpacing: '-0.02em',
              }}
            >
              {t('dashboard.zones')}
            </Typography>
            {/* Stats chips */}
            <Box display="flex" gap={1}>
              <Chip
                label={`${visibleAreas.length} ${t('dashboard.total', 'total')}`}
                size="small"
                sx={{
                  fontWeight: 500,
                  background: alpha('#64748b', 0.1),
                  border: '1px solid rgba(255, 255, 255, 0.06)',
                }}
              />
              {heatingCount > 0 && (
                <Chip
                  label={`${heatingCount} ${t('area.heating', 'heating')}`}
                  size="small"
                  sx={{
                    fontWeight: 500,
                    background: `linear-gradient(135deg, ${alpha(thermalColors.heat.primary, 0.15)} 0%, ${alpha(thermalColors.heat.secondary, 0.15)} 100%)`,
                    border: `1px solid ${alpha(thermalColors.heat.primary, 0.2)}`,
                    color: thermalColors.heat.primary,
                  }}
                />
              )}
              {hiddenCount > 0 && !showHidden && (
                <Chip
                  label={t('dashboard.hiddenCount', { count: hiddenCount })}
                  size="small"
                  sx={{
                    fontWeight: 500,
                    background: alpha('#64748b', 0.1),
                    border: '1px solid rgba(255, 255, 255, 0.06)',
                  }}
                />
              )}
            </Box>
          </Box>
          {hiddenCount > 0 && (
            <Button
              startIcon={showHidden ? <VisibilityOffIcon /> : <VisibilityIcon />}
              onClick={onToggleShowHidden}
              variant="outlined"
              size="small"
              sx={{
                fontWeight: 500,
                borderRadius: 2,
                px: 2,
                borderColor: 'rgba(255, 255, 255, 0.15)',
                '&:hover': {
                  borderColor: thermalColors.heat.primary,
                  background: alpha(thermalColors.heat.primary, 0.08),
                },
              }}
            >
              {showHidden ? t('dashboard.hideHiddenAreas') : t('dashboard.showHiddenAreas')}
            </Button>
          )}
        </Box>

        {visibleAreas.length === 0 ? (
          <Box
            sx={{
              p: 6,
              textAlign: 'center',
              borderRadius: 4,
              background: theme =>
                theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)',
              border: '1px dashed',
              borderColor: 'divider',
            }}
          >
            <Typography variant="h6" color="text.secondary" gutterBottom>
              {t('dashboard.noAreasFound')}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Create areas in Home Assistant to get started
            </Typography>
          </Box>
        ) : (
          <SortableContext items={visibleAreas.map(a => a.id)} strategy={rectSortingStrategy}>
            <Box
              className="stagger-fade-in"
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                  md: 'repeat(2, 1fr)',
                  lg: 'repeat(3, 1fr)',
                  xl: 'repeat(4, 1fr)',
                },
                gap: { xs: 2, sm: 2.5, md: 3 },
                minHeight: 100,
                borderRadius: 2,
              }}
            >
              {visibleAreas.map(area => (
                <ZoneCard key={area.id} area={area} onUpdate={onUpdate} onPatchArea={onPatchArea} />
              ))}
            </Box>
          </SortableContext>
        )}
      </Box>
    </DndContext>
  )
}

export default ZoneList
