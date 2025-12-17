'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Responsive, WidthProvider, Layout } from 'react-grid-layout';
import { Settings, Maximize2, RefreshCw, MoreVertical } from 'lucide-react';
import { cn } from '@/lib/utils';
import { MetricCard, ChartWidget, TableWidget, GaugeWidget } from './widgets';
import type { Widget, WidgetData, Layout as DashboardLayout, GridPosition } from '@/types/dashboard';

// Wrapping ResponsiveGridLayout with WidthProvider for auto-sizing
const ResponsiveGridLayout = WidthProvider(Responsive);

interface DashboardGridProps {
  widgets: Widget[];
  layout: DashboardLayout;
  widgetData: Record<string, WidgetData>;
  isEditing?: boolean;
  onLayoutChange?: (layout: Layout[]) => void;
  onWidgetEdit?: (widgetId: string) => void;
  onWidgetDelete?: (widgetId: string) => void;
  onWidgetRefresh?: (widgetId: string) => void;
}

const defaultPosition: GridPosition = {
  x: 0,
  y: 0,
  w: 4,
  h: 3,
  minW: 2,
  minH: 2,
};

export const DashboardGrid: React.FC<DashboardGridProps> = ({
  widgets,
  layout,
  widgetData,
  isEditing = false,
  onLayoutChange,
  onWidgetEdit,
  onWidgetDelete,
  onWidgetRefresh,
}) => {
  const [hoveredWidget, setHoveredWidget] = useState<string | null>(null);
  const [expandedWidget, setExpandedWidget] = useState<string | null>(null);
  
  // Convert layout items to react-grid-layout format
  const gridLayout = useMemo(() => {
    return layout.items.map(item => ({
      i: item.widgetId,
      x: item.position.x,
      y: item.position.y,
      w: item.position.w,
      h: item.position.h,
      minW: item.position.minW || 2,
      minH: item.position.minH || 2,
      maxW: item.position.maxW,
      maxH: item.position.maxH,
    }));
  }, [layout.items]);
  
  const handleLayoutChange = useCallback((newLayout: Layout[]) => {
    if (onLayoutChange && isEditing) {
      onLayoutChange(newLayout);
    }
  }, [onLayoutChange, isEditing]);
  
  const renderWidget = useCallback((widget: Widget) => {
    const data = widgetData[widget.id];
    const isLoading = data?.loading ?? true;
    const error = data?.error;
    const widgetContent = data?.data;
    
    switch (widget.type) {
      case 'metric_card':
        return (
          <MetricCard
            widget={widget}
            value={typeof widgetContent === 'number' ? widgetContent : (widgetContent as Record<string, unknown>)?.value as number || 0}
            previousValue={(widgetContent as Record<string, unknown>)?.previousValue as number}
            loading={isLoading}
            error={error}
            sparklineData={(widgetContent as Record<string, unknown>)?.sparkline as number[]}
          />
        );
      
      case 'line_chart':
      case 'area_chart':
      case 'bar_chart':
      case 'pie_chart':
      case 'donut_chart':
        return (
          <ChartWidget
            widget={widget}
            data={Array.isArray(widgetContent) ? widgetContent as Record<string, unknown>[] : []}
            loading={isLoading}
            error={error}
          />
        );
      
      case 'table':
        return (
          <TableWidget
            widget={widget}
            data={Array.isArray(widgetContent) ? widgetContent as Record<string, unknown>[] : []}
            loading={isLoading}
            error={error}
          />
        );
      
      case 'gauge':
        return (
          <GaugeWidget
            widget={widget}
            value={typeof widgetContent === 'number' ? widgetContent : (widgetContent as Record<string, unknown>)?.value as number || 0}
            loading={isLoading}
            error={error}
          />
        );
      
      default:
        return (
          <div className="p-4 rounded-lg border bg-card h-full flex items-center justify-center">
            <p className="text-sm text-muted-foreground">
              Widget type &apos;{widget.type}&apos; not implemented
            </p>
          </div>
        );
    }
  }, [widgetData]);
  
  // Render expanded widget modal
  if (expandedWidget) {
    const widget = widgets.find(w => w.id === expandedWidget);
    if (widget) {
      return (
        <div className="fixed inset-0 z-50 bg-background/80 backdrop-blur-sm">
          <div className="fixed inset-4 z-50 bg-background rounded-lg border shadow-lg overflow-hidden">
            <div className="flex items-center justify-between p-4 border-b">
              <h2 className="text-lg font-semibold">{widget.title}</h2>
              <button
                onClick={() => setExpandedWidget(null)}
                className="p-2 rounded hover:bg-muted"
                title="Close expanded view"
                aria-label="Close expanded view"
              >
                <Maximize2 className="h-4 w-4" />
              </button>
            </div>
            <div className="p-4 h-[calc(100%-60px)]">
              {renderWidget(widget)}
            </div>
          </div>
        </div>
      );
    }
  }
  
  return (
    <ResponsiveGridLayout
      className="layout"
      layouts={{ lg: gridLayout }}
      breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
      cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
      rowHeight={layout.rowHeight || 100}
      margin={[layout.gap || 16, layout.gap || 16]}
      isDraggable={isEditing}
      isResizable={isEditing}
      onLayoutChange={handleLayoutChange}
      draggableHandle=".widget-drag-handle"
    >
      {widgets.map(widget => {
        const layoutItem = layout.items.find(i => i.widgetId === widget.id);
        const position = layoutItem?.position || widget.position || defaultPosition;
        
        return (
          <div
            key={widget.id}
            data-grid={{
              ...position,
              i: widget.id,
            }}
            className="relative"
            onMouseEnter={() => setHoveredWidget(widget.id)}
            onMouseLeave={() => setHoveredWidget(null)}
          >
            {/* Widget toolbar (shown on hover or in edit mode) */}
            {(hoveredWidget === widget.id || isEditing) && (
              <div className={cn(
                'absolute top-2 right-2 z-10 flex items-center gap-1',
                'bg-background/90 rounded-md border p-1',
                'transition-opacity',
                hoveredWidget === widget.id || isEditing ? 'opacity-100' : 'opacity-0'
              )}>
                {isEditing && (
                  <div 
                    className="widget-drag-handle cursor-move p-1 hover:bg-muted rounded"
                    title="Drag to reposition"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </div>
                )}
                
                <button
                  onClick={() => onWidgetRefresh?.(widget.id)}
                  className="p-1 hover:bg-muted rounded"
                  title="Refresh widget"
                  aria-label="Refresh widget"
                >
                  <RefreshCw className="h-4 w-4" />
                </button>
                
                <button
                  onClick={() => setExpandedWidget(widget.id)}
                  className="p-1 hover:bg-muted rounded"
                  title="Expand widget"
                  aria-label="Expand widget"
                >
                  <Maximize2 className="h-4 w-4" />
                </button>
                
                {isEditing && (
                  <button
                    onClick={() => onWidgetEdit?.(widget.id)}
                    className="p-1 hover:bg-muted rounded"
                    title="Edit widget"
                    aria-label="Edit widget"
                  >
                    <Settings className="h-4 w-4" />
                  </button>
                )}
              </div>
            )}
            
            {/* Widget content */}
            <div className="h-full">
              {renderWidget(widget)}
            </div>
          </div>
        );
      })}
    </ResponsiveGridLayout>
  );
};

export default DashboardGrid;
