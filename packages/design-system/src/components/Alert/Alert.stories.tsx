import type { Meta, StoryObj } from '@storybook/react'
import { Alert } from './Alert'
import { Info, CheckCircle, AlertTriangle, XCircle, Mail } from 'lucide-react'

const meta: Meta<typeof Alert> = {
  title: 'Components/Alert',
  component: Alert,
  tags: ['autodocs'],
  parameters: {
    layout: 'padded',
  },
  argTypes: {
    variant: {
      control: 'select',
      options: ['info', 'success', 'warning', 'error'],
    },
  },
}

export default meta
type Story = StoryObj<typeof Alert>

export const InfoAlert: Story = {
  args: {
    variant: 'info',
    title: 'Informação',
    description: 'Esta é uma mensagem informativa para o usuário.',
    icon: <Info size={20} />,
  },
}

export const SuccessAlert: Story = {
  args: {
    variant: 'success',
    title: 'Sucesso!',
    description: 'A operação foi concluída com sucesso.',
    icon: <CheckCircle size={20} />,
  },
}

export const WarningAlert: Story = {
  args: {
    variant: 'warning',
    title: 'Atenção',
    description: 'Esta ação pode ter consequências. Por favor, revise antes de continuar.',
    icon: <AlertTriangle size={20} />,
  },
}

export const ErrorAlert: Story = {
  args: {
    variant: 'error',
    title: 'Erro',
    description: 'Ocorreu um erro ao processar sua solicitação. Tente novamente.',
    icon: <XCircle size={20} />,
  },
}

export const WithoutTitle: Story = {
  args: {
    variant: 'info',
    description: 'Alerta simples sem título, apenas com descrição.',
    icon: <Info size={20} />,
  },
}

export const WithCustomContent: Story = {
  args: {
    variant: 'info',
    title: 'Dúvidas?',
    icon: <Mail size={20} />,
    description: (
      <span>
        Entre em contato:{' '}
        <a href="mailto:suporte@empresa.com" className="text-color-info hover:underline">
          suporte@empresa.com
        </a>
      </span>
    ),
  },
}

export const AllVariants: Story = {
  render: () => (
    <div className="space-y-4">
      <Alert
        variant="info"
        title="Informação"
        description="Alerta informativo."
        icon={<Info size={20} />}
      />
      <Alert
        variant="success"
        title="Sucesso"
        description="Alerta de sucesso."
        icon={<CheckCircle size={20} />}
      />
      <Alert
        variant="warning"
        title="Atenção"
        description="Alerta de aviso."
        icon={<AlertTriangle size={20} />}
      />
      <Alert
        variant="error"
        title="Erro"
        description="Alerta de erro."
        icon={<XCircle size={20} />}
      />
    </div>
  ),
}
