import { ReactNode, useEffect, useState } from 'react'
import { DragDropContext, Droppable, Draggable, DropResult } from 'react-beautiful-dnd'
import { Box, Alert, IconButton, useTheme, useMediaQuery } from '@mui/material'
import RestoreIcon from '@mui/icons-material/Restore'
import SettingsSection from './SettingsSection'

export interface SettingSection {
  id: string
  title: string
  description?: string
  icon?: ReactNode
  badge?: string | number
  content: ReactNode
  defaultExpanded?: boolean
}

interface DraggableSettingsProps {
  sections: SettingSection[]
  storageKey?: string
  expandedCard: string | null
  onExpandedChange: (cardId: string | null) => void
}

const DraggableSettings = ({ sections, storageKey = 'settings-order', expandedCard, onExpandedChange }: DraggableSettingsProps) => {
  const [orderedSections, setOrderedSections] = useState<SettingSection[]>(sections)
  const [hasCustomOrder, setHasCustomOrder] = useState(false)
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('md'))
  const isTablet = useMediaQuery(theme.breakpoints.down('lg'))

  // Load saved order from localStorage
  useEffect(() => {
    const savedOrder = localStorage.getItem(storageKey)
    if (savedOrder) {
      try {
        const orderIds = JSON.parse(savedOrder) as string[]
        const reordered = orderIds
          .map(id => sections.find(s => s.id === id))
          .filter(Boolean) as SettingSection[]
        
        // Add any new sections that weren't in saved order
        const newSections = sections.filter(s => !orderIds.includes(s.id))
        setOrderedSections([...reordered, ...newSections])
        setHasCustomOrder(true)
      } catch (error) {
        console.error('Failed to load settings order:', error)
        setOrderedSections(sections)
      }
    } else {
      setOrderedSections(sections)
    }
  }, [sections, storageKey])

  const handleDragEnd = (result: DropResult) => {
    if (!result.destination) {
      return
    }

    const items = Array.from(orderedSections)
    const [reorderedItem] = items.splice(result.source.index, 1)
    items.splice(result.destination.index, 0, reorderedItem)

    setOrderedSections(items)
    setHasCustomOrder(true)

    // Save to localStorage
    const orderIds = items.map(item => item.id)
    localStorage.setItem(storageKey, JSON.stringify(orderIds))
  }

  const handleResetOrder = () => {
    setOrderedSections(sections)
    setHasCustomOrder(false)
    localStorage.removeItem(storageKey)
  }

  return (
    <Box>
      {hasCustomOrder && (
        <Alert 
          severity="info" 
          sx={{ mb: 2 }}
          action={
            <IconButton
              color="inherit"
              size="small"
              onClick={handleResetOrder}
              title="Reset to default order"
            >
              <RestoreIcon fontSize="small" />
            </IconButton>
          }
        >
          Cards have been reordered. Drag cards to customize the layout or click the restore icon to reset.
        </Alert>
      )}

      <DragDropContext onDragEnd={handleDragEnd}>
        <Droppable droppableId="settings-sections">
          {(provided, snapshot) => (
            <Box
              {...provided.droppableProps}
              ref={provided.innerRef}
              sx={{
                display: 'grid',
                gridTemplateColumns: isMobile 
                  ? '1fr' 
                  : isTablet 
                    ? 'repeat(2, 1fr)' 
                    : 'repeat(3, 1fr)',
                gap: 2,
                bgcolor: snapshot.isDraggingOver ? 'action.hover' : 'transparent',
                transition: 'background-color 0.2s',
                borderRadius: 1,
                p: 1,
              }}
            >
              {orderedSections.map((section, index) => (
                <Draggable key={section.id} draggableId={section.id} index={index}>
                  {(provided, snapshot) => (
                    <Box
                      ref={provided.innerRef}
                      {...provided.draggableProps}
                      sx={{
                        opacity: snapshot.isDragging ? 0.8 : 1,
                        transform: snapshot.isDragging ? 'scale(1.05)' : 'scale(1)',
                        transition: 'all 0.2s',
                      }}
                    >
                      <SettingsSection
                        id={section.id}
                        title={section.title}
                        description={section.description}
                        icon={section.icon}
                        badge={section.badge}
                        defaultExpanded={section.defaultExpanded}
                        expanded={expandedCard === section.id}
                        onExpandedChange={(expanded) => onExpandedChange(expanded ? section.id : null)}
                        dragHandleProps={provided.dragHandleProps}
                      >
                        {section.content}
                      </SettingsSection>
                    </Box>
                  )}
                </Draggable>
              ))}
              {provided.placeholder}
            </Box>
          )}
        </Droppable>
      </DragDropContext>
    </Box>
  )
}

export default DraggableSettings
