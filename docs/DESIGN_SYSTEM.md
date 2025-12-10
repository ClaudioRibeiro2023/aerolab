# Design System - Template Platform

> Documentação completa do sistema de design para a Template Platform.

**Última atualização:** 10 de Dezembro de 2025

---

## 1. Visão Geral

O Design System da Template Platform fornece uma biblioteca coesa de tokens, componentes e utilitários CSS para construir interfaces consistentes e acessíveis.

### Estrutura

```
packages/design-system/        # Componentes React reutilizáveis
├── src/components/
│   ├── Alert/                 # Componente de alerta
│   ├── Button/
│   ├── Card/
│   ├── Dropdown/
│   ├── Input/
│   ├── Modal/
│   ├── Skeleton/
│   ├── StatusBadge/           # Badge de status semântico
│   ├── Table/
│   ├── Tabs/
│   └── Toast/
├── src/layout/
│   ├── EmptyState/            # Estado vazio para listas
│   └── PageHeader/            # Cabeçalho de páginas

apps/web/src/styles/           # Estilos globais e tokens
├── index.css                  # Tokens + utilitários
├── design-system.css          # Reset e base
└── module-functions-panel.css # Componentes específicos
```

---

## 2. Design Tokens

### 2.1 Cores

#### Cores de Marca

```css
--brand-primary: #0087A8;
--brand-secondary: #005F73;
--brand-accent: #94D2BD;
```

#### Cores de Superfície

```css
/* Light Mode */
--surface-base: #F8FAFC;
--surface-elevated: #FFFFFF;
--surface-muted: #F1F5F9;

/* Dark Mode */
--surface-base: #0F172A;
--surface-elevated: #1E293B;
--surface-muted: #334155;
```

#### Cores de Texto

```css
/* Light Mode */
--text-primary: #0F172A;
--text-secondary: #475569;
--text-muted: #94A3B8;

/* Dark Mode */
--text-primary: #F8FAFC;
--text-secondary: #CBD5E1;
--text-muted: #64748B;
```

#### Cores Semânticas

```css
/* Success */
--color-success: #10B981;
--color-success-light: #D1FAE5;
--status-success-bg: #ECFDF5;

/* Warning */
--color-warning: #F59E0B;
--color-warning-light: #FEF3C7;
--status-warning-bg: #FFFBEB;

/* Error */
--color-error: #EF4444;
--color-error-light: #FEE2E2;
--status-error-bg: #FEF2F2;

/* Info */
--color-info: #3B82F6;
--color-info-light: #DBEAFE;
--status-info-bg: #EFF6FF;
```

### 2.2 Espaçamento

```css
--spacing-xs: 0.25rem;   /* 4px */
--spacing-sm: 0.5rem;    /* 8px */
--spacing-md: 1rem;      /* 16px */
--spacing-lg: 1.5rem;    /* 24px */
--spacing-xl: 2rem;      /* 32px */
--spacing-2xl: 3rem;     /* 48px */
```

### 2.3 Tipografia

```css
--font-size-xs: 0.75rem;    /* 12px */
--font-size-sm: 0.875rem;   /* 14px */
--font-size-base: 1rem;     /* 16px */
--font-size-lg: 1.125rem;   /* 18px */
--font-size-xl: 1.25rem;    /* 20px */
--font-size-2xl: 1.5rem;    /* 24px */
--font-size-3xl: 1.875rem;  /* 30px */
```

### 2.4 Bordas e Sombras

```css
/* Border Radius */
--radius-sm: 0.25rem;
--radius-md: 0.375rem;
--radius-lg: 0.5rem;
--radius-xl: 0.75rem;
--radius-full: 9999px;

/* Shadows */
--shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
--shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1);
--shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1);
--shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1);
```

### 2.5 Transições

```css
--transition-fast: 150ms ease;
--transition-normal: 300ms ease;
--transition-slow: 500ms ease;
```

### 2.6 Z-Index

```css
--z-dropdown: 50;
--z-sticky: 100;
--z-modal-backdrop: 200;
--z-modal: 210;
--z-tooltip: 300;
--z-toast: 400;
```

