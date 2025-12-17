import { useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@template/shared'
import { LogIn } from 'lucide-react'

export function LoginPage() {
  const { isAuthenticated, login, isLoading } = useAuth()
  const navigate = useNavigate()

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/', { replace: true })
    }
  }, [isAuthenticated, navigate])

  const handleLogin = () => {
    login()
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface-base">
      <div className="max-w-md w-full mx-4">
        <div className="bg-surface-elevated rounded-2xl shadow-xl p-8 border border-gray-200 dark:border-gray-700">
          {/* Logo */}
          <div className="text-center mb-8">
            <div className="w-16 h-16 rounded-2xl bg-brand-primary mx-auto flex items-center justify-center mb-4">
              <span className="text-white font-bold text-2xl">A</span>
            </div>
            <h1 className="text-2xl font-bold text-text-primary">AeroLab</h1>
            <p className="text-text-secondary mt-2">Faça login para continuar</p>
          </div>

          {/* Login Button */}
          <button
            onClick={handleLogin}
            disabled={isLoading}
            className="w-full flex items-center justify-center gap-3 px-6 py-3 bg-brand-primary text-white rounded-xl font-medium hover:bg-brand-secondary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                <span>Conectando...</span>
              </>
            ) : (
              <>
                <LogIn size={20} />
                <span>Entrar com SSO</span>
              </>
            )}
          </button>

          {/* Footer */}
          <p className="text-center text-text-muted text-sm mt-6">
            Autenticação via Keycloak/OIDC
          </p>
        </div>
      </div>
    </div>
  )
}
