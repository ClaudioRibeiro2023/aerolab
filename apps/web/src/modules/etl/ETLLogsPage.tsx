import { useState, useMemo } from 'react'
import {
  History,
  Search,
  Filter,
  Download,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
} from 'lucide-react'
import { Button, PageHeader } from '@template/design-system'
import type { ImportLogEntry, ImportStatus } from './types'

interface LogEntry {
  id: string
  jobId: string
  sourceName: string
  status: ImportStatus
  startedAt: string
  completedAt?: string
  duration?: string
  recordsTotal: number
  recordsSuccess: number
  recordsError: number
  logs: ImportLogEntry[]
}

// Mock data
const MOCK_LOGS: LogEntry[] = [
  {
    id: '1',
    jobId: 'job-001',
    sourceName: 'Planilha Vendas Q1',
    status: 'completed',
    startedAt: '2024-03-12T10:00:00',
    completedAt: '2024-03-12T10:05:30',
    duration: '5m 30s',
    recordsTotal: 5000,
    recordsSuccess: 4985,
    recordsError: 15,
    logs: [
      { timestamp: '2024-03-12T10:00:00', level: 'info', message: 'Iniciando importação' },
      { timestamp: '2024-03-12T10:01:00', level: 'info', message: 'Processando 5000 registros' },
      {
        timestamp: '2024-03-12T10:04:00',
        level: 'warning',
        message: '15 registros com erros de validação',
      },
      {
        timestamp: '2024-03-12T10:05:30',
        level: 'info',
        message: 'Importação concluída com sucesso',
      },
    ],
  },
  {
    id: '2',
    jobId: 'job-002',
    sourceName: 'API CRM',
    status: 'completed',
    startedAt: '2024-03-12T09:00:00',
    completedAt: '2024-03-12T09:15:00',
    duration: '15m',
    recordsTotal: 10000,
    recordsSuccess: 10000,
    recordsError: 0,
    logs: [
      { timestamp: '2024-03-12T09:00:00', level: 'info', message: 'Conectando à API' },
      { timestamp: '2024-03-12T09:00:05', level: 'info', message: 'Conexão estabelecida' },
      { timestamp: '2024-03-12T09:15:00', level: 'info', message: 'Sincronização completa' },
    ],
  },
  {
    id: '3',
    jobId: 'job-003',
    sourceName: 'Eventos JSON',
    status: 'failed',
    startedAt: '2024-03-12T08:00:00',
    completedAt: '2024-03-12T08:02:15',
    duration: '2m 15s',
    recordsTotal: 2000,
    recordsSuccess: 600,
    recordsError: 1400,
    logs: [
      { timestamp: '2024-03-12T08:00:00', level: 'info', message: 'Iniciando parse do JSON' },
      {
        timestamp: '2024-03-12T08:01:00',
        level: 'warning',
        message: 'Formato inconsistente detectado',
      },
      {
        timestamp: '2024-03-12T08:02:15',
        level: 'error',
        message: 'Erro fatal: JSON malformado na linha 601',
      },
    ],
  },
  {
    id: '4',
    jobId: 'job-004',
    sourceName: 'Shapefile Municípios',
    status: 'completed',
    startedAt: '2024-03-11T14:00:00',
    completedAt: '2024-03-11T14:10:00',
    duration: '10m',
    recordsTotal: 141,
    recordsSuccess: 141,
    recordsError: 0,
    logs: [
      { timestamp: '2024-03-11T14:00:00', level: 'info', message: 'Lendo shapefile' },
      {
        timestamp: '2024-03-11T14:05:00',
        level: 'info',
        message: 'Convertendo coordenadas para EPSG:4326',
      },
      {
        timestamp: '2024-03-11T14:10:00',
        level: 'info',
        message: 'Importação geoespacial concluída',
      },
    ],
  },
]

const STATUS_CONFIG: Record<
  ImportStatus,
  { icon: typeof CheckCircle; color: string; label: string }
> = {
  completed: { icon: CheckCircle, color: 'text-green-500', label: 'Concluído' },
  failed: { icon: XCircle, color: 'text-red-500', label: 'Falha' },
  running: { icon: Clock, color: 'text-blue-500', label: 'Em execução' },
  pending: { icon: Clock, color: 'text-gray-500', label: 'Pendente' },
  cancelled: { icon: XCircle, color: 'text-gray-400', label: 'Cancelado' },
}

const LOG_LEVEL_COLORS = {
  info: 'text-blue-600 bg-blue-50 dark:bg-blue-900/20',
  warning: 'text-yellow-600 bg-yellow-50 dark:bg-yellow-900/20',
  error: 'text-red-600 bg-red-50 dark:bg-red-900/20',
}