---

## 3. Componentes

### 3.1 Button

```tsx
import { Button } from '@template/design-system'

// Variants
<Button variant="primary">Primary</Button>
<Button variant="secondary">Secondary</Button>
<Button variant="outline">Outline</Button>
<Button variant="ghost">Ghost</Button>
<Button variant="danger">Danger</Button>

// Sizes
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>

// With icon
<Button leftIcon={<Icon />}>With Icon</Button>

// Loading
<Button loading>Loading...</Button>
```

### 3.2 Input

```tsx
import { Input } from '@template/design-system'

// Basic
<Input label="Email" placeholder="seu@email.com" />

// With error
<Input 
  label="Senha" 
  type="password"
  error="Senha muito curta"
/>

// With icons
<Input 
  leftIcon={<SearchIcon />}
  rightIcon={<ClearIcon />}
/>

// Sizes
<Input size="sm" />
<Input size="md" />
<Input size="lg" />
```

### 3.3 Card

```tsx
import { Card } from '@template/design-system'

// Variants
<Card variant="elevated">Elevated Card</Card>
<Card variant="outlined">Outlined Card</Card>
<Card variant="filled">Filled Card</Card>

// Interactive
<Card interactive onClick={handleClick}>
  Clickable Card
</Card>

// With padding
<Card padding="lg">Large padding</Card>
```

### 3.4 Modal

```tsx
import { Modal, useModal } from '@template/design-system'

function Example() {
  const modal = useModal()

  return (
    <>
      <Button onClick={modal.open}>Abrir Modal</Button>
      
      <Modal 
        isOpen={modal.isOpen} 
        onClose={modal.close}
        title="Título do Modal"
      >
        <p>Conteúdo do modal</p>
        <Modal.Footer>
          <Button variant="outline" onClick={modal.close}>Cancelar</Button>
          <Button variant="primary">Confirmar</Button>
        </Modal.Footer>
      </Modal>
    </>
  )
}
```

### 3.5 Toast

```tsx
import { useToast } from '@template/design-system'

function Example() {
  const toast = useToast()

  return (
    <Button onClick={() => toast.success('Salvo com sucesso!')}>
      Salvar
    </Button>
  )
}

// Tipos
toast.success('Sucesso!')
toast.error('Erro!')
toast.warning('Atenção!')
toast.info('Informação')
```

### 3.6 Table

```tsx
import { Table, TableHeader, TableBody, TableRow, TableCell } from '@template/design-system'

<Table>
  <TableHeader>
    <TableRow>
      <TableCell sortable onSort={handleSort}>Nome</TableCell>
      <TableCell>Email</TableCell>
      <TableCell>Status</TableCell>
    </TableRow>
  </TableHeader>
  <TableBody>
    {data.map(item => (
      <TableRow key={item.id}>
        <TableCell>{item.name}</TableCell>
        <TableCell>{item.email}</TableCell>
        <TableCell>{item.status}</TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

### 3.7 Tabs

```tsx
import { Tabs, TabList, Tab, TabPanels, TabPanel } from '@template/design-system'

<Tabs defaultValue="tab1">
  <TabList>
    <Tab value="tab1">Tab 1</Tab>
    <Tab value="tab2">Tab 2</Tab>
    <Tab value="tab3">Tab 3</Tab>
  </TabList>
  <TabPanels>
    <TabPanel value="tab1">Conteúdo 1</TabPanel>
    <TabPanel value="tab2">Conteúdo 2</TabPanel>
    <TabPanel value="tab3">Conteúdo 3</TabPanel>
  </TabPanels>
</Tabs>
```

### 3.8 Dropdown

```tsx
import { Dropdown, DropdownTrigger, DropdownMenu, DropdownItem } from '@template/design-system'

<Dropdown>
  <DropdownTrigger>
    <Button>Opções</Button>
  </DropdownTrigger>
  <DropdownMenu>
    <DropdownItem onClick={handleEdit}>Editar</DropdownItem>
    <DropdownItem onClick={handleDuplicate}>Duplicar</DropdownItem>
    <DropdownItem onClick={handleDelete} danger>Excluir</DropdownItem>
  </DropdownMenu>
