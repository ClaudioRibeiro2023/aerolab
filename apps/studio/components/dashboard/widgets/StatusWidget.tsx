'use client';

import React from 'react';
import { CheckCircle, XCircle, AlertCircle, Clock, Minus } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { Widget } from '@/types/dashboard';

type Status = 'healthy' | 'warning' | 'critical' | 'unknown' | 'pending';

interface StatusWidgetProps {
  widget: Widget;
  status: Status;
  message?: string;
  lastChecked?: string;
  loading?: boolean;
  error?: string;
}

const statusConfig: Record<Status, { icon: React.ReactNode; color: string; bg: string }> = {
  healthy: {
    icon: <CheckCircle className="h-8 w-8" />,
    color: 'text-green-600 dark:text-green-400',
    bg: 'bg-green-100 dark:bg-green-900/30',
  },
  warning: {
    icon: <AlertCircle className="h-8 w-8" />,
    color: 'text-yellow-600 dark:text-yellow-400',
    bg: 'bg-yellow-100 dark:bg-yellow-900/30',
  },
  critical: {
    icon: <XCircle className="h-8 w-8" />,
    color: 'text-red-600 dark:text-red-400',
    bg: 'bg-red-100 dark:bg-red-900/30',
  },
  unknown: {
    icon: <Minus className="h-8 w-8" />,
    color: 'text-gray-600 dark:text-gray-400',
    bg: 'bg-gray-100 dark:bg-gray-900/30',
  },
  pending: {
    icon: <Clock className="h-8 w-8" />,
    color: 'text-blue-600 dark:text-blue-400',
    bg: 'bg-blue-100 dark:bg-blue-900/30',
  },
};

export const StatusWidget: React.FC<StatusWidgetProps> = ({
  widget,
  status,
  message,
  lastChecked,
  loading = false,
  error,
}) => {
  const config = statusConfig[status] || statusConfig.unknown;
  
  if (loading) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full animate-pulse">
        <div className="h-4 w-32 bg-muted rounded mb-4" />
        <div className="h-16 w-16 bg-muted rounded-full mx-auto" />
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
    <div className="p-4 rounded-lg border bg-card h-full flex flex-col items-center justify-center">
      <h3 className="text-sm font-medium mb-4">{widget.title}</h3>
      
      <div className={cn('p-4 rounded-full', config.bg, config.color)}>
        {config.icon}
      </div>
      
      <p className={cn('mt-3 text-lg font-semibold capitalize', config.color)}>
        {status}
      </p>
      
      {message && (
        <p className="mt-1 text-sm text-muted-foreground text-center">
          {message}
        </p>
      )}
      
      {lastChecked && (
        <p className="mt-2 text-xs text-muted-foreground">
          Last checked: {new Date(lastChecked).toLocaleTimeString()}
        </p>
      )}
    </div>
  );
};

export default StatusWidget;
