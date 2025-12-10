import { useState } from 'react'
import {
  User,
  Download,
  Trash2,
  AlertTriangle,
  CheckCircle,
  Clock,
  FileDown,
  Mail,
} from 'lucide-react'
import { Button, StatusBadge } from '@template/design-system'
import { EmptyState } from '@template/design-system'
import { Alert } from '@template/design-system'

type RequestStatus = 'pending' | 'processing' | 'completed'

interface DataRequest {
  id: string
  type: 'export' | 'delete'
  status: RequestStatus
  createdAt: string
  completedAt?: string
}

const MOCK_REQUESTS: DataRequest[] = [
  {
    id: '1',
    type: 'export',
    status: 'completed',
    createdAt: '2024-02-15T10:00:00',
    completedAt: '2024-02-15T10:30:00',
  },
  { id: '2', type: 'export', status: 'processing', createdAt: '2024-03-10T14:00:00' },
]

const STATUS_CONFIG: Record<
  RequestStatus,
  { icon: typeof Clock; label: string; variant: 'warning' | 'info' | 'success' }
> = {
  pending: { icon: Clock, label: 'Pendente', variant: 'warning' },
  processing: { icon: Clock, label: 'Em processamento', variant: 'info' },
  completed: { icon: CheckCircle, label: 'Concluído', variant: 'success' },
}

export default function MyDataPage() {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [requests, setRequests] = useState<DataRequest[]>(MOCK_REQUESTS)

  const requestExport = () => {
    const newRequest: DataRequest = {
      id: Date.now().toString(),
      type: 'export',
      status: 'pending',
      createdAt: new Date().toISOString(),
    }
    setRequests([newRequest, ...requests])
  }

  const requestDelete = () => {
    // API call to request deletion
    setShowDeleteConfirm(false)
    alert('Solicitação de exclusão enviada. Você receberá um email de confirmação.')
  }

  return (
    <div className="min-h-screen bg-surface-base">
      {/* Header */}
      <div className="bg-surface-elevated border-b border-border-default">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-brand-accent/20 text-brand-secondary">
              <User size={28} />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-text-primary">Meus Dados</h1>
              <p className="text-text-secondary">Exportar ou excluir seus dados pessoais</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          {/* Export Data */}
          <div className="bg-surface-elevated rounded-xl border border-border-default p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-color-info/10 text-color-info">
                <Download size={24} />
              </div>
              <h2 className="text-lg font-semibold text-text-primary">Exportar Dados</h2>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Solicite uma cópia de todos os seus dados pessoais armazenados em nosso sistema. O
              arquivo será enviado para seu email em até 24 horas.
            </p>
            <Button
              variant="primary"
              fullWidth
              leftIcon={<FileDown size={18} />}
              onClick={requestExport}
            >
              Solicitar Exportação
            </Button>
          </div>

          {/* Delete Data */}
          <div className="bg-surface-elevated rounded-xl border border-border-default p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 rounded-lg bg-color-error/10 text-color-error">
                <Trash2 size={24} />
              </div>
              <h2 className="text-lg font-semibold text-text-primary">Excluir Dados</h2>
            </div>
            <p className="text-sm text-text-secondary mb-4">
              Solicite a exclusão permanente de todos os seus dados pessoais. Esta ação é
              irreversível e pode levar até 30 dias.
            </p>
            <Button
              variant="danger"
              fullWidth
              leftIcon={<Trash2 size={18} />}
              onClick={() => setShowDeleteConfirm(true)}
            >
              Solicitar Exclusão
            </Button>
          </div>
        </div>

        {/* Delete Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-surface-elevated rounded-xl max-w-md w-full p-6 animate-scale-in">
              <div className="flex items-center gap-3 mb-4 text-color-error">
                <AlertTriangle size={28} />
                <h3 className="text-xl font-bold">Confirmar Exclusão</h3>
              </div>
              <p className="text-text-secondary mb-4">
                Você está prestes a solicitar a exclusão permanente de todos os seus dados pessoais.
                Esta ação é <strong>irreversível</strong>.
              </p>
              <ul className="text-sm text-text-muted mb-6 space-y-1">
                <li>• Sua conta será desativada</li>
                <li>• Todos os dados serão removidos em até 30 dias</li>
                <li>• Você receberá uma confirmação por email</li>
              </ul>
              <div className="flex gap-3">
                <Button variant="outline" fullWidth onClick={() => setShowDeleteConfirm(false)}>
                  Cancelar
                </Button>
                <Button variant="danger" fullWidth onClick={requestDelete}>
                  Confirmar Exclusão
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Request History */}
        <div className="bg-surface-elevated rounded-xl border border-border-default p-6">
          <h2 className="text-lg font-semibold text-text-primary mb-4">
            Histórico de Solicitações
          </h2>

          {requests.length === 0 ? (
            <EmptyState
              title="Nenhuma solicitação realizada"
              description="Suas solicitações de exportação ou exclusão de dados aparecerão aqui."
              icon={<Clock size={24} />}
            />
          ) : (
            <div className="space-y-3">
              {requests.map(request => {
                const config = STATUS_CONFIG[request.status]
                const StatusIcon = config.icon
                return (
                  <div
                    key={request.id}
                    className="flex items-center justify-between p-4 bg-surface-muted rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      {request.type === 'export' ? (
                        <Download size={20} className="text-color-info" />
                      ) : (
                        <Trash2 size={20} className="text-color-error" />
                      )}
                      <div>
                        <p className="font-medium text-text-primary">
                          {request.type === 'export' ? 'Exportação de Dados' : 'Exclusão de Dados'}
                        </p>
                        <p className="text-sm text-text-muted">
                          Solicitado em {new Date(request.createdAt).toLocaleDateString('pt-BR')}
                          {request.completedAt &&
                            ` · Concluído em ${new Date(request.completedAt).toLocaleDateString('pt-BR')}`}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusIcon size={16} className="text-text-muted" />
                      <StatusBadge variant={config.variant} size="sm">
                        {config.label}
                      </StatusBadge>
                      {request.status === 'completed' && request.type === 'export' && (
                        <button
                          type="button"
                          className="ml-2 p-1.5 rounded hover:bg-surface-muted"
                          title="Download"
                        >
                          <FileDown size={16} className="text-brand-primary" />
                        </button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        {/* Contact */}
        <Alert
          variant="info"
          icon={<Mail size={20} />}
          description={
            <span>
              Dúvidas? Entre em contato:{' '}
              <a href="mailto:dpo@empresa.com.br" className="text-color-info hover:underline">
                dpo@empresa.com.br
              </a>
            </span>
          }
          className="mt-8"
        />
      </div>
    </div>
  )
}
