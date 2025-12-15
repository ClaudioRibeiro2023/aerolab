/**
 * Analytics Dashboard Component
 *
 * Displays metrics, engagement data, and trends.
 */

import React, { useState } from 'react'
import {
  TrendingUp,
  TrendingDown,
  Users,
  Clock,
  MousePointer,
  Eye,
  Activity,
  Calendar,
  Download,
  Filter,
} from 'lucide-react'

// ============================================================================
// Types
// ============================================================================

interface MetricCard {
  id: string
  title: string
  value: string | number
  change: number
  changeLabel: string
  icon: React.ReactNode
  color: 'blue' | 'green' | 'purple' | 'orange'
}

interface ChartData {
  label: string
  value: number
  previousValue?: number
}

interface TimeRange {
  label: string
  value: '7d' | '30d' | '90d' | 'custom'
}

// ============================================================================
// Mock Data (replace with real API calls)
// ============================================================================

const MOCK_METRICS: MetricCard[] = [
  {
    id: 'page_views',
    title: 'Visualizações',
    value: '45.2K',
    change: 12.5,
    changeLabel: 'vs período anterior',
    icon: <Eye className="w-5 h-5" />,
    color: 'blue',
  },
  {
    id: 'unique_users',
    title: 'Usuários Únicos',
    value: '8.4K',
    change: 8.2,
    changeLabel: 'vs período anterior',
    icon: <Users className="w-5 h-5" />,
    color: 'green',
  },
  {
    id: 'avg_session',
    title: 'Sessão Média',
    value: '4m 32s',
    change: -2.1,
    changeLabel: 'vs período anterior',
    icon: <Clock className="w-5 h-5" />,
    color: 'purple',
  },
  {
    id: 'interactions',
    title: 'Interações',
    value: '12.8K',
    change: 15.7,
    changeLabel: 'vs período anterior',
    icon: <MousePointer className="w-5 h-5" />,
    color: 'orange',
  },
]

const MOCK_CHART_DATA: ChartData[] = [
  { label: 'Seg', value: 4200, previousValue: 3800 },
  { label: 'Ter', value: 5100, previousValue: 4500 },
  { label: 'Qua', value: 4800, previousValue: 4200 },
  { label: 'Qui', value: 6200, previousValue: 5800 },
  { label: 'Sex', value: 7500, previousValue: 6900 },
  { label: 'Sáb', value: 3200, previousValue: 2800 },
  { label: 'Dom', value: 2800, previousValue: 2400 },
]

const MOCK_TOP_PAGES = [
  { path: '/dashboard', views: 12450, percentage: 28 },
  { path: '/etl', views: 8320, percentage: 19 },
  { path: '/config', views: 6180, percentage: 14 },
  { path: '/users', views: 4920, percentage: 11 },
  { path: '/docs', views: 3650, percentage: 8 },
]

const TIME_RANGES: TimeRange[] = [
  { label: 'Últimos 7 dias', value: '7d' },
  { label: 'Últimos 30 dias', value: '30d' },
  { label: 'Últimos 90 dias', value: '90d' },
  { label: 'Personalizado', value: 'custom' },
]

// ============================================================================
// Sub-Components
// ============================================================================

interface MetricCardProps {
  metric: MetricCard
}

function MetricCardComponent({ metric }: MetricCardProps) {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600 dark:bg-blue-900/20 dark:text-blue-400',
    green: 'bg-green-50 text-green-600 dark:bg-green-900/20 dark:text-green-400',
    purple: 'bg-purple-50 text-purple-600 dark:bg-purple-900/20 dark:text-purple-400',
    orange: 'bg-orange-50 text-orange-600 dark:bg-orange-900/20 dark:text-orange-400',
  }

  const isPositive = metric.change >= 0

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-4">
        <div className={`p-2 rounded-lg ${colorClasses[metric.color]}`}>{metric.icon}</div>
        <div
          className={`flex items-center text-sm ${isPositive ? 'text-green-600' : 'text-red-600'}`}
        >
          {isPositive ? (
            <TrendingUp className="w-4 h-4 mr-1" />
          ) : (
            <TrendingDown className="w-4 h-4 mr-1" />
          )}
          {Math.abs(metric.change)}%
        </div>
      </div>
      <h3 className="text-2xl font-bold text-gray-900 dark:text-white">{metric.value}</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{metric.title}</p>
      <p className="text-xs text-gray-400 dark:text-gray-500 mt-2">{metric.changeLabel}</p>
    </div>
  )
}

