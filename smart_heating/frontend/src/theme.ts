import { createTheme, alpha } from '@mui/material'
import type { Theme } from '@mui/material/styles'

/**
 * Thermal Glass Theme - A refined Nordic-inspired design system
 *
 * Design Philosophy:
 * - Glassmorphism surfaces with depth and dimension
 * - Thermal-inspired color gradients (warm oranges, cool blues)
 * - Premium typography with DM Sans + JetBrains Mono
 * - Generous spacing and refined micro-interactions
 * - Dark-first design optimized for ambient dashboards
 */

// Custom color tokens
const thermalColors = {
  // Thermal gradients
  heat: {
    primary: '#ff6b35',
    secondary: '#f59e0b',
    glow: 'rgba(255, 107, 53, 0.4)',
  },
  cool: {
    primary: '#06b6d4',
    secondary: '#3b82f6',
    glow: 'rgba(6, 182, 212, 0.4)',
  },
  // Surface colors
  glass: {
    light: 'rgba(255, 255, 255, 0.08)',
    medium: 'rgba(255, 255, 255, 0.12)',
    strong: 'rgba(255, 255, 255, 0.18)',
    border: 'rgba(255, 255, 255, 0.1)',
  },
  // Accent colors
  accent: {
    amber: '#f59e0b',
    emerald: '#10b981',
    rose: '#f43f5e',
    violet: '#8b5cf6',
  },
}

// CSS variables to be injected
export const cssVariables = `
  :root {
    --thermal-heat-primary: ${thermalColors.heat.primary};
    --thermal-heat-secondary: ${thermalColors.heat.secondary};
    --thermal-heat-glow: ${thermalColors.heat.glow};
    --thermal-cool-primary: ${thermalColors.cool.primary};
    --thermal-cool-secondary: ${thermalColors.cool.secondary};
    --thermal-cool-glow: ${thermalColors.cool.glow};
    --glass-surface: ${thermalColors.glass.light};
    --glass-border: ${thermalColors.glass.border};
  }
`

