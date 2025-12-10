import type { Meta, StoryObj } from '@storybook/react'
import { StatusBadge } from './StatusBadge'
import { Check, Clock, X, Info as InfoIcon } from 'lucide-react'

const meta: Meta<typeof StatusBadge> = {
  title: 'Components/StatusBadge',
  component: StatusBadge,
  tags: ['autodocs'],
  parameters: {
    layout: 'centered',
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['success', 'warning', 'error', 'info', 'pending'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md'],
    },
  },
}

export default meta
type Story = StoryObj<typeof StatusBadge>

export const Success: Story = {
  args: {
    variant: 'success',
    children: 'Concluído',
  },
}

export const Warning: Story = {
  args: {
    variant: 'warning',
    children: 'Pendente',
  },
}

export const Error: Story = {
  args: {
    variant: 'error',
    children: 'Falhou',
  },
}

export const InfoVariant: Story = {
  args: {
    variant: 'info',
    children: 'Em processamento',
  },
}

export const Pending: Story = {
  args: {
    variant: 'pending',
    children: 'Aguardando',
  },
}

export const WithIcon: Story = {
  args: {
    variant: 'success',
    icon: <Check size={12} />,
    children: 'Aprovado',
  },
}

export const SmallSize: Story = {
  args: {
    variant: 'info',
    size: 'sm',
    children: 'Small',
  },
}

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2">
      <StatusBadge variant="success" icon={<Check size={12} />}>
        Concluído
      </StatusBadge>
      <StatusBadge variant="warning" icon={<Clock size={12} />}>
        Pendente
      </StatusBadge>
      <StatusBadge variant="error" icon={<X size={12} />}>
        Erro
      </StatusBadge>
      <StatusBadge variant="info" icon={<InfoIcon size={12} />}>
        Info
      </StatusBadge>
      <StatusBadge variant="pending" icon={<Clock size={12} />}>
        Aguardando
      </StatusBadge>
    </div>
  ),
}
