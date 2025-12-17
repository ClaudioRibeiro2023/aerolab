"use client";

import React, { useState, useEffect, useRef } from "react";
import { motion, useInView, useSpring, useTransform } from "framer-motion";
import { cn } from "@/lib/utils";

// ============================================================
// ANIMATED NUMBER
// ============================================================

interface AnimatedNumberProps {
  value: number;
  duration?: number;
  className?: string;
  prefix?: string;
  suffix?: string;
  decimals?: number;
}

export function AnimatedNumber({
  value,
  duration = 2,
  className,
  prefix = "",
  suffix = "",
  decimals = 0,
}: AnimatedNumberProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true });
  const spring = useSpring(0, { duration: duration * 1000 });
  const display = useTransform(spring, (current) =>
    `${prefix}${current.toFixed(decimals).replace(/\B(?=(\d{3})+(?!\d))/g, ",")}${suffix}`
  );

  useEffect(() => {
    if (isInView) {
      spring.set(value);
    }
  }, [isInView, spring, value]);

  return (
    <motion.span ref={ref} className={className}>
      {display}
    </motion.span>
  );
}

// ============================================================
// ANIMATED PROGRESS RING
// ============================================================

interface ProgressRingProps {
  progress: number;
  size?: number;
  strokeWidth?: number;
  className?: string;
  color?: string;
  bgColor?: string;
  showPercentage?: boolean;
  animated?: boolean;
}

export function ProgressRing({
  progress,
  size = 120,
  strokeWidth = 8,
  className,
  color = "#3b82f6",
  bgColor = "#1e293b",
  showPercentage = true,
  animated = true,
}: ProgressRingProps) {
  const ref = useRef<SVGSVGElement>(null);
  const isInView = useInView(ref, { once: true });
  
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const [offset, setOffset] = useState(circumference);

  useEffect(() => {
    if (isInView && animated) {
      const timer = setTimeout(() => {
        setOffset(circumference - (progress / 100) * circumference);
      }, 100);
      return () => clearTimeout(timer);
    } else if (!animated) {
      setOffset(circumference - (progress / 100) * circumference);
    }
  }, [circumference, progress, isInView, animated]);

  return (
    <div className={cn("relative inline-flex", className)}>
      <svg
        ref={ref}
        width={size}
        height={size}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={bgColor}
          strokeWidth={strokeWidth}
        />
        
        {/* Progress circle */}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          style={{
            transition: animated ? "stroke-dashoffset 1s ease-out" : "none",
          }}
        />
      </svg>
      
      {showPercentage && (
        <div className="absolute inset-0 flex items-center justify-center">
          <AnimatedNumber
            value={progress}
            suffix="%"
            className="text-xl font-bold text-white"
          />
        </div>
      )}
    </div>
  );
}

// ============================================================
// ANIMATED BAR CHART
// ============================================================

interface BarData {
  label: string;
  value: number;
  color?: string;
}

interface AnimatedBarChartProps {
  data: BarData[];
  height?: number;
  className?: string;
  showValues?: boolean;
  horizontal?: boolean;
}

