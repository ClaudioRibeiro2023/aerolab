import type { UserManagerSettings} from 'oidc-client-ts';
import { WebStorageStateStore } from 'oidc-client-ts'

type ImportMetaEnvAuth = {
  VITE_KEYCLOAK_URL?: string
  VITE_KEYCLOAK_REALM?: string
  VITE_KEYCLOAK_CLIENT_ID?: string
  VITE_APP_URL?: string
}

const env: ImportMetaEnvAuth =
  typeof import.meta !== 'undefined'
    ? ((import.meta as unknown as { env?: ImportMetaEnvAuth }).env ?? {})
    : {}

const KEYCLOAK_URL = env.VITE_KEYCLOAK_URL || 'http://localhost:8080'
const KEYCLOAK_REALM = env.VITE_KEYCLOAK_REALM || 'template'
const KEYCLOAK_CLIENT_ID = env.VITE_KEYCLOAK_CLIENT_ID || 'template-web'
const APP_URL = env.VITE_APP_URL || (typeof window !== 'undefined' ? window.location.origin : 'http://localhost:13000')

export const oidcConfig: UserManagerSettings = {
  authority: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`,
  client_id: KEYCLOAK_CLIENT_ID,
  redirect_uri: `${APP_URL}/auth/callback`,
  post_logout_redirect_uri: `${APP_URL}/`,
  silent_redirect_uri: `${APP_URL}/auth/silent-renew`,
  response_type: 'code',
  scope: 'openid profile email roles',
  automaticSilentRenew: true,
  loadUserInfo: true,
  monitorSession: true,
  revokeTokensOnSignout: true,
  filterProtocolClaims: true,
  userStore: typeof window !== 'undefined' ? new WebStorageStateStore({ store: window.localStorage }) : undefined,
  stateStore: typeof window !== 'undefined' ? new WebStorageStateStore({ store: window.sessionStorage }) : undefined,
  // No client_secret = PKCE will be used automatically
  metadata: {
    issuer: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}`,
    authorization_endpoint: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/auth`,
    token_endpoint: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/token`,
    userinfo_endpoint: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/userinfo`,
    end_session_endpoint: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/logout`,
    jwks_uri: `${KEYCLOAK_URL}/realms/${KEYCLOAK_REALM}/protocol/openid-connect/certs`,
  }
}
