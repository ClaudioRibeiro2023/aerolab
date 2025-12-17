'use client';

/**
 * Agno Flow Studio v3.0 - Flow Canvas
 * 
 * Main canvas component using React Flow
 */

import React, { useCallback, useRef, useMemo } from 'react';
import {
  ReactFlow,
  Controls,
  MiniMap,
  Background,
  BackgroundVariant,
  Panel,
  useReactFlow,
  ReactFlowProvider,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ZoomIn, ZoomOut, Maximize2, Lock, Unlock, 
  Grid3X3, Map, Undo2, Redo2, Play, Square, Bug
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useFlowStudioStore } from './store';
import { FlowNode, FlowEdge, FlowNodeData, FlowEdgeData } from './types';
import { CustomNode } from './nodes/CustomNode';
import { CustomEdge } from './edges/CustomEdge';
import type { NodeTypes, EdgeTypes } from '@xyflow/react';

// ============================================================
// Node Types Registration
// ============================================================

const nodeTypes: NodeTypes = {
  custom: CustomNode as NodeTypes['custom'],
};

const edgeTypes: EdgeTypes = {
  custom: CustomEdge as EdgeTypes['custom'],
};

// ============================================================
// Canvas Controls Component
// ============================================================

interface CanvasControlsProps {
  onFitView: () => void;
  onZoomIn: () => void;
  onZoomOut: () => void;
}

const CanvasControls: React.FC<CanvasControlsProps> = ({
  onFitView,
  onZoomIn,
  onZoomOut,
}) => {
  const { 
    canvasSettings, 
    updateCanvasSettings,
    ui,
    startExecution,
    stopExecution,
  } = useFlowStudioStore();

  return (
    <Panel position="top-right" className="flex flex-col gap-2">
      {/* Zoom Controls */}
      <div className="flex items-center gap-1 bg-white dark:bg-slate-800 rounded-xl p-1 shadow-lg border border-gray-200 dark:border-slate-700">
        <button
          onClick={onZoomOut}
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Zoom Out (Ctrl+-)"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={onFitView}
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Fit View (Ctrl+0)"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <button
          onClick={onZoomIn}
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Zoom In (Ctrl++)"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
      </div>

      {/* Canvas Options */}
      <div className="flex items-center gap-1 bg-white dark:bg-slate-800 rounded-xl p-1 shadow-lg border border-gray-200 dark:border-slate-700">
        <button
          onClick={() => updateCanvasSettings({ snapToGrid: !canvasSettings.snapToGrid })}
          className={cn(
            "p-2 rounded-lg transition-colors",
            canvasSettings.snapToGrid 
              ? "bg-blue-100 dark:bg-blue-900/30 text-blue-600" 
              : "hover:bg-gray-100 dark:hover:bg-slate-700"
          )}
          title="Snap to Grid"
        >
          <Grid3X3 className="w-4 h-4" />
        </button>
        <button
          onClick={() => updateCanvasSettings({ showMinimap: !canvasSettings.showMinimap })}
          className={cn(
            "p-2 rounded-lg transition-colors",
            canvasSettings.showMinimap 
              ? "bg-blue-100 dark:bg-blue-900/30 text-blue-600" 
              : "hover:bg-gray-100 dark:hover:bg-slate-700"
          )}
          title="Toggle Minimap"
        >
          <Map className="w-4 h-4" />
        </button>
        <button
          onClick={() => updateCanvasSettings({ panOnDrag: !canvasSettings.panOnDrag })}
          className={cn(
            "p-2 rounded-lg transition-colors",
            !canvasSettings.panOnDrag 
              ? "bg-amber-100 dark:bg-amber-900/30 text-amber-600" 
              : "hover:bg-gray-100 dark:hover:bg-slate-700"
          )}
          title={canvasSettings.panOnDrag ? "Lock Canvas" : "Unlock Canvas"}
        >
          {canvasSettings.panOnDrag ? <Unlock className="w-4 h-4" /> : <Lock className="w-4 h-4" />}
        </button>
      </div>

      {/* Execution Controls */}
      <div className="flex items-center gap-1 bg-white dark:bg-slate-800 rounded-xl p-1 shadow-lg border border-gray-200 dark:border-slate-700">
        {!ui.isExecuting ? (
          <button
            onClick={() => startExecution()}
            className="p-2 hover:bg-green-100 dark:hover:bg-green-900/30 text-green-600 rounded-lg transition-colors"
            title="Run Workflow (F5)"
          >
            <Play className="w-4 h-4" />
          </button>
        ) : (
          <button
            onClick={stopExecution}
            className="p-2 hover:bg-red-100 dark:hover:bg-red-900/30 text-red-600 rounded-lg transition-colors"
            title="Stop Execution"
          >
            <Square className="w-4 h-4" />
          </button>
        )}
        <button
          onClick={() => {/* TODO: Toggle debug mode */}}
          className={cn(
            "p-2 rounded-lg transition-colors",
            ui.isDebugging 
              ? "bg-purple-100 dark:bg-purple-900/30 text-purple-600" 
              : "hover:bg-gray-100 dark:hover:bg-slate-700"
          )}
          title="Debug Mode"
        >
          <Bug className="w-4 h-4" />
        </button>
      </div>
    </Panel>
  );
};

