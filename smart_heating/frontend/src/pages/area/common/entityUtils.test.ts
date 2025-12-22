import { loadEntityStatesForZone } from '../entityUtils'
import * as api from '../../../../api/config'

describe('loadEntityStatesForZone', () => {
  beforeEach(() => {
    vi.resetAllMocks()
  })

  it('loads presence and window sensor states', async () => {
    const zone: any = {
      presence_sensors: ['binary_sensor.presence_1'],
      window_sensors: [{ entity_id: 'binary_sensor.window_1' }],
    }

    const spy = vi.spyOn(api, 'getEntityState').mockImplementation(async id => {
      return { state: id.includes('presence') ? 'on' : 'off', attributes: { friendly_name: id } }
    })

    const states = await loadEntityStatesForZone(zone)

    expect(states['binary_sensor.presence_1'].state).toBe('on')
    expect(states['binary_sensor.window_1'].state).toBe('off')
    spy.mockRestore()
  })
})
