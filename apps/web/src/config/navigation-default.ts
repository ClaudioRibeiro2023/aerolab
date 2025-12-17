/**
 * Configuração Padrão de Navegação
 * 
 * Este arquivo contém a configuração inicial/fallback para a navegação.
 * Em produção, esta configuração pode ser sobrescrita pela API.
 */

import type { 
  NavigationConfig, 
  ModuleConfig, 
  FilterConfig,
  CategoryConfig
} from './navigation-schema'

// ═══════════════════════════════════════════════════════════════
// CATEGORIAS PADRÃO
// ═══════════════════════════════════════════════════════════════

export const DEFAULT_CATEGORIES: CategoryConfig[] = [
  { id: 'ANALISE', label: 'Análise', order: 1, defaultExpanded: true },
  { id: 'MAPEAMENTO', label: 'Mapeamento', order: 2, defaultExpanded: true },
  { id: 'INDICADORES', label: 'Indicadores', order: 3, defaultExpanded: true },
  { id: 'CONTROLE', label: 'Controle', order: 4, defaultExpanded: true },
  { id: 'OPERACIONAL', label: 'Operacional', order: 5, defaultExpanded: true },
  { id: 'CONFIG', label: 'Configuração', order: 6, defaultExpanded: false },
  { id: 'OTHER', label: 'Outros', order: 99, defaultExpanded: true },
]

// ═══════════════════════════════════════════════════════════════
// FILTROS PADRÃO
// ═══════════════════════════════════════════════════════════════

export const DEFAULT_FILTERS: FilterConfig[] = [
  {
    id: 'filter-category',
    name: 'Categoria',
    type: 'multiselect',
    placeholder: 'Filtrar por categoria...',
    options: [
      { value: 'ANALISE', label: 'Análise' },
      { value: 'MAPEAMENTO', label: 'Mapeamento' },
      { value: 'INDICADORES', label: 'Indicadores' },
      { value: 'CONTROLE', label: 'Controle' },
      { value: 'OPERACIONAL', label: 'Operacional' },
    ],
    order: 1,
    enabled: true,
    appliesTo: { global: true },
  },
  {
    id: 'filter-status',
    name: 'Status',
    type: 'select',
    placeholder: 'Todos os status',
    options: [
      { value: 'all', label: 'Todos' },
      { value: 'active', label: 'Ativos' },
      { value: 'inactive', label: 'Inativos' },
      { value: 'beta', label: 'Beta' },
    ],
    order: 2,
    enabled: true,
    appliesTo: { modules: ['etl', 'observabilidade'] },
  },
  {
    id: 'filter-date',
    name: 'Período',
    type: 'daterange',
    placeholder: 'Selecionar período...',
    order: 3,
    enabled: true,
    appliesTo: { modules: ['relatorios', 'observabilidade'] },
  },
]

// ═══════════════════════════════════════════════════════════════
// MÓDULOS PADRÃO
// ═══════════════════════════════════════════════════════════════

