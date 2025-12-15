import axios from 'axios'
import { getEntityState } from './config'
const API_BASE = '/api/smart_heating'

export const getOpenThermLogs = async (limit?: number): Promise<any> => {
  const params = limit ? `?limit=${limit}` : ''
  const response = await axios.get(`${API_BASE}/opentherm/logs${params}`)
  return response.data
}

export const getOpenThermCapabilities = async (): Promise<any> => {
  const response = await axios.get(`${API_BASE}/opentherm/capabilities`)
  return response.data
}

export const discoverOpenThermCapabilities = async (): Promise<any> => {
  const response = await axios.post(`${API_BASE}/opentherm/capabilities/discover`)
  return response.data
}

export const clearOpenThermLogs = async (): Promise<any> => {
  const response = await axios.post(`${API_BASE}/opentherm/logs/clear`)
  return response.data
}

export const setOpenthermGateway = async (gatewayId: string): Promise<void> => {
  await axios.post(`${API_BASE}/opentherm_gateway`, { gateway_id: gatewayId })
}

export const getOpenThermSensorStates = async (): Promise<any> => {
  // Get multiple sensor states in parallel
  const sensorIds = [
    'sensor.opentherm_ketel_regel_instelpunt_1',
    'sensor.opentherm_ketel_relatief_modulatieniveau',
    'sensor.opentherm_ketel_centrale_verwarming_1_watertemperatuur',
    'sensor.opentherm_ketel_temperatuur_retourwater',
    'sensor.opentherm_thermostaat_kamertemperatuur',
    'sensor.opentherm_thermostaat_room_setpoint_1',
    'binary_sensor.opentherm_ketel_vlam',
    'sensor.opentherm_ketel_waterdruk_centrale_verwarming',
    'binary_sensor.opentherm_ketel_centrale_verwarming_1',
    'binary_sensor.opentherm_ketel_heet_water',
    'binary_sensor.opentherm_ketel_storingsindicatie',
    'binary_sensor.opentherm_ketel_diagnostische_indicatie',
    'binary_sensor.opentherm_ketel_lage_waterdruk',
    'binary_sensor.opentherm_ketel_gasstoring',
    'binary_sensor.opentherm_ketel_luchtdrukfout',
    'binary_sensor.opentherm_ketel_water_overtemperature',
    'binary_sensor.opentherm_ketel_service_vereist',
  ]

  const results = await Promise.allSettled(
    sensorIds.map(id => getEntityState(id).catch(() => null))
  )

  const sensorMapping: Array<{
    keyword: string
    stateKey: string
    parser: (value: string) => number | boolean
  }> = [
    { keyword: 'regel_instelpunt_1', stateKey: 'control_setpoint', parser: Number.parseFloat },
    {
      keyword: 'relatief_modulatieniveau',
      stateKey: 'modulation_level',
      parser: Number.parseFloat,
    },
    {
      keyword: 'centrale_verwarming_1_watertemperatuur',
      stateKey: 'ch_water_temp',
      parser: Number.parseFloat,
    },
    {
      keyword: 'temperatuur_retourwater',
      stateKey: 'return_water_temp',
      parser: Number.parseFloat,
    },
    { keyword: 'kamertemperatuur', stateKey: 'room_temp', parser: Number.parseFloat },
    { keyword: 'room_setpoint_1', stateKey: 'room_setpoint', parser: Number.parseFloat },
    { keyword: 'vlam', stateKey: 'flame_on', parser: v => v === 'on' },
    { keyword: 'waterdruk', stateKey: 'ch_pressure', parser: Number.parseFloat },
    { keyword: 'centrale_verwarming_1', stateKey: 'ch_active', parser: v => v === 'on' },
    { keyword: 'heet_water', stateKey: 'dhw_active', parser: v => v === 'on' },
    { keyword: 'storingsindicatie', stateKey: 'fault', parser: v => v === 'on' },
    { keyword: 'diagnostische', stateKey: 'diagnostic', parser: v => v === 'on' },
    { keyword: 'lage_waterdruk', stateKey: 'low_water_pressure', parser: v => v === 'on' },
    { keyword: 'gasstoring', stateKey: 'gas_fault', parser: v => v === 'on' },
    { keyword: 'luchtdrukfout', stateKey: 'air_pressure_fault', parser: v => v === 'on' },
    { keyword: 'water_overtemperature', stateKey: 'water_overtemp', parser: v => v === 'on' },
    { keyword: 'service_vereist', stateKey: 'service_required', parser: v => v === 'on' },
  ]

  const states: any = {}

  for (let i = 0; i < results.length; i++) {
    const result = results[i]
    if (result.status === 'fulfilled' && result.value) {
      const sensorId = sensorIds[i]
      const value = result.value.state
      const mapping = sensorMapping.find(m => sensorId.includes(m.keyword))
      if (mapping) {
        states[mapping.stateKey] = mapping.parser(value)
      }
    }
  }

  return states
}

export const getOpenthermGateways = async (): Promise<
  Array<{ gateway_id: string; title: string }>
> => {
  const response = await axios.get(`${API_BASE}/opentherm/gateways`)
  return response.data.gateways
}

export const calibrateOpentherm = async (): Promise<any> => {
  const response = await axios.post(`${API_BASE}/opentherm/calibrate`, {})
  return response.data
}

export default {}
