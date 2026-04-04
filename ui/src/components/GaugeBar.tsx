import { fmt } from '../shared/utils'

export function GaugeBar({ label, value, max = 100, unit = '%', color }: {
  label: string
  value: number
  max?: number
  unit?: string
  color?: string
}) {
  const pct = Math.min(100, (value / max) * 100)
  const col = color || (pct > 80 ? 'var(--red)' : pct > 60 ? 'var(--amber)' : 'var(--green)')
  return (
    <div className="gauge-row">
      <div className="gauge-label">{label}</div>
      <div className="gauge-bar-wrap">
        <div className="gauge-bar-bg">
          <div className="gauge-bar-fill" style={{ width: `${pct}%`, background: col }} />
        </div>
      </div>
      <div className="gauge-val" style={{ color: col }}>{fmt(value)}{unit}</div>
    </div>
  )
}
