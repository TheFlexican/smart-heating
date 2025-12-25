import { createTheme } from '@mui/material'

/**
 * Home Assistant theme factory - matches HA's native theme with enhanced visual polish
 *
 * Enhancements for desktop:
 * - Card hover effects and elevation
 * - Smooth transitions on interactive elements
 * - Better button hover states
 * - Improved shadows and depth
 * - Enhanced spacing and padding
 */
export const createHATheme = (mode: 'light' | 'dark') =>
  createTheme({
    palette: {
      mode,
      primary: {
        main: '#03a9f4', // HA blue accent
        light: '#42c0fb',
        dark: '#0286c2',
      },
      secondary: {
        main: '#ffc107', // HA amber accent
        light: '#ffd54f',
        dark: '#c79100',
      },
      background:
        mode === 'dark'
          ? {
              default: '#111111', // HA dark background
              paper: '#1c1c1c', // HA card background
            }
          : {
              default: '#fafafa', // HA light background
              paper: '#ffffff', // HA light card background
            },
      text:
        mode === 'dark'
          ? {
              primary: '#e1e1e1',
              secondary: '#9e9e9e',
            }
          : {
              primary: '#212121',
              secondary: '#757575',
            },
      divider: mode === 'dark' ? '#2c2c2c' : '#e0e0e0',
      error: {
        main: '#f44336',
      },
      warning: {
        main: '#ff9800',
      },
      success: {
        main: '#4caf50',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 600,
      },
      h5: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 600,
      },
    },
    shape: {
      borderRadius: 8,
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
            transition: 'box-shadow 0.3s ease-in-out, transform 0.2s ease-in-out',
            // Desktop hover effect
            '@media (min-width:900px)': {
              '&:hover': {
                boxShadow:
                  mode === 'dark'
                    ? '0 4px 12px rgba(0, 0, 0, 0.5)'
                    : '0 4px 12px rgba(0, 0, 0, 0.15)',
              },
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            transition: 'all 0.2s ease-in-out',
            // Desktop hover effect
            '@media (min-width:900px)': {
              '&:hover': {
                transform: 'translateY(-1px)',
                boxShadow:
                  mode === 'dark' ? '0 2px 8px rgba(0, 0, 0, 0.3)' : '0 2px 8px rgba(0, 0, 0, 0.1)',
              },
            },
          },
          contained: {
            boxShadow:
              mode === 'dark' ? '0 2px 4px rgba(0, 0, 0, 0.3)' : '0 2px 4px rgba(0, 0, 0, 0.1)',
          },
        },
      },
      MuiIconButton: {
        styleOverrides: {
          root: {
            transition: 'all 0.2s ease-in-out',
            // Desktop hover effect
            '@media (min-width:900px)': {
              '&:hover': {
                transform: 'scale(1.1)',
              },
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: {
            fontWeight: 500,
            transition: 'all 0.2s ease-in-out',
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: {
            backgroundImage: 'none',
          },
          elevation1: {
            boxShadow:
              mode === 'dark' ? '0 1px 3px rgba(0, 0, 0, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.08)',
          },
          elevation2: {
            boxShadow:
              mode === 'dark' ? '0 2px 6px rgba(0, 0, 0, 0.4)' : '0 2px 6px rgba(0, 0, 0, 0.1)',
          },
          elevation3: {
            boxShadow:
              mode === 'dark' ? '0 4px 8px rgba(0, 0, 0, 0.5)' : '0 4px 8px rgba(0, 0, 0, 0.12)',
          },
          elevation4: {
            boxShadow:
              mode === 'dark' ? '0 6px 12px rgba(0, 0, 0, 0.6)' : '0 6px 12px rgba(0, 0, 0, 0.15)',
          },
        },
      },
      MuiAppBar: {
        styleOverrides: {
          root: {
            boxShadow:
              mode === 'dark' ? '0 1px 3px rgba(0, 0, 0, 0.3)' : '0 1px 3px rgba(0, 0, 0, 0.08)',
          },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 500,
            transition: 'all 0.2s ease-in-out',
            '&.Mui-selected': {
              fontWeight: 600,
            },
          },
        },
      },
      MuiListItemButton: {
        styleOverrides: {
          root: {
            transition: 'all 0.2s ease-in-out',
            borderRadius: 8,
            '&:hover': {
              backgroundColor:
                mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.04)',
            },
          },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          root: {
            '& .MuiSwitch-thumb': {
              transition: 'all 0.2s ease-in-out',
            },
            '& .MuiSwitch-track': {
              transition: 'all 0.2s ease-in-out',
            },
          },
        },
      },
      MuiSlider: {
        styleOverrides: {
          root: {
            '& .MuiSlider-thumb': {
              transition: 'box-shadow 0.2s ease-in-out',
              '&:hover': {
                boxShadow:
                  mode === 'dark'
                    ? '0 0 0 8px rgba(3, 169, 244, 0.16)'
                    : '0 0 0 8px rgba(3, 169, 244, 0.16)',
              },
            },
          },
        },
      },
    },
  })
