import type { ReactNode } from 'react'
import { createContext, useContext, useEffect, useState, useCallback } from 'react'
import type { User } from 'oidc-client-ts'
import { UserManager } from 'oidc-client-ts'
import type { UserRole, AuthUser, AuthContextType } from './types'
import { ALL_ROLES } from './types'
import { oidcConfig } from './oidcConfig'
import { authLogger } from '../utils/logger'

type ImportMetaEnvAuth = {
  VITE_DEMO_MODE?: string
  MODE?: string
}

const authEnv: ImportMetaEnvAuth =
  typeof import.meta !== 'undefined'
    ? ((import.meta as unknown as { env?: ImportMetaEnvAuth }).env ?? {})
    : {}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

let userManager: UserManager | null = null

export const getUserManager = (): UserManager => {
  if (!userManager) {
    userManager = new UserManager(oidcConfig)
  }
  return userManager
}

// ============================================================================
// Helper: Parse roles from OIDC User
// ============================================================================
function parseRolesFromOidcUser(oidcUser: User): UserRole[] {
  const roles: UserRole[] = []

  // Get roles from profile
  const profile = oidcUser.profile as {
    realm_access?: { roles?: string[] }
    resource_access?: Record<string, { roles?: string[] }>
  }
  const realmRoles = profile?.realm_access?.roles || []
  const clientRoles = profile?.resource_access?.[oidcConfig.client_id]?.roles || []

  // Also try to decode from access_token
  let tokenRoles: string[] = []
  try {
    const token = oidcUser.access_token
    if (token) {
      const payloadPart = token.split('.')[1]
      if (payloadPart) {
        const json = JSON.parse(atob(payloadPart.replace(/-/g, '+').replace(/_/g, '/')))
        const ra = json?.realm_access?.roles || []
        const rc = json?.resource_access?.[oidcConfig.client_id]?.roles || []
        tokenRoles = [...ra, ...rc]
      }
    }
  } catch (e) {
    authLogger.error('Error decoding token', { error: String(e) })
  }

  const allRoles = [...realmRoles, ...clientRoles, ...tokenRoles]
  const validRoles: UserRole[] = ['ADMIN', 'GESTOR', 'OPERADOR', 'VIEWER']

  for (const role of allRoles) {
    const upperRole = String(role).toUpperCase() as UserRole
    if (validRoles.includes(upperRole) && !roles.includes(upperRole)) {
      roles.push(upperRole)
    }
  }

  return roles.length > 0 ? roles : ['VIEWER']
}

// ============================================================================
// Helper: Create AuthUser from OIDC User
// ============================================================================
function createAuthUser(oidcUser: User): AuthUser {
  return {
    id: oidcUser.profile.sub,
    email: oidcUser.profile.email || '',
    name: oidcUser.profile.name || oidcUser.profile.preferred_username || '',
    roles: parseRolesFromOidcUser(oidcUser),
    avatar: undefined,
  }
}

