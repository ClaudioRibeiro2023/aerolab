'use client';

import React from 'react';
import { ArrowUp, ArrowDown, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Widget } from '@/types/dashboard';

interface StatItem {
  label: string;
  value: number;
  previousValue?: number;
  format?: 'number' | 'currency' | 'percent';
}

interface StatComparisonWidgetProps {
  widget: Widget;
  stats: StatItem[];
  loading?: boolean;
  error?: string;
}

const formatValue = (value: number, format?: string): string => {
  switch (format) {
    case 'currency':
      return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      }).format(value);
    case 'percent':
      return `${(value * 100).toFixed(1)}%`;
    default:
      if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
      if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
      return value.toLocaleString();
  }
};

export const StatComparisonWidget: React.FC<StatComparisonWidgetProps> = ({
  widget,
  stats,
  loading = false,
  error,
}) => {
  if (loading) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full animate-pulse">
        <div className="h-4 w-32 bg-muted rounded mb-4" />
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i}>
              <div className="h-8 bg-muted rounded" />
              <div className="h-3 bg-muted rounded w-2/3 mt-2" />
            </div>
          ))}
        </div>
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
  
  return (
    <div className="p-4 rounded-lg border bg-card h-full">
      <h3 className="text-sm font-medium mb-4">{widget.title}</h3>
      
      <div className="grid grid-cols-2 gap-4">
        {stats.map((stat, idx) => {
          const change = stat.previousValue !== undefined
            ? ((stat.value - stat.previousValue) / stat.previousValue) * 100
            : null;
          
          const isPositive = change !== null && change > 0;
          const isNegative = change !== null && change < 0;
          
          return (
            <div key={idx} className="p-3 bg-muted/30 rounded-lg">
              <p className="text-2xl font-bold">
                {formatValue(stat.value, stat.format)}
              </p>
              
              <div className="flex items-center justify-between mt-1">
                <span className="text-xs text-muted-foreground">{stat.label}</span>
                
                {change !== null && (
                  <span
                    className={cn(
                      'flex items-center text-xs font-medium',
                      isPositive && 'text-green-600',
                      isNegative && 'text-red-600',
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
            </div>
          );
        })}
      </div>
      
      {widget.description && (
        <p className="text-xs text-muted-foreground mt-4">
          {widget.description}
        </p>
      )}
    </div>
  );
};

export default StatComparisonWidget;
