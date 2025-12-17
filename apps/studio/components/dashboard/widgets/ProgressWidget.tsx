'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { Widget } from '@/types/dashboard';

interface ProgressWidgetProps {
  widget: Widget;
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  color?: 'primary' | 'success' | 'warning' | 'error';
  loading?: boolean;
  error?: string;
}

const colorClasses = {
  primary: 'bg-primary',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
};

export const ProgressWidget: React.FC<ProgressWidgetProps> = ({
  widget,
  value,
  max = 100,
  label,
  showPercentage = true,
  color = 'primary',
  loading = false,
  error,
}) => {
  const percentage = Math.min(Math.max((value / max) * 100, 0), 100);
  
  // Auto color based on percentage
  const autoColor = percentage >= 90 ? 'error' : percentage >= 70 ? 'warning' : color;
  
  if (loading) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full animate-pulse">
        <div className="h-4 w-32 bg-muted rounded mb-4" />
        <div className="h-4 bg-muted rounded" />
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
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-medium">{widget.title}</h3>
        {showPercentage && (
          <span className="text-sm font-semibold">{percentage.toFixed(0)}%</span>
        )}
      </div>
      
      <div className="h-3 bg-muted rounded-full overflow-hidden">
        <div
          className={cn('h-full rounded-full transition-all duration-500', colorClasses[autoColor])}
          style={{ width: `${percentage}%` }}
        />
      </div>
      
      <div className="flex items-center justify-between mt-2 text-xs text-muted-foreground">
        <span>{label || `${value.toLocaleString()} / ${max.toLocaleString()}`}</span>
        {widget.description && <span>{widget.description}</span>}
      </div>
    </div>
  );
};

export default ProgressWidget;
