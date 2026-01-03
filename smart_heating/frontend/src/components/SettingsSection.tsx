import { ReactNode, useState } from 'react'
import { Paper, Box, Typography, Collapse, Chip } from '@mui/material'
import DragIndicatorIcon from '@mui/icons-material/DragIndicator'

// Vibrant badge styling based on content
const getBadgeStyle = (badge: string | number) => {
  const badgeStr = String(badge).toUpperCase()

  // Active/On states - vibrant gradient
  if (badgeStr.includes('ACTIVE') || badgeStr.includes('ON') || badgeStr === 'AUTO') {
    return {
      background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
      color: '#ffffff',
      fontWeight: 700,
      boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)',
      border: 'none',
    }
  }

  // Learning/Smart states - purple gradient
  if (badgeStr.includes('LEARNING') || badgeStr.includes('SMART')) {
    return {
      background: 'linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)',
      color: '#ffffff',
      fontWeight: 700,
      boxShadow: '0 2px 8px rgba(139, 92, 246, 0.3)',
      border: 'none',
    }
  }

  // Off/Disabled states - slate gradient
  if (badgeStr === 'OFF' || badgeStr.includes('DISABLED')) {
    return {
      background: 'linear-gradient(135deg, #64748b 0%, #475569 100%)',
      color: '#ffffff',
      fontWeight: 600,
      border: 'none',
    }
  }

  // Count badges (numbers) - cyan gradient
  if (!Number.isNaN(Number(badge)) && Number(badge) > 0) {
    return {
      background: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
      color: '#ffffff',
      fontWeight: 700,
      boxShadow: '0 2px 8px rgba(6, 182, 212, 0.3)',
      border: 'none',
    }
  }

  // Heat/Fire related - thermal gradient
  if (badgeStr.includes('HEAT') || badgeStr.includes('FIRE') || badgeStr.includes('HOT')) {
    return {
      background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
      color: '#ffffff',
      fontWeight: 700,
      boxShadow: '0 2px 8px rgba(255, 107, 53, 0.3)',
      border: 'none',
    }
  }

  // Cool/AC related - cool gradient
  if (badgeStr.includes('COOL') || badgeStr.includes('AIRCO') || badgeStr.includes('AC')) {
    return {
      background: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
      color: '#ffffff',
      fontWeight: 700,
      boxShadow: '0 2px 8px rgba(6, 182, 212, 0.3)',
      border: 'none',
    }
  }

  // Default vibrant gradient for other cases
  return {
    background: 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)',
    color: '#ffffff',
    fontWeight: 600,
    boxShadow: '0 2px 8px rgba(245, 158, 11, 0.3)',
    border: 'none',
  }
}

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

  // Use controlled or uncontrolled state (prefer nullish coalescing)
  const expanded = controlledExpanded ?? internalExpanded

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
        <Box sx={{ flexGrow: 1, minWidth: 0, overflow: 'hidden' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
            <Typography
              variant="h6"
              component="div"
              sx={{
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
                wordBreak: 'break-word',
              }}
            >
              {title}
            </Typography>
            {badge !== undefined && (
              <Chip
                label={badge}
                size="small"
                sx={{
                  height: 22,
                  fontSize: '0.7rem',
                  letterSpacing: '0.03em',
                  transition: 'all 0.2s ease',
                  ...getBadgeStyle(badge),
                  '&:hover': {
                    transform: 'scale(1.05)',
                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.2)',
                  },
                }}
              />
            )}
          </Box>
          {description && (
            <Typography
              variant="caption"
              color="text.secondary"
              sx={{
                mt: 0.5,
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical',
              }}
            >
              {description}
            </Typography>
          )}
        </Box>
      </Box>

      {/* Content */}
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box
          sx={{
            p: 3,
            pt: 2,
            bgcolor: 'background.default',
            overflow: 'auto',
            maxWidth: '100%',
          }}
        >
          {children}
        </Box>
      </Collapse>
    </Paper>
  )
}

export default SettingsSection
