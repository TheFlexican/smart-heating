import { Zone } from '../../../types'
import { getEntityState } from '../../../api/config'

export const loadEntityStatesForZone = async (zone: Zone): Promise<Record<string, any>> => {
  const states: Record<string, any> = {}

  if (zone.presence_sensors) {
    for (const sensor of zone.presence_sensors) {
      const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
      try {
        const s = await getEntityState(entity_id)
        states[entity_id] = { state: s?.state, name: s?.attributes?.friendly_name }
      } catch {
        // ignore best-effort
      }
    }
  }

  if (zone.window_sensors) {
    for (const sensor of zone.window_sensors) {
      const entity_id = typeof sensor === 'string' ? sensor : sensor.entity_id
      try {
        const s = await getEntityState(entity_id)
        states[entity_id] = { state: s?.state, name: s?.attributes?.friendly_name }
      } catch {
        // ignore
      }
    }
  }

  return states
}

export default { loadEntityStatesForZone }