export default function ETLLogsPage() {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<ImportStatus | 'all'>('all')
  const [selectedLog, setSelectedLog] = useState<LogEntry | null>(null)

  const filteredLogs = useMemo(() => {
    return MOCK_LOGS.filter(log => {
      if (statusFilter !== 'all' && log.status !== statusFilter) return false
      if (search && !log.sourceName.toLowerCase().includes(search.toLowerCase())) return false
      return true
    })
  }, [search, statusFilter])

  return (
    <div className="min-h-screen bg-surface-base">
      {/* Header */}
      <div className="bg-surface-elevated border-b border-border-default">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <PageHeader
            title="Logs & Histórico"
            description="Rastreabilidade e reprocessamento"
            icon={<History size={28} />}
            actions={
              <div className="flex items-center gap-2">
                <Button variant="ghost" leftIcon={<Download size={18} />}>
                  Exportar
                </Button>
                <Button variant="ghost" leftIcon={<RefreshCw size={18} />}>
                  Atualizar
                </Button>
              </div>
            }
          />
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-6 p-4 bg-surface-elevated rounded-lg border border-border-default">
          <div className="relative flex-1 min-w-[200px]">
            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" />
            <input
              type="text"
              placeholder="Buscar por fonte..."
              value={search}
              onChange={e => setSearch(e.target.value)}
              className="form-input pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <Filter size={16} className="text-gray-400" />
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value as ImportStatus | 'all')}
              aria-label="Filtrar por status"
              className="form-input form-select"
            >
              <option value="all">Todos os status</option>
              <option value="completed">Concluído</option>
              <option value="failed">Falha</option>
              <option value="running">Em execução</option>
            </select>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Logs List */}
          <div className="space-y-3">
            {filteredLogs.map(log => {
              const config = STATUS_CONFIG[log.status]
              const StatusIcon = config.icon
              return (
                <button
                  key={log.id}
                  type="button"
                  onClick={() => setSelectedLog(log)}
                  className={`w-full p-4 rounded-lg border text-left transition-all ${
                    selectedLog?.id === log.id
                      ? 'border-primary bg-primary/5'
                      : 'border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 hover:border-primary/50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900 dark:text-white">
                      {log.sourceName}
                    </span>
                    <div className={`flex items-center gap-1 ${config.color}`}>
                      <StatusIcon size={16} />
                      <span className="text-sm">{config.label}</span>
                    </div>
                  </div>
                  <div className="text-xs text-gray-500 mb-2">
                    Job: {log.jobId} • {new Date(log.startedAt).toLocaleString('pt-BR')}
                  </div>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-gray-500">
                      Total: {log.recordsTotal.toLocaleString()}
                    </span>
                    <span className="text-green-600">✓ {log.recordsSuccess.toLocaleString()}</span>
                    {log.recordsError > 0 && (
                      <span className="text-red-600">✗ {log.recordsError.toLocaleString()}</span>
                    )}
                    {log.duration && <span className="text-gray-400">⏱ {log.duration}</span>}
                  </div>
                </button>
              )
            })}
            {filteredLogs.length === 0 && (
              <div className="text-center py-12 text-gray-500">
                <History size={48} className="mx-auto mb-3 opacity-50" />
                <p>Nenhum log encontrado</p>
              </div>
            )}
          </div>

          {/* Log Detail */}
          <div>
            {selectedLog ? (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-6 sticky top-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-bold text-gray-900 dark:text-white">
                    {selectedLog.sourceName}
                  </h2>
                  <button
                    type="button"
                    className="flex items-center gap-1 text-sm text-primary hover:underline"
                  >
                    <RefreshCw size={14} />
                    Reprocessar
                  </button>
                </div>

                {/* Stats */}
                <div className="grid grid-cols-3 gap-3 mb-4">
                  <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded text-center">
                    <div className="text-xs text-gray-500">Total</div>
                    <div className="font-bold text-gray-900 dark:text-white">
                      {selectedLog.recordsTotal.toLocaleString()}
                    </div>
                  </div>
                  <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded text-center">
                    <div className="text-xs text-green-600">Sucesso</div>
                    <div className="font-bold text-green-700">
                      {selectedLog.recordsSuccess.toLocaleString()}
                    </div>
                  </div>
                  <div className="p-3 bg-red-50 dark:bg-red-900/20 rounded text-center">
                    <div className="text-xs text-red-600">Erros</div>
                    <div className="font-bold text-red-700">
                      {selectedLog.recordsError.toLocaleString()}
                    </div>
                  </div>
                </div>

                {/* Timeline */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">
                    Timeline
                  </h3>
                  <div className="space-y-2 max-h-[400px] overflow-y-auto">
                    {selectedLog.logs.map((entry, idx) => (
                      <div
                        key={idx}
                        className={`flex gap-3 p-2 rounded ${LOG_LEVEL_COLORS[entry.level]}`}
                      >
                        <span className="text-xs font-mono whitespace-nowrap opacity-75">
                          {new Date(entry.timestamp).toLocaleTimeString('pt-BR')}
                        </span>
                        <span className="text-xs uppercase font-medium w-16">{entry.level}</span>
                        <span className="text-sm flex-1">{entry.message}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg border p-12 text-center sticky top-6">
                <History size={48} className="mx-auto mb-4 text-gray-300" />
                <p className="text-gray-500">Selecione um log para ver detalhes</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
