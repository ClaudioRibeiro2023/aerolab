# Guia de Início Rápido

Este documento guia você na configuração inicial do template para seu novo projeto.

## 1. Clonar e Renomear

```bash
# Clone o template
git clone <template-repo> meu-novo-projeto
cd meu-novo-projeto

# Remova o histórico git do template
rm -rf .git

# Inicialize um novo repositório
git init
git add .
git commit -m "Initial commit from template"
```

## 2. Personalizar Nomes

Substitua as referências ao template pelo nome do seu projeto:

### package.json (raiz)
```json
{
  "name": "@meu-projeto/platform",
  "description": "Meu Projeto - Descrição"
}
```

### apps/web/package.json
```json
{
  "name": "@meu-projeto/web"
}
```

### packages/*/package.json
Atualize o nome de cada pacote para `@meu-projeto/*`

## 3. Configurar Keycloak

1. Acesse o Keycloak Admin: http://localhost:8080
2. Faça login com `admin/admin`
3. Crie um novo Realm com o nome do seu projeto
4. Configure um Client para o frontend
5. Atualize `.env` com as configurações

## 4. Configurar Cores e Logo

### Cores
Edite `apps/web/src/styles/index.css`:
```css
:root {
  --brand-primary: #SUA_COR;
  --brand-secondary: #SUA_COR;
  --brand-accent: #SUA_COR;
}
```

### Logo
- Substitua o favicon em `apps/web/public/`
- Atualize o logo no `AppSidebar.tsx` e `LoginPage.tsx`

## 5. Criar Primeiro Módulo

```bash
mkdir -p apps/web/src/modules/meu-modulo/{components,hooks,services}
```

Crie o arquivo principal:
```tsx
// apps/web/src/modules/meu-modulo/index.tsx
export function MeuModuloPage() {
  return <div>Meu Módulo</div>
}
```

Adicione a rota em `App.tsx`:
```tsx
import { MeuModuloPage } from '@/modules/meu-modulo'

// Na seção de rotas:
<Route path="/meu-modulo" element={<MeuModuloPage />} />
```

## 6. Rodar o Projeto

```bash
# Instalar dependências
pnpm install

# Modo desenvolvimento (com demo mode)
VITE_DEMO_MODE=true pnpm dev

# Ou crie um arquivo .env
echo "VITE_DEMO_MODE=true" > apps/web/.env
pnpm dev
```

O servidor de desenvolvimento iniciará em **http://localhost:13000**.

## 7. Portas Padrão

| Serviço | Porta | URL |
|---------|-------|-----|
| Frontend | 13000 | http://localhost:13000 |
| API | 8000 | http://localhost:8000 |
| Keycloak | 8080 | http://localhost:8080 |
| Storybook | 6006 | http://localhost:6006 |

## Próximos Passos

- [ ] Configurar CI/CD
- [ ] Adicionar testes E2E para seu módulo
- [ ] Configurar ambiente de produção
- [ ] Documentar APIs
