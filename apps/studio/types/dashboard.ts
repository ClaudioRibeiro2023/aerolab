/**
 * Dashboard Types - Tipos TypeScript para o módulo de dashboards.
 */

// ============================================================
// Widget Types
// ============================================================

export type WidgetType =
  | 'metric_card'
  | 'line_chart'
  | 'area_chart'
  | 'bar_chart'
  | 'pie_chart'
  | 'donut_chart'
  | 'scatter_chart'
  | 'heatmap'
  | 'table'
  | 'text'
  | 'markdown'
  | 'gauge'
  | 'sparkline'
  | 'stat_comparison'
  | 'progress'
  | 'status_indicator'
  | 'timeline'
  | 'log_viewer'
  | 'trace_viewer'
  | 'map'
  | 'sankey'
  | 'treemap'
  | 'funnel'
  | 'radar'
  | 'flame_graph'
  | 'custom';

export type WidgetSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'full';

export interface GridPosition {
  x: number;
  y: number;
  w: number;
  h: number;
  minW?: number;
  minH?: number;
  maxW?: number;
  maxH?: number;
}

export interface ChartConfig {
  xAxis?: string;
  yAxis?: string;
  seriesField?: string;
  colorScheme?: string[];
  showLegend?: boolean;
  showGrid?: boolean;
  showTooltip?: boolean;
  stacked?: boolean;
  smooth?: boolean;
  areaOpacity?: number;
}

export interface TableConfig {
  columns: TableColumn[];
  sortable?: boolean;
  filterable?: boolean;
  pagination?: boolean;
  pageSize?: number;
  rowActions?: string[];
}

export interface TableColumn {
  key: string;
  title: string;
  width?: number;
  align?: 'left' | 'center' | 'right';
  format?: 'text' | 'number' | 'currency' | 'percent' | 'date' | 'duration' | 'badge';
  sortable?: boolean;
}

export interface GaugeConfig {
  min?: number;
  max?: number;
  thresholds?: GaugeThreshold[];
  showValue?: boolean;
  unit?: string;
}

export interface GaugeThreshold {
  value: number;
  color: string;
  label?: string;
}

export interface MetricConfig {
  format?: 'number' | 'currency' | 'percent' | 'duration' | 'bytes';
  precision?: number;
  prefix?: string;
  suffix?: string;
  showTrend?: boolean;
  trendPeriod?: string;
  sparkline?: boolean;
}

export interface WidgetConfig {
  chart?: ChartConfig;
  table?: TableConfig;
  metric?: MetricConfig;
  gauge?: GaugeConfig;
  filters?: Record<string, unknown>;
  drilldown?: DrilldownConfig;
}

export interface DrilldownConfig {
  enabled: boolean;
  targetDashboard?: string;
  targetWidget?: string;
  params?: Record<string, string>;
}

export interface Widget {
  id: string;
  title: string;
  description?: string;
  type: WidgetType;
  dataSourceId?: string;
  query: string;
  config: WidgetConfig;
  position?: GridPosition;
  refreshIntervalSeconds?: number;
  tags?: string[];
  createdAt?: string;
  updatedAt?: string;
}

export interface WidgetData {
  widgetId: string;
  data: unknown;
  loading: boolean;
  error?: string;
  lastUpdated?: string;
}

// ============================================================
// Layout Types
// ============================================================

export type LayoutType = 'grid' | 'tabs' | 'split' | 'masonry' | 'free';

export interface LayoutItem {
  widgetId: string;
  position: GridPosition;
  visible?: boolean;
}

export interface TabConfig {
  id: string;
  label: string;
  icon?: string;
  widgetIds: string[];
}

export interface Layout {
  id: string;
  type: LayoutType;
  items: LayoutItem[];
  columns?: number;
  rowHeight?: number;
  gap?: number;
  tabs?: TabConfig[];
}

// ============================================================
// Dashboard Types
// ============================================================

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  slug: string;
  widgets: Widget[];
  layout: Layout;
  themeId?: string;
  defaultTimeRange: string;
  timeZone: string;
  autoRefresh: boolean;
  refreshIntervalSeconds: number;
  globalFilters: Record<string, unknown>;
  variables: Record<string, unknown>;
  folderId?: string;
  tags: string[];
  version: number;
  createdAt: string;
  updatedAt: string;
  createdBy: string;
  isFavorite: boolean;
  isTemplate: boolean;
  isPublished: boolean;
}

