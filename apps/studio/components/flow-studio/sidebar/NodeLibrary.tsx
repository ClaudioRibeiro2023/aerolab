'use client';

/**
 * Agno Flow Studio v3.0 - Node Library Sidebar
 * 
 * Searchable, categorized node library with drag-to-add functionality
 */

import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Search, ChevronDown, ChevronRight, Star, Clock,
  Bot, GitBranch, Database, Brain, Plug, Shield,
  ArrowDownToLine, ArrowUpFromLine, Plus
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { NodeCategory, NodeDefinition, FlowNodeType } from '../types';
import { useFlowStudioStore } from '../store';

// ============================================================
// Node Definitions (60+ nodes)
// ============================================================

export const nodeDefinitions: NodeDefinition[] = [
  // AGENTS
  { type: 'agent', category: 'agents', name: 'Agent', description: 'AI Agent with LLM', icon: 'Bot', color: '#3B82F6', defaultInputs: [{ name: 'message', type: 'input', dataType: 'message', required: true }], defaultOutputs: [{ name: 'response', type: 'output', dataType: 'string' }], configSchema: { model: { type: 'select', label: 'Model', options: [{ value: 'gpt-4o', label: 'GPT-4o' }, { value: 'gpt-4o-mini', label: 'GPT-4o Mini' }, { value: 'claude-3-5-sonnet', label: 'Claude 3.5 Sonnet' }], default: 'gpt-4o' }, instructions: { type: 'code', label: 'Instructions' }, temperature: { type: 'number', label: 'Temperature', default: 0.7 } } },
  { type: 'team', category: 'agents', name: 'Team', description: 'Multi-agent team', icon: 'Users', color: '#8B5CF6', defaultInputs: [{ name: 'task', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'string' }], configSchema: { workflow: { type: 'select', label: 'Workflow', options: [{ value: 'sequential', label: 'Sequential' }, { value: 'hierarchical', label: 'Hierarchical' }] } } },
  { type: 'supervisor', category: 'agents', name: 'Supervisor', description: 'Orchestrates other agents', icon: 'Crown', color: '#3B82F6', defaultInputs: [{ name: 'task', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'string' }], configSchema: {} },
  { type: 'critic', category: 'agents', name: 'Critic', description: 'Reviews and validates output', icon: 'MessageSquareWarning', color: '#3B82F6', defaultInputs: [{ name: 'content', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'feedback', type: 'output', dataType: 'string' }], configSchema: {} },
  { type: 'planner', category: 'agents', name: 'Planner', description: 'Creates execution plans', icon: 'ListTodo', color: '#3B82F6', defaultInputs: [{ name: 'goal', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'plan', type: 'output', dataType: 'array' }], configSchema: {} },
  { type: 'researcher', category: 'agents', name: 'Researcher', description: 'Research and gather info', icon: 'Search', color: '#3B82F6', defaultInputs: [{ name: 'query', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'findings', type: 'output', dataType: 'string' }], configSchema: {} },
  { type: 'coder', category: 'agents', name: 'Coder', description: 'Writes and reviews code', icon: 'Code', color: '#3B82F6', defaultInputs: [{ name: 'task', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'code', type: 'output', dataType: 'string' }], configSchema: {} },
  
  // LOGIC
  { type: 'condition', category: 'logic', name: 'Condition', description: 'If/else branching', icon: 'GitBranch', color: '#F59E0B', defaultInputs: [{ name: 'value', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'true', type: 'output', dataType: 'any' }, { name: 'false', type: 'output', dataType: 'any' }], configSchema: { condition: { type: 'code', label: 'Condition' } } },
  { type: 'switch', category: 'logic', name: 'Switch', description: 'Multi-way branching', icon: 'Route', color: '#F59E0B', defaultInputs: [{ name: 'value', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'default', type: 'output', dataType: 'any' }], configSchema: { cases: { type: 'json', label: 'Cases' } } },
  { type: 'loop', category: 'logic', name: 'Loop', description: 'Iterate over items', icon: 'Repeat', color: '#6366F1', defaultInputs: [{ name: 'items', type: 'input', dataType: 'array', required: true }], defaultOutputs: [{ name: 'item', type: 'output', dataType: 'any' }, { name: 'complete', type: 'output', dataType: 'array' }], configSchema: { maxIterations: { type: 'number', label: 'Max Iterations', default: 10 } } },
  { type: 'parallel', category: 'logic', name: 'Parallel', description: 'Run branches in parallel', icon: 'GitFork', color: '#EC4899', defaultInputs: [{ name: 'input', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'results', type: 'output', dataType: 'array' }], configSchema: { branches: { type: 'number', label: 'Branches', default: 2 } } },
  { type: 'join', category: 'logic', name: 'Join', description: 'Wait for all inputs', icon: 'GitMerge', color: '#EC4899', defaultInputs: [{ name: 'input1', type: 'input', dataType: 'any' }, { name: 'input2', type: 'input', dataType: 'any' }], defaultOutputs: [{ name: 'output', type: 'output', dataType: 'array' }], configSchema: {} },
  { type: 'delay', category: 'logic', name: 'Delay', description: 'Wait for duration', icon: 'Timer', color: '#9CA3AF', defaultInputs: [{ name: 'input', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'output', type: 'output', dataType: 'any' }], configSchema: { seconds: { type: 'number', label: 'Seconds', default: 1 } } },
  { type: 'retry', category: 'logic', name: 'Retry', description: 'Retry on failure', icon: 'RefreshCw', color: '#F59E0B', defaultInputs: [{ name: 'input', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'output', type: 'output', dataType: 'any' }, { name: 'error', type: 'output', dataType: 'string' }], configSchema: { maxRetries: { type: 'number', label: 'Max Retries', default: 3 } } },
  { type: 'circuit-breaker', category: 'logic', name: 'Circuit Breaker', description: 'Fail fast on errors', icon: 'Zap', color: '#EF4444', defaultInputs: [{ name: 'input', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'output', type: 'output', dataType: 'any' }, { name: 'fallback', type: 'output', dataType: 'any' }], configSchema: { threshold: { type: 'number', label: 'Threshold', default: 5 } } },
  { type: 'rate-limiter', category: 'logic', name: 'Rate Limiter', description: 'Control execution rate', icon: 'Gauge', color: '#F59E0B', defaultInputs: [{ name: 'input', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'output', type: 'output', dataType: 'any' }], configSchema: { ratePerMinute: { type: 'number', label: 'Rate/min', default: 60 } } },
  
  // DATA
  { type: 'transform', category: 'data', name: 'Transform', description: 'Transform data with code', icon: 'Wand2', color: '#10B981', defaultInputs: [{ name: 'data', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'any' }], configSchema: { code: { type: 'code', label: 'Code' } } },
  { type: 'map', category: 'data', name: 'Map', description: 'Transform each item', icon: 'Map', color: '#10B981', defaultInputs: [{ name: 'items', type: 'input', dataType: 'array', required: true }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'array' }], configSchema: { expression: { type: 'code', label: 'Expression' } } },
  { type: 'filter', category: 'data', name: 'Filter', description: 'Filter items', icon: 'Filter', color: '#10B981', defaultInputs: [{ name: 'items', type: 'input', dataType: 'array', required: true }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'array' }], configSchema: { condition: { type: 'code', label: 'Condition' } } },
  { type: 'merge', category: 'data', name: 'Merge', description: 'Merge multiple inputs', icon: 'Combine', color: '#10B981', defaultInputs: [{ name: 'input1', type: 'input', dataType: 'any' }, { name: 'input2', type: 'input', dataType: 'any' }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'object' }], configSchema: {} },
  { type: 'split', category: 'data', name: 'Split', description: 'Split into multiple outputs', icon: 'Split', color: '#10B981', defaultInputs: [{ name: 'data', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'output1', type: 'output', dataType: 'any' }, { name: 'output2', type: 'output', dataType: 'any' }], configSchema: {} },
  { type: 'cache', category: 'data', name: 'Cache', description: 'Cache results', icon: 'HardDrive', color: '#10B981', defaultInputs: [{ name: 'key', type: 'input', dataType: 'string', required: true }, { name: 'value', type: 'input', dataType: 'any' }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'any' }], configSchema: { ttl: { type: 'number', label: 'TTL (seconds)', default: 3600 } } },
  
  // MEMORY
  { type: 'memory-read', category: 'memory', name: 'Memory Read', description: 'Read from memory', icon: 'BookOpen', color: '#06B6D4', defaultInputs: [{ name: 'query', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'memories', type: 'output', dataType: 'array' }], configSchema: { limit: { type: 'number', label: 'Limit', default: 10 } } },
  { type: 'memory-write', category: 'memory', name: 'Memory Write', description: 'Write to memory', icon: 'BookPlus', color: '#06B6D4', defaultInputs: [{ name: 'content', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'id', type: 'output', dataType: 'string' }], configSchema: {} },
  { type: 'rag-search', category: 'memory', name: 'RAG Search', description: 'Search documents', icon: 'FileSearch', color: '#14B8A6', defaultInputs: [{ name: 'query', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'documents', type: 'output', dataType: 'array' }], configSchema: { limit: { type: 'number', label: 'Limit', default: 5 } } },
  { type: 'vector-store', category: 'memory', name: 'Vector Store', description: 'Store embeddings', icon: 'Layers', color: '#06B6D4', defaultInputs: [{ name: 'text', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'id', type: 'output', dataType: 'string' }], configSchema: {} },
  
  // INTEGRATIONS
  { type: 'http', category: 'integrations', name: 'HTTP Request', description: 'Make HTTP requests', icon: 'Globe', color: '#8B5CF6', defaultInputs: [{ name: 'body', type: 'input', dataType: 'any' }], defaultOutputs: [{ name: 'response', type: 'output', dataType: 'any' }], configSchema: { method: { type: 'select', label: 'Method', options: [{ value: 'GET', label: 'GET' }, { value: 'POST', label: 'POST' }, { value: 'PUT', label: 'PUT' }, { value: 'DELETE', label: 'DELETE' }] }, url: { type: 'string', label: 'URL' } } },
  { type: 'webhook', category: 'integrations', name: 'Webhook', description: 'Receive webhooks', icon: 'Webhook', color: '#8B5CF6', defaultInputs: [], defaultOutputs: [{ name: 'payload', type: 'output', dataType: 'object' }], configSchema: {} },
  { type: 'database', category: 'integrations', name: 'Database', description: 'Query database', icon: 'Database', color: '#8B5CF6', defaultInputs: [{ name: 'query', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'array' }], configSchema: { connection: { type: 'string', label: 'Connection String' } } },
  { type: 'email', category: 'integrations', name: 'Email', description: 'Send emails', icon: 'Mail', color: '#8B5CF6', defaultInputs: [{ name: 'to', type: 'input', dataType: 'string', required: true }, { name: 'body', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'success', type: 'output', dataType: 'boolean' }], configSchema: {} },
  { type: 'slack', category: 'integrations', name: 'Slack', description: 'Send to Slack', icon: 'MessageSquare', color: '#8B5CF6', defaultInputs: [{ name: 'message', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'success', type: 'output', dataType: 'boolean' }], configSchema: { channel: { type: 'string', label: 'Channel' } } },
  { type: 'mcp-tool', category: 'integrations', name: 'MCP Tool', description: 'Use MCP server tool', icon: 'Puzzle', color: '#8B5CF6', defaultInputs: [{ name: 'args', type: 'input', dataType: 'object', required: true }], defaultOutputs: [{ name: 'result', type: 'output', dataType: 'any' }], configSchema: { server: { type: 'string', label: 'Server' }, tool: { type: 'string', label: 'Tool' } } },
  
  // GOVERNANCE
  { type: 'human-approval', category: 'governance', name: 'Human Approval', description: 'Request human approval', icon: 'UserCheck', color: '#EF4444', defaultInputs: [{ name: 'request', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'approved', type: 'output', dataType: 'any' }, { name: 'rejected', type: 'output', dataType: 'any' }], configSchema: { approvers: { type: 'string', label: 'Approvers' } } },
  { type: 'audit-log', category: 'governance', name: 'Audit Log', description: 'Log for auditing', icon: 'FileText', color: '#EF4444', defaultInputs: [{ name: 'event', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'logged', type: 'output', dataType: 'boolean' }], configSchema: {} },
  { type: 'secret-fetch', category: 'governance', name: 'Secret Fetch', description: 'Fetch secrets', icon: 'Key', color: '#EF4444', defaultInputs: [{ name: 'name', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'value', type: 'output', dataType: 'string' }], configSchema: {} },
  { type: 'cost-guard', category: 'governance', name: 'Cost Guard', description: 'Limit costs', icon: 'DollarSign', color: '#EF4444', defaultInputs: [{ name: 'input', type: 'input', dataType: 'any', required: true }], defaultOutputs: [{ name: 'output', type: 'output', dataType: 'any' }, { name: 'blocked', type: 'output', dataType: 'any' }], configSchema: { maxCost: { type: 'number', label: 'Max Cost ($)', default: 10 } } },
  { type: 'pii-detector', category: 'governance', name: 'PII Detector', description: 'Detect PII data', icon: 'ShieldAlert', color: '#EF4444', defaultInputs: [{ name: 'text', type: 'input', dataType: 'string', required: true }], defaultOutputs: [{ name: 'clean', type: 'output', dataType: 'string' }, { name: 'detected', type: 'output', dataType: 'array' }], configSchema: {} },
  
  // I/O
  { type: 'input', category: 'input', name: 'Input', description: 'Workflow input', icon: 'ArrowDownToLine', color: '#22C55E', defaultInputs: [], defaultOutputs: [{ name: 'data', type: 'output', dataType: 'any' }], configSchema: { schema: { type: 'json', label: 'Schema' } } },
  { type: 'output', category: 'output', name: 'Output', description: 'Workflow output', icon: 'ArrowUpFromLine', color: '#F43F5E', defaultInputs: [{ name: 'data', type: 'input', dataType: 'any', required: true }], defaultOutputs: [], configSchema: {} },
];

