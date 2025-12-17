'use client';

/**
 * Agno Flow Studio v3.0 - Custom Node Component
 * 
 * Highly customizable node component with ports, status indicators, and animations
 */

import React, { memo, useMemo } from 'react';
import { Handle, Position, type NodeProps } from '@xyflow/react';
import type { Node } from '@xyflow/react';
import { motion } from 'framer-motion';
import { 
  Bot, GitBranch, Database, Brain, Plug, Shield, 
  ArrowDownToLine, ArrowUpFromLine, MoreHorizontal,
  Play, CheckCircle, XCircle, Loader2, AlertCircle, Clock
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { FlowNodeData, NodeCategory, Port } from '../types';

// ============================================================
// Category Icons & Colors
// ============================================================

const categoryConfig: Record<NodeCategory, { icon: React.ElementType; gradient: string; glow: string }> = {
  agents: { 
    icon: Bot, 
    gradient: 'from-blue-500 to-blue-600',
    glow: 'shadow-blue-500/25'
  },
  logic: { 
    icon: GitBranch, 
    gradient: 'from-amber-500 to-orange-500',
    glow: 'shadow-amber-500/25'
  },
  data: { 
    icon: Database, 
    gradient: 'from-emerald-500 to-teal-500',
    glow: 'shadow-emerald-500/25'
  },
  memory: { 
    icon: Brain, 
    gradient: 'from-cyan-500 to-blue-500',
    glow: 'shadow-cyan-500/25'
  },
  integrations: { 
    icon: Plug, 
    gradient: 'from-violet-500 to-purple-500',
    glow: 'shadow-violet-500/25'
  },
  governance: { 
    icon: Shield, 
    gradient: 'from-red-500 to-rose-500',
    glow: 'shadow-red-500/25'
  },
  input: { 
    icon: ArrowDownToLine, 
    gradient: 'from-green-500 to-emerald-500',
    glow: 'shadow-green-500/25'
  },
  output: { 
    icon: ArrowUpFromLine, 
    gradient: 'from-rose-500 to-pink-500',
    glow: 'shadow-rose-500/25'
  },
};

// ============================================================
// Status Indicators
// ============================================================

const StatusIndicator: React.FC<{ status?: FlowNodeData['status'] }> = ({ status }) => {
  const config = {
    idle: { icon: null, color: 'bg-gray-400', animate: false },
    running: { icon: Loader2, color: 'bg-blue-500', animate: true },
    success: { icon: CheckCircle, color: 'bg-green-500', animate: false },
    error: { icon: XCircle, color: 'bg-red-500', animate: false },
    skipped: { icon: AlertCircle, color: 'bg-gray-500', animate: false },
    waiting: { icon: Clock, color: 'bg-amber-500', animate: true },
  };

  const current = status ? config[status] : config.idle;
  const Icon = current.icon;

  if (!Icon && status === 'idle') return null;

  return (
    <motion.div
      initial={{ scale: 0 }}
      animate={{ scale: 1 }}
      className={cn(
        "absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center",
        current.color
      )}
    >
      {Icon && (
        <Icon 
          className={cn(
            "w-3 h-3 text-white",
            current.animate && "animate-spin"
          )} 
        />
      )}
    </motion.div>
  );
};

// ============================================================
// Port Handle Component
// ============================================================

interface PortHandleProps {
  port: Port;
  position: Position;
  index: number;
  total: number;
}

const PortHandle: React.FC<PortHandleProps> = ({ port, position, index, total }) => {
  // Calculate position offset for multiple ports
  const offset = total > 1 ? ((index + 1) / (total + 1)) * 100 : 50;
  
  const style = position === Position.Left || position === Position.Right
    ? { top: `${offset}%` }
    : { left: `${offset}%` };

  return (
    <Handle
      type={port.type === 'input' ? 'target' : 'source'}
      position={position}
      id={port.id}
      style={style}
      className={cn(
        "!w-3 !h-3 !border-2 !border-white dark:!border-slate-800 transition-all",
        port.type === 'input' 
          ? "!bg-blue-500 hover:!bg-blue-600" 
          : "!bg-emerald-500 hover:!bg-emerald-600",
        port.required && "!ring-2 !ring-amber-500/50"
      )}
      title={`${port.name} (${port.dataType})`}
    />
  );
};

// ============================================================
// Main Custom Node Component
// ============================================================

type FlowNodeProps = NodeProps<Node<FlowNodeData>>;

const CustomNodeComponent: React.FC<FlowNodeProps> = (props) => {
  const { selected, dragging } = props;
  const data = props.data as FlowNodeData;
  const category = categoryConfig[data.category] || categoryConfig.agents;
  const CategoryIcon = category.icon;

  // Memoize ports rendering
  const inputPorts = useMemo(() => 
    data.inputs?.map((port, i) => (
      <PortHandle 
        key={port.id} 
        port={port} 
        position={Position.Left} 
        index={i}
        total={data.inputs?.length || 0}
      />
    )), 
    [data.inputs]
  );

  const outputPorts = useMemo(() => 
    data.outputs?.map((port, i) => (
      <PortHandle 
        key={port.id} 
        port={port} 
        position={Position.Right} 
        index={i}
        total={data.outputs?.length || 0}
      />
    )), 
    [data.outputs]
  );

  return (
    <motion.div
      initial={{ scale: 0.8, opacity: 0 }}
      animate={{ 
        scale: dragging ? 1.05 : 1, 
        opacity: 1,
        boxShadow: selected 
          ? '0 0 0 2px #3b82f6, 0 8px 30px rgba(0,0,0,0.12)' 
          : '0 4px 20px rgba(0,0,0,0.08)'
      }}
      transition={{ 
        duration: 0.2,
        type: 'spring',
        stiffness: 300,
        damping: 25
      }}
      className={cn(
        "relative min-w-[180px] max-w-[280px] bg-white dark:bg-slate-800 rounded-xl border-2 transition-colors",
        selected 
          ? "border-blue-500" 
          : "border-gray-200 dark:border-slate-700",
        data.status === 'running' && "animate-pulse",
        data.status === 'error' && "border-red-500",
        data.status === 'success' && "border-green-500"
      )}
    >
      {/* Input Ports */}
      {inputPorts}

      {/* Output Ports */}
      {outputPorts}

      {/* Status Indicator */}
      <StatusIndicator status={data.status} />

      {/* Header */}
      <div className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-t-lg bg-gradient-to-r",
        category.gradient
      )}>
        <CategoryIcon className="w-4 h-4 text-white" />
        <span className="text-sm font-medium text-white truncate flex-1">
          {data.label}
        </span>
        <button 
          className="p-0.5 hover:bg-white/20 rounded transition-colors"
          onClick={(e) => {
            e.stopPropagation();
            // TODO: Open node menu
          }}
        >
          <MoreHorizontal className="w-4 h-4 text-white/80" />
        </button>
      </div>

      {/* Body */}
      <div className="px-3 py-2">
        {data.description && (
          <p className="text-xs text-gray-500 dark:text-gray-400 mb-2 line-clamp-2">
            {data.description}
          </p>
        )}

        {/* Config preview */}
        {data.config && Object.keys(data.config).length > 0 && !data.collapsed && (
          <div className="space-y-1">
            {Object.entries(data.config).slice(0, 3).map(([key, value]) => (
              <div key={key} className="flex items-center justify-between text-xs">
                <span className="text-gray-500 dark:text-gray-400">{key}:</span>
                <span className="text-gray-700 dark:text-gray-300 truncate ml-2 max-w-[120px]">
                  {typeof value === 'string' ? value : JSON.stringify(value)}
                </span>
              </div>
            ))}
          </div>
        )}

        {/* Execution metrics */}
        {data.status === 'success' && (data.executionTime || data.tokenUsage) && (
          <div className="mt-2 pt-2 border-t border-gray-100 dark:border-slate-700 flex items-center gap-3 text-xs text-gray-500">
            {data.executionTime && (
              <span>{data.executionTime}ms</span>
            )}
            {data.tokenUsage && (
              <span>{data.tokenUsage} tokens</span>
            )}
            {data.cost && (
              <span>${data.cost.toFixed(4)}</span>
            )}
          </div>
        )}

        {/* Error message */}
        {data.status === 'error' && data.error && (
          <div className="mt-2 p-2 bg-red-50 dark:bg-red-900/20 rounded-lg">
            <p className="text-xs text-red-600 dark:text-red-400 line-clamp-2">
              {data.error}
            </p>
          </div>
        )}
      </div>

      {/* Validation errors */}
      {data.validationErrors && data.validationErrors.length > 0 && (
        <div className="absolute -bottom-6 left-0 right-0 text-center">
          <span className="text-xs text-red-500 bg-red-50 dark:bg-red-900/30 px-2 py-0.5 rounded">
            {data.validationErrors.length} error(s)
          </span>
        </div>
      )}
    </motion.div>
  );
};

export const CustomNode = memo(CustomNodeComponent);
export default CustomNode;
