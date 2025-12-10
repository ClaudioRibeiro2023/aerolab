import type { Meta, StoryObj } from '@storybook/react'
import { PageHeader } from './PageHeader'
import { Database, Activity, History, Plus, RefreshCw } from 'lucide-react'
import { Button } from '../../components/Button'

const meta: Meta<typeof PageHeader> = {
  title: 'Layout/PageHeader',
  component: PageHeader,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof PageHeader>

export const Default: Story = {
  args: {
    title: 'Título da Página',
    description: 'Descrição curta explicando o propósito da página.',
  },
}

export const WithIcon: Story = {
  args: {
    title: 'ETL & Integração',
    description: 'Importação, tratamento e catálogo de dados',
    icon: <Database size={28} />,
  },
}

export const WithActions: Story = {
  args: {
    title: 'Métricas',
    description: 'Prometheus/metrics de API e jobs',
    icon: <Activity size={28} />,
    actions: (
      <Button variant="ghost" leftIcon={<RefreshCw size={18} />}>
        Atualizar
      </Button>
    ),
  },
}

export const WithMultipleActions: Story = {
  args: {
    title: 'Logs & Histórico',
    description: 'Rastreabilidade e reprocessamento',
    icon: <History size={28} />,
    actions: (
      <div className="flex items-center gap-2">
        <Button variant="ghost" leftIcon={<RefreshCw size={18} />}>
          Atualizar
        </Button>
        <Button variant="primary" leftIcon={<Plus size={18} />}>
          Novo
        </Button>
      </div>
    ),
  },
}

export const MinimalHeader: Story = {
  args: {
    title: 'Página Simples',
  },
}
