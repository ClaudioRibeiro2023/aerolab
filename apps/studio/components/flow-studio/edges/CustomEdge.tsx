'use client';

/**
 * Agno Flow Studio v3.0 - Custom Edge Component
 * 
 * Animated edge with data flow visualization and labels
 */

import React, { memo } from 'react';
import {
  BaseEdge,
  type EdgeProps,
  getBezierPath,
  EdgeLabelRenderer,
} from '@xyflow/react';
import { motion } from 'framer-motion';
import { X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { FlowEdgeData } from '../types';
import { useFlowStudioStore } from '../store';

// ============================================================
// Edge Path Styles
// ============================================================

const pathStyles = {
  default: {
    stroke: '#6366f1',
    strokeWidth: 2,
  },
  success: {
    stroke: '#22c55e',
    strokeWidth: 2,
  },
  error: {
    stroke: '#ef4444',
    strokeWidth: 2,
    strokeDasharray: '5,5',
  },
  conditional: {
    stroke: '#f59e0b',
    strokeWidth: 2,
    strokeDasharray: '10,5',
  },
};

// ============================================================
// Custom Edge Component
// ============================================================

const CustomEdgeComponent = (props: EdgeProps) => {
  const {
    id,
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
    selected,
    markerEnd,
    data: rawData,
  } = props;
  const data = (rawData ?? {}) as FlowEdgeData;
  const { removeEdge, ui } = useFlowStudioStore();
  const pathType = data.pathType || 'default';
  const style = pathStyles[pathType] || pathStyles.default;
  
  // Extract typed values for JSX
  const edgeCondition: string | null = typeof data.condition === 'string' ? data.condition : null;

  // Calculate bezier path
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
    curvature: 0.25,
  });

  // Handle edge deletion
  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    removeEdge(id);
  };

  return (
    <>
      {/* Base Edge Path */}
      <BaseEdge
        id={id}
        path={edgePath}
        style={{
          ...style,
          opacity: selected ? 1 : 0.8,
        }}
        markerEnd={markerEnd}
      />

      {/* Animated Flow Indicator */}
      {data?.animated && (
        <motion.circle
          r={4}
          fill={style.stroke}
          initial={{ offsetDistance: '0%' }}
          animate={{ offsetDistance: '100%' }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'linear',
          }}
          style={{
            offsetPath: `path("${edgePath}")`,
          }}
        />
      )}

      {/* Selection Highlight */}
      {selected && (
        <path
          d={edgePath}
          fill="none"
          stroke={style.stroke}
          strokeWidth={8}
          strokeOpacity={0.2}
          className="pointer-events-none"
        />
      )}

      {/* Edge Label Renderer */}
      <EdgeLabelRenderer>
        <div
          style={{
            position: 'absolute',
            transform: `translate(-50%, -50%) translate(${labelX}px,${labelY}px)`,
            pointerEvents: 'all',
          }}
          className="nodrag nopan"
        >
          {/* Condition Label */}
          {edgeCondition && (
            <div className={cn(
              "px-2 py-1 text-xs font-medium rounded-lg shadow-sm",
              "bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300",
              "border border-amber-200 dark:border-amber-800"
            )}>
              {edgeCondition}
            </div>
          )}

          {/* Custom Label - temporarily disabled due to TS inference issue */}

          {/* Delete Button (shown on hover/selection) */}
          {selected && ui.isEditing && (
            <motion.button
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
              onClick={handleDelete}
              className={cn(
                "absolute -top-3 -right-3 w-6 h-6 rounded-full",
                "bg-red-500 hover:bg-red-600 text-white",
                "flex items-center justify-center shadow-lg",
                "transition-colors"
              )}
              title="Delete Connection"
            >
              <X className="w-3 h-3" />
            </motion.button>
          )}

          {/* Data Preview on Hover */}
          {data?.dataPreview !== undefined ? (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={cn(
                "absolute top-full mt-2 left-1/2 -translate-x-1/2",
                "px-3 py-2 text-xs rounded-lg shadow-lg",
                "bg-slate-800 text-white",
                "border border-slate-700",
                "max-w-[200px] truncate"
              )}
            >
              <pre className="whitespace-pre-wrap">
                {typeof data.dataPreview === 'string' 
                  ? data.dataPreview 
                  : JSON.stringify(data.dataPreview, null, 2)}
              </pre>
            </motion.div>
          ) : null}
        </div>
      </EdgeLabelRenderer>
    </>
  );
};

export const CustomEdge = memo(CustomEdgeComponent);
export default CustomEdge;