export function AnimatedBarChart({
  data,
  height = 200,
  className,
  showValues = true,
  horizontal = false,
}: AnimatedBarChartProps) {
  const ref = useRef<HTMLDivElement>(null);
  const isInView = useInView(ref, { once: true, margin: "-100px" });
  const maxValue = Math.max(...data.map((d) => d.value));

  if (horizontal) {
    return (
      <div ref={ref} className={cn("space-y-3", className)}>
        {data.map((item, index) => (
          <div key={item.label} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">{item.label}</span>
              {showValues && (
                <AnimatedNumber
                  value={isInView ? item.value : 0}
                  className="font-medium text-white"
                />
              )}
            </div>
            <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
              <motion.div
                className="h-full rounded-full"
                style={{ backgroundColor: item.color || "#3b82f6" }}
                initial={{ width: 0 }}
                animate={{ width: isInView ? `${(item.value / maxValue) * 100}%` : 0 }}
                transition={{ duration: 0.8, delay: index * 0.1, ease: "easeOut" }}
              />
            </div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div ref={ref} className={cn("flex items-end gap-2", className)} style={{ height }}>
      {data.map((item, index) => (
        <div key={item.label} className="flex-1 flex flex-col items-center gap-2">
          <motion.div
            className="w-full rounded-t-lg"
            style={{ backgroundColor: item.color || "#3b82f6" }}
            initial={{ height: 0 }}
            animate={{ height: isInView ? `${(item.value / maxValue) * 100}%` : 0 }}
            transition={{ duration: 0.8, delay: index * 0.1, ease: "easeOut" }}
          />
          <span className="text-xs text-slate-400 truncate w-full text-center">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}

// ============================================================
// ANIMATED LINE CHART
// ============================================================

interface LineData {
  x: number;
  y: number;
}

interface AnimatedLineChartProps {
  data: LineData[];
  width?: number;
  height?: number;
  className?: string;
  color?: string;
  showDots?: boolean;
  showArea?: boolean;
  showGrid?: boolean;
}

export function AnimatedLineChart({
  data,
  width = 400,
  height = 200,
  className,
  color = "#3b82f6",
  showDots = true,
  showArea = true,
  showGrid = true,
}: AnimatedLineChartProps) {
  const ref = useRef<SVGSVGElement>(null);
  const isInView = useInView(ref, { once: true });
  
  const padding = 20;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  
  const maxX = Math.max(...data.map((d) => d.x));
  const maxY = Math.max(...data.map((d) => d.y));
  
  const points = data.map((d) => ({
    x: padding + (d.x / maxX) * chartWidth,
    y: height - padding - (d.y / maxY) * chartHeight,
  }));
  
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
  const areaPath = `${linePath} L ${points[points.length - 1].x} ${height - padding} L ${padding} ${height - padding} Z`;

  return (
    <svg ref={ref} width={width} height={height} className={className}>
      {/* Grid */}
      {showGrid && (
        <g className="text-slate-700">
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => (
            <line
              key={ratio}
              x1={padding}
              y1={padding + chartHeight * ratio}
              x2={width - padding}
              y2={padding + chartHeight * ratio}
              stroke="currentColor"
              strokeWidth="1"
              strokeDasharray="4 4"
            />
          ))}
        </g>
      )}
      
      {/* Area */}
      {showArea && (
        <motion.path
          d={areaPath}
          fill={`${color}20`}
          initial={{ opacity: 0 }}
          animate={{ opacity: isInView ? 1 : 0 }}
          transition={{ duration: 1 }}
        />
      )}
      
      {/* Line */}
      <motion.path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: isInView ? 1 : 0 }}
        transition={{ duration: 1.5, ease: "easeOut" }}
      />
      
      {/* Dots */}
      {showDots && points.map((point, i) => (
        <motion.circle
          key={i}
          cx={point.x}
          cy={point.y}
          r="4"
          fill={color}
          initial={{ scale: 0 }}
          animate={{ scale: isInView ? 1 : 0 }}
          transition={{ duration: 0.3, delay: 0.5 + i * 0.1 }}
        />
      ))}
    </svg>
  );
}

// ============================================================
// ANIMATED DONUT CHART
// ============================================================

interface DonutData {
  label: string;
  value: number;
  color: string;
}

interface AnimatedDonutChartProps {
  data: DonutData[];
  size?: number;
  thickness?: number;
  className?: string;
  showLegend?: boolean;
}

export function AnimatedDonutChart({
  data,
  size = 200,
  thickness = 30,
  className,
  showLegend = true,
}: AnimatedDonutChartProps) {
  const ref = useRef<SVGSVGElement>(null);
  const isInView = useInView(ref, { once: true });
  
  const total = data.reduce((sum, d) => sum + d.value, 0);
  const radius = (size - thickness) / 2;
  const circumference = radius * 2 * Math.PI;
  
  let cumulativeOffset = 0;

  return (
    <div className={cn("flex items-center gap-6", className)}>
      <div className="relative">
        <svg ref={ref} width={size} height={size}>
          {data.map((item, index) => {
            const percentage = item.value / total;
            const strokeDasharray = circumference;
            const strokeDashoffset = circumference - percentage * circumference;
            const rotation = cumulativeOffset * 360 - 90;
            cumulativeOffset += percentage;

            return (
              <motion.circle
                key={item.label}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="none"
                stroke={item.color}
                strokeWidth={thickness}
                strokeDasharray={strokeDasharray}
                strokeDashoffset={isInView ? strokeDashoffset : circumference}
                strokeLinecap="round"
                style={{
                  transformOrigin: "center",
                  transform: `rotate(${rotation}deg)`,
                }}
                initial={{ strokeDashoffset: circumference }}
                animate={{ strokeDashoffset: isInView ? strokeDashoffset : circumference }}
                transition={{ duration: 1, delay: index * 0.2, ease: "easeOut" }}
              />
            );
          })}
        </svg>
        
        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <AnimatedNumber value={total} className="text-2xl font-bold text-white" />
          <span className="text-xs text-slate-400">Total</span>
        </div>
      </div>
      
      {showLegend && (
        <div className="space-y-2">
          {data.map((item) => (
            <div key={item.label} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <span className="text-sm text-slate-300">{item.label}</span>
              <span className="text-sm font-medium text-white">{item.value}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ============================================================
// SPARKLINE
// ============================================================

interface SparklineProps {
  data: number[];
  width?: number;
  height?: number;
  color?: string;
  className?: string;
}

export function Sparkline({
  data,
  width = 100,
  height = 30,
  color = "#3b82f6",
  className,
}: SparklineProps) {
  const maxValue = Math.max(...data);
  const minValue = Math.min(...data);
  const range = maxValue - minValue || 1;
  
  const points = data.map((value, index) => ({
    x: (index / (data.length - 1)) * width,
    y: height - ((value - minValue) / range) * height,
  }));
  
  const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  return (
    <svg width={width} height={height} className={className}>
      <motion.path
        d={path}
        fill="none"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={{ pathLength: 0 }}
        animate={{ pathLength: 1 }}
        transition={{ duration: 1 }}
      />
    </svg>
  );
}

export default {
  AnimatedNumber,
  ProgressRing,
  AnimatedBarChart,
  AnimatedLineChart,
  AnimatedDonutChart,
  Sparkline,
};
