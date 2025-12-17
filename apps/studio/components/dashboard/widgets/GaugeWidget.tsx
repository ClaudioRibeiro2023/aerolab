'use client';

import React from 'react';
import type { Widget, GaugeConfig } from '@/types/dashboard';

interface GaugeWidgetProps {
  widget: Widget;
  value: number;
  loading?: boolean;
  error?: string;
}

export const GaugeWidget: React.FC<GaugeWidgetProps> = ({
  widget,
  value,
  loading = false,
  error,
}) => {
  const config = widget.config?.gauge || {} as GaugeConfig;
  const min = config.min ?? 0;
  const max = config.max ?? 100;
  const unit = config.unit || '';
  
  // Calculate percentage
  const percentage = Math.min(Math.max((value - min) / (max - min), 0), 1);
  const angle = percentage * 180; // 180 degree arc
  
  // Determine color based on thresholds
  const getColor = (): string => {
    if (config.thresholds && config.thresholds.length > 0) {
      const sortedThresholds = [...config.thresholds].sort((a, b) => b.value - a.value);
      for (const threshold of sortedThresholds) {
        if (value >= threshold.value) {
          return threshold.color;
        }
      }
    }
    
    // Default colors based on percentage
    if (percentage <= 0.33) return '#10b981'; // green
    if (percentage <= 0.66) return '#f59e0b'; // amber
    return '#ef4444'; // red
  };
  
  const color = getColor();
  
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
  
  // SVG dimensions
  const size = 160;
  const strokeWidth = 16;
  const radius = (size - strokeWidth) / 2;
  const center = size / 2;
  
  // Arc path calculation
  const getArcPath = (startAngle: number, endAngle: number): string => {
    const startRad = (startAngle - 90) * (Math.PI / 180);
    const endRad = (endAngle - 90) * (Math.PI / 180);
    
    const startX = center + radius * Math.cos(startRad);
    const startY = center + radius * Math.sin(startRad);
    const endX = center + radius * Math.cos(endRad);
    const endY = center + radius * Math.sin(endRad);
    
    const largeArc = endAngle - startAngle > 180 ? 1 : 0;
    
    return `M ${startX} ${startY} A ${radius} ${radius} 0 ${largeArc} 1 ${endX} ${endY}`;
  };
  
  return (
    <div className="p-4 rounded-lg border bg-card h-full flex flex-col items-center justify-center">
      <h3 className="text-sm font-medium mb-2">{widget.title}</h3>
      
      <div className="relative">
        <svg 
          width={size} 
          height={size / 2 + 20} 
          viewBox={`0 0 ${size} ${size / 2 + 20}`}
        >
          {/* Background arc */}
          <path
            d={getArcPath(0, 180)}
            fill="none"
            stroke="currentColor"
            strokeWidth={strokeWidth}
            strokeLinecap="round"
            className="text-muted/30"
          />
          
          {/* Value arc */}
          {angle > 0 && (
            <path
              d={getArcPath(0, angle)}
              fill="none"
              stroke={color}
              strokeWidth={strokeWidth}
              strokeLinecap="round"
            />
          )}
          
          {/* Threshold markers */}
          {config.thresholds?.map((threshold, idx) => {
            const thresholdAngle = ((threshold.value - min) / (max - min)) * 180;
            const markerRad = (thresholdAngle - 90) * (Math.PI / 180);
            const innerRadius = radius - strokeWidth / 2 - 4;
            const outerRadius = radius + strokeWidth / 2 + 4;
            
            const x1 = center + innerRadius * Math.cos(markerRad);
            const y1 = center + innerRadius * Math.sin(markerRad);
            const x2 = center + outerRadius * Math.cos(markerRad);
            const y2 = center + outerRadius * Math.sin(markerRad);
            
            return (
              <line
                key={idx}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={threshold.color}
                strokeWidth={2}
              />
            );
          })}
          
          {/* Value needle */}
          <line
            x1={center}
            y1={center}
            x2={center + (radius - 20) * Math.cos((angle - 90) * (Math.PI / 180))}
            y2={center + (radius - 20) * Math.sin((angle - 90) * (Math.PI / 180))}
            stroke="currentColor"
            strokeWidth={3}
            strokeLinecap="round"
            className="text-foreground"
          />
          
          {/* Center dot */}
          <circle cx={center} cy={center} r={6} fill="currentColor" className="text-foreground" />
        </svg>
        
        {/* Value display */}
        {config.showValue !== false && (
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 text-center">
            <span className="text-2xl font-bold">{value.toFixed(1)}</span>
            {unit && <span className="text-sm text-muted-foreground ml-1">{unit}</span>}
          </div>
        )}
      </div>
      
      {/* Min/Max labels */}
      <div className="flex justify-between w-full px-4 mt-2 text-xs text-muted-foreground">
        <span>{min}{unit}</span>
        <span>{max}{unit}</span>
      </div>
      
      {widget.description && (
        <p className="text-xs text-muted-foreground mt-2 text-center">
          {widget.description}
        </p>
      )}
    </div>
  );
};

export default GaugeWidget;
