import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'
import { AreaLearningTab } from './AreaLearningTab'
import { Zone } from '../../types'

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'areaDetail.adaptiveLearning': 'Adaptive Learning',
        'areaDetail.learningDescription': 'Learning system description',
        'areaDetail.smartNightBoostActive': 'Smart Night Boost is Active',
        'areaDetail.learningSystemText': 'System is learning your heating patterns',
        'areaDetail.learningNote': 'This feature learns over time',
        'areaDetail.configuration': 'Configuration',
        'areaDetail.targetWakeupTime': 'Target Wakeup Time',
        'areaDetail.weatherSensor': 'Weather Sensor',
        'areaDetail.notConfigured': 'Not configured',
        'areaDetail.learningProcessTitle': 'How Learning Works',
        'settingsCards.learningStep1': 'Step 1',
        'settingsCards.learningStep2': 'Step 2',
        'settingsCards.learningStep3': 'Step 3',
        'settingsCards.learningStep4': 'Step 4',
        'settingsCards.learningStep5': 'Step 5',
        'settingsCards.smartNightBoostNotEnabled': 'Smart Night Boost not enabled',
        'settingsCards.enableSmartNightBoostInfo': 'Enable it in settings',
        'settingsCards.adaptiveLearningInfo': 'Additional info about learning',
      }
      return translations[key] || key
    },
  }),
}))