export interface DashboardSummary {
  id: string;
  name: string;
  slug: string;
  description?: string;
  tags: string[];
  isFavorite: boolean;
  isTemplate: boolean;
  updatedAt: string;
  widgetCount: number;
}

export interface DashboardFolder {
  id: string;
  name: string;
  parentId?: string;
  createdAt: string;
  dashboardCount?: number;
}

// ============================================================
// Data Source Types
// ============================================================

export type DataSourceType =
  | 'internal'
  | 'agent_metrics'
  | 'system_metrics'
  | 'postgresql'
  | 'mysql'
  | 'mongodb'
  | 'elasticsearch'
  | 'prometheus'
  | 'graphite'
  | 'influxdb'
  | 'http'
  | 'graphql';

export interface DataSource {
  id: string;
  name: string;
  type: DataSourceType;
  description?: string;
  isDefault?: boolean;
  config?: Record<string, unknown>;
  createdAt?: string;
}

// ============================================================
// Theme Types
// ============================================================

export type ThemeMode = 'light' | 'dark' | 'system';

export interface ColorPalette {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  info: string;
  background: string;
  surface: string;
  text: string;
  textSecondary: string;
  border: string;
  chart: string[];
}

export interface DashboardTheme {
  id: string;
  name: string;
  mode: ThemeMode;
  colors: ColorPalette;
  isDefault?: boolean;
  isCustom?: boolean;
}

// ============================================================
// Alert Types
// ============================================================

export type AlertSeverity = 'info' | 'warning' | 'error' | 'critical';
export type AlertState = 'ok' | 'pending' | 'firing' | 'resolved';

export interface AlertCondition {
  metric: string;
  operator: string;
  threshold: number;
  duration?: string;
  labels?: Record<string, string>;
}

export interface AlertRule {
  id: string;
  name: string;
  description?: string;
  conditions: AlertCondition[];
  conditionLogic: 'and' | 'or';
  severity: AlertSeverity;
  channelIds: string[];
  enabled: boolean;
  state: AlertState;
  silencedUntil?: string;
  summary?: string;
  runbookUrl?: string;
  labels?: Record<string, string>;
  lastEvaluation?: string;
  firingSince?: string;
  createdAt: string;
}

export interface AlertEvent {
  ruleId: string;
  ruleName: string;
  state: AlertState;
  severity: AlertSeverity;
  timestamp: string;
  message: string;
  values: Record<string, number>;
  labels: Record<string, string>;
}

// ============================================================
// Incident Types
// ============================================================

export type IncidentStatus =
  | 'open'
  | 'acknowledged'
  | 'investigating'
  | 'identified'
  | 'monitoring'
  | 'resolved'
  | 'closed';

export type IncidentSeverity = 'sev1' | 'sev2' | 'sev3' | 'sev4';

export interface IncidentUpdate {
  id: string;
  timestamp: string;
  author: string;
  message: string;
  statusChange?: IncidentStatus;
}

export interface Incident {
  id: string;
  title: string;
  description?: string;
  alertRuleIds: string[];
  severity: IncidentSeverity;
  status: IncidentStatus;
  impactedServices: string[];
  owner?: string;
  responders: string[];
  updates: IncidentUpdate[];
  createdAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  duration?: string;
  rootCause?: string;
  resolution?: string;
  labels: Record<string, string>;
}

// ============================================================
// Metrics Types
// ============================================================

export interface MetricPoint {
  timestamp: string;
  value: number;
  labels?: Record<string, string>;
}

export interface MetricSeries {
  metric: string;
  labels: Record<string, string>;
  points: MetricPoint[];
}

export interface QueryResult {
  data: unknown[];
  metric?: string;
  labels?: Record<string, string>;
  executionTimeMs?: number;
  pointsScanned?: number;
  scalar?: number;
  error?: string;
}

// ============================================================
// LLM Observability Types
// ============================================================

export type SpanType = 'llm_call' | 'tool_call' | 'retrieval' | 'embedding' | 'chain' | 'agent';
export type SpanStatus = 'pending' | 'running' | 'success' | 'error';

