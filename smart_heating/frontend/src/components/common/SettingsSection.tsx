import { ReactNode, useState } from 'react'
import { Paper, Box, Typography, Collapse, Chip } from '@mui/material'
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'

interface SettingsSectionProps {
  id: string
  title: string
  description?: string
  icon?: ReactNode
  badge?: string | number
  children: ReactNode
  defaultExpanded?: boolean
  expanded?: boolean
  onExpandedChange?: (expanded: boolean) => void
  dragHandleProps?: any
}

const SettingsSection = ({
  id,
  title,
  description,
  icon,
  badge,
  children,
  defaultExpanded = false,
  expanded: controlledExpanded,
  onExpandedChange,
  dragHandleProps,
}: SettingsSectionProps) => {
  const [internalExpanded, setInternalExpanded] = useState(defaultExpanded)
  const [isToggling, setIsToggling] = useState(false)

  // Use controlled or uncontrolled state
  const expanded = controlledExpanded !== undefined ? controlledExpanded : internalExpanded

  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault()
    if (isToggling) return

    setIsToggling(true)
    const newExpanded = !expanded

    if (onExpandedChange) {
      onExpandedChange(newExpanded)
    } else {
      setInternalExpanded(newExpanded)
    }

    setTimeout(() => setIsToggling(false), 300)
  }

  return (
    <Paper
      data-testid={`settings-card-${id.toLowerCase().replaceAll(' ', '-')}`}
      sx={{
        overflow: 'hidden',
        transition: 'all 0.2s ease',
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        minHeight: expanded ? 'auto' : '120px',
        '&:hover': {
          boxShadow: 4,
        },
      }}
    >
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          gap: 2,
          cursor: 'pointer',
          bgcolor: expanded ? 'action.hover' : 'background.paper',
          transition: 'background-color 0.2s',
          '&:hover': {
            bgcolor: 'action.hover',
          },
          userSelect: 'none',
        }}
        onClick={handleClick}
        onDoubleClick={(e: React.MouseEvent) => e.preventDefault()}
      >
        {/* Drag Handle */}
        <Box
          {...dragHandleProps}
          sx={{
            display: 'flex',
            alignItems: 'center',
            cursor: 'grab',
            '&:active': {
              cursor: 'grabbing',
            },
            color: 'action.active',
            '&:hover': {
              color: 'primary.main',
            },
          }}
          onClick={(e: React.MouseEvent) => e.stopPropagation()}
        >
          <DragIndicatorIcon />
        </Box>

        {/* Icon */}
        {icon && (
          <Box sx={{ display: 'flex', alignItems: 'center', color: 'primary.main' }}>{icon}</Box>
        )}

        {/* Title & Description */}
        <Box sx={{ flexGrow: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography variant="h6" component="div" noWrap>
              {title}
            </Typography>
            {badge !== undefined && (
              <Chip label={badge} size="small" color="primary" sx={{ height: 20 }} />
            )}
          </Box>
          {description && (
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
              {description}
            </Typography>
          )}
        </Box>
      </Box>

      {/* Content */}
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box sx={{ p: 3, pt: 2, bgcolor: 'background.default' }}>{children}</Box>
      </Collapse>
    </Paper>
  )
}

export default SettingsSection
