# AeroLab UX Guidelines

> **Last Updated:** 2024-12-17

---

## Overview

This document outlines UX patterns and accessibility guidelines for AeroLab Studio.

---

## Component Inventory

### Agent Builder Components

| Component | Purpose | Status |
|-----------|---------|--------|
| `AgentTemplateSelector` | Template selection | ✅ Implemented |
| `AgentProfileSelector` | Profile configuration | ✅ Implemented |
| `AgentToolsSelector` | Tools selection | ✅ Implemented |
| `AgentRAGConfig` | RAG configuration | ✅ Implemented |
| `AgentHITLConfig` | Human-in-the-loop | ✅ Implemented |
| `AgentMemoryViewer` | Memory inspection | ✅ Implemented |
| `AgentInsights` | Analytics | ✅ Implemented |
| `AgentPreview` | Preview mode | ✅ Implemented |

### UX Components

| Component | Purpose | Status |
|-----------|---------|--------|
| `OnboardingWizard` | First-time user flow | ✅ Implemented |
| `EmptyState` | Empty state handling | ✅ Implemented |
| `CommandPalette` | Keyboard navigation | ✅ Implemented |
| `NotificationCenter` | Notifications | ✅ Implemented |
| `FeedbackWidget` | User feedback | ✅ Implemented |

---

## Accessibility (a11y) Checklist

### Keyboard Navigation
- [x] All interactive elements focusable
- [x] Tab order logical
- [x] Command palette (Cmd+K)
- [ ] Skip links for main content

### Screen Readers
- [x] Semantic HTML structure
- [x] ARIA labels on icons
- [ ] Live regions for dynamic content
- [ ] Form error announcements

### Visual
- [x] Color contrast (WCAG AA)
- [x] Focus indicators
- [x] Dark mode support
- [ ] Reduced motion preference

### Forms
- [x] Labels associated with inputs
- [x] Error messages visible
- [x] Required fields marked
- [ ] Autocomplete attributes

---

## UX Patterns

### Loading States

```tsx
// Skeleton loading
<CardListSkeleton count={3} />

// Inline loading
<Button loading>Saving...</Button>

// Page loading
<PageLoader message="Loading agents..." />
```

### Empty States

```tsx
<EmptyState
  icon={<Bot />}
  title="No agents yet"
  description="Create your first agent to get started"
  action={
    <Button onClick={handleCreate}>
      Create Agent
    </Button>
  }
/>
```

### Error States

```tsx
<ErrorBoundary
  fallback={
    <ErrorState
      title="Something went wrong"
      action={<Button onClick={retry}>Try Again</Button>}
    />
  }
>
  <Component />
</ErrorBoundary>
```

---

## Design Tokens

### Colors (Tailwind)

```css
/* Primary */
--primary: hsl(222, 47%, 11%);
--primary-foreground: hsl(210, 40%, 98%);

/* Accent */
--accent: hsl(210, 40%, 96%);

/* Destructive */
--destructive: hsl(0, 84%, 60%);

/* Muted */
--muted: hsl(210, 40%, 96%);
--muted-foreground: hsl(215, 16%, 47%);
```

### Spacing Scale

```
4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px
```

### Typography

```
Font: Inter, system-ui, sans-serif
Sizes: 12px, 14px, 16px, 18px, 24px, 30px, 36px
```

---

## Responsive Breakpoints

| Breakpoint | Width | Use Case |
|------------|-------|----------|
| `sm` | 640px | Mobile landscape |
| `md` | 768px | Tablet |
| `lg` | 1024px | Desktop |
| `xl` | 1280px | Large desktop |
| `2xl` | 1536px | Wide screens |

---

## Future Improvements

1. **Storybook** - Component documentation and playground
2. **a11y Testing** - Automated accessibility testing with axe-core
3. **Design Tokens** - Extract to CSS custom properties
4. **Animation** - Respect prefers-reduced-motion
5. **i18n** - Internationalization support

---

_Generated during AeroLab Audit - December 2024_
