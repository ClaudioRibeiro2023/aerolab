import { useState, useCallback, useEffect, useRef } from 'react';
import type { 
  Dashboard, 
  Widget, 
  WidgetData, 
  TimeRange,
  PresetTimeRange,
  QueryResult 
} from '@/types/dashboard';

interface UseDashboardOptions {
  autoRefresh?: boolean;
  refreshInterval?: number;
  onError?: (error: Error) => void;
}

interface UseDashboardReturn {
  // Dashboard state
  dashboard: Dashboard | null;
  loading: boolean;
  error: string | null;
  
  // Widget data
  widgetData: Record<string, WidgetData>;
  
  // Time range
  timeRange: TimeRange;
  setTimeRange: (range: TimeRange | PresetTimeRange) => void;
  
  // Actions
  loadDashboard: (id: string) => Promise<void>;
  refreshWidget: (widgetId: string) => Promise<void>;
  refreshAll: () => Promise<void>;
  updateWidget: (widget: Widget) => void;
  addWidget: (widget: Omit<Widget, 'id'>) => void;
  removeWidget: (widgetId: string) => void;
  
  // Editing
  isEditing: boolean;
  setIsEditing: (editing: boolean) => void;
  saveDashboard: () => Promise<void>;
  
  // Filters
  globalFilters: Record<string, unknown>;
  setGlobalFilters: (filters: Record<string, unknown>) => void;
}

// Parse preset time range to TimeRange
const parsePresetTimeRange = (preset: PresetTimeRange): TimeRange => {
  const now = new Date();
  const end = now.toISOString();
  
  const durations: Record<PresetTimeRange, number> = {
    '5m': 5 * 60 * 1000,
    '15m': 15 * 60 * 1000,
    '30m': 30 * 60 * 1000,
    '1h': 60 * 60 * 1000,
    '3h': 3 * 60 * 60 * 1000,
    '6h': 6 * 60 * 60 * 1000,
    '12h': 12 * 60 * 60 * 1000,
    '24h': 24 * 60 * 60 * 1000,
    '2d': 2 * 24 * 60 * 60 * 1000,
    '7d': 7 * 24 * 60 * 60 * 1000,
    '30d': 30 * 24 * 60 * 60 * 1000,
    '90d': 90 * 24 * 60 * 60 * 1000,
  };
  
  const duration = durations[preset] || durations['24h'];
  const start = new Date(now.getTime() - duration).toISOString();
  
  return { start, end, label: preset };
};

// Mock API functions (replace with real API calls)
const fetchDashboard = async (id: string): Promise<Dashboard> => {
  // Simulate API call
  await new Promise(r => setTimeout(r, 500));
  
  return {
    id,
    name: 'Overview Dashboard',
    slug: 'overview',
    description: 'Main system overview',
    widgets: [
      {
        id: 'w1',
        title: 'Total Requests',
        type: 'metric_card',
        query: 'sum(requests_total)',
        config: { metric: { format: 'number', showTrend: true } },
      },
      {
        id: 'w2',
        title: 'Success Rate',
        type: 'metric_card',
        query: 'rate(success_total) / rate(requests_total)',
        config: { metric: { format: 'percent', showTrend: true } },
      },
      {
        id: 'w3',
        title: 'Request Rate',
        type: 'line_chart',
        query: 'rate(requests_total[5m])',
        config: { chart: { showLegend: true, smooth: true } },
      },
    ],
    layout: {
      id: 'layout1',
      type: 'grid',
      columns: 12,
      rowHeight: 100,
      gap: 16,
      items: [
        { widgetId: 'w1', position: { x: 0, y: 0, w: 3, h: 2 } },
        { widgetId: 'w2', position: { x: 3, y: 0, w: 3, h: 2 } },
        { widgetId: 'w3', position: { x: 0, y: 2, w: 6, h: 3 } },
      ],
    },
    defaultTimeRange: '24h',
    timeZone: 'UTC',
    autoRefresh: true,
    refreshIntervalSeconds: 30,
    globalFilters: {},
    variables: {},
    tags: [],
    version: 1,
    createdAt: new Date().toISOString(),
    updatedAt: new Date().toISOString(),
    createdBy: 'system',
    isFavorite: false,
    isTemplate: false,
    isPublished: true,
  };
};

