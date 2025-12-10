# Levantamento de Melhorias UI/UX - Template Platform

> **Objetivo**: Servir como repositório matriz para múltiplos projetos.
> **Data**: Dezembro 2025

---

## Sumário Executivo

Este documento identifica melhorias para tornar o template mais profissional, consistente e fácil de customizar para diferentes projetos derivados.

### Métricas Atuais

| Aspecto | Estado | Prioridade |
|---------|--------|------------|
| Design System | 🟡 Parcial | P0 |
| Tokens de Design | 🟡 Parcial | P0 |
| Componentes Reutilizáveis | 🟡 Parcial | P0 |
| Acessibilidade | 🟠 Necessita Melhorias | P1 |
| Dark Mode | 🟡 Incompleto | P1 |
| Responsividade | 🟡 Básica | P1 |
| Animações/Transições | 🟡 Inconsistente | P2 |
| Documentação UI | 🔴 Ausente | P1 |

---

## 1. DESIGN SYSTEM & TOKENS

### 1.1 Problemas Identificados

#### Tokens Insuficientes
O `index.css` define apenas tokens básicos. Faltam:

```css
/* FALTAM: */
--spacing-xs, --spacing-sm, --spacing-md, --spacing-lg, --spacing-xl
--radius-sm, --radius-md, --radius-lg, --radius-full
--shadow-sm, --shadow-md, --shadow-lg, --shadow-xl
--font-size-xs, --font-size-sm, --font-size-base, --font-size-lg, --font-size-xl
--font-weight-normal, --font-weight-medium, --font-weight-semibold, --font-weight-bold
--transition-fast, --transition-normal, --transition-slow
--z-dropdown, --z-modal, --z-tooltip, --z-toast
```

#### Cores Inconsistentes
- Uso misto de cores Tailwind (`gray-200`, `teal-500`) e variáveis CSS (`--brand-primary`)
- Dark mode usa cores diferentes em cada página (ex: `dark:bg-gray-700` vs `dark:bg-gray-800`)

### 1.2 Ações Recomendadas

```
[ ] P0 - Criar tokens de design completos em `styles/tokens.css`
[ ] P0 - Criar preset Tailwind em `tailwind.preset.js` para projetos derivados
[ ] P0 - Substituir todas as cores hardcoded por tokens semânticos
[ ] P0 - Documentar paleta de cores com propósito de cada cor
[ ] P1 - Adicionar tokens de animação/easing
[ ] P1 - Criar ferramenta de theming (ex: JSON → CSS Variables)
```

---

## 2. COMPONENTES BASE

### 2.1 Componentes Ausentes ou Incompletos

| Componente | Estado | Descrição |
|------------|--------|-----------|
| `Button` | 🔴 Ausente | Não existe componente Button reutilizável |
| `Input` | 🔴 Ausente | Inputs são definidos inline em cada página |
| `Select` | 🔴 Ausente | Apenas inline |
| `Checkbox` | 🔴 Ausente | Apenas inline |
| `Toggle/Switch` | 🔴 Ausente | Definido inline com CSS complexo |
| `Modal/Dialog` | 🔴 Ausente | |
| `Tooltip` | 🔴 Ausente | |
| `Toast/Notification` | 🔴 Ausente | |
| `Card` | 🔴 Ausente | Pattern repetido mas não componentizado |
| `Badge` | 🔴 Ausente | |
| `Avatar` | 🔴 Ausente | |
| `Tabs` | 🔴 Ausente | Definido inline em ConfigPage |
| `Dropdown` | 🔴 Ausente | |
| `Table` | 🔴 Ausente | |
| `Pagination` | 🔴 Ausente | |
| `Breadcrumb` | 🟡 Inline | Definido no Header, não componentizado |
| `Alert` | 🔴 Ausente | |
| `Progress` | 🔴 Ausente | |
| `Skeleton` | 🔴 Ausente | Para loading states |

### 2.2 Ações Recomendadas

