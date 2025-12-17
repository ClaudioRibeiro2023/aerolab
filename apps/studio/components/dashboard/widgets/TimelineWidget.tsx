'use client';

import React from 'react';
import { cn } from '@/lib/utils';
import type { Widget } from '@/types/dashboard';

interface TimelineEvent {
  id: string;
  timestamp: string;
  title: string;
  description?: string;
  type?: 'info' | 'success' | 'warning' | 'error';
  icon?: React.ReactNode;
}

interface TimelineWidgetProps {
  widget: Widget;
  events: TimelineEvent[];
  loading?: boolean;
  error?: string;
}

const typeColors = {
  info: 'bg-blue-500',
  success: 'bg-green-500',
  warning: 'bg-yellow-500',
  error: 'bg-red-500',
};

export const TimelineWidget: React.FC<TimelineWidgetProps> = ({
  widget,
  events,
  loading = false,
  error,
}) => {
  if (loading) {
    return (
      <div className="p-4 rounded-lg border bg-card h-full animate-pulse">
        <div className="h-4 w-32 bg-muted rounded mb-4" />
        <div className="space-y-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="flex gap-4">
              <div className="w-3 h-3 bg-muted rounded-full" />
              <div className="flex-1">
                <div className="h-4 bg-muted rounded w-3/4" />
                <div className="h-3 bg-muted rounded w-1/2 mt-2" />
              </div>
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
  
  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    
    if (diff < 60000) return 'Just now';
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return date.toLocaleDateString();
  };
  
  return (
    <div className="p-4 rounded-lg border bg-card h-full flex flex-col">
      <h3 className="text-sm font-medium mb-4">{widget.title}</h3>
      
      <div className="flex-1 overflow-auto">
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-1.5 top-0 bottom-0 w-px bg-border" />
          
          <div className="space-y-4">
            {events.map((event, idx) => (
              <div key={event.id} className="relative flex gap-4 pl-6">
                {/* Dot */}
                <div
                  className={cn(
                    'absolute left-0 w-3 h-3 rounded-full ring-4 ring-background',
                    typeColors[event.type || 'info']
                  )}
                />
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <p className="text-sm font-medium truncate">{event.title}</p>
                    <span className="text-xs text-muted-foreground whitespace-nowrap">
                      {formatTime(event.timestamp)}
                    </span>
                  </div>
                  
                  {event.description && (
                    <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                      {event.description}
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
          
          {events.length === 0 && (
            <p className="text-sm text-muted-foreground text-center py-8">
              No events to display
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default TimelineWidget;