const executeQuery = async (
  query: string, 
  timeRange: TimeRange,
  filters: Record<string, unknown>
): Promise<QueryResult> => {
  // Simulate query execution
  await new Promise(r => setTimeout(r, 300 + Math.random() * 200));
  
  // Generate mock data based on query
  if (query.includes('sum(requests_total)')) {
    return {
      data: [{ value: Math.floor(10000 + Math.random() * 5000), previousValue: 9500 }],
    };
  }
  
  if (query.includes('rate(success_total)')) {
    return {
      data: [{ value: 0.95 + Math.random() * 0.04, previousValue: 0.94 }],
    };
  }
  
  if (query.includes('rate(requests_total[5m])')) {
    // Generate time series data
    const points = [];
    const now = new Date();
    for (let i = 24; i >= 0; i--) {
      points.push({
        timestamp: new Date(now.getTime() - i * 60 * 60 * 1000).toISOString(),
        value: 100 + Math.random() * 50,
      });
    }
    return { data: points };
  }
  
  return { data: [] };
};

export function useDashboard(options: UseDashboardOptions = {}): UseDashboardReturn {
  const {
    autoRefresh = true,
    refreshInterval = 30000,
    onError,
  } = options;
  
  const [dashboard, setDashboard] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [widgetData, setWidgetData] = useState<Record<string, WidgetData>>({});
  const [timeRange, setTimeRangeState] = useState<TimeRange>(
    parsePresetTimeRange('24h')
  );
  const [isEditing, setIsEditing] = useState(false);
  const [globalFilters, setGlobalFilters] = useState<Record<string, unknown>>({});
  
  const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  // Load dashboard
  const loadDashboard = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await fetchDashboard(id);
      setDashboard(data);
      setGlobalFilters(data.globalFilters);
      
      // Set initial time range from dashboard
      if (data.defaultTimeRange) {
        setTimeRangeState(parsePresetTimeRange(data.defaultTimeRange as PresetTimeRange));
      }
      
      // Load widget data
      await refreshAllWidgets(data.widgets);
      
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load dashboard';
      setError(message);
      onError?.(err instanceof Error ? err : new Error(message));
    } finally {
      setLoading(false);
    }
  }, [onError]);
  
  // Refresh single widget
  const refreshWidget = useCallback(async (widgetId: string) => {
    const widget = dashboard?.widgets.find(w => w.id === widgetId);
    if (!widget) return;
    
    setWidgetData(prev => ({
      ...prev,
      [widgetId]: { ...prev[widgetId], widgetId, loading: true, data: prev[widgetId]?.data },
    }));
    
    try {
      const result = await executeQuery(widget.query, timeRange, globalFilters);
      
      setWidgetData(prev => ({
        ...prev,
        [widgetId]: {
          widgetId,
          data: Array.isArray(result.data) && result.data.length === 1 
            ? result.data[0] 
            : result.data,
          loading: false,
          lastUpdated: new Date().toISOString(),
        },
      }));
    } catch (err) {
      setWidgetData(prev => ({
        ...prev,
        [widgetId]: {
          widgetId,
          data: prev[widgetId]?.data,
          loading: false,
          error: err instanceof Error ? err.message : 'Query failed',
        },
      }));
    }
  }, [dashboard, timeRange, globalFilters]);
  
  // Refresh all widgets
  const refreshAllWidgets = useCallback(async (widgets: Widget[]) => {
    await Promise.all(widgets.map(async (widget) => {
      setWidgetData(prev => ({
        ...prev,
        [widget.id]: { widgetId: widget.id, data: prev[widget.id]?.data, loading: true },
      }));
      
      try {
        const result = await executeQuery(widget.query, timeRange, globalFilters);
        
        setWidgetData(prev => ({
          ...prev,
          [widget.id]: {
            widgetId: widget.id,
            data: Array.isArray(result.data) && result.data.length === 1 
              ? result.data[0] 
              : result.data,
            loading: false,
            lastUpdated: new Date().toISOString(),
          },
        }));
      } catch (err) {
        setWidgetData(prev => ({
          ...prev,
          [widget.id]: {
            widgetId: widget.id,
            data: null,
            loading: false,
            error: err instanceof Error ? err.message : 'Query failed',
          },
        }));
      }
    }));
  }, [timeRange, globalFilters]);
  
  const refreshAll = useCallback(async () => {
    if (dashboard?.widgets) {
      await refreshAllWidgets(dashboard.widgets);
    }
  }, [dashboard, refreshAllWidgets]);
  
  // Set time range
  const setTimeRange = useCallback((range: TimeRange | PresetTimeRange) => {
    const newRange = typeof range === 'string' 
      ? parsePresetTimeRange(range)
      : range;
    setTimeRangeState(newRange);
  }, []);
  
  // Update widget
  const updateWidget = useCallback((widget: Widget) => {
    setDashboard(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        widgets: prev.widgets.map(w => w.id === widget.id ? widget : w),
      };
    });
  }, []);
  
  // Add widget
  const addWidget = useCallback((widget: Omit<Widget, 'id'>) => {
    const newWidget: Widget = {
      ...widget,
      id: `widget_${Date.now()}`,
    };
    
    setDashboard(prev => {
      if (!prev) return prev;
      
      // Find next available position
      const maxY = Math.max(...prev.layout.items.map(i => i.position.y + i.position.h), 0);
      
      return {
        ...prev,
        widgets: [...prev.widgets, newWidget],
        layout: {
          ...prev.layout,
          items: [
            ...prev.layout.items,
            {
              widgetId: newWidget.id,
              position: { x: 0, y: maxY, w: 4, h: 3 },
            },
          ],
        },
      };
    });
  }, []);
  
  // Remove widget
  const removeWidget = useCallback((widgetId: string) => {
    setDashboard(prev => {
      if (!prev) return prev;
      return {
        ...prev,
        widgets: prev.widgets.filter(w => w.id !== widgetId),
        layout: {
          ...prev.layout,
          items: prev.layout.items.filter(i => i.widgetId !== widgetId),
        },
      };
    });
    
    setWidgetData(prev => {
      const newData = { ...prev };
      delete newData[widgetId];
      return newData;
    });
  }, []);
  
  // Save dashboard
  const saveDashboard = useCallback(async () => {
    if (!dashboard) return;
    
    // TODO: Implement actual API call
    console.log('Saving dashboard:', dashboard);
    
    setDashboard(prev => prev ? {
      ...prev,
      updatedAt: new Date().toISOString(),
      version: prev.version + 1,
    } : prev);
  }, [dashboard]);
  
  // Auto refresh effect
  useEffect(() => {
    if (autoRefresh && dashboard && !isEditing) {
      refreshTimerRef.current = setInterval(() => {
        refreshAll();
      }, refreshInterval);
      
      return () => {
        if (refreshTimerRef.current) {
          clearInterval(refreshTimerRef.current);
        }
      };
    }
  }, [autoRefresh, dashboard, isEditing, refreshInterval, refreshAll]);
  
  // Refresh when time range or filters change
  useEffect(() => {
    if (dashboard) {
      refreshAll();
    }
  }, [timeRange, globalFilters]);
  
  return {
    dashboard,
    loading,
    error,
    widgetData,
    timeRange,
    setTimeRange,
    loadDashboard,
    refreshWidget,
    refreshAll,
    updateWidget,
    addWidget,
    removeWidget,
    isEditing,
    setIsEditing,
    saveDashboard,
    globalFilters,
    setGlobalFilters,
  };
}

export default useDashboard;