interface SimpleBarChartProps {
  data: ChartData[]
  height?: number
}

function SimpleBarChart({ data, height = 200 }: SimpleBarChartProps) {
  const maxValue = Math.max(...data.map(d => Math.max(d.value, d.previousValue || 0)))

  return (
    <div className="flex items-end justify-between gap-2" style={{ height }}>
      {data.map((item, index) => {
        const currentHeight = (item.value / maxValue) * 100
        const previousHeight = ((item.previousValue || 0) / maxValue) * 100

        return (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full flex items-end justify-center gap-1"
              style={{ height: height - 24 }}
            >
              {item.previousValue && (
                <div
                  className="w-3 bg-gray-200 dark:bg-gray-700 rounded-t transition-all"
                  style={{ height: `${previousHeight}%` }}
                  title={`Anterior: ${item.previousValue}`}
                />
              )}
              <div
                className="w-3 bg-blue-500 rounded-t transition-all"
                style={{ height: `${currentHeight}%` }}
                title={`Atual: ${item.value}`}
              />
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">{item.label}</span>
          </div>
        )
      })}
    </div>
  )
}

// ============================================================================
// Main Component
// ============================================================================

export function AnalyticsDashboard() {
  const [timeRange, setTimeRange] = useState<TimeRange['value']>('7d')
  const [_isLoading, _setIsLoading] = useState(false)

  const handleExport = () => {
    // TODO: Implement export functionality
    alert('Export functionality coming soon!')
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            Métricas de uso e engajamento da plataforma
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Time Range Selector */}
          <div className="relative">
            <select
              value={timeRange}
              onChange={e => setTimeRange(e.target.value as TimeRange['value'])}
              aria-label="Selecionar período de tempo"
              className="appearance-none bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg px-4 py-2 pr-8 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {TIME_RANGES.map(range => (
                <option key={range.value} value={range.value}>
                  {range.label}
                </option>
              ))}
            </select>
            <Calendar className="absolute right-2 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400 pointer-events-none" />
          </div>

          {/* Export Button */}
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-4 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg text-sm font-medium transition-colors"
          >
            <Download className="w-4 h-4" />
            Exportar
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {MOCK_METRICS.map(metric => (
          <MetricCardComponent key={metric.id} metric={metric} />
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Chart */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                Visualizações por Dia
              </h2>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                Comparativo com período anterior
              </p>
            </div>
            <div className="flex items-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-blue-500 rounded" />
                <span className="text-gray-600 dark:text-gray-400">Atual</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 bg-gray-200 dark:bg-gray-700 rounded" />
                <span className="text-gray-600 dark:text-gray-400">Anterior</span>
              </div>
            </div>
          </div>
          <SimpleBarChart data={MOCK_CHART_DATA} height={250} />
        </div>

        {/* Top Pages */}
        <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
            Páginas Mais Visitadas
          </h2>
          <div className="space-y-4">
            {MOCK_TOP_PAGES.map((page, index) => (
              <div key={page.path} className="flex items-center gap-3">
                <span className="w-6 h-6 flex items-center justify-center bg-gray-100 dark:bg-gray-700 rounded text-xs font-medium text-gray-600 dark:text-gray-400">
                  {index + 1}
                </span>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                    {page.path}
                  </p>
                  <div className="mt-1 h-1.5 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${page.percentage}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm text-gray-500 dark:text-gray-400">
                  {page.views.toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Activity Feed */}
      <div className="bg-white dark:bg-gray-800 rounded-lg p-6 shadow-sm border border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Atividade Recente</h2>
          <button className="text-sm text-blue-600 hover:text-blue-700 font-medium">
            Ver tudo
          </button>
        </div>
        <div className="space-y-4">
          {[
            { action: 'Novo usuário registrado', time: '2 min atrás', icon: Users },
            { action: 'ETL executado com sucesso', time: '15 min atrás', icon: Activity },
            { action: 'Configuração atualizada', time: '1 hora atrás', icon: Filter },
            { action: 'Relatório exportado', time: '2 horas atrás', icon: Download },
          ].map((activity, index) => (
            <div key={index} className="flex items-center gap-3 py-2">
              <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded-lg">
                <activity.icon className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </div>
              <div className="flex-1">
                <p className="text-sm text-gray-900 dark:text-white">{activity.action}</p>
                <p className="text-xs text-gray-500 dark:text-gray-400">{activity.time}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

export default AnalyticsDashboard
