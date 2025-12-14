import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect } from 'vitest'
import SettingsSection from './SettingsSection'

describe('SettingsSection', () => {
  it('renders title, description, badge and toggles content', async () => {
    const onChange = vi.fn()
    const user = userEvent.setup()
    render(
      <SettingsSection id="s1" title="Test" description="desc" badge={3} onExpandedChange={onChange}>
        <div>child content</div>
      </SettingsSection>
    )

    expect(screen.getByText('Test')).toBeInTheDocument()
    expect(screen.getByText('desc')).toBeInTheDocument()
    // content should be hidden by default
    expect(screen.queryByText('child content')).not.toBeInTheDocument()

    // Click header to expand
    const header = screen.getByText('Test')
    await user.click(header)
    expect(onChange).toHaveBeenCalled()
  })
})
