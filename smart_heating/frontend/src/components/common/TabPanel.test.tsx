import React from 'react'
import { render, screen } from '@testing-library/react'
import TabPanel from './TabPanel'

test('TabPanel shows children when value matches index', () => {
  render(
    <TabPanel value={0} index={0}>
      <div>Visible</div>
    </TabPanel>,
  )
  expect(screen.getByText('Visible')).toBeInTheDocument()
})

test('TabPanel hides children when value does not match index', () => {
  render(
    <TabPanel value={1} index={0}>
      <div>Hidden</div>
    </TabPanel>,
  )
  expect(screen.queryByText('Hidden')).not.toBeInTheDocument()
})