</Dropdown>
```

### 3.9 StatusBadge

Componente para exibir status com cores semânticas.

```tsx
import { StatusBadge } from '@template/design-system'

// Variantes
<StatusBadge variant="success">Concluído</StatusBadge>
<StatusBadge variant="warning">Pendente</StatusBadge>
<StatusBadge variant="error">Erro</StatusBadge>
<StatusBadge variant="info">Em processamento</StatusBadge>
<StatusBadge variant="pending">Aguardando</StatusBadge>

// Tamanhos
<StatusBadge size="sm">Pequeno</StatusBadge>
<StatusBadge size="md">Médio</StatusBadge>

// Com ícone
<StatusBadge variant="success" icon={<Check size={12} />}>
  Aprovado
</StatusBadge>
```

### 3.10 Alert

Componente para exibir mensagens de alerta.

```tsx
import { Alert } from '@template/design-system'

// Variantes
<Alert variant="info" title="Informação" description="Mensagem informativa" />
<Alert variant="success" title="Sucesso" description="Operação realizada" />
<Alert variant="warning" title="Atenção" description="Verifique os dados" />
<Alert variant="error" title="Erro" description="Algo deu errado" />

// Com ícone customizado
<Alert 
  variant="info" 
  icon={<InfoIcon />}
  title="Título"
  description="Descrição"
/>
```

### 3.11 PageHeader

Componente para cabeçalho de páginas.

```tsx
import { PageHeader } from '@template/design-system'

// Básico
<PageHeader 
  title="Título da Página"
  description="Descrição opcional"
/>

// Com ícone
<PageHeader 
  title="Dashboard"
  description="Visão geral do sistema"
  icon={<LayoutDashboard size={28} />}
/>

// Com ações
<PageHeader 
  title="Usuários"
  description="Gerenciar usuários"
  icon={<Users size={28} />}
  actions={
    <Button variant="primary" leftIcon={<Plus />}>
      Novo Usuário
    </Button>
  }
/>

// Com conteúdo adicional
<PageHeader title="Documentação">
  <SearchInput placeholder="Buscar..." />
</PageHeader>
```

### 3.12 EmptyState

Componente para estados vazios.

```tsx
import { EmptyState } from '@template/design-system'

// Básico
<EmptyState 
  title="Nenhum item encontrado"
  description="Não há dados para exibir"
/>

// Com ícone
<EmptyState 
  title="Lista vazia"
  description="Adicione seu primeiro item"
  icon={<Inbox size={48} />}
/>

// Com ações
<EmptyState 
  title="Nenhum resultado"
  description="Tente ajustar os filtros"
  icon={<SearchX size={48} />}
  actions={
    <Button variant="primary">Limpar Filtros</Button>
  }
/>
```

---

## 4. Classes Utilitárias CSS

### 4.1 Status Badges

```html
<span class="status-badge status-badge--success">Concluído</span>
<span class="status-badge status-badge--warning">Pendente</span>
<span class="status-badge status-badge--error">Erro</span>
<span class="status-badge status-badge--info">Info</span>
```

### 4.2 Status Cards

```html
<div class="status-card status-card--success">
  Card de sucesso
</div>
```

### 4.3 Formulários

```html
<!-- Input com validação -->
<div class="form-group">
  <label class="form-label form-label--required">Email</label>
  <input class="form-input form-input--error" />
  <span class="form-helper form-helper--error">Email inválido</span>
</div>

<!-- Checkbox customizado -->
<label class="form-checkbox">
  <input type="checkbox" />
  <span>Aceito os termos</span>
</label>
```

### 4.4 Animações

```html
<!-- Fade -->
<div class="animate-fade-in">Aparece com fade</div>

<!-- Slide -->
<div class="animate-slide-up">Desliza para cima</div>
<div class="animate-slide-left">Desliza da direita</div>

<!-- Scale -->
<div class="animate-scale-in">Escala entrando</div>

