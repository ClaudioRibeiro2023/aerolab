import { useState, useEffect } from 'react'
import {
  HeartPulse,
  CheckCircle,
  XCircle,
  AlertTriangle,
  RefreshCw,
  Clock,
  Database,
  Server,
  Wifi,
} from 'lucide-react'
import { Button, PageHeader } from '@template/design-system'

type HealthStatus = 'healthy' | 'degraded' | 'unhealthy'

interface HealthCheck {
  name: string
  status: HealthStatus
  latency?: number
  message?: string
  lastCheck: string
  details?: Record<string, unknown>
}

// Mock health data
const MOCK_HEALTH: HealthCheck[] = [
  { name: 'API Server', status: 'healthy', latency: 12, lastCheck: new Date().toISOString() },
  {
    name: 'PostgreSQL',
    status: 'healthy',
    latency: 25,
    lastCheck: new Date().toISOString(),
    details: { connections: 45, maxConnections: 100 },
  },
  {
    name: 'Redis Cache',
    status: 'healthy',
    latency: 2,
    lastCheck: new Date().toISOString(),
    details: { usedMemory: '256MB', hitRate: '98.5%' },
  },
  { name: 'Keycloak Auth', status: 'healthy', latency: 85, lastCheck: new Date().toISOString() },
  {
    name: 'File Storage',
    status: 'degraded',
    latency: 450,
    message: 'Alta latência detectada',
    lastCheck: new Date().toISOString(),
  },
  {
    name: 'Email Service',
    status: 'unhealthy',
    message: 'Conexão recusada',
    lastCheck: new Date().toISOString(),
  },
  {
    name: 'Background Jobs',
    status: 'healthy',
    lastCheck: new Date().toISOString(),
    details: { queued: 12, processing: 3, failed: 0 },
  },
]

const STATUS_CONFIG = {
  healthy: {
    icon: CheckCircle,
    color: 'text-green-500',
    bg: 'bg-green-50 dark:bg-green-900/20',
    label: 'Saudável',
  },
  degraded: {
    icon: AlertTriangle,
    color: 'text-yellow-500',
    bg: 'bg-yellow-50 dark:bg-yellow-900/20',
    label: 'Degradado',
  },
  unhealthy: {
    icon: XCircle,
    color: 'text-red-500',
    bg: 'bg-red-50 dark:bg-red-900/20',
    label: 'Indisponível',
  },
}

export default function HealthPage() {
  const [isRefreshing, setIsRefreshing] = useState(false)
  const [lastRefresh, setLastRefresh] = useState(new Date())

  const overallStatus: HealthStatus = MOCK_HEALTH.some(h => h.status === 'unhealthy')
    ? 'unhealthy'
    : MOCK_HEALTH.some(h => h.status === 'degraded')
      ? 'degraded'
      : 'healthy'

  const refresh = () => {
    setIsRefreshing(true)
    setTimeout(() => {
      setIsRefreshing(false)
      setLastRefresh(new Date())
    }, 1000)
  }

  useEffect(() => {
    const interval = setInterval(refresh, 30000) // Auto-refresh every 30s
    return () => clearInterval(interval)
  }, [])

  const getIcon = (name: string) => {
    if (name.includes('PostgreSQL') || name.includes('Redis')) return Database
    if (name.includes('Server') || name.includes('Jobs')) return Server
    return Wifi
  }

  return (
    <div className="min-h-screen bg-surface-base">
      {/* Header */}
      <div className="bg-surface-elevated border-b border-border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <PageHeader
            title="Saúde do Sistema"
            description="Health checks, filas e storage"
            icon={<HeartPulse size={28} />}
            actions={
              <div className="flex items-center gap-4">
                <span className="text-sm text-text-muted">
                  Última atualização: {lastRefresh.toLocaleTimeString('pt-BR')}
                </span>
                <Button
                  variant="ghost"
                  leftIcon={<RefreshCw size={18} className={isRefreshing ? 'animate-spin' : ''} />}
                  onClick={refresh}
                  disabled={isRefreshing}
                >
                  Atualizar
                </Button>
              </div>
            }
          />
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Overall Status */}
        <div className={`p-6 rounded-lg mb-6 ${STATUS_CONFIG[overallStatus].bg}`}>
          <div className="flex items-center gap-3">
            {(() => {
              const Icon = STATUS_CONFIG[overallStatus].icon
              return <Icon size={32} className={STATUS_CONFIG[overallStatus].color} />
            })()}
            <div>
              <h2 className="text-xl font-bold text-text-primary">
                Status Geral: {STATUS_CONFIG[overallStatus].label}
              </h2>
              <p className="text-text-secondary">
                {MOCK_HEALTH.filter(h => h.status === 'healthy').length} de {MOCK_HEALTH.length}{' '}
                serviços operacionais
              </p>
            </div>
          </div>
        </div>

        {/* Health Checks Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {MOCK_HEALTH.map(check => {
            const config = STATUS_CONFIG[check.status]
            const StatusIcon = config.icon
            const ServiceIcon = getIcon(check.name)

            return (
              <div
                key={check.name}
                className={`p-4 rounded-lg border ${config.bg} border-gray-200 dark:border-gray-700`}
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <ServiceIcon size={18} className="text-gray-400" />
                    <span className="font-medium text-gray-900 dark:text-white">{check.name}</span>
                  </div>
                  <StatusIcon size={20} className={config.color} />
                </div>

                <div className="flex items-center gap-4 text-sm">
                  <span
                    className={`px-2 py-0.5 rounded-full text-xs font-medium ${config.bg} ${config.color}`}
                  >
                    {config.label}
                  </span>
                  {check.latency !== undefined && (
                    <span className="flex items-center gap-1 text-gray-500">
                      <Clock size={12} />
                      {check.latency}ms
                    </span>
                  )}
                </div>

                {check.message && (
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">{check.message}</p>
                )}

                {check.details && (
                  <div className="mt-3 pt-3 border-t border-gray-200 dark:border-gray-600">
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(check.details).map(([key, value]) => (
                        <div key={key}>
                          <span className="text-gray-500">{key}: </span>
                          <span className="font-medium text-gray-700 dark:text-gray-300">
                            {String(value)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* Endpoints */}
        <div className="mt-6 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-4">
            Endpoints de Health Check
          </h3>
          <div className="space-y-2 font-mono text-sm">
            <div className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
              <span className="text-green-600">GET</span>
              <span className="text-gray-600 dark:text-gray-400">/health/live</span>
              <span className="text-gray-400">→ Liveness probe (K8s)</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
              <span className="text-green-600">GET</span>
              <span className="text-gray-600 dark:text-gray-400">/health/ready</span>
              <span className="text-gray-400">→ Readiness probe (dependências)</span>
            </div>
            <div className="flex items-center gap-3 p-2 bg-gray-50 dark:bg-gray-700/50 rounded">
              <span className="text-green-600">GET</span>
              <span className="text-gray-600 dark:text-gray-400">/metrics</span>
              <span className="text-gray-400">→ Prometheus metrics</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
