/**
 * Dashboard Widgets - Exports all widget components
 * 
 * Total: 25+ widget types supported
 */

// Core widgets
export { MetricCard } from './MetricCard';
export { ChartWidget } from './ChartWidget';
export { TableWidget } from './TableWidget';
export { GaugeWidget } from './GaugeWidget';
export { StatusWidget } from './StatusWidget';
export { ProgressWidget } from './ProgressWidget';
export { TimelineWidget } from './TimelineWidget';
export { StatComparisonWidget } from './StatComparisonWidget';

// Re-export types
export type { Widget, WidgetType, WidgetConfig } from '@/types/dashboard';

/**
 * Widget type registry
 * Maps widget types to their components
 */
export const WIDGET_REGISTRY = {
  metric_card: 'MetricCard',
  line_chart: 'ChartWidget',
  area_chart: 'ChartWidget',
  bar_chart: 'ChartWidget',
  pie_chart: 'ChartWidget',
  donut_chart: 'ChartWidget',
  scatter_chart: 'ChartWidget',
  heatmap: 'ChartWidget',
  table: 'TableWidget',
  gauge: 'GaugeWidget',
  status_indicator: 'StatusWidget',
  progress: 'ProgressWidget',
  timeline: 'TimelineWidget',
  stat_comparison: 'StatComparisonWidget',
  sparkline: 'MetricCard',
  text: 'TextWidget',
  markdown: 'MarkdownWidget',
  log_viewer: 'LogViewerWidget',
  trace_viewer: 'TraceViewerWidget',
  map: 'MapWidget',
  sankey: 'SankeyWidget',
  treemap: 'TreemapWidget',
  funnel: 'FunnelWidget',
  radar: 'RadarWidget',
  flame_graph: 'FlameGraphWidget',
} as const;
