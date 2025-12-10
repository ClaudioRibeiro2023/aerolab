import {
  Activity,
  TrendingUp,
  TrendingDown,
  Clock,
  Server,
  Database,
  Zap,
  RefreshCw,
} from 'lucide-react'
import { Button, PageHeader } from '@template/design-system'

// Mock metrics data
const MOCK_METRICS = {
  requests: { value: 15420, change: 12.5, unit: 'req/min' },
  latency: { value: 45, change: -8.2, unit: 'ms' },
  errors: { value: 0.12, change: -25, unit: '%' },
  uptime: { value: 99.99, change: 0, unit: '%' },
}

const SERVICES = [
  { name: 'API Gateway', status: 'healthy', requests: 5200, latency: 12, errors: 0.01 },
  { name: 'Auth Service', status: 'healthy', requests: 3100, latency: 25, errors: 0 },
  { name: 'Data Service', status: 'warning', requests: 4500, latency: 85, errors: 0.5 },
  { name: 'Cache (Redis)', status: 'healthy', requests: 12000, latency: 2, errors: 0 },
  { name: 'Database (PostgreSQL)', status: 'healthy', requests: 2800, latency: 35, errors: 0.02 },
]

const STATUS_COLORS = {
  healthy: 'bg-green-500',
  warning: 'bg-yellow-500',
  critical: 'bg-red-500',
}

export default function MetricsPage() {
  return (
    <div className="min-h-screen bg-surface-base">
      {/* Header */}
      <div className="bg-surface-elevated border-b border-border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <PageHeader
            title="Métricas"
            description="Prometheus/metrics de API e jobs"
            icon={<Activity size={28} />}
            actions={
              <Button variant="ghost" leftIcon={<RefreshCw size={18} />}>
                Atualizar
              </Button>
            }
          />
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <MetricCard
            title="Requisições"
            value={MOCK_METRICS.requests.value.toLocaleString()}
            unit={MOCK_METRICS.requests.unit}
            change={MOCK_METRICS.requests.change}
            icon={<Zap size={20} />}
          />
          <MetricCard
            title="Latência Média"
            value={MOCK_METRICS.latency.value.toString()}
            unit={MOCK_METRICS.latency.unit}
            change={MOCK_METRICS.latency.change}
            icon={<Clock size={20} />}
          />
          <MetricCard
            title="Taxa de Erros"
            value={MOCK_METRICS.errors.value.toString()}
            unit={MOCK_METRICS.errors.unit}
            change={MOCK_METRICS.errors.change}
            icon={<Activity size={20} />}
          />
          <MetricCard
            title="Uptime"
            value={MOCK_METRICS.uptime.value.toString()}
            unit={MOCK_METRICS.uptime.unit}
            change={MOCK_METRICS.uptime.change}
            icon={<Server size={20} />}
          />
        </div>

        {/* Services Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-lg font-medium text-gray-900 dark:text-white">Serviços</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200 dark:border-gray-700 text-left">
                  <th className="px-4 py-3 text-sm font-medium text-gray-500">Serviço</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-500">Status</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-500">Requisições/min</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-500">Latência</th>
                  <th className="px-4 py-3 text-sm font-medium text-gray-500">Erros</th>
                </tr>
              </thead>
              <tbody>
                {SERVICES.map(service => (
                  <tr
                    key={service.name}
                    className="border-b border-gray-100 dark:border-gray-700/50 hover:bg-gray-50 dark:hover:bg-gray-700/30"
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        {service.name.includes('Redis') ? (
                          <Database size={16} className="text-gray-400" />
                        ) : service.name.includes('PostgreSQL') ? (
                          <Database size={16} className="text-gray-400" />
                        ) : (
                          <Server size={16} className="text-gray-400" />
                        )}
                        <span className="font-medium text-gray-900 dark:text-white">
                          {service.name}
                        </span>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium ${
                          service.status === 'healthy'
                            ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400'
                            : service.status === 'warning'
                              ? 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
                              : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
                        }`}
                      >
                        <span
                          className={`w-1.5 h-1.5 rounded-full ${STATUS_COLORS[service.status as keyof typeof STATUS_COLORS]}`}
                        />
                        {service.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {service.requests.toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {service.latency}ms
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      {service.errors}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* Charts Placeholder */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
              Requisições por Tempo
            </h3>
            <div className="h-48 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Activity size={40} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">Gráfico de requisições</p>
                <p className="text-xs mt-1">Integrar com Grafana/Prometheus</p>
              </div>
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
            <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-4">
              Latência p95/p99
            </h3>
            <div className="h-48 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <Clock size={40} className="mx-auto mb-2 opacity-50" />
                <p className="text-sm">Gráfico de latência</p>
                <p className="text-xs mt-1">Integrar com Grafana/Prometheus</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

interface MetricCardProps {
  title: string
  value: string
  unit: string
  change: number
  icon: React.ReactNode
}

function MetricCard({ title, value, unit, change, icon }: MetricCardProps) {
  const isPositive = change > 0
  const isNeutral = change === 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-500">{title}</span>
        <span className="text-gray-400">{icon}</span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-2xl font-bold text-gray-900 dark:text-white">{value}</span>
        <span className="text-sm text-gray-500">{unit}</span>
      </div>
      {!isNeutral && (
        <div
          className={`flex items-center gap-1 mt-2 text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}
        >
          {isPositive ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span>{Math.abs(change)}%</span>
        </div>
      )}
    </div>
  )
}
