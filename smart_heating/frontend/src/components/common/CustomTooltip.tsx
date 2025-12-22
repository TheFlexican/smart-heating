import { TooltipProps } from 'recharts'

// Use correct generics for TooltipProps and access props as object
const CustomTooltip = (props: TooltipProps<any, any>) => {
  const { active } = props
  // payload and label are not top-level props, but exist on props
  const payload = (props as any).payload
  const label = (props as any).label
  if (active && payload?.length) {
    return (
      <div
        style={{
          background: '#222',
          color: '#fff',
          padding: 8,
          borderRadius: 4,
          border: '1px solid #444',
        }}
        data-testid="history-custom-tooltip"
      >
        <div>
          <strong>{label}</strong>
        </div>
        {payload.map((entry: any) => (
          <div key={entry.dataKey || entry.name} style={{ color: entry.color }}>
            {entry.name}: <strong>{entry.value}</strong>
          </div>
        ))}
      </div>
    )
  }
  return null
}

export default CustomTooltip
