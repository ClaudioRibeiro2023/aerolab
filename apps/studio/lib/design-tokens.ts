/**
 * AGNO Design System v5.0 ULTIMATE - Design Tokens
 * 
 * Centralized design tokens for consistent styling across the platform.
 */

// ============================================================
// COLOR PALETTE
// ============================================================

export const colors = {
  // Primary - Electric Blue
  primary: {
    50: '#eff6ff',
    100: '#dbeafe',
    200: '#bfdbfe',
    300: '#93c5fd',
    400: '#60a5fa',
    500: '#3b82f6',
    600: '#2563eb',
    700: '#1d4ed8',
    800: '#1e40af',
    900: '#1e3a8a',
    950: '#172554',
  },
  
  // Accent - Cosmic Purple
  accent: {
    50: '#faf5ff',
    100: '#f3e8ff',
    200: '#e9d5ff',
    300: '#d8b4fe',
    400: '#c084fc',
    500: '#a855f7',
    600: '#9333ea',
    700: '#7e22ce',
    800: '#6b21a8',
    900: '#581c87',
    950: '#3b0764',
  },
  
  // Success - Emerald
  success: {
    50: '#ecfdf5',
    100: '#d1fae5',
    400: '#34d399',
    500: '#10b981',
    600: '#059669',
  },
  
  // Warning - Amber
  warning: {
    50: '#fffbeb',
    100: '#fef3c7',
    400: '#fbbf24',
    500: '#f59e0b',
    600: '#d97706',
  },
  
  // Error - Red
  error: {
    50: '#fef2f2',
    100: '#fee2e2',
    400: '#f87171',
    500: '#ef4444',
    600: '#dc2626',
  },
  
  // Slate - Neutrals
  slate: {
    50: '#f8fafc',
    100: '#f1f5f9',
    200: '#e2e8f0',
    300: '#cbd5e1',
    400: '#94a3b8',
    500: '#64748b',
    600: '#475569',
    700: '#334155',
    800: '#1e293b',
    900: '#0f172a',
    950: '#020617',
  },
} as const;

// ============================================================
// GRADIENTS
// ============================================================

export const gradients = {
  // Signature gradients
  agno: 'linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%)',
  aurora: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
  cosmic: 'linear-gradient(135deg, #1e3a5f 0%, #0f172a 100%)',
  sunset: 'linear-gradient(135deg, #f97316 0%, #ec4899 100%)',
  ocean: 'linear-gradient(135deg, #06b6d4 0%, #3b82f6 100%)',
  forest: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
  
  // Glass effects
  glass: 'linear-gradient(135deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%)',
  glassDark: 'linear-gradient(135deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.1) 100%)',
  
  // Domain-specific
  legal: 'linear-gradient(135deg, #dc2626 0%, #f43f5e 100%)',
  finance: 'linear-gradient(135deg, #10b981 0%, #14b8a6 100%)',
  healthcare: 'linear-gradient(135deg, #0ea5e9 0%, #06b6d4 100%)',
  data: 'linear-gradient(135deg, #8b5cf6 0%, #a855f7 100%)',
  geo: 'linear-gradient(135deg, #f59e0b 0%, #f97316 100%)',
  devops: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)',
  hr: 'linear-gradient(135deg, #ec4899 0%, #f43f5e 100%)',
  marketing: 'linear-gradient(135deg, #f97316 0%, #eab308 100%)',
  sales: 'linear-gradient(135deg, #22c55e 0%, #10b981 100%)',
  education: 'linear-gradient(135deg, #3b82f6 0%, #6366f1 100%)',
  realestate: 'linear-gradient(135deg, #78716c 0%, #a8a29e 100%)',
  insurance: 'linear-gradient(135deg, #0891b2 0%, #0e7490 100%)',
  government: 'linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%)',
  energy: 'linear-gradient(135deg, #eab308 0%, #84cc16 100%)',
  supply: 'linear-gradient(135deg, #7c3aed 0%, #6d28d9 100%)',
} as const;

// ============================================================
// TYPOGRAPHY
// ============================================================