export const createHATheme = (mode: 'light' | 'dark'): Theme => {
  const isDark = mode === 'dark'

  return createTheme({
    palette: {
      mode,
      primary: {
        main: '#ff6b35',
        light: '#ff8f66',
        dark: '#e55a28',
        contrastText: '#ffffff',
      },
      secondary: {
        main: '#06b6d4',
        light: '#22d3ee',
        dark: '#0891b2',
        contrastText: '#ffffff',
      },
      background: isDark
        ? {
            default: '#0a0a0f',
            paper: '#12121a',
          }
        : {
            default: '#f8fafc',
            paper: '#ffffff',
          },
      text: isDark
        ? {
            primary: '#f1f5f9',
            secondary: '#94a3b8',
          }
        : {
            primary: '#0f172a',
            secondary: '#64748b',
          },
      divider: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.08)',
      error: {
        main: '#f43f5e',
        light: '#fb7185',
        dark: '#e11d48',
      },
      warning: {
        main: '#f59e0b',
        light: '#fbbf24',
        dark: '#d97706',
      },
      success: {
        main: '#10b981',
        light: '#34d399',
        dark: '#059669',
      },
      info: {
        main: '#3b82f6',
        light: '#60a5fa',
        dark: '#2563eb',
      },
    },
    typography: {
      fontFamily: '"DM Sans", "Inter", system-ui, -apple-system, sans-serif',
      h1: {
        fontFamily: '"Outfit", "DM Sans", sans-serif',
        fontWeight: 700,
        letterSpacing: '-0.02em',
      },
      h2: {
        fontFamily: '"Outfit", "DM Sans", sans-serif',
        fontWeight: 700,
        letterSpacing: '-0.02em',
      },
      h3: {
        fontFamily: '"Outfit", "DM Sans", sans-serif',
        fontWeight: 600,
        letterSpacing: '-0.01em',
      },
      h4: {
        fontFamily: '"Outfit", "DM Sans", sans-serif',
        fontWeight: 600,
        letterSpacing: '-0.01em',
      },
      h5: {
        fontFamily: '"DM Sans", sans-serif',
        fontWeight: 600,
      },
      h6: {
        fontFamily: '"DM Sans", sans-serif',
        fontWeight: 600,
      },
      body1: {
        fontFamily: '"DM Sans", sans-serif',
        fontSize: '0.9375rem',
        lineHeight: 1.6,
      },
      body2: {
        fontFamily: '"DM Sans", sans-serif',
        fontSize: '0.875rem',
        lineHeight: 1.5,
      },
      button: {
        fontFamily: '"DM Sans", sans-serif',
        fontWeight: 500,
        letterSpacing: '0.01em',
      },
      caption: {
        fontFamily: '"DM Sans", sans-serif',
        fontSize: '0.75rem',
        letterSpacing: '0.02em',
      },
      overline: {
        fontFamily: '"DM Sans", sans-serif',
        fontSize: '0.6875rem',
        fontWeight: 600,
        letterSpacing: '0.08em',
        textTransform: 'uppercase',
      },
    },
    shape: {
      borderRadius: 16,
    },
    shadows: [
      'none',
      isDark ? '0 1px 2px rgba(0, 0, 0, 0.4)' : '0 1px 2px rgba(0, 0, 0, 0.05)',
      isDark ? '0 2px 4px rgba(0, 0, 0, 0.5)' : '0 2px 4px rgba(0, 0, 0, 0.08)',
      isDark ? '0 4px 8px rgba(0, 0, 0, 0.5)' : '0 4px 8px rgba(0, 0, 0, 0.1)',
      isDark ? '0 6px 12px rgba(0, 0, 0, 0.6)' : '0 6px 12px rgba(0, 0, 0, 0.1)',
      isDark ? '0 8px 16px rgba(0, 0, 0, 0.6)' : '0 8px 16px rgba(0, 0, 0, 0.12)',
      isDark ? '0 12px 24px rgba(0, 0, 0, 0.7)' : '0 12px 24px rgba(0, 0, 0, 0.14)',
      isDark ? '0 16px 32px rgba(0, 0, 0, 0.7)' : '0 16px 32px rgba(0, 0, 0, 0.16)',
      isDark ? '0 20px 40px rgba(0, 0, 0, 0.8)' : '0 20px 40px rgba(0, 0, 0, 0.18)',
      isDark ? '0 24px 48px rgba(0, 0, 0, 0.8)' : '0 24px 48px rgba(0, 0, 0, 0.2)',
      // Elevated shadows (10-24)
      ...Array(15)
        .fill(null)
        .map(() => (isDark ? '0 24px 48px rgba(0, 0, 0, 0.8)' : '0 24px 48px rgba(0, 0, 0, 0.2)')),
    ] as Theme['shadows'],
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            scrollbarColor: isDark ? '#374151 #0a0a0f' : '#d1d5db #f8fafc',
            '&::-webkit-scrollbar, & *::-webkit-scrollbar': {
              width: 8,
              height: 8,
            },
            '&::-webkit-scrollbar-track, & *::-webkit-scrollbar-track': {
              background: isDark ? '#0a0a0f' : '#f8fafc',
            },
            '&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb': {
              background: isDark ? '#374151' : '#d1d5db',
              borderRadius: 4,
            },
            '&::-webkit-scrollbar-thumb:hover, & *::-webkit-scrollbar-thumb:hover': {
              background: isDark ? '#4b5563' : '#9ca3af',
            },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            background: isDark
              ? `linear-gradient(135deg, ${alpha('#1e1e2a', 0.95)} 0%, ${alpha('#12121a', 0.98)} 100%)`
              : `linear-gradient(135deg, ${alpha('#ffffff', 0.98)} 0%, ${alpha('#f8fafc', 0.95)} 100%)`,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)'}`,
            borderRadius: 20,
            transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
            overflow: 'visible',
            '@media (min-width:900px)': {
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: isDark
                  ? '0 20px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1)'
                  : '0 20px 40px rgba(0, 0, 0, 0.12)',
              },
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
          elevation0: {
            background: isDark ? alpha('#12121a', 0.8) : alpha('#ffffff', 0.9),
            backdropFilter: 'blur(12px)',
          },
          elevation1: {
            background: isDark
              ? `linear-gradient(135deg, ${alpha('#1e1e2a', 0.9)} 0%, ${alpha('#12121a', 0.95)} 100%)`
              : `linear-gradient(135deg, ${alpha('#ffffff', 0.95)} 0%, ${alpha('#f8fafc', 0.9)} 100%)`,
            backdropFilter: 'blur(16px)',
            border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.04)'}`,
            boxShadow: isDark ? '0 4px 12px rgba(0, 0, 0, 0.4)' : '0 4px 12px rgba(0, 0, 0, 0.06)',
          },
          elevation2: {
            background: isDark
              ? `linear-gradient(135deg, ${alpha('#1e1e2a', 0.95)} 0%, ${alpha('#12121a', 0.98)} 100%)`
              : `linear-gradient(135deg, ${alpha('#ffffff', 0.98)} 0%, ${alpha('#f8fafc', 0.95)} 100%)`,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)'}`,
            boxShadow: isDark ? '0 8px 24px rgba(0, 0, 0, 0.5)' : '0 8px 24px rgba(0, 0, 0, 0.08)',
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            borderRadius: 12,
            padding: '10px 20px',
            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
          },
          contained: {
            background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
            boxShadow: '0 4px 12px rgba(255, 107, 53, 0.3)',
            '&:hover': {
              background: 'linear-gradient(135deg, #ff8f66 0%, #fbbf24 100%)',
              boxShadow: '0 6px 20px rgba(255, 107, 53, 0.4)',
              transform: 'translateY(-2px)',
            },
          },
          outlined: {
            borderColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
            backdropFilter: 'blur(8px)',
            '&:hover': {
              borderColor: '#ff6b35',
              backgroundColor: alpha('#ff6b35', 0.08),
            },
          },
          text: {
            '&:hover': {
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
            },
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            transition: 'all 0.25s cubic-bezier(0.4, 0, 0.2, 1)',
            '&:hover': {
              backgroundColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.06)',
              transform: 'scale(1.08)',
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 500,
            borderRadius: 10,
            backdropFilter: 'blur(8px)',
            transition: 'all 0.2s ease',
          },
          filled: {
            background: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.06)',
          },
          outlined: {
            borderColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.15)',
          },
          colorError: {
            background: `linear-gradient(135deg, ${alpha('#ff6b35', 0.9)} 0%, ${alpha('#f43f5e', 0.9)} 100%)`,
            color: '#ffffff',
            '& .MuiChip-icon': {
              color: '#ffffff',
            },
          },
          colorSuccess: {
            background: `linear-gradient(135deg, ${alpha('#10b981', 0.9)} 0%, ${alpha('#059669', 0.9)} 100%)`,
            color: '#ffffff',
          },
          colorWarning: {
            background: `linear-gradient(135deg, ${alpha('#f59e0b', 0.9)} 0%, ${alpha('#d97706', 0.9)} 100%)`,
            color: '#ffffff',
          },
          colorInfo: {
            background: `linear-gradient(135deg, ${alpha('#3b82f6', 0.9)} 0%, ${alpha('#2563eb', 0.9)} 100%)`,
            color: '#ffffff',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            background: isDark
              ? `linear-gradient(180deg, ${alpha('#0a0a0f', 0.95)} 0%, ${alpha('#12121a', 0.9)} 100%)`
              : `linear-gradient(180deg, ${alpha('#ffffff', 0.98)} 0%, ${alpha('#f8fafc', 0.95)} 100%)`,
            backdropFilter: 'blur(20px)',
            borderBottom: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)'}`,
            boxShadow: 'none',
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            fontSize: '0.9rem',
            minWidth: 'auto',
            padding: '12px 20px',
            borderRadius: 12,
            margin: '0 4px',
            transition: 'all 0.25s ease',
            '&.Mui-selected': {
              fontWeight: 600,
              background: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
            },
            '&:hover': {
              background: isDark ? 'rgba(255, 255, 255, 0.05)' : 'rgba(0, 0, 0, 0.02)',
            },
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          indicator: {
            height: 3,
            borderRadius: 3,
            background: 'linear-gradient(90deg, #ff6b35 0%, #f59e0b 100%)',
          },
        },
      },
      MuiSlider: {
        styleOverrides: {
          root: {
            height: 8,
            '& .MuiSlider-track': {
              border: 'none',
              background: 'linear-gradient(90deg, #ff6b35 0%, #f59e0b 100%)',
            },
            '& .MuiSlider-rail': {
              opacity: 0.3,
              background: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)',
            },
            '& .MuiSlider-thumb': {
              width: 24,
              height: 24,
              background: '#ffffff',
              border: '3px solid #ff6b35',
              boxShadow: '0 4px 12px rgba(255, 107, 53, 0.3)',
              transition: 'all 0.2s ease',
              '&:hover, &.Mui-focusVisible': {
                boxShadow: '0 0 0 8px rgba(255, 107, 53, 0.16)',
              },
              '&.Mui-active': {
                boxShadow: '0 0 0 12px rgba(255, 107, 53, 0.2)',
              },
            },
            '& .MuiSlider-mark': {
              display: 'none',
            },
            '& .MuiSlider-markLabel': {
              fontSize: '0.75rem',
              color: isDark ? 'rgba(255, 255, 255, 0.5)' : 'rgba(0, 0, 0, 0.4)',
            },
            '& .MuiSlider-valueLabel': {
              background: 'linear-gradient(135deg, #ff6b35 0%, #f59e0b 100%)',
              borderRadius: 8,
              fontSize: '0.875rem',
              fontWeight: 600,
            },
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          root: {
            width: 52,
            height: 30,
            padding: 0,
            '& .MuiSwitch-switchBase': {
              padding: 3,
              '&.Mui-checked': {
                transform: 'translateX(22px)',
                '& + .MuiSwitch-track': {
                  background: 'linear-gradient(90deg, #ff6b35 0%, #f59e0b 100%)',
                  opacity: 1,
                },
                '& .MuiSwitch-thumb': {
                  background: '#ffffff',
                },
              },
            },
            '& .MuiSwitch-thumb': {
              width: 24,
              height: 24,
              background: isDark ? '#94a3b8' : '#ffffff',
              boxShadow: '0 2px 6px rgba(0, 0, 0, 0.2)',
              transition: 'all 0.2s ease',
            },
            '& .MuiSwitch-track': {
              borderRadius: 15,
              background: isDark ? 'rgba(255, 255, 255, 0.15)' : 'rgba(0, 0, 0, 0.12)',
              opacity: 1,
              transition: 'all 0.3s ease',
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 12,
              background: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.02)',
              transition: 'all 0.2s ease',
              '& fieldset': {
                borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
                transition: 'all 0.2s ease',
              },
              '&:hover fieldset': {
                borderColor: isDark ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.2)',
              },
              '&.Mui-focused fieldset': {
                borderColor: '#ff6b35',
                borderWidth: 2,
              },
            },
          },
        },
      },
      MuiSelect: {
        styleOverrides: {
          root: {
            borderRadius: 12,
          },
        },
      },
      MuiMenu: {
        styleOverrides: {
          paper: {
            borderRadius: 16,
            background: isDark
              ? `linear-gradient(135deg, ${alpha('#1e1e2a', 0.98)} 0%, ${alpha('#12121a', 0.99)} 100%)`
              : `linear-gradient(135deg, ${alpha('#ffffff', 0.99)} 0%, ${alpha('#f8fafc', 0.98)} 100%)`,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)'}`,
            boxShadow: isDark
              ? '0 20px 40px rgba(0, 0, 0, 0.5)'
              : '0 20px 40px rgba(0, 0, 0, 0.12)',
          },
        },
      },
      MuiMenuItem: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            margin: '2px 8px',
            padding: '10px 16px',
            transition: 'all 0.2s ease',
            '&:hover': {
              background: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
            },
            '&.Mui-selected': {
              background: alpha('#ff6b35', 0.15),
              '&:hover': {
                background: alpha('#ff6b35', 0.2),
              },
            },
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            borderRadius: 24,
            background: isDark
              ? `linear-gradient(135deg, ${alpha('#1e1e2a', 0.98)} 0%, ${alpha('#12121a', 0.99)} 100%)`
              : `linear-gradient(135deg, ${alpha('#ffffff', 0.99)} 0%, ${alpha('#f8fafc', 0.98)} 100%)`,
            backdropFilter: 'blur(24px)',
            border: `1px solid ${isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)'}`,
            boxShadow: isDark
              ? '0 32px 64px rgba(0, 0, 0, 0.6)'
              : '0 32px 64px rgba(0, 0, 0, 0.15)',
          },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            background: isDark ? 'rgba(30, 30, 42, 0.95)' : 'rgba(15, 23, 42, 0.95)',
            backdropFilter: 'blur(12px)',
            borderRadius: 10,
            fontSize: '0.8125rem',
            padding: '8px 14px',
            boxShadow: '0 8px 24px rgba(0, 0, 0, 0.3)',
          },
          arrow: {
            color: isDark ? 'rgba(30, 30, 42, 0.95)' : 'rgba(15, 23, 42, 0.95)',
          },
        },
      },
      MuiAlert: {
        styleOverrides: {
          root: {
            borderRadius: 14,
            backdropFilter: 'blur(12px)',
          },
          standardError: {
            background: alpha('#f43f5e', 0.15),
            border: `1px solid ${alpha('#f43f5e', 0.3)}`,
          },
          standardWarning: {
            background: alpha('#f59e0b', 0.15),
            border: `1px solid ${alpha('#f59e0b', 0.3)}`,
          },
          standardSuccess: {
            background: alpha('#10b981', 0.15),
            border: `1px solid ${alpha('#10b981', 0.3)}`,
          },
          standardInfo: {
            background: alpha('#3b82f6', 0.15),
            border: `1px solid ${alpha('#3b82f6', 0.3)}`,
          },
        },
      },
      MuiList: {
        styleOverrides: {
          root: {
            padding: 8,
          },
        },
      },
      MuiListItem: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            marginBottom: 4,
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            padding: '12px 16px',
            transition: 'all 0.2s ease',
            '&:hover': {
              background: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.04)',
            },
            '&.Mui-selected': {
              background: alpha('#ff6b35', 0.12),
              '&:hover': {
                background: alpha('#ff6b35', 0.16),
              },
            },
          },
        },
      },
      MuiDivider: {
        styleOverrides: {
          root: {
            borderColor: isDark ? 'rgba(255, 255, 255, 0.06)' : 'rgba(0, 0, 0, 0.06)',
          },
        },
      },
      MuiAccordion: {
        styleOverrides: {
          root: {
            background: 'transparent',
            boxShadow: 'none',
            '&:before': {
              display: 'none',
            },
            '&.Mui-expanded': {
              margin: 0,
            },
          },
        },
      },
      MuiAccordionSummary: {
        styleOverrides: {
          root: {
            borderRadius: 14,
            padding: '0 16px',
            minHeight: 56,
            background: isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(0, 0, 0, 0.02)',
            transition: 'all 0.2s ease',
            '&:hover': {
              background: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
            },
            '&.Mui-expanded': {
              minHeight: 56,
              background: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
            },
          },
          content: {
            margin: '12px 0',
            '&.Mui-expanded': {
              margin: '12px 0',
            },
          },
        },
      },
      MuiCircularProgress: {
        styleOverrides: {
          root: {
            color: '#ff6b35',
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: {
            height: 6,
            borderRadius: 3,
            background: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)',
          },
          bar: {
            borderRadius: 3,
            background: 'linear-gradient(90deg, #ff6b35 0%, #f59e0b 100%)',
          },
        },
      },
      MuiBadge: {
        styleOverrides: {
          badge: {
            fontWeight: 600,
            fontSize: '0.7rem',
          },
        },
      },
    },
  })
}

// Export thermal colors for use in components
export { thermalColors }
