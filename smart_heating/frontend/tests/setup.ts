// Adds custom Jest matchers for DOM testing (toBeDisabled, toBeVisible, etc.)
import '@testing-library/jest-dom'
import { beforeAll, afterAll, vi } from 'vitest'

// Ensure react-i18next is mocked during tests to avoid NO_I18NEXT_INSTANCE warnings
vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t: (k: string, _v?: any) => k, i18n: { language: 'en', changeLanguage: () => Promise.resolve() } }),
  initReactI18next: { type: '3rdParty' },
}))

// Suppress known console warnings that don't affect test reliability
const originalError = console.error
const originalWarn = console.warn

beforeAll(() => {
  console.error = (...args: any[]) => {
    // Suppress act() warnings from MUI components (TouchRipple, ButtonBase, etc.)
    if (
      typeof args[0] === 'string' &&
      (
        args[0].includes('Warning: An update to') ||
        args[0].includes('inside a test was not wrapped in act') ||
        args[0].includes('NO_I18NEXT_INSTANCE')
      )
    ) {
      return
    }
    originalError.call(console, ...args)
  }

  console.warn = (...args: any[]) => {
    // Suppress React Router future flag warnings and known MUI warnings in tests
    if (
      typeof args[0] === 'string' &&
      (
        args[0].includes('React Router Future Flag Warning') ||
        args[0].includes('v7_startTransition') ||
        args[0].includes('v7_relativeSplatPath') ||
        args[0].includes('out-of-range value') ||
        args[0].includes('<p> cannot contain a nested <div>')
      )
    ) {
      return
    }
    originalWarn.call(console, ...args)
  }
})

afterAll(() => {
  console.error = originalError
  console.warn = originalWarn
})