export const typography = {
  fonts: {
    display: '"Cal Sans", "Inter", system-ui, -apple-system, sans-serif',
    body: '"Inter", system-ui, -apple-system, sans-serif',
    mono: '"JetBrains Mono", "Fira Code", monospace',
  },
  
  sizes: {
    xs: '0.75rem',     // 12px
    sm: '0.875rem',    // 14px
    base: '1rem',      // 16px
    lg: '1.125rem',    // 18px
    xl: '1.25rem',     // 20px
    '2xl': '1.5rem',   // 24px
    '3xl': '1.875rem', // 30px
    '4xl': '2.25rem',  // 36px
    '5xl': '3rem',     // 48px
    '6xl': '3.75rem',  // 60px
    '7xl': '4.5rem',   // 72px
  },
  
  weights: {
    normal: '400',
    medium: '500',
    semibold: '600',
    bold: '700',
    extrabold: '800',
  },
  
  lineHeights: {
    tight: '1.25',
    normal: '1.5',
    relaxed: '1.75',
  },
} as const;

// ============================================================
// SPACING
// ============================================================

export const spacing = {
  0: '0',
  px: '1px',
  0.5: '0.125rem',
  1: '0.25rem',
  1.5: '0.375rem',
  2: '0.5rem',
  2.5: '0.625rem',
  3: '0.75rem',
  3.5: '0.875rem',
  4: '1rem',
  5: '1.25rem',
  6: '1.5rem',
  7: '1.75rem',
  8: '2rem',
  9: '2.25rem',
  10: '2.5rem',
  12: '3rem',
  14: '3.5rem',
  16: '4rem',
  20: '5rem',
  24: '6rem',
  28: '7rem',
  32: '8rem',
  36: '9rem',
  40: '10rem',
} as const;

// ============================================================
// BORDER RADIUS
// ============================================================

export const radius = {
  none: '0',
  sm: '0.375rem',
  md: '0.5rem',
  lg: '0.75rem',
  xl: '1rem',
  '2xl': '1.5rem',
  '3xl': '2rem',
  full: '9999px',
} as const;

// ============================================================
// SHADOWS
// ============================================================

export const shadows = {
  sm: '0 1px 2px 0 rgb(0 0 0 / 0.05)',
  md: '0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)',
  lg: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
  xl: '0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)',
  '2xl': '0 25px 50px -12px rgb(0 0 0 / 0.25)',
  inner: 'inset 0 2px 4px 0 rgb(0 0 0 / 0.05)',
  
  // Glow effects
  glow: {
    blue: '0 0 40px rgba(59, 130, 246, 0.3)',
    purple: '0 0 40px rgba(139, 92, 246, 0.3)',
    pink: '0 0 40px rgba(236, 72, 153, 0.3)',
    emerald: '0 0 40px rgba(16, 185, 129, 0.3)',
  },
} as const;

// ============================================================
// ANIMATIONS
// ============================================================

export const animations = {
  durations: {
    fast: '150ms',
    normal: '200ms',
    slow: '300ms',
    slower: '500ms',
  },
  
  easings: {
    default: 'cubic-bezier(0.4, 0, 0.2, 1)',
    in: 'cubic-bezier(0.4, 0, 1, 1)',
    out: 'cubic-bezier(0, 0, 0.2, 1)',
    inOut: 'cubic-bezier(0.4, 0, 0.2, 1)',
    bounce: 'cubic-bezier(0.68, -0.55, 0.265, 1.55)',
  },
} as const;

// ============================================================
// BREAKPOINTS
// ============================================================

export const breakpoints = {
  xs: '475px',
  sm: '640px',
  md: '768px',
  lg: '1024px',
  xl: '1280px',
  '2xl': '1536px',
} as const;

// ============================================================
// Z-INDEX
// ============================================================

export const zIndex = {
  hide: -1,
  base: 0,
  dropdown: 10,
  sticky: 20,
  fixed: 30,
  overlay: 40,
  modal: 50,
  popover: 60,
  tooltip: 70,
  toast: 80,
  spotlight: 90,
  max: 100,
} as const;

