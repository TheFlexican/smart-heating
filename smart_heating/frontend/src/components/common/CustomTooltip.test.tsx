import React from 'react'
import { render } from '@testing-library/react'
import CustomTooltip from './CustomTooltip'

test('renders CustomTooltip', () => {
  const { container } = render(
    <CustomTooltip title="Hi">
      {' '}
      <span>child</span>{' '}
    </CustomTooltip>,
  )
  expect(container).toBeTruthy()
})
