'use client';

import React, { useMemo } from 'react';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import type { Widget, ChartConfig } from '@/types/dashboard';

interface ChartWidgetProps {
  widget: Widget;
  data: Record<string, unknown>[];
  loading?: boolean;
  error?: string;
}

const DEFAULT_COLORS = [
  '#3b82f6', // blue
  '#10b981', // green
  '#f59e0b', // amber
  '#ef4444', // red
  '#8b5cf6', // violet
  '#ec4899', // pink
  '#06b6d4', // cyan
  '#84cc16', // lime
];

const formatXAxis = (value: string | number): string => {
  if (typeof value === 'string') {
    // Try to parse as date
    const date = new Date(value);
    if (!isNaN(date.getTime())) {
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    }
    return value.length > 15 ? value.slice(0, 12) + '...' : value;
  }
  return String(value);
};

const formatYAxis = (value: number): string => {
  if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
  if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
  return value.toFixed(1);
};

const CustomTooltip: React.FC<{
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}> = ({ active, payload, label }) => {
  if (!active || !payload) return null;
  
  return (
    <div className="bg-background border rounded-lg shadow-lg p-3 text-sm">
      <p className="font-medium mb-1">{label}</p>
      {payload.map((entry, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <div 
            className="w-3 h-3 rounded-full" 
            style={{ backgroundColor: entry.color }} 
          />
          <span className="text-muted-foreground">{entry.name}:</span>
          <span className="font-medium">{formatYAxis(entry.value)}</span>
        </div>
      ))}
    </div>
  );
};

export const ChartWidget: React.FC<ChartWidgetProps> = ({
  widget,
  data,
  loading = false,
  error,
}) => {
  const config = widget.config?.chart || {};
  const colors = config.colorScheme || DEFAULT_COLORS;
  
  const { chartType, dataKeys } = useMemo(() => {
    const type = widget.type;
    
    // Extract data keys from first data point
    let keys: string[] = [];
    if (data.length > 0) {
      keys = Object.keys(data[0]).filter(
        k => k !== (config.xAxis || 'timestamp') && typeof data[0][k] === 'number'
      );
    }
    
    return { chartType: type, dataKeys: keys };
  }, [widget.type, data, config.xAxis]);
  
  if (loading) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full flex items-center justify-center">
        <div className="animate-pulse text-muted-foreground">Loading...</div>
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full">
        <p className="text-sm font-medium">{widget.title}</p>
        <p className="text-sm text-destructive mt-2">{error}</p>
      </div>
    );
  }
  
  if (!data || data.length === 0) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full flex items-center justify-center">
        <p className="text-muted-foreground">No data available</p>
      </div>
    );
  }
  
  const xAxisKey = config.xAxis || 'timestamp';
  
  const renderChart = () => {
    switch (chartType) {
      case 'line_chart':
        return (
          <LineChart data={data}>
            {config.showGrid !== false && (
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            )}
            <XAxis 
              dataKey={xAxisKey} 
              tickFormatter={formatXAxis}
              className="text-xs fill-muted-foreground"
            />
            <YAxis 
              tickFormatter={formatYAxis}
              className="text-xs fill-muted-foreground"
            />
            {config.showTooltip !== false && <Tooltip content={<CustomTooltip />} />}
            {config.showLegend && <Legend />}
            {dataKeys.map((key, idx) => (
              <Line
                key={key}
                type={config.smooth ? 'monotone' : 'linear'}
                dataKey={key}
                stroke={colors[idx % colors.length]}
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4 }}
              />
            ))}
          </LineChart>
        );
      
      case 'area_chart':
        return (
          <AreaChart data={data}>
            {config.showGrid !== false && (
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            )}
            <XAxis 
              dataKey={xAxisKey} 
              tickFormatter={formatXAxis}
              className="text-xs fill-muted-foreground"
            />
            <YAxis 
              tickFormatter={formatYAxis}
              className="text-xs fill-muted-foreground"
            />
            {config.showTooltip !== false && <Tooltip content={<CustomTooltip />} />}
            {config.showLegend && <Legend />}
            {dataKeys.map((key, idx) => (
              <Area
                key={key}
                type={config.smooth ? 'monotone' : 'linear'}
                dataKey={key}
                stroke={colors[idx % colors.length]}
                fill={colors[idx % colors.length]}
                fillOpacity={config.areaOpacity ?? 0.3}
                stackId={config.stacked ? 'stack' : undefined}
              />
            ))}
          </AreaChart>
        );
      
      case 'bar_chart':
        return (
          <BarChart data={data}>
            {config.showGrid !== false && (
              <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            )}
            <XAxis 
              dataKey={xAxisKey} 
              tickFormatter={formatXAxis}
              className="text-xs fill-muted-foreground"
            />
            <YAxis 
              tickFormatter={formatYAxis}
              className="text-xs fill-muted-foreground"
            />
            {config.showTooltip !== false && <Tooltip content={<CustomTooltip />} />}
            {config.showLegend && <Legend />}
            {dataKeys.map((key, idx) => (
              <Bar
                key={key}
                dataKey={key}
                fill={colors[idx % colors.length]}
                stackId={config.stacked ? 'stack' : undefined}
                radius={[4, 4, 0, 0]}
              />
            ))}
          </BarChart>
        );
      
      case 'pie_chart':
      case 'donut_chart':
        const pieData = data.map((item, idx) => ({
          name: String(item[xAxisKey] || `Item ${idx + 1}`),
          value: Number(item[dataKeys[0]] || 0),
        }));
        
        return (
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={chartType === 'donut_chart' ? '60%' : 0}
              outerRadius="80%"
              paddingAngle={2}
              dataKey="value"
              label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {pieData.map((_, idx) => (
                <Cell key={idx} fill={colors[idx % colors.length]} />
              ))}
            </Pie>
            {config.showTooltip !== false && <Tooltip />}
            {config.showLegend && <Legend />}
          </PieChart>
        );
      
      default:
        return (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            Unsupported chart type: {chartType}
          </div>
        );
    }
  };
  
  return (
    <div className="p-4 rounded-lg border bg-card h-full flex flex-col">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-sm font-medium">{widget.title}</h3>
          {widget.description && (
            <p className="text-xs text-muted-foreground">{widget.description}</p>
          )}
        </div>
      </div>
      
      <div className="flex-1 min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default ChartWidget;
