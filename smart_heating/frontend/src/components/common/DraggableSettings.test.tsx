import React from 'react'
import { render, screen } from '@testing-library/react'
import { vi, describe, it, expect } from 'vitest'
import DraggableSettings from './DraggableSettings'

vi.mock('react-i18next', () => ({ useTranslation: () => ({ t: (k: string) => k }) }))

const sections = [
  { id: 's1', title: 'One', content: <div>One</div> },
  { id: 's2', title: 'Two', content: <div>Two</div> },
]

describe('DraggableSettings', () => {
  it('renders provided sections', () => {
    render(
      <DraggableSettings
        sections={sections as any}
        expandedCard={null}
        onExpandedChange={() => {}}
      />,
    )

    expect(screen.getByText('One')).toBeInTheDocument()
    expect(screen.getByText('Two')).toBeInTheDocument()
  })
})