```
[ ] P0 - Criar componente Button (variants: primary, secondary, ghost, danger)
[ ] P0 - Criar componente Input (variants: text, password, email, search)
[ ] P0 - Criar componente Select (native e custom)
[ ] P0 - Criar componente Checkbox
[ ] P0 - Criar componente Toggle/Switch
[ ] P0 - Criar componente Card
[ ] P0 - Criar componente Modal/Dialog
[ ] P0 - Criar componente Toast/Notification system
[ ] P1 - Criar componente Tabs
[ ] P1 - Criar componente Badge
[ ] P1 - Criar componente Tooltip
[ ] P1 - Criar componente Dropdown/Menu
[ ] P1 - Criar componente Table (sortable, selectable)
[ ] P1 - Criar componente Pagination
[ ] P1 - Criar componente Skeleton
[ ] P2 - Criar componente Avatar
[ ] P2 - Criar componente Alert
[ ] P2 - Criar componente Progress (bar e circular)
```

---

## 3. LAYOUT & ESTRUTURA

### 3.1 Problemas Identificados

#### AppLayout
- Usa `NAVIGATION` hardcoded diretamente (já refatorando)
- CSS variables não documentadas (`--functions-panel-width`)

#### Sidebar
- Usa `style={{ background: '...' }}` inline (viola boas práticas)
- Ícones importados manualmente em vez de usar sistema dinâmico
- Largura fixa, não há estado "collapsed"

#### Header
- Breadcrumb gerado por regex simples, não semântico
- Dark mode toggle não persiste preferência
- Busca não implementada (apenas visual)

### 3.2 Ações Recomendadas

```
[ ] P0 - Remover todos os inline styles (style={})
[ ] P0 - Implementar sidebar collapsible com transição suave
[ ] P1 - Criar sistema de breadcrumb baseado em routes
[ ] P1 - Persistir preferência de tema (localStorage/cookie)
[ ] P1 - Implementar busca global real (Command Palette / Ctrl+K)
[ ] P2 - Adicionar suporte a múltiplos layouts (full-width, centered, etc.)
```

---

## 4. ACESSIBILIDADE (A11Y)

### 4.1 Problemas Identificados

| Arquivo | Problema |
|---------|----------|
| `DataSourceCard.tsx:46` | Botão sem texto discernível |
| `ETLFilters.tsx:55,68` | Select sem nome acessível |
| `FiltersConfigPage.tsx:505,527` | Inputs sem labels |
| `FilterMultiSelect.tsx` | ARIA attributes inválidos |

#### Problemas Gerais
- Foco não visível em alguns elementos
- Não há skip-links
- Contrast ratio não verificado
- Screen reader: muitos elementos não têm labels adequados
- Keyboard navigation incompleta em modais/dropdowns

### 4.2 Ações Recomendadas

```
[ ] P0 - Corrigir todos os warnings de acessibilidade existentes
[ ] P0 - Adicionar aria-labels a todos os botões com apenas ícones
[ ] P0 - Adicionar labels/title a todos os inputs e selects
[ ] P1 - Implementar skip-links
[ ] P1 - Verificar e ajustar contrast ratios (WCAG 2.1 AA)
[ ] P1 - Implementar focus trap em modais
[ ] P1 - Adicionar suporte a reduced-motion
[ ] P2 - Testar com screen readers (NVDA, VoiceOver)
[ ] P2 - Criar guia de acessibilidade para desenvolvedores
```

---

## 5. DARK MODE

### 5.1 Problemas Identificados

- Cores dark mode inconsistentes entre páginas
- Alguns componentes não respeitam dark mode
- Gradientes não adaptados para dark mode
- Imagens/ícones não têm versão dark

### 5.2 Ações Recomendadas

```
[ ] P0 - Criar paleta dark mode completa e consistente
[ ] P0 - Auditar todos os componentes para dark mode
[ ] P1 - Ajustar gradientes para dark mode
[ ] P1 - Persistir preferência com system fallback
[ ] P2 - Adicionar transição suave na troca de tema
```

---

## 6. RESPONSIVIDADE

### 6.1 Problemas Identificados

- Sidebar não responsiva (não colapsa em mobile)
- Muitas grids usam valores fixos
- Tabelas não têm versão mobile
- Alguns textos muito pequenos em mobile

### 6.2 Ações Recomendadas

```
[ ] P0 - Implementar sidebar mobile (drawer/overlay)
[ ] P0 - Revisar breakpoints e adaptar layouts
[ ] P1 - Criar versão mobile para tabelas (cards ou scroll)
[ ] P1 - Aumentar touch targets (mínimo 44x44px)
[ ] P1 - Testar em dispositivos reais
[ ] P2 - Adicionar suporte a PWA
```

---

## 7. ANIMAÇÕES & MICRO-INTERAÇÕES