// ============================================================
// Category Config
// ============================================================

const categories: { id: NodeCategory; name: string; icon: React.ElementType }[] = [
  { id: 'agents', name: 'Agents', icon: Bot },
  { id: 'logic', name: 'Logic & Control', icon: GitBranch },
  { id: 'data', name: 'Data', icon: Database },
  { id: 'memory', name: 'Memory & RAG', icon: Brain },
  { id: 'integrations', name: 'Integrations', icon: Plug },
  { id: 'governance', name: 'Governance', icon: Shield },
  { id: 'input', name: 'Input', icon: ArrowDownToLine },
  { id: 'output', name: 'Output', icon: ArrowUpFromLine },
];

// ============================================================
// Node Item Component
// ============================================================

interface NodeItemProps {
  definition: NodeDefinition;
  onAdd: () => void;
}

const NodeItem: React.FC<NodeItemProps> = ({ definition, onAdd }) => {
  return (
    <motion.div
      draggable
      onDragStart={(e) => {
        (e as any).dataTransfer?.setData('application/reactflow', JSON.stringify(definition));
      }}
      whileHover={{ scale: 1.02, x: 4 }}
      whileTap={{ scale: 0.98 }}
      className={cn(
        "flex items-center gap-3 p-3 rounded-xl cursor-grab active:cursor-grabbing",
        "bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700",
        "hover:border-blue-300 dark:hover:border-blue-600 hover:shadow-md",
        "transition-all group"
      )}
    >
      <div
        className="w-8 h-8 rounded-lg flex items-center justify-center text-white text-sm"
        style={{ backgroundColor: definition.color }}
      >
        {definition.name.charAt(0)}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
          {definition.name}
        </p>
        <p className="text-xs text-gray-500 dark:text-gray-400 truncate">
          {definition.description}
        </p>
      </div>
      <button
        onClick={(e) => { e.stopPropagation(); onAdd(); }}
        className="p-1 opacity-0 group-hover:opacity-100 hover:bg-gray-100 dark:hover:bg-slate-700 rounded transition-all"
        title="Add to canvas"
      >
        <Plus className="w-4 h-4" />
      </button>
    </motion.div>
  );
};

