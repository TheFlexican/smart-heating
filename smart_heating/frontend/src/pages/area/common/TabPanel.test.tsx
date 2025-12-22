import React from 'react'
import { render, screen } from '@testing-library/react'
import TabPanel from '../TabPanel'

describe('TabPanel', () => {
  it('renders children when value equals index', () => {
    render(
      <TabPanel value={1} index={1}>
        <div>Visible Content</div>
      </TabPanel>,
    )

    expect(screen.getByText('Visible Content')).toBeInTheDocument()
  })

  it('does not render children when value does not equal index', () => {
    render(
      <TabPanel value={0} index={1}>
        <div>Hidden Content</div>
      </TabPanel>,
    )

    expect(screen.queryByText('Hidden Content')).toBeNull()
  })
})