### 7.1 Problemas Identificados

- Animações inconsistentes (alguns elementos têm, outros não)
- Não há feedback visual em ações (save, delete, etc.)
- Transições muito rápidas ou ausentes
- Loading states básicos

### 7.2 Ações Recomendadas

```
[ ] P1 - Definir tokens de animação (duration, easing)
[ ] P1 - Adicionar animações de entrada em páginas
[ ] P1 - Criar estados de loading skeleton
[ ] P1 - Adicionar micro-interações em botões/links
[ ] P2 - Implementar animações de feedback (success, error)
[ ] P2 - Adicionar suporte a prefers-reduced-motion
```

---

## 8. ÍCONES

### 8.1 Estado Atual

- Usa Lucide React (boa escolha)
- Ícones importados manualmente em cada arquivo
- Não há sistema centralizado de ícones

### 8.2 Ações Recomendadas

```
[ ] P1 - Criar sistema de ícones com mapa dinâmico
[ ] P1 - Documentar ícones disponíveis
[ ] P2 - Criar componente Icon wrapper com tamanhos padronizados
```

---

## 9. FORMULÁRIOS

### 9.1 Problemas Identificados

- Validação inline ausente
- Mensagens de erro não padronizadas
- Não há estados de loading em submits
- Labels não associados corretamente

### 9.2 Ações Recomendadas

```
[ ] P0 - Criar componentes de form (Form, FormField, FormLabel, FormError)
[ ] P0 - Implementar validação com feedback visual
[ ] P1 - Integrar com react-hook-form ou similar
[ ] P1 - Criar estados de loading/disabled consistentes
[ ] P2 - Adicionar suporte a máscaras de input
```

---

## 10. DOCUMENTAÇÃO & STORYBOOK

### 10.1 Estado Atual

- Design system existe mas está vazio
- Sem documentação de componentes
- Sem exemplos de uso

### 10.2 Ações Recomendadas

```
[ ] P0 - Criar README no design-system com instruções
[ ] P1 - Configurar Storybook para documentar componentes
[ ] P1 - Criar stories para cada componente
[ ] P1 - Documentar padrões de uso e variantes
[ ] P2 - Adicionar testes visuais (Chromatic ou similar)
```

---

## 11. PERFORMANCE

### 11.1 Problemas Identificados

- Lazy loading já implementado (bom)
- Bundle size pode ser otimizado
- Imagens não otimizadas

### 11.2 Ações Recomendadas

```
[ ] P1 - Analisar bundle com `vite-bundle-analyzer`
[ ] P1 - Implementar image optimization
[ ] P2 - Adicionar prefetching de rotas
[ ] P2 - Implementar virtualização em listas grandes
```

---

## 12. CSS & ORGANIZAÇÃO

### 12.1 Problemas Identificados

- Mix de CSS puro e Tailwind
- Inline styles em alguns componentes
- CSS files dispersos (`filters.css`, `module-functions-panel.css`)
- Não há padrão claro de quando usar CSS vs Tailwind

### 12.2 Ações Recomendadas

```
[ ] P0 - Definir convenção: Tailwind para layout, CSS para componentes complexos
[ ] P0 - Remover todos os inline styles
[ ] P1 - Consolidar CSS files em estrutura organizada
[ ] P1 - Usar @apply do Tailwind para patterns repetidos
[ ] P1 - Implementar CSS Modules ou styled-components onde necessário
```

---

## 13. PLANO DE AÇÃO RESUMIDO

### Fase 1 - Fundação (P0) - 2-3 semanas
1. Criar tokens de design completos
2. Criar componentes base (Button, Input, Select, Card, Modal, Toast)
3. Remover inline styles
4. Corrigir problemas de acessibilidade existentes
5. Padronizar dark mode

### Fase 2 - Componentes (P1) - 2-3 semanas
1. Criar componentes restantes (Tabs, Table, Dropdown, etc.)
2. Implementar sidebar responsiva
3. Sistema de busca global
4. Melhorar formulários
5. Configurar Storybook

### Fase 3 - Polish (P2) - 1-2 semanas
1. Animações e micro-interações
2. Performance optimization
3. Testes de acessibilidade
4. Documentação completa

---

## 14. ESTRUTURA DE ARQUIVOS PROPOSTA

