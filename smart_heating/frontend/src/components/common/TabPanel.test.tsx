import { render, screen } from '@testing-library/react'
import { TabPanel } from './TabPanel'

describe('TabPanel', () => {
  it('renders without crashing', () => {
    render(
      <TabPanel value={0} index={0}>
        Test content
      </TabPanel>,
    )
    expect(screen.getByText('Test content')).toBeInTheDocument()
  })

  it('shows content when value matches index', () => {
    render(
      <TabPanel value={1} index={1}>
        Visible content
      </TabPanel>,
    )
    expect(screen.getByText('Visible content')).toBeVisible()
  })

  it('hides content when value does not match index', () => {
    render(
      <TabPanel value={0} index={1}>
        Hidden content
      </TabPanel>,
    )
    const panel = screen.getByRole('tabpanel', { hidden: true })
    expect(panel).toHaveAttribute('hidden')
  })

  it('sets correct ARIA attributes', () => {
    render(
      <TabPanel value={2} index={2}>
        Content
      </TabPanel>,
    )
    const panel = screen.getByRole('tabpanel')
    expect(panel).toHaveAttribute('id', 'tabpanel-2')
    expect(panel).toHaveAttribute('aria-labelledby', 'tab-2')
  })

  it('renders children correctly', () => {
    render(
      <TabPanel value={0} index={0}>
        <div data-testid="child-element">Child Element</div>
      </TabPanel>,
    )
    expect(screen.getByTestId('child-element')).toBeInTheDocument()
  })
})
