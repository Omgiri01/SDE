import { useWebSocket } from './hooks/useWebSocket'
import { PriceGrid } from './components/PriceGrid'
import { RiskPanel } from './components/RiskPanel'
import { PortfolioPanel } from './components/PortfolioPanel'
import { FrontierChart } from './components/FrontierChart'
import { AlertBanner } from './components/AlertBanner'
import { HealthBar } from './components/HealthBar'

export default function App() {
  const { prices, alerts, connected } = useWebSocket()

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-header__left">
          <span className="app-logo">⚡</span>
          <span className="app-title">QuantRiskPro</span>
          <span className="app-subtitle">Real-Time Risk &amp; Portfolio Intelligence</span>
        </div>
        <HealthBar />
      </header>

      <AlertBanner alerts={alerts} />

      <main className="app-main">
        <PriceGrid prices={prices} connected={connected} />

        <div className="two-col">
          <RiskPanel />
          <PortfolioPanel />
        </div>

        <FrontierChart />
      </main>

      <footer className="app-footer">
        QuantRiskPro · FastAPI + TimescaleDB + Redis + Kafka · Built for fintech SWE roles
      </footer>
    </div>
  )
}
