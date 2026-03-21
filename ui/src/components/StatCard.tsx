import React from 'react'

export interface StatCardProps {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  accent?: string
}

export function StatCard({ icon, label, value, sub, accent }: StatCardProps) {
  return (
    <div className="stat-card">
      <div className="stat-icon" style={{ color: accent || 'var(--green)' }}>{icon}</div>
      <div className="stat-body">
        <div className="stat-label">{label}</div>
        <div className="stat-value" style={{ color: accent || 'var(--text-h)' }}>{value}</div>
        {sub && <div className="stat-sub">{sub}</div>}
      </div>
    </div>
  )
}