export interface LLMSpan {
  id: string;
  traceId: string;
  parentId?: string;
  name: string;
  type: SpanType;
  startTime: string;
  endTime?: string;
  durationMs: number;
  model?: string;
  provider?: string;
  tokensInput: number;
  tokensOutput: number;
  tokensTotal: number;
  costUsd: number;
  timeToFirstTokenMs?: number;
  tokensPerSecond?: number;
  status: SpanStatus;
  error?: string;
  metadata?: Record<string, unknown>;
}

export interface LLMTrace {
  id: string;
  sessionId?: string;
  userId?: string;
  conversationId?: string;
  spans: LLMSpan[];
  startTime: string;
  endTime?: string;
  totalDurationMs: number;
  totalTokens: number;
  totalCostUsd: number;
  input: string;
  output: string;
  status: SpanStatus;
  tags: string[];
  metadata?: Record<string, unknown>;
}

export interface LatencyPercentiles {
  p50: number;
  p75: number;
  p90: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
  avg: number;
  count: number;
}

export interface CostSummary {
  totalCost: number;
  totalTokens: number;
  inputTokens: number;
  outputTokens: number;
  requestCount: number;
  avgCostPerRequest: number;
  topModels: Record<string, number>;
}

// ============================================================
// Insights Types
// ============================================================

export type AnomalyType = 'spike' | 'drop' | 'trend' | 'outlier' | 'missing' | 'pattern';
export type AnomalySeverity = 'low' | 'medium' | 'high' | 'critical';

export interface Anomaly {
  id: string;
  metric: string;
  type: AnomalyType;
  severity: AnomalySeverity;
  value: number;
  expectedValue: number;
  deviation: number;
  timestamp: string;
  duration?: string;
  description: string;
  possibleCauses: string[];
  confidence: number;
}

export interface ForecastPoint {
  timestamp: string;
  value: number;
  lowerBound: number;
  upperBound: number;
}

export interface Forecast {
  metric: string;
  method: string;
  points: ForecastPoint[];
  confidence: number;
  mape?: number;
  trend: 'up' | 'down' | 'stable';
  trendStrength: number;
  hasSeasonality: boolean;
  seasonalityPeriod?: number;
}

export type RecommendationType =
  | 'optimization'
  | 'cost_saving'
  | 'reliability'
  | 'security'
  | 'scaling'
  | 'configuration';

export type RecommendationPriority = 'low' | 'medium' | 'high' | 'critical';

export interface Recommendation {
  id: string;
  type: RecommendationType;
  priority: RecommendationPriority;
  title: string;
  description: string;
  rationale?: string;
  action: string;
  actionUrl?: string;
  expectedImpact: string;
  estimatedSavings?: number;
  estimatedImprovement?: number;
  affectedResources: string[];
  relatedMetrics: string[];
  dismissed: boolean;
  implemented: boolean;
  createdAt: string;
  confidence: number;
}

export interface InsightSummary {
  period: string;
  generatedAt: string;
  headline: string;
  summary: string;
  keyMetrics: KeyMetric[];
  highlights: string[];
  concerns: string[];
  topRecommendations: string[];
}

export interface KeyMetric {
  name: string;
  value: number;
  format: 'number' | 'percent' | 'currency' | 'ms' | 'duration';
  change?: number;
}

// ============================================================
// Time Range Types
// ============================================================

export interface TimeRange {
  start: string;
  end: string;
  label?: string;
}

export type PresetTimeRange =
  | '5m'
  | '15m'
  | '30m'
  | '1h'
  | '3h'
  | '6h'
  | '12h'
  | '24h'
  | '2d'
  | '7d'
  | '30d'
  | '90d';

// ============================================================
// API Response Types
// ============================================================

export interface DashboardListResponse {
  dashboards: DashboardSummary[];
  total: number;
  page: number;
  pageSize: number;
}

export interface AlertSummary {
  totalRules: number;
  enabled: number;
  byState: Record<AlertState, number>;
  bySeverity: Record<AlertSeverity, number>;
  firingAlerts: AlertRule[];
  recentEvents: AlertEvent[];
}

export interface IncidentStats {
  total: number;
  open: number;
  acknowledged: number;
  resolved: number;
  avgResolutionTimeMinutes?: number;
  bySeverity: Record<IncidentSeverity, number>;
}