// ============================================================================
// Real Auth Provider (Production with Keycloak/OIDC)
// ============================================================================
function RealAuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [oidcUser, setOidcUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const manager = getUserManager()

    manager
      .getUser()
      .then(loadedUser => {
        if (loadedUser && !loadedUser.expired) {
          setOidcUser(loadedUser)
          setUser(createAuthUser(loadedUser))
          authLogger.info('User loaded', {
            email: loadedUser.profile.email || loadedUser.profile.preferred_username,
          })
        }
        setIsLoading(false)
      })
      .catch((error: unknown) => {
        authLogger.error('Failed to load user', { error: String(error) })
        setIsLoading(false)
      })

    const handleUserLoaded = (loadedUser: User) => {
      setOidcUser(loadedUser)
      setUser(createAuthUser(loadedUser))
      authLogger.info('Token renewed')
    }
    const handleUserUnloaded = () => {
      setOidcUser(null)
      setUser(null)
      authLogger.info('User logged out')
    }
    const handleAccessTokenExpiring = () => {
      authLogger.warn('Token expiring soon')
    }
    const handleAccessTokenExpired = () => {
      authLogger.info('Token expired')
      setOidcUser(null)
      setUser(null)
    }
    const handleSilentRenewError = (error: Error) => {
      authLogger.error('Silent renew error', { error: error.message })
    }

    manager.events.addUserLoaded(handleUserLoaded)
    manager.events.addUserUnloaded(handleUserUnloaded)
    manager.events.addAccessTokenExpiring(handleAccessTokenExpiring)
    manager.events.addAccessTokenExpired(handleAccessTokenExpired)
    manager.events.addSilentRenewError(handleSilentRenewError)

    return () => {
      manager.events.removeUserLoaded(handleUserLoaded)
      manager.events.removeUserUnloaded(handleUserUnloaded)
      manager.events.removeAccessTokenExpiring(handleAccessTokenExpiring)
      manager.events.removeAccessTokenExpired(handleAccessTokenExpired)
      manager.events.removeSilentRenewError(handleSilentRenewError)
    }
  }, [])

  const login = useCallback(async () => {
    try {
      await getUserManager().signinRedirect()
    } catch (error) {
      authLogger.error('Login failed', { error: String(error) })
      throw error
    }
  }, [])

  const logout = useCallback(async () => {
    const manager = getUserManager()
    let currentUser: User | null = oidcUser

    try {
      if (!currentUser || !currentUser.id_token) {
        currentUser = await manager.getUser()
      }
      if (!currentUser || !currentUser.id_token) {
        currentUser = await manager.signinSilent()
      }
    } catch {
      /* no-op */
    }

    const postLogout = oidcConfig.post_logout_redirect_uri || `${window.location.origin}/`
    const endSession = oidcConfig.metadata?.end_session_endpoint

    if (endSession) {
      const params = new URLSearchParams()
      params.set('post_logout_redirect_uri', postLogout)
      if (currentUser?.id_token) {
        params.set('id_token_hint', currentUser.id_token)
      } else {
        params.set('client_id', oidcConfig.client_id)
      }
      try {
        await manager.removeUser()
      } catch {
        /* no-op */
      }
      window.location.href = `${endSession}?${params.toString()}`
      return
    }

    try {
      await manager.removeUser()
    } catch {
      /* no-op */
    }
    window.location.href = postLogout
  }, [oidcUser])

  const hasRole = useCallback(
    (role: UserRole | UserRole[]): boolean => {
      if (!user) return false
      const rolesToCheck = Array.isArray(role) ? role : [role]
      return rolesToCheck.every(r => user.roles.includes(r))
    },
    [user]
  )

  const hasAnyRole = useCallback(
    (roles: UserRole[]): boolean => {
      if (!user) return false
      return roles.some(r => user.roles.includes(r))
    },
    [user]
  )

  const getAccessToken = useCallback(async (): Promise<string | null> => {
    try {
      return (await getUserManager().getUser())?.access_token || null
    } catch (error) {
      authLogger.error('Failed to get access token', { error: String(error) })
      return null
    }
  }, [])

  const value: AuthContextType = {
    user,
    isAuthenticated: !!user,
    isLoading,
    login,
    logout,
    hasRole,
    hasAnyRole,
    getAccessToken,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ============================================================================
// Bypass Auth Provider (Demo/E2E mode)
// ============================================================================
function BypassAuthProvider({ children }: { children: ReactNode }) {
  const [roles, setRoles] = useState<UserRole[]>(ALL_ROLES)
  const MODE = authEnv.MODE

  useEffect(() => {
    if (MODE !== 'e2e') return

    // Check for roles in query params or localStorage
    const params = new URLSearchParams(window.location.search)
    const rolesParam = params.get('e2e-roles') || params.get('roles')
    const storedRoles = localStorage.getItem('e2e-roles')

    const rawRoles = rolesParam || storedRoles
    if (rawRoles) {
      try {
        // Try JSON parse first
        const parsed = JSON.parse(rawRoles)
        if (Array.isArray(parsed)) {
          const validRoles = parsed.filter(r => ALL_ROLES.includes(r as UserRole)) as UserRole[]
          if (validRoles.length > 0) {
            setRoles(validRoles)
            localStorage.setItem('e2e-roles', JSON.stringify(validRoles))
          }
        }
      } catch {
        // Fallback to CSV
        const csvRoles = rawRoles.split(',').map(r => r.trim().toUpperCase())
        const validRoles = csvRoles.filter(r => ALL_ROLES.includes(r as UserRole)) as UserRole[]
        if (validRoles.length > 0) {
          setRoles(validRoles)
          localStorage.setItem('e2e-roles', JSON.stringify(validRoles))
        }
      }
    }
  }, [MODE])

  const mockUser: AuthUser = {
    id: 'demo-user-001',
    email: 'demo@template.com',
    name: 'Demo User',
    roles,
    avatar: undefined,
  }

  const hasRole = useCallback(
    (role: UserRole | UserRole[]): boolean => {
      const rolesToCheck = Array.isArray(role) ? role : [role]
      return rolesToCheck.every(r => roles.includes(r))
    },
    [roles]
  )

  const hasAnyRole = useCallback(
    (rolesToCheck: UserRole[]): boolean => {
      return rolesToCheck.some(r => roles.includes(r))
    },
    [roles]
  )

  const value: AuthContextType = {
    user: mockUser,
    isAuthenticated: true,
    isLoading: false,
    login: async () => {},
    logout: async () => {
      window.location.href = '/login'
    },
    hasRole,
    hasAnyRole,
    getAccessToken: async () => 'demo-token',
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// ============================================================================
// Exports
// ============================================================================
export function AuthProvider({ children }: { children: ReactNode }) {
  const DEMO_MODE = authEnv.VITE_DEMO_MODE === 'true'
  const MODE = authEnv.MODE
  const BYPASS = DEMO_MODE || MODE === 'e2e'

  return BYPASS ? (
    <BypassAuthProvider>{children}</BypassAuthProvider>
  ) : (
    <RealAuthProvider>{children}</RealAuthProvider>
  )
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
