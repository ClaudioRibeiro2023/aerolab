'use client';

import React from 'react';
import { ArrowUp, ArrowDown, Minus, TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Widget, MetricConfig } from '@/types/dashboard';

interface MetricCardProps {
  widget: Widget;
  value: number | string;
  previousValue?: number;
  loading?: boolean;
  error?: string;
  sparklineData?: number[];
}

const formatValue = (value: number | string, config?: MetricConfig): string => {
  if (typeof value === 'string') return value;
  
  const format = config?.format || 'number';
  const precision = config?.precision ?? 2;
  
  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: precision,
        maximumFractionDigits: precision,
      }).format(value);
    
    case 'percent':
      return `${(value * 100).toFixed(precision)}%`;
    
    case 'duration':
      if (value < 1000) return `${value.toFixed(0)}ms`;
      if (value < 60000) return `${(value / 1000).toFixed(1)}s`;
      return `${(value / 60000).toFixed(1)}m`;
    
    case 'bytes':
      if (value < 1024) return `${value}B`;
      if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)}KB`;
      if (value < 1024 * 1024 * 1024) return `${(value / (1024 * 1024)).toFixed(1)}MB`;
      return `${(value / (1024 * 1024 * 1024)).toFixed(2)}GB`;
    
    default:
      if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
      if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
      return value.toFixed(precision);
  }
};

const calculateChange = (current: number, previous: number): number => {
  if (previous === 0) return current > 0 ? 100 : 0;
  return ((current - previous) / previous) * 100;
};

const Sparkline: React.FC<{ data: number[]; color?: string }> = ({ data, color = '#3b82f6' }) => {
  if (!data || data.length < 2) return null;
  
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1;
  
  const height = 24;
  const width = 80;
  const stepX = width / (data.length - 1);
  
  const points = data.map((v, i) => {
    const x = i * stepX;
    const y = height - ((v - min) / range) * height;
    return `${x},${y}`;
  }).join(' ');
  
  return (
    <svg width={width} height={height} className="overflow-visible">
      <polyline
        points={points}
        fill="none"
        stroke={color}
        strokeWidth={1.5}
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
};

export const MetricCard: React.FC<MetricCardProps> = ({
  widget,
  value,
  previousValue,
  loading = false,
  error,
  sparklineData,
}) => {
  const config = widget.config?.metric;
  const formattedValue = formatValue(value, config);
  
  const change = previousValue !== undefined && typeof value === 'number'
    ? calculateChange(value, previousValue)
    : null;
  
  const isPositive = change !== null && change > 0;
  const isNegative = change !== null && change < 0;
  
  if (loading) {
    return (
      <div className="p-4 rounded-lg border bg-card animate-pulse">
        <div className="h-4 w-24 bg-muted rounded mb-2" />
        <div className="h-8 w-32 bg-muted rounded" />
      </div>
    );
  }
  
  if (error) {
    return (
      <div className="p-4 rounded-lg border bg-card">
        <p className="text-sm text-muted-foreground">{widget.title}</p>
        <p className="text-sm text-destructive mt-1">{error}</p>
      </div>
    );
  }
  
  return (
    <div className="p-4 rounded-lg border bg-card hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <p className="text-sm font-medium text-muted-foreground">
          {widget.title}
        </p>
        
        {config?.sparkline && sparklineData && (
          <Sparkline data={sparklineData} />
        )}
      </div>
      
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-bold">
          {config?.prefix}{formattedValue}{config?.suffix}
        </span>
        
        {change !== null && config?.showTrend !== false && (
          <span
            className={cn(
              'flex items-center text-sm font-medium',
              isPositive && 'text-green-600 dark:text-green-400',
              isNegative && 'text-red-600 dark:text-red-400',
              !isPositive && !isNegative && 'text-muted-foreground'
            )}
          >
            {isPositive ? (
              <ArrowUp className="h-3 w-3 mr-0.5" />
            ) : isNegative ? (
              <ArrowDown className="h-3 w-3 mr-0.5" />
            ) : (
              <Minus className="h-3 w-3 mr-0.5" />
            )}
            {Math.abs(change).toFixed(1)}%
          </span>
        )}
      </div>
      
      {widget.description && (
        <p className="mt-1 text-xs text-muted-foreground">
          {widget.description}
        </p>
      )}
    </div>
  );
};

export default MetricCard;
