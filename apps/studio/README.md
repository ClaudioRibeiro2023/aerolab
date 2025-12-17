# Agno Agents UI (Frontend)

Frontend Next.js para o AgentOS.

## Requisitos
- Node 20+
- Backend AgentOS rodando e com CORS permitindo o domínio do frontend

## Variáveis de ambiente
Crie `.env.local` em `frontend/` com:
```
NEXT_PUBLIC_AGENTOS_API_BASE=http://127.0.0.1:8000
NEXT_PUBLIC_APP_NAME=Agno Agents UI
```
Ajuste `CORS_ALLOW_ORIGINS` no backend para incluir `http://localhost:3000` e o domínio da Netlify.

## Scripts
- `npm install`
- `npm run dev` (http://localhost:3000)
- `npm run build` e `npm start`

## Notas
- Login usa `POST /auth/login` e persiste o token no localStorage.
- Interceptor Axios adiciona `Authorization: Bearer <token>`.