export const DEFAULT_MODULES: ModuleConfig[] = [
  // ─────────────────────────────────────────────────────────────
  // DASHBOARD
  // ─────────────────────────────────────────────────────────────
  {
    id: 'dashboard',
    name: 'Dashboard',
    description: 'Painel principal com KPIs e visão geral',
    icon: 'LayoutGrid',
    path: '/dashboard',
    enabled: true,
    order: 1,
    roles: [],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Principal',
    functions: [
      { id: 'dashboard-main', moduleId: 'dashboard', name: 'Visão Geral', subtitle: 'KPIs e métricas principais', path: '/dashboard', category: 'INDICADORES', enabled: true, order: 0, roles: [], tags: ['kpi', 'metricas'] },
      { id: 'dashboard-analytics', moduleId: 'dashboard', name: 'Analytics', subtitle: 'Análises detalhadas', path: '/dashboard/analytics', category: 'ANALISE', enabled: true, order: 1, roles: [], tags: ['graficos', 'analise'] },
      { id: 'dashboard-alerts', moduleId: 'dashboard', name: 'Alertas', subtitle: 'Notificações e watchlist', path: '/dashboard/alerts', category: 'CONTROLE', enabled: true, order: 2, roles: [], tags: ['alertas', 'notificacoes'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // RELATÓRIOS
  // ─────────────────────────────────────────────────────────────
  {
    id: 'relatorios',
    name: 'Relatórios',
    description: 'Relatórios e exportações',
    icon: 'BarChart3',
    path: '/relatorios',
    enabled: true,
    order: 2,
    roles: [],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Principal',
    functions: [
      { id: 'relatorios-gerenciais', moduleId: 'relatorios', name: 'Gerenciais', subtitle: 'Relatórios de gestão', path: '/relatorios', category: 'INDICADORES', enabled: true, order: 0, roles: [], tags: ['relatorios', 'gestao'] },
      { id: 'relatorios-operacionais', moduleId: 'relatorios', name: 'Operacionais', subtitle: 'Relatórios de operação', path: '/relatorios/operacionais', category: 'OPERACIONAL', enabled: true, order: 1, roles: [], tags: ['relatorios', 'operacao'] },
      { id: 'exportacoes', moduleId: 'relatorios', name: 'Exportações', subtitle: 'Download de dados', path: '/relatorios/export', category: 'OPERACIONAL', enabled: true, order: 2, roles: [], tags: ['export', 'download'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // EXEMPLO
  // ─────────────────────────────────────────────────────────────
  {
    id: 'exemplo',
    name: 'Módulo Exemplo',
    description: 'Exemplo de módulo com submenus',
    icon: 'LayoutGrid',
    path: '/exemplo',
    enabled: true,
    order: 3,
    roles: [],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Módulos',
    functions: [
      { id: 'exemplo-listagem', moduleId: 'exemplo', name: 'Listagem', subtitle: 'Lista de registros', path: '/exemplo', category: 'OPERACIONAL', enabled: true, order: 0, roles: [], tags: ['listagem', 'registros'] },
      { id: 'exemplo-cadastro', moduleId: 'exemplo', name: 'Cadastro', subtitle: 'Novo registro', path: '/exemplo/novo', category: 'OPERACIONAL', enabled: true, order: 1, roles: [], tags: ['cadastro', 'novo'] },
      { id: 'exemplo-mapa', moduleId: 'exemplo', name: 'Mapa', subtitle: 'Visualização espacial', path: '/exemplo/mapa', category: 'MAPEAMENTO', enabled: true, order: 2, roles: [], tags: ['mapa', 'geo'] },
      { id: 'exemplo-graficos', moduleId: 'exemplo', name: 'Gráficos', subtitle: 'Análises visuais', path: '/exemplo/graficos', category: 'ANALISE', enabled: true, order: 3, roles: [], tags: ['graficos', 'analise'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // ETL & INTEGRAÇÃO
  // ─────────────────────────────────────────────────────────────
  {
    id: 'etl',
    name: 'ETL & Integração',
    description: 'Importadores, tratamento e catálogo de dados',
    icon: 'Database',
    path: '/admin/etl',
    enabled: true,
    order: 10,
    roles: ['ADMIN'],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Administração',
    metadata: { badge: 'BETA' },
    functions: [
      { id: 'etl-import-csv', moduleId: 'etl', name: 'Importar CSV', subtitle: 'Arquivos CSV e planilhas', path: '/admin/etl?src=csv', category: 'OPERACIONAL', enabled: true, order: 0, roles: [], tags: ['import', 'csv'] },
      { id: 'etl-import-json', moduleId: 'etl', name: 'Importar JSON', subtitle: 'Arquivos JSON e APIs', path: '/admin/etl?src=json', category: 'OPERACIONAL', enabled: true, order: 1, roles: [], tags: ['import', 'json'] },
      { id: 'etl-import-shape', moduleId: 'etl', name: 'Importar Shapefile', subtitle: 'Dados geoespaciais', path: '/admin/etl?src=shapefile', category: 'OPERACIONAL', enabled: true, order: 2, roles: [], tags: ['import', 'shapefile', 'geo'] },
      { id: 'etl-import-api', moduleId: 'etl', name: 'Conectores API', subtitle: 'Integrações externas', path: '/admin/etl?src=api', category: 'OPERACIONAL', enabled: true, order: 3, roles: [], tags: ['api', 'integracao'] },
      { id: 'etl-transform', moduleId: 'etl', name: 'Tratamento/Mapeamento', subtitle: 'Transformação de dados', path: '/admin/etl/transform', category: 'OPERACIONAL', enabled: true, order: 4, roles: [], tags: ['transform', 'mapeamento'] },
      { id: 'etl-validation', moduleId: 'etl', name: 'Validação', subtitle: 'Regras de validação', path: '/admin/etl/validation', category: 'CONTROLE', enabled: true, order: 5, roles: [], tags: ['validacao', 'regras'] },
      { id: 'etl-catalogo', moduleId: 'etl', name: 'Catálogo de Dados', subtitle: 'Metadados e dicionário', path: '/admin/etl/catalog', category: 'CONTROLE', enabled: true, order: 6, roles: [], tags: ['catalogo', 'metadados'] },
      { id: 'etl-lineage', moduleId: 'etl', name: 'Linhagem de Dados', subtitle: 'Origem e transformações', path: '/admin/etl/lineage', category: 'ANALISE', enabled: true, order: 7, roles: [], tags: ['lineage', 'origem'] },
      { id: 'etl-qualidade', moduleId: 'etl', name: 'Qualidade', subtitle: 'Completude, consistência e outliers', path: '/admin/etl/quality', category: 'CONTROLE', enabled: true, order: 8, roles: [], tags: ['qualidade', 'dados'] },
      { id: 'etl-profiling', moduleId: 'etl', name: 'Data Profiling', subtitle: 'Estatísticas e distribuições', path: '/admin/etl/profiling', category: 'ANALISE', enabled: true, order: 9, roles: [], tags: ['profiling', 'estatisticas'] },
      { id: 'etl-jobs', moduleId: 'etl', name: 'Jobs & Agendamentos', subtitle: 'Execuções programadas', path: '/admin/etl/jobs', category: 'OPERACIONAL', enabled: true, order: 10, roles: [], tags: ['jobs', 'agendamento'] },
      { id: 'etl-logs', moduleId: 'etl', name: 'Logs & Reprocesso', subtitle: 'Histórico e rastreabilidade', path: '/admin/etl/logs', category: 'CONTROLE', enabled: true, order: 11, roles: [], tags: ['logs', 'historico'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // CONFIGURAÇÕES
  // ─────────────────────────────────────────────────────────────
  {
    id: 'configuracoes',
    name: 'Configurações',
    description: 'Parâmetros do sistema',
    icon: 'Settings',
    path: '/admin/config',
    enabled: true,
    order: 11,
    roles: ['ADMIN', 'GESTOR'],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Administração',
    functions: [
      { id: 'config-geral', moduleId: 'configuracoes', name: 'Geral', subtitle: 'Configurações gerais', path: '/admin/config', category: 'CONFIG', enabled: true, order: 0, roles: [], tags: ['config', 'geral'] },
      { id: 'config-aparencia', moduleId: 'configuracoes', name: 'Aparência', subtitle: 'Tema e personalização', path: '/admin/config/aparencia', category: 'CONFIG', enabled: true, order: 1, roles: [], tags: ['tema', 'aparencia'] },
      { id: 'config-notificacoes', moduleId: 'configuracoes', name: 'Notificações', subtitle: 'Alertas e emails', path: '/admin/config/notificacoes', category: 'CONFIG', enabled: true, order: 2, roles: [], tags: ['notificacoes', 'alertas'] },
      { id: 'config-integracao', moduleId: 'configuracoes', name: 'Integrações', subtitle: 'APIs e webhooks', path: '/admin/config/integracoes', category: 'CONFIG', enabled: true, order: 3, roles: [], tags: ['api', 'webhook'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // OBSERVABILIDADE
  // ─────────────────────────────────────────────────────────────
  {
    id: 'observabilidade',
    name: 'Observabilidade',
    description: 'Métricas, logs e qualidade operacional',
    icon: 'Activity',
    path: '/admin/observability',
    enabled: true,
    order: 12,
    roles: ['ADMIN'],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Administração',
    metadata: { badge: 'DEV' },
    functions: [
      { id: 'obs-metricas', moduleId: 'observabilidade', name: 'Métricas', subtitle: 'Prometheus/metrics de API e jobs', path: '/admin/observability/metrics', category: 'CONTROLE', enabled: true, order: 0, roles: [], tags: ['metricas', 'prometheus'] },
      { id: 'obs-logs', moduleId: 'observabilidade', name: 'Logs', subtitle: 'Estruturados e correlação por request-id', path: '/admin/observability/logs', category: 'CONTROLE', enabled: true, order: 1, roles: [], tags: ['logs', 'request'] },
      { id: 'obs-health', moduleId: 'observabilidade', name: 'Saúde', subtitle: 'Health checks, filas e storage', path: '/admin/observability/health', category: 'CONTROLE', enabled: true, order: 2, roles: [], tags: ['health', 'saude'] },
      { id: 'obs-quality', moduleId: 'observabilidade', name: 'Qualidade de Dados', subtitle: 'Checks recorrentes e painéis', path: '/admin/observability/data-quality', category: 'CONTROLE', enabled: true, order: 3, roles: [], tags: ['qualidade', 'dados'] },
      { id: 'obs-traces', moduleId: 'observabilidade', name: 'Traces', subtitle: 'Rastreamento distribuído', path: '/admin/observability/traces', category: 'ANALISE', enabled: true, order: 4, roles: [], tags: ['traces', 'rastreamento'] },
      { id: 'obs-alerts', moduleId: 'observabilidade', name: 'Alertas', subtitle: 'Configuração de alertas', path: '/admin/observability/alerts', category: 'CONTROLE', enabled: true, order: 5, roles: [], tags: ['alertas', 'config'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // DOCUMENTAÇÃO
  // ─────────────────────────────────────────────────────────────
  {
    id: 'documentacao',
    name: 'Documentação',
    description: 'Guias, tutoriais e referências',
    icon: 'FileText',
    path: '/docs',
    enabled: true,
    order: 20,
    roles: [],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Suporte',
    functions: [
      { id: 'docs-inicio', moduleId: 'documentacao', name: 'Início Rápido', subtitle: 'Primeiros passos', path: '/docs', category: 'INDICADORES', enabled: true, order: 0, roles: [], tags: ['inicio', 'tutorial'] },
      { id: 'docs-guias', moduleId: 'documentacao', name: 'Guias', subtitle: 'Tutoriais detalhados', path: '/docs/guias', category: 'INDICADORES', enabled: true, order: 1, roles: [], tags: ['guia', 'tutorial'] },
      { id: 'docs-api', moduleId: 'documentacao', name: 'API Reference', subtitle: 'Documentação da API', path: '/docs/api', category: 'CONTROLE', enabled: true, order: 2, roles: [], tags: ['api', 'referencia'] },
      { id: 'docs-arquitetura', moduleId: 'documentacao', name: 'Arquitetura', subtitle: 'Decisões técnicas (ADRs)', path: '/docs/arquitetura', category: 'ANALISE', enabled: true, order: 3, roles: [], tags: ['arquitetura', 'adr'] },
      { id: 'docs-changelog', moduleId: 'documentacao', name: 'Changelog', subtitle: 'Histórico de versões', path: '/docs/changelog', category: 'INDICADORES', enabled: true, order: 4, roles: [], tags: ['changelog', 'versoes'] },
      { id: 'docs-faq', moduleId: 'documentacao', name: 'FAQ', subtitle: 'Perguntas frequentes', path: '/docs/faq', category: 'INDICADORES', enabled: true, order: 5, roles: [], tags: ['faq', 'ajuda'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // LGPD
  // ─────────────────────────────────────────────────────────────
  {
    id: 'lgpd',
    name: 'LGPD & Privacidade',
    description: 'Compliance e proteção de dados',
    icon: 'Shield',
    path: '/lgpd',
    enabled: true,
    order: 21,
    roles: [],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Suporte',
    functions: [
      { id: 'lgpd-politica', moduleId: 'lgpd', name: 'Política de Privacidade', subtitle: 'Termos e condições', path: '/lgpd', category: 'INDICADORES', enabled: true, order: 0, roles: [], tags: ['politica', 'privacidade'] },
      { id: 'lgpd-consentimento', moduleId: 'lgpd', name: 'Consentimento', subtitle: 'Gerenciar permissões', path: '/lgpd/consentimento', category: 'CONTROLE', enabled: true, order: 1, roles: [], tags: ['consentimento', 'permissoes'] },
      { id: 'lgpd-dados', moduleId: 'lgpd', name: 'Meus Dados', subtitle: 'Exportar/excluir dados pessoais', path: '/lgpd/meus-dados', category: 'OPERACIONAL', enabled: true, order: 2, roles: [], tags: ['dados', 'pessoais'] },
      { id: 'lgpd-cookies', moduleId: 'lgpd', name: 'Cookies', subtitle: 'Preferências de cookies', path: '/lgpd/cookies', category: 'CONTROLE', enabled: true, order: 3, roles: [], tags: ['cookies', 'preferencias'] },
      { id: 'lgpd-solicitacoes', moduleId: 'lgpd', name: 'Solicitações', subtitle: 'Requisições de titulares', path: '/lgpd/solicitacoes', category: 'OPERACIONAL', enabled: true, order: 4, roles: ['ADMIN'], tags: ['solicitacoes', 'titulares'] },
      { id: 'lgpd-auditoria', moduleId: 'lgpd', name: 'Auditoria LGPD', subtitle: 'Logs de consentimento', path: '/lgpd/auditoria', category: 'CONTROLE', enabled: true, order: 5, roles: ['ADMIN'], tags: ['auditoria', 'logs'] },
    ],
  },

  // ─────────────────────────────────────────────────────────────
  // ADMINISTRAÇÃO
  // ─────────────────────────────────────────────────────────────
  {
    id: 'administracao',
    name: 'Administração',
    description: 'Gestão de usuários e sistema',
    icon: 'Users',
    path: '/admin',
    enabled: true,
    order: 30,
    roles: ['ADMIN'],
    showInSidebar: true,
    showInFunctionsPanel: true,
    group: 'Administração',
    functions: [
      { id: 'admin-usuarios', moduleId: 'administracao', name: 'Usuários', subtitle: 'Gestão de usuários', path: '/admin/usuarios', category: 'CONTROLE', enabled: true, order: 0, roles: ['ADMIN'], tags: ['usuarios', 'gestao'] },
      { id: 'admin-perfis', moduleId: 'administracao', name: 'Perfis e Roles', subtitle: 'Permissões', path: '/admin/perfis', category: 'CONTROLE', enabled: true, order: 1, roles: ['ADMIN'], tags: ['perfis', 'roles'] },
      { id: 'admin-entidades', moduleId: 'administracao', name: 'Entidades', subtitle: 'Organizações e unidades', path: '/admin/entidades', category: 'CONTROLE', enabled: true, order: 2, roles: [], tags: ['entidades', 'organizacoes'] },
      { id: 'admin-auditoria', moduleId: 'administracao', name: 'Auditoria', subtitle: 'Logs de ações', path: '/admin/auditoria', category: 'CONTROLE', enabled: true, order: 3, roles: [], tags: ['auditoria', 'logs'] },
    ],
  },
]

// ═══════════════════════════════════════════════════════════════
// CONFIGURAÇÃO COMPLETA PADRÃO
// ═══════════════════════════════════════════════════════════════

export const DEFAULT_NAVIGATION_CONFIG: NavigationConfig = {
  version: '1.0.0',
  appName: 'AeroLab',
  appVersion: '0.1.0',
  modules: DEFAULT_MODULES,
  filters: DEFAULT_FILTERS,
  categories: DEFAULT_CATEGORIES,
  settings: {
    enableFavorites: true,
    enableGlobalSearch: true,
    enableKeyboardShortcuts: true,
    defaultTheme: 'system',
    defaultLanguage: 'pt-BR',
  },
  updatedAt: new Date().toISOString(),
}

export default DEFAULT_NAVIGATION_CONFIG