```
packages/design-system/
├── src/
│   ├── tokens/
│   │   ├── colors.ts
│   │   ├── spacing.ts
│   │   ├── typography.ts
│   │   ├── shadows.ts
│   │   └── index.ts
│   ├── components/
│   │   ├── Button/
│   │   │   ├── Button.tsx
│   │   │   ├── Button.stories.tsx
│   │   │   ├── Button.test.tsx
│   │   │   └── index.ts
│   │   ├── Input/
│   │   ├── Select/
│   │   ├── Card/
│   │   ├── Modal/
│   │   ├── Toast/
│   │   ├── Table/
│   │   └── ...
│   ├── hooks/
│   │   ├── useTheme.ts
│   │   ├── useMediaQuery.ts
│   │   └── useToast.ts
│   ├── styles/
│   │   ├── tokens.css
│   │   ├── base.css
│   │   └── utilities.css
│   └── index.ts
├── tailwind.preset.js    # Preset para projetos derivados
└── package.json
```

---

## 15. MÉTRICAS DE SUCESSO

| Métrica | Atual | Meta |
|---------|-------|------|
| Componentes reutilizáveis | ~5 | 20+ |
| Cobertura dark mode | ~60% | 100% |
| A11y issues | 15+ | 0 |
| Lighthouse Performance | N/A | 90+ |
| Lighthouse Accessibility | N/A | 100 |
| Bundle size (gzip) | 35KB | <30KB |
| Time to First Paint | N/A | <1.5s |

---

## Próximos Passos Imediatos

1. **Revisar este documento** com stakeholders
2. **Priorizar tarefas** no `todo.md`
3. **Começar pela Fase 1** - Fundação
4. **Criar componentes incrementalmente** - Um por vez, com testes

---

## 16. PROGRESSO DE IMPLEMENTAÇÃO

> **Última atualização:** 10 de Dezembro de 2025

### ✅ Fase 1 - Fundação (CONCLUÍDO)

#### Design Tokens
- [x] **Tokens de cores completos** (`index.css`)
  - Cores semânticas: `--color-success`, `--color-warning`, `--color-error`, `--color-info`
  - Status backgrounds para light/dark mode
  - Spacing, typography, radius, shadows, z-index
- [x] **Dark mode consistente**
  - Todas as variáveis com valores para `.dark`
  - Cores semânticas ajustadas para contraste adequado

#### Componentes Base (Design System)
- [x] Button, Input, Card, Modal, Toast, Tabs, Table, Dropdown, Skeleton
- [x] Storybook configurado (http://localhost:6007)

#### Acessibilidade (A11y)
- [x] **ARIA attributes corrigidos:**
  - `FilterMultiSelect.tsx` - aria-expanded, role, aria-label
  - `FilterToggle.tsx` - aria-checked para string
  - `Input.tsx` - aria-invalid para string  
  - `Dropdown.tsx` - aria-expanded para string
  - `Tabs.tsx` - aria-selected para string

#### Layout & Responsividade
- [x] **Sidebar colapsível** com toggle e persistência
- [x] **Mobile sidebar** (drawer) com overlay
- [x] **Botão toggle do painel** reposicionado
- [x] **Welcome banner** com gradiente correto

#### Utilitários CSS
- [x] Classes de progresso: `.progress-bar-track`, `.progress-bar-fill--*`
- [x] Classes de status: `.status-badge--*`, `.status-card--*`
- [x] Classes de texto: `.text-success`, `.text-warning`, etc.
- [x] Page utilities: `.page-header`, `.page-title`, `.section`

### 🔄 Fase 2 - Componentes (EM PROGRESSO)

- [x] Sidebar responsiva implementada
- [ ] Sistema de busca global (Ctrl+K)
- [ ] Melhorar formulários
- [x] Storybook configurado

### ⏳ Fase 3 - Polish (PENDENTE)

- [ ] Animações e micro-interações
- [ ] Performance optimization
- [ ] Testes de acessibilidade completos
- [ ] Documentação completa

### Métricas Atualizadas

| Métrica | Anterior | Atual | Meta |
|---------|----------|-------|------|
| Componentes DS | ~5 | 9 | 20+ |
| Cobertura dark mode | ~60% | ~90% | 100% |
| A11y issues | 15+ | ~5 | 0 |
| CSS Bundle | 64KB | 69KB | <80KB |

---

*Documento atualizado manualmente. Última atualização: 10 Dezembro 2025*
