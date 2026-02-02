'use client'

interface StatsCardProps {
  count: number
}

export function StatsCard({ count }: StatsCardProps) {
  return (
    <section className="bento-card card-stats">
      <div className="stats-number">{count}</div>
      <div className="stats-label">Concours<br/>Surveillés</div>
      <div className="stats-decoration"></div>
    </section>
  )
}