describe('AreaLearningTab', () => {
  const mockAreaEnabled: Zone = {
    id: 'living_room',
    name: 'Living Room',
    state: 'heating',
    enabled: true,
    target_temperature: 21.0,
    current_temperature: 20.5,
    preset_mode: 'none',
    devices: [],
    schedules: [],
    smart_boost_enabled: true,
    smart_boost_target_time: '07:00',
    weather_entity_id: 'weather.home',
  } as Zone

  const mockAreaDisabled: Zone = {
    ...mockAreaEnabled,
    smart_boost_enabled: false,
  } as Zone

  const mockLearningStats = {
    total_events_all_time: 50,
    data_points: 30,
    avg_heating_rate: 0.0125,
    ready_for_predictions: true,
    first_event_time: '2024-01-01T06:00:00Z',
    last_event_time: '2024-01-15T06:00:00Z',
    recent_events: [
      { timestamp: '2024-01-15T06:00:00Z', heating_rate: 0.012 },
      { timestamp: '2024-01-14T06:00:00Z', heating_rate: 0.013 },
    ],
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders without crashing when smart boost is enabled', () => {
    render(
      <AreaLearningTab
        area={mockAreaEnabled}
        learningStats={mockLearningStats}
        learningStatsLoading={false}
      />,
    )
    expect(screen.getByText('Adaptive Learning')).toBeInTheDocument()
  })

  it('renders title and description', () => {
    render(
      <AreaLearningTab area={mockAreaEnabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(screen.getByText('Adaptive Learning')).toBeInTheDocument()
    expect(screen.getByText('Learning system description')).toBeInTheDocument()
  })

  it('shows smart boost active message when enabled', () => {
    render(
      <AreaLearningTab area={mockAreaEnabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(screen.getByText(/Smart Night Boost is Active/)).toBeInTheDocument()
  })

  it('shows configuration section with target wakeup time', () => {
    render(
      <AreaLearningTab area={mockAreaEnabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(screen.getByText('Configuration')).toBeInTheDocument()
    expect(screen.getByText('Target Wakeup Time')).toBeInTheDocument()
    expect(screen.getByText('07:00')).toBeInTheDocument()
  })

  it('shows weather sensor when configured', () => {
    render(
      <AreaLearningTab area={mockAreaEnabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(screen.getByText('Weather Sensor')).toBeInTheDocument()
    expect(screen.getByText('weather.home')).toBeInTheDocument()
  })

  it('shows not configured when weather sensor is missing', () => {
    const areaWithoutWeather = { ...mockAreaEnabled, weather_entity_id: undefined }
    render(
      <AreaLearningTab
        area={areaWithoutWeather}
        learningStats={null}
        learningStatsLoading={false}
      />,
    )
    expect(screen.getByText('Not configured')).toBeInTheDocument()
  })

  it('shows loading message when learningStatsLoading is true', () => {
    render(
      <AreaLearningTab area={mockAreaEnabled} learningStats={null} learningStatsLoading={true} />,
    )
    expect(screen.getByText('Loading statistics...')).toBeInTheDocument()
  })

  it('displays learning statistics when available', () => {
    render(
      <AreaLearningTab
        area={mockAreaEnabled}
        learningStats={mockLearningStats}
        learningStatsLoading={false}
      />,
    )
    expect(screen.getByText('Learning Data')).toBeInTheDocument()
    expect(screen.getByText('Total Events')).toBeInTheDocument()
    expect(screen.getByText('50')).toBeInTheDocument()
    expect(screen.getByText('Data Points (Last 30 Days)')).toBeInTheDocument()
    expect(screen.getByText('30')).toBeInTheDocument()
  })

  it('shows average heating rate when available', () => {
    render(
      <AreaLearningTab
        area={mockAreaEnabled}
        learningStats={mockLearningStats}
        learningStatsLoading={false}
      />,
    )
    expect(screen.getByText('Average Heating Rate')).toBeInTheDocument()
    expect(screen.getByText('0.0125°C/min')).toBeInTheDocument()
  })

  it('shows ready for predictions status', () => {
    render(
      <AreaLearningTab
        area={mockAreaEnabled}
        learningStats={mockLearningStats}
        learningStatsLoading={false}
      />,
    )
    expect(screen.getByText('Ready for Predictions')).toBeInTheDocument()
    expect(screen.getByText('Yes')).toBeInTheDocument()
  })

  it('shows not ready message when insufficient events', () => {
    const statsNotReady = { ...mockLearningStats, ready_for_predictions: false }
    render(
      <AreaLearningTab
        area={mockAreaEnabled}
        learningStats={statsNotReady}
        learningStatsLoading={false}
      />,
    )
    expect(screen.getByText('No (need 20+ events)')).toBeInTheDocument()
  })

  it('displays recent events when available', () => {
    render(
      <AreaLearningTab
        area={mockAreaEnabled}
        learningStats={mockLearningStats}
        learningStatsLoading={false}
      />,
    )
    expect(screen.getByText('Recent Events (Last 10):')).toBeInTheDocument()
    expect(screen.getByText('0.0120°C/min')).toBeInTheDocument()
    expect(screen.getByText('0.0130°C/min')).toBeInTheDocument()
  })

  it('shows no data message when learningStats is null', () => {
    render(
      <AreaLearningTab area={mockAreaEnabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(
      screen.getByText('No learning data available yet. Start heating cycles to collect data.'),
    ).toBeInTheDocument()
  })

  it('renders learning process steps', () => {
    render(
      <AreaLearningTab area={mockAreaEnabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(screen.getByText('How Learning Works')).toBeInTheDocument()
    expect(screen.getByText('Step 1')).toBeInTheDocument()
    expect(screen.getByText('Step 2')).toBeInTheDocument()
    expect(screen.getByText('Step 3')).toBeInTheDocument()
    expect(screen.getByText('Step 4')).toBeInTheDocument()
    expect(screen.getByText('Step 5')).toBeInTheDocument()
  })

  it('shows disabled message when smart boost is not enabled', () => {
    render(
      <AreaLearningTab area={mockAreaDisabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(screen.getByText('Smart Night Boost not enabled')).toBeInTheDocument()
    expect(screen.getByText('Enable it in settings')).toBeInTheDocument()
    expect(screen.getByText('Additional info about learning')).toBeInTheDocument()
  })

  it('does not show configuration when smart boost is disabled', () => {
    render(
      <AreaLearningTab area={mockAreaDisabled} learningStats={null} learningStatsLoading={false} />,
    )
    expect(screen.queryByText('Configuration')).not.toBeInTheDocument()
    expect(screen.queryByText('Target Wakeup Time')).not.toBeInTheDocument()
  })
})
