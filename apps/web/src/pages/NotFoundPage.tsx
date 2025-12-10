import { Link } from 'react-router-dom'
import { Home, ArrowLeft } from 'lucide-react'
import { Button } from '@template/design-system'

export function NotFoundPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-base">
      <div className="text-center">
        <h1 className="text-9xl font-bold text-brand-primary/20">404</h1>
        <h2 className="text-2xl font-semibold text-text-primary mt-4">Página não encontrada</h2>
        <p className="text-text-secondary mt-2 mb-8">
          A página que você procura não existe ou foi movida.
        </p>
        <div className="flex items-center justify-center gap-4">
          <Button variant="outline" leftIcon={<ArrowLeft size={18} />} onClick={() => window.history.back()}>
            Voltar
          </Button>
          <Link to="/">
            <Button variant="primary" leftIcon={<Home size={18} />}>
              Início
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
