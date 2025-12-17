# Troubleshooting

Guia de resolução de problemas comuns no Template Platform.

## Índice

- [Ambiente de Desenvolvimento](#ambiente-de-desenvolvimento)
- [Build e Deploy](#build-e-deploy)
- [Autenticação](#autenticação)
- [API e Backend](#api-e-backend)
- [Docker e Infraestrutura](#docker-e-infraestrutura)

---

## Ambiente de Desenvolvimento

### `pnpm install` falha com erro de permissão

**Sintoma:** Erro de permissão ao instalar dependências.

**Solução:**

```bash
# Windows (Admin PowerShell)
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned

# Linux/Mac
sudo chown -R $(whoami) ~/.pnpm-store
```

---

### TypeScript não reconhece imports de `@template/*`

**Sintoma:** Erro "Cannot find module '@template/shared'"

**Soluções:**

1. Verifique se os packages foram buildados:

   ```bash
   pnpm build:packages
   ```

2. Reinicie o TypeScript Server no VS Code:
   - `Ctrl+Shift+P` → "TypeScript: Restart TS Server"

3. Verifique `tsconfig.json` tem os paths corretos:
   ```json
   "paths": {
     "@template/*": ["./packages/*/src"]
   }
   ```

---

### Hot reload não funciona

**Sintoma:** Alterações não refletem automaticamente.

**Soluções:**

1. Verifique se o dev server está rodando:

   ```bash
   pnpm dev
   ```

2. Limpe o cache do Vite:

   ```bash
   rm -rf node_modules/.vite
   pnpm dev
   ```

3. Verifique se o arquivo está sendo importado corretamente.

---

## Build e Deploy

### Build falha com "out of memory"

**Sintoma:** `FATAL ERROR: CALL_AND_RETRY_LAST Allocation failed`

**Solução:**

```bash
# Aumentar memória do Node
NODE_OPTIONS="--max-old-space-size=4096" pnpm build
```

---

### Build falha com erros de tipo

**Sintoma:** TypeScript errors durante o build.

**Soluções:**

1. Execute typecheck primeiro:

   ```bash
   pnpm typecheck
   ```

2. Corrija os erros indicados.

3. Se usar `// @ts-ignore`, considere resolver o erro real.

---

### Assets não carregam em produção

**Sintoma:** Imagens/fonts 404 em produção.

**Soluções:**

1. Verifique se assets estão em `public/` ou importados corretamente.

2. Verifique `base` no `vite.config.ts`:
   ```ts
   export default defineConfig({
     base: '/', // ou '/subpath/' se necessário
   })
   ```

---

## Autenticação

### Login redireciona mas não autentica

**Sintoma:** Após login no Keycloak, volta para a página sem autenticar.

**Soluções:**

1. Verifique as variáveis de ambiente:

   ```env
   VITE_KEYCLOAK_URL=http://localhost:8080
   VITE_KEYCLOAK_REALM=template
   VITE_KEYCLOAK_CLIENT_ID=template-web
   ```

2. Verifique se o client no Keycloak tem:
   - Valid Redirect URIs: `http://localhost:5173/*`
   - Web Origins: `http://localhost:5173`

3. Verifique console do browser para erros de CORS.

---

### "Invalid token" após refresh

**Sintoma:** Token expira e não renova automaticamente.

**Soluções:**

1. Verifique se `oidc-client-ts` está configurado com `automaticSilentRenew`:

   ```ts
   const config = {
     automaticSilentRenew: true,
     silent_redirect_uri: 'http://localhost:5173/silent-renew.html',
   }
   ```

2. Crie o arquivo `public/silent-renew.html` se não existir.

---

### DEMO_MODE não funciona

**Sintoma:** Autenticação não é bypassada em modo demo.

**Soluções:**

1. Verifique se a variável está setada:

   ```env
   VITE_DEMO_MODE=true
   ```

2. Reinicie o dev server após alterar `.env`.

---

## API e Backend

### Erro 500 na API

**Sintoma:** API retorna Internal Server Error.

**Soluções:**

1. Verifique logs da API:

   ```bash
   docker-compose logs api
   # ou
   cd api-template && uvicorn app.main:app --reload
   ```

2. Verifique conexão com banco de dados.

3. Verifique variáveis de ambiente da API.

---

### CORS error no browser

**Sintoma:** "Access-Control-Allow-Origin" error.

**Soluções:**

1. Verifique se a origem está permitida no FastAPI:

   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["http://localhost:5173"],
       ...
   )
   ```

2. Verifique se o FRONTEND_URL está correto no `.env` da API.

---

### Timeout em requisições

**Sintoma:** Requests demoram e falham.

**Soluções:**

1. Aumente o timeout no API client:

   ```ts
   const client = createApiClient({ timeout: 60000 })
   ```

2. Verifique se a API está sobrecarregada.

3. Verifique conexão de rede/VPN.

---

## Docker e Infraestrutura

### Container não inicia

**Sintoma:** `docker-compose up` falha.

**Soluções:**

1. Verifique logs:

   ```bash
   docker-compose logs <service-name>
   ```

2. Verifique se as portas estão livres:

   ```bash
   # Windows
   netstat -ano | findstr :5432
   # Linux/Mac
   lsof -i :5432
   ```

3. Remova volumes e recrie:
   ```bash
   docker-compose down -v
   docker-compose up -d
   ```

---

### Keycloak não inicia

**Sintoma:** Keycloak container reinicia constantemente.

**Soluções:**

1. Verifique memória disponível (mínimo 512MB para Keycloak).

2. Verifique se o banco de dados está acessível.

3. Remova o container e volume:
   ```bash
   docker-compose rm -f keycloak
   docker volume rm template_keycloak_data
   docker-compose up -d keycloak
   ```

---

### Banco de dados não conecta

**Sintoma:** "Connection refused" para PostgreSQL.

**Soluções:**

1. Verifique se o container está rodando:

   ```bash
   docker-compose ps postgres
   ```

2. Verifique credenciais no `.env`.

3. Teste conexão manual:
   ```bash
   docker-compose exec postgres psql -U template -d template_db
   ```

---

## Ainda com problemas?

1. Pesquise nas [issues do repositório](https://github.com/ClaudioRibeiro2023/Modelo/issues)
2. Consulte o [portal de documentação](./INDEX.md)
3. Abra uma nova issue com:
   - Descrição do problema
   - Passos para reproduzir
   - Logs relevantes
   - Ambiente (OS, versões)
