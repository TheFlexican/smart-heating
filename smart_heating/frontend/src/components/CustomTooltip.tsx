import { Box } from '@mui/material'

interface Props {
  active?: boolean
  payload?: any
  t: any
}

const CustomTooltip = ({ active, payload, t }: Props) => {
  if (active && payload?.length) {
    const data = payload[0]?.payload
    return (
      <Box
        sx={{
          backgroundColor: '#1c1c1c',
          border: '1px solid #2c2c2c',
          borderRadius: '8px',
          padding: '8px 12px',
          color: '#e1e1e1',
        }}
      >
        <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>{data.time}</div>
        <div style={{ color: '#03a9f4' }}>Current: {data.current.toFixed(1)}°C</div>
        <div style={{ color: '#ffc107' }}>Target: {data.target.toFixed(1)}°C</div>
        {(() => {
          let stateLabel: string
          let color: string
          if (data.heatingState === 'heating') {
            stateLabel = `${t('areaDetail.heatingActiveLineShort', 'Heating')}: Active`
            color = '#f44336'
          } else if (data.heatingState === 'cooling') {
            stateLabel = `${t('areaDetail.coolingActiveLineShort', 'Cooling')}: Active`
            color = '#03a9f4'
          } else {
            stateLabel = `${t('areaDetail.heatingActiveLineShort', 'Heating')}: Inactive`
            color = '#e1e1e1'
          }
          return <div style={{ color }}>{stateLabel}</div>
        })()}
      </Box>
    )
  }
  return null
}

export default CustomTooltip
