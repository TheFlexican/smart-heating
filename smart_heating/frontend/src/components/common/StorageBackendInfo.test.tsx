import React from 'react'
import { render } from '@testing-library/react'
import StorageBackendInfo from './StorageBackendInfo'

test('renders StorageBackendInfo', () => {
  const { container } = render(<StorageBackendInfo />)
  expect(container).toBeTruthy()
})
