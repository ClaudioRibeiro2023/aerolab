import type { Meta, StoryObj } from '@storybook/react'
import { EmptyState } from './EmptyState'
import { FileX, Search, Inbox, Clock, Plus } from 'lucide-react'
import { Button } from '../../components/Button'

const meta: Meta<typeof EmptyState> = {
  title: 'Layout/EmptyState',
  component: EmptyState,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
}

export default meta
type Story = StoryObj<typeof EmptyState>

export const Default: Story = {
  args: {
    title: 'Nenhum item encontrado',
    description: 'Não há itens para exibir no momento.',
  },
}

export const WithIcon: Story = {
  args: {
    title: 'Nenhum resultado',
    description: 'Sua busca não retornou nenhum resultado. Tente outros termos.',
    icon: <Search size={24} />,
  },
}

export const WithAction: Story = {
  args: {
    title: 'Caixa de entrada vazia',
    description: 'Você não tem novas mensagens.',
    icon: <Inbox size={24} />,
    actions: (
      <Button variant="primary" leftIcon={<Plus size={18} />}>
        Nova Mensagem
      </Button>
    ),
  },
}

export const NoData: Story = {
  args: {
    title: 'Sem dados',
    description: 'Comece adicionando seu primeiro registro.',
    icon: <FileX size={24} />,
    actions: (
      <Button variant="primary" leftIcon={<Plus size={18} />}>
        Adicionar
      </Button>
    ),
  },
}

export const PendingRequests: Story = {
  args: {
    title: 'Nenhuma solicitação realizada',
    description: 'Suas solicitações de exportação ou exclusão de dados aparecerão aqui.',
    icon: <Clock size={24} />,
  },
}

export const WithMultipleActions: Story = {
  args: {
    title: 'Nenhum projeto encontrado',
    description: 'Você ainda não tem projetos. Comece criando um novo ou importe de um template.',
    icon: <FileX size={24} />,
    actions: (
      <div className="flex gap-2">
        <Button variant="secondary">Importar</Button>
        <Button variant="primary" leftIcon={<Plus size={18} />}>
          Criar Projeto
        </Button>
      </div>
    ),
  },
}