// ============================================================
// Main Node Library Component
// ============================================================

export const NodeLibrary: React.FC = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<NodeCategory[]>(['agents', 'logic']);
  const { addNode, nodes } = useFlowStudioStore();

  // Filter nodes by search
  const filteredNodes = useMemo(() => {
    if (!searchQuery) return nodeDefinitions;
    const query = searchQuery.toLowerCase();
    return nodeDefinitions.filter(
      n => n.name.toLowerCase().includes(query) || 
           n.description.toLowerCase().includes(query) ||
           n.category.toLowerCase().includes(query)
    );
  }, [searchQuery]);

  // Group by category
  const groupedNodes = useMemo(() => {
    const groups: Record<NodeCategory, NodeDefinition[]> = {} as any;
    categories.forEach(c => { groups[c.id] = []; });
    filteredNodes.forEach(n => {
      if (groups[n.category]) groups[n.category].push(n);
    });
    return groups;
  }, [filteredNodes]);

  // Toggle category
  const toggleCategory = (cat: NodeCategory) => {
    setExpandedCategories(prev =>
      prev.includes(cat) ? prev.filter(c => c !== cat) : [...prev, cat]
    );
  };

  // Add node to canvas
  const handleAddNode = (definition: NodeDefinition) => {
    const newNode = {
      id: `node_${Date.now()}`,
      type: 'custom',
      position: { x: 200 + Math.random() * 200, y: 100 + Math.random() * 200 },
      data: {
        label: definition.name,
        description: definition.description,
        nodeType: definition.type,
        category: definition.category,
        icon: definition.icon,
        color: definition.color,
        inputs: definition.defaultInputs.map((p, i) => ({ ...p, id: `input_${i}` })),
        outputs: definition.defaultOutputs.map((p, i) => ({ ...p, id: `output_${i}` })),
        config: Object.fromEntries(
          Object.entries(definition.configSchema).map(([k, v]) => [k, v.default])
        ),
        status: 'idle',
      },
    };
    addNode(newNode as any);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-4 border-b border-gray-200 dark:border-slate-700">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search nodes..."
            className={cn(
              "w-full pl-9 pr-4 py-2 text-sm rounded-xl",
              "bg-gray-100 dark:bg-slate-800 border border-gray-200 dark:border-slate-700",
              "focus:ring-2 focus:ring-blue-500 focus:border-transparent",
              "placeholder-gray-400 dark:placeholder-gray-500"
            )}
          />
        </div>
      </div>

      {/* Quick Actions */}
      <div className="px-4 py-2 border-b border-gray-200 dark:border-slate-700">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <button className="flex items-center gap-1 px-2 py-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded transition-colors">
            <Star className="w-3 h-3" /> Favorites
          </button>
          <button className="flex items-center gap-1 px-2 py-1 hover:bg-gray-100 dark:hover:bg-slate-800 rounded transition-colors">
            <Clock className="w-3 h-3" /> Recent
          </button>
        </div>
      </div>

      {/* Categories */}
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {categories.map(cat => {
          const catNodes = groupedNodes[cat.id];
          if (!catNodes || catNodes.length === 0) return null;
          
          const isExpanded = expandedCategories.includes(cat.id);
          const Icon = cat.icon;

          return (
            <div key={cat.id} className="space-y-2">
              <button
                onClick={() => toggleCategory(cat.id)}
                className={cn(
                  "flex items-center gap-2 w-full px-3 py-2 text-sm font-medium rounded-lg",
                  "hover:bg-gray-100 dark:hover:bg-slate-800 transition-colors",
                  "text-gray-700 dark:text-gray-300"
                )}
              >
                {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                <Icon className="w-4 h-4" />
                <span className="flex-1 text-left">{cat.name}</span>
                <span className="text-xs text-gray-400">{catNodes.length}</span>
              </button>
              
              <AnimatePresence>
                {isExpanded && (
                  <motion.div
                    initial={{ height: 0, opacity: 0 }}
                    animate={{ height: 'auto', opacity: 1 }}
                    exit={{ height: 0, opacity: 0 }}
                    transition={{ duration: 0.2 }}
                    className="space-y-2 pl-4 overflow-hidden"
                  >
                    {catNodes.map(node => (
                      <NodeItem
                        key={node.type}
                        definition={node}
                        onAdd={() => handleAddNode(node)}
                      />
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          );
        })}
      </div>

      {/* Stats */}
      <div className="p-4 border-t border-gray-200 dark:border-slate-700">
        <p className="text-xs text-gray-500 text-center">
          {nodeDefinitions.length} nodes available • {nodes.length} in canvas
        </p>
      </div>
    </div>
  );
};

export default NodeLibrary;
