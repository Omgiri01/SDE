interface Props {
  alerts: { symbol: string; alert: string }[]
}

export function AlertBanner({ alerts }: Props) {
  if (alerts.length === 0) return null

  return (
    <div className="alert-banner">
      <span className="alert-banner__icon">⚠</span>
      <div className="alert-banner__list">
        {alerts.map((a, i) => (
          <span key={i} className="alert-banner__item">
            <strong>{a.symbol}:</strong> {a.alert}
          </span>
        ))}
      </div>
    </div>
  )
}