// ============================================================
// DOMAIN THEMES
// ============================================================

export const domainThemes = {
  legal: {
    name: 'Jurídico',
    icon: '⚖️',
    primary: colors.error[600],
    gradient: gradients.legal,
    pattern: 'scales',
  },
  finance: {
    name: 'Financeiro',
    icon: '📈',
    primary: colors.success[500],
    gradient: gradients.finance,
    pattern: 'charts',
  },
  healthcare: {
    name: 'Saúde',
    icon: '🏥',
    primary: '#0ea5e9',
    gradient: gradients.healthcare,
    pattern: 'pulse',
  },
  data: {
    name: 'Dados',
    icon: '📊',
    primary: colors.accent[500],
    gradient: gradients.data,
    pattern: 'grid',
  },
  geo: {
    name: 'Geolocalização',
    icon: '🗺️',
    primary: colors.warning[500],
    gradient: gradients.geo,
    pattern: 'map',
  },
  devops: {
    name: 'DevOps',
    icon: '🔧',
    primary: '#6366f1',
    gradient: gradients.devops,
    pattern: 'code',
  },
  hr: {
    name: 'RH',
    icon: '👥',
    primary: '#ec4899',
    gradient: gradients.hr,
    pattern: 'people',
  },
  marketing: {
    name: 'Marketing',
    icon: '📢',
    primary: '#f97316',
    gradient: gradients.marketing,
    pattern: 'megaphone',
  },
  sales: {
    name: 'Vendas',
    icon: '💰',
    primary: '#22c55e',
    gradient: gradients.sales,
    pattern: 'money',
  },
  education: {
    name: 'Educação',
    icon: '📚',
    primary: colors.primary[500],
    gradient: gradients.education,
    pattern: 'books',
  },
  realestate: {
    name: 'Imobiliário',
    icon: '🏠',
    primary: '#78716c',
    gradient: gradients.realestate,
    pattern: 'buildings',
  },
  insurance: {
    name: 'Seguros',
    icon: '🛡️',
    primary: '#0891b2',
    gradient: gradients.insurance,
    pattern: 'shield',
  },
  government: {
    name: 'Governo',
    icon: '🏛️',
    primary: '#1e40af',
    gradient: gradients.government,
    pattern: 'flag',
  },
  energy: {
    name: 'Energia',
    icon: '⚡',
    primary: '#eab308',
    gradient: gradients.energy,
    pattern: 'bolt',
  },
  supply: {
    name: 'Supply Chain',
    icon: '📦',
    primary: '#7c3aed',
    gradient: gradients.supply,
    pattern: 'boxes',
  },
} as const;

// ============================================================
// KEYBOARD SHORTCUTS
// ============================================================

export const shortcuts = {
  global: {
    commandPalette: 'mod+k',
    showShortcuts: 'mod+/',
    newAgent: 'mod+n',
    newTeam: 'mod+t',
    newWorkflow: 'mod+shift+n',
    toggleSidebar: 'mod+.',
    settings: 'mod+,',
    dashboard: 'mod+1',
    agents: 'mod+2',
    teams: 'mod+3',
    workflows: 'mod+4',
    domains: 'mod+5',
    search: 'mod+f',
    help: '?',
    escape: 'esc',
  },
  navigation: {
    goToDashboard: 'g d',
    goToAgents: 'g a',
    goToTeams: 'g t',
    goToWorkflows: 'g w',
    goToDomains: 'g o',
    goToSettings: 'g s',
  },
  actions: {
    save: 'mod+s',
    delete: 'mod+backspace',
    duplicate: 'mod+d',
    undo: 'mod+z',
    redo: 'mod+shift+z',
  },
} as const;

// ============================================================
// EXPORTS
// ============================================================

export const tokens = {
  colors,
  gradients,
  typography,
  spacing,
  radius,
  shadows,
  animations,
  breakpoints,
  zIndex,
  domainThemes,
  shortcuts,
} as const;

export default tokens;