<!-- Efeitos de hover -->
<button class="hover-lift">Levanta ao hover</button>
<button class="hover-glow">Brilha ao hover</button>

<!-- Skeleton loading -->
<div class="skeleton skeleton-text"></div>
<div class="skeleton skeleton-avatar"></div>

<!-- Stagger (animação em sequência) -->
<div class="stagger-children">
  <div>Item 1</div>
  <div>Item 2</div>
  <div>Item 3</div>
</div>
```

### 4.5 Progress Bars

```html
<div class="progress-bar-track">
  <div class="progress-bar-fill progress-bar-fill--primary" style="width: 75%"></div>
</div>

<div class="progress-bar-track progress-bar-track--sm">
  <div class="progress-bar-fill progress-bar-fill--success" style="width: 100%"></div>
</div>
```

---

## 5. Acessibilidade

### 5.1 ARIA Attributes

Todos os componentes seguem as melhores práticas de acessibilidade:

- `aria-expanded` para elementos expansíveis
- `aria-selected` para tabs e listas
- `aria-label` para elementos interativos
- `role` apropriados para landmarks

### 5.2 Focus Management

```css
/* Focus ring padrão */
.focus-ring:focus-visible {
  outline: none;
  box-shadow: 0 0 0 2px var(--surface-base), 0 0 0 4px var(--brand-primary);
}
```

### 5.3 Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## 6. Dark Mode

O dark mode é ativado automaticamente baseado na preferência do sistema ou pode ser controlado manualmente:

```tsx
// Hook para controle de tema
function useTheme() {
  const [theme, setTheme] = useState(() => {
    const saved = localStorage.getItem('theme')
    if (saved) return saved
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  })

  useEffect(() => {
    document.documentElement.classList.toggle('dark', theme === 'dark')
    localStorage.setItem('theme', theme)
  }, [theme])

  return { theme, setTheme, toggle: () => setTheme(t => t === 'dark' ? 'light' : 'dark') }
}
```

---

## 7. Responsividade

### Breakpoints

| Nome | Tamanho | Uso |
|------|---------|-----|
| sm | 640px | Mobile landscape |
| md | 768px | Tablet |
| lg | 1024px | Desktop |
| xl | 1280px | Large desktop |
| 2xl | 1536px | Wide screens |

### Layout Responsivo

```css
/* Mobile first */
.container {
  padding: var(--spacing-sm);
}

@media (min-width: 768px) {
  .container {
    padding: var(--spacing-md);
  }
}

@media (min-width: 1024px) {
  .container {
    padding: var(--spacing-lg);
  }
}
```

---

## 8. Storybook

O Storybook está configurado para documentação interativa dos componentes:

```bash
# Iniciar Storybook
cd packages/design-system
pnpm storybook

# Acessar em http://localhost:6007
```

---

## 9. Guia de Uso

### Instalação

```bash
# Importar componentes do Design System
import { Button, Input, Card } from '@template/design-system'

# Importar estilos globais (já incluídos no main.tsx)
import '@/styles/index.css'
```

### Boas Práticas

1. **Use tokens, não valores hardcoded**
   ```css
   /* ❌ Evite */
   color: #0087A8;
   
   /* ✅ Prefira */
   color: var(--brand-primary);
   ```

2. **Use classes utilitárias quando possível**
   ```html
   <!-- ❌ Evite -->
   <div style="margin-bottom: 16px">
   
   <!-- ✅ Prefira -->
   <div class="form-group">
   ```

3. **Mantenha consistência**
   - Use os componentes do Design System
   - Siga os padrões de espaçamento
   - Respeite a hierarquia visual

---

## 10. Changelog

### v1.0.0 (Dezembro 2025)

- ✅ Tokens de design completos
- ✅ Dark mode consistente
- ✅ 9 componentes base
- ✅ Classes utilitárias CSS
- ✅ Animações e micro-interações
- ✅ Suporte a acessibilidade
- ✅ Responsividade mobile-first

---

*Documentação gerada automaticamente. Para contribuir, edite `docs/DESIGN_SYSTEM.md`.*