// ============================================================
// History Controls Component  
// ============================================================

const HistoryControls: React.FC = () => {
  const { useStore } = useFlowStudioStore as any;
  
  return (
    <Panel position="bottom-left" className="flex items-center gap-1 bg-white dark:bg-slate-800 rounded-xl p-1 shadow-lg border border-gray-200 dark:border-slate-700">
      <button
        onClick={() => {/* TODO: Undo */}}
        className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
        title="Undo (Ctrl+Z)"
      >
        <Undo2 className="w-4 h-4" />
      </button>
      <button
        onClick={() => {/* TODO: Redo */}}
        className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors disabled:opacity-50"
        title="Redo (Ctrl+Y)"
      >
        <Redo2 className="w-4 h-4" />
      </button>
    </Panel>
  );
};

// ============================================================
// Main Flow Canvas Component
// ============================================================

const FlowCanvasInner: React.FC = () => {
  const reactFlowInstance = useReactFlow();
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  
  const {
    nodes,
    edges,
    canvasSettings,
    ui,
    onNodesChange,
    onEdgesChange,
    onConnect,
    selectNode,
    clearSelection,
  } = useFlowStudioStore();

  // Handlers
  const handleFitView = useCallback(() => {
    reactFlowInstance.fitView({ padding: 0.2, duration: 300 });
  }, [reactFlowInstance]);

  const handleZoomIn = useCallback(() => {
    reactFlowInstance.zoomIn({ duration: 200 });
  }, [reactFlowInstance]);

  const handleZoomOut = useCallback(() => {
    reactFlowInstance.zoomOut({ duration: 200 });
  }, [reactFlowInstance]);

  const handleNodeClick = useCallback((event: React.MouseEvent, node: FlowNode) => {
    selectNode(node.id, event.ctrlKey || event.metaKey);
  }, [selectNode]);

  const handlePaneClick = useCallback(() => {
    clearSelection();
  }, [clearSelection]);

  // Keyboard shortcuts
  React.useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case '0':
            e.preventDefault();
            handleFitView();
            break;
          case '=':
          case '+':
            e.preventDefault();
            handleZoomIn();
            break;
          case '-':
            e.preventDefault();
            handleZoomOut();
            break;
        }
      }
      
      if (e.key === 'Delete' || e.key === 'Backspace') {
        if (document.activeElement?.tagName !== 'INPUT' && 
            document.activeElement?.tagName !== 'TEXTAREA') {
          e.preventDefault();
          useFlowStudioStore.getState().deleteSelected();
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleFitView, handleZoomIn, handleZoomOut]);

  // Memoized props
  const defaultEdgeOptions = useMemo(() => ({
    type: 'custom',
    animated: true,
  }), []);

  return (
    <div ref={reactFlowWrapper} className="w-full h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={handleNodeClick}
        onPaneClick={handlePaneClick}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        defaultEdgeOptions={defaultEdgeOptions}
        snapToGrid={canvasSettings.snapToGrid}
        snapGrid={[canvasSettings.gridSize, canvasSettings.gridSize]}
        panOnDrag={canvasSettings.panOnDrag}
        zoomOnScroll={canvasSettings.zoomOnScroll}
        fitView={canvasSettings.fitViewOnInit}
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={4}
        deleteKeyCode={null} // We handle delete manually
        className="bg-gray-50 dark:bg-slate-900"
      >
        {/* Background Grid */}
        {canvasSettings.showGrid && (
          <Background
            variant={BackgroundVariant.Dots}
            gap={canvasSettings.gridSize}
            size={1}
            color="#94a3b8"
            className="opacity-30"
          />
        )}

        {/* Minimap */}
        <AnimatePresence>
          {canvasSettings.showMinimap && (
            <motion.div
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8 }}
              transition={{ duration: 0.2 }}
            >
              <MiniMap
                nodeColor={(node) => {
                  const data = node.data as FlowNodeData | undefined;
                  return data?.color || '#6366f1';
                }}
                maskColor="rgba(0, 0, 0, 0.1)"
                className="!bg-white dark:!bg-slate-800 !rounded-xl !border !border-gray-200 dark:!border-slate-700 !shadow-lg"
                pannable
                zoomable
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Controls */}
        <CanvasControls
          onFitView={handleFitView}
          onZoomIn={handleZoomIn}
          onZoomOut={handleZoomOut}
        />

        {/* History Controls */}
        <HistoryControls />

        {/* Default Controls (hidden, we use custom) */}
        <Controls 
          showZoom={false}
          showFitView={false}
          showInteractive={false}
          className="hidden"
        />
      </ReactFlow>
    </div>
  );
};

// ============================================================
// Exported Component with Provider
// ============================================================

export const FlowCanvas: React.FC = () => {
  return (
    <ReactFlowProvider>
      <FlowCanvasInner />
    </ReactFlowProvider>
  );
};

export default FlowCanvas;
