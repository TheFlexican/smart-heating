import React from 'react'
import { render, screen } from '@testing-library/react'
import LearningStats from './LearningStats'

test('renders loading state and then data', () => {
  const { rerender } = render(<LearningStats loading={true} learningStats={null} />)
  expect(screen.getByText(/Loading statistics/i)).toBeInTheDocument()

  rerender(
    <LearningStats
      loading={false}
      learningStats={{ total_events_all_time: 5, data_points: 10, ready_for_predictions: false }}
    />,
  )
  expect(screen.getByText(/Total Events/i)).toBeInTheDocument()
})
