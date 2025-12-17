'use client';

/**
 * Agno Flow Studio v3.0 - Main Page
 */

import React, { useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen,
  Save, Play, Settings, FileJson, Download, Upload, Undo2, Redo2,
  Sun, Moon, HelpCircle
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { FlowCanvas, NodeLibrary, useFlowStudioStore } from '@/components/flow-studio';
import Protected from '@/components/Protected';
import { PageHeader } from '@/components/PageHeader';

// ============================================================
// Header Component
// ============================================================

const Header: React.FC = () => {
  const { workflow, isDirty, saveWorkflow, ui, setTheme } = useFlowStudioStore();

  return (
    <header className="h-14 border-b border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-800 flex items-center justify-between px-4">
      {/* Left - Branding & Workflow Name */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">A</span>
          </div>
          <span className="font-semibold text-gray-900 dark:text-white">Flow Studio</span>
        </div>
        
        <div className="h-6 w-px bg-gray-200 dark:bg-slate-700" />
        
        <div className="flex items-center gap-2">
          <input
            type="text"
            value={workflow?.name || 'Untitled Workflow'}
            onChange={() => {}}
            className="bg-transparent font-medium text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
          />
          {isDirty && (
            <span className="text-xs text-amber-500 font-medium">• Unsaved</span>
          )}
        </div>
      </div>

      {/* Center - Actions */}
      <div className="flex items-center gap-1">
        <button
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Undo (Ctrl+Z)"
        >
          <Undo2 className="w-4 h-4" />
        </button>
        <button
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Redo (Ctrl+Y)"
        >
          <Redo2 className="w-4 h-4" />
        </button>
        
        <div className="h-6 w-px bg-gray-200 dark:bg-slate-700 mx-2" />
        
        <button
          onClick={() => saveWorkflow()}
          className={cn(
            "flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-colors",
            isDirty
              ? "bg-blue-500 hover:bg-blue-600 text-white"
              : "bg-gray-100 dark:bg-slate-700 text-gray-600 dark:text-gray-300"
          )}
        >
          <Save className="w-4 h-4" />
          Save
        </button>
        
        <button
          className="flex items-center gap-2 px-3 py-1.5 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors"
        >
          <Play className="w-4 h-4" />
          Run
        </button>
      </div>

      {/* Right - Settings */}
      <div className="flex items-center gap-1">
        <button
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Import"
        >
          <Upload className="w-4 h-4" />
        </button>
        <button
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Export"
        >
          <Download className="w-4 h-4" />
        </button>
        <button
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="View JSON"
        >
          <FileJson className="w-4 h-4" />
        </button>
        
        <div className="h-6 w-px bg-gray-200 dark:bg-slate-700 mx-2" />
        
        <button
          onClick={() => setTheme(ui.theme === 'dark' ? 'light' : 'dark')}
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Toggle Theme"
        >
          {ui.theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
        <button
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Settings"
        >
          <Settings className="w-4 h-4" />
        </button>
        <button
          className="p-2 hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
          title="Help"
        >
          <HelpCircle className="w-4 h-4" />
        </button>
      </div>
    </header>
  );
};

// ============================================================
// Sidebar Component
// ============================================================

const Sidebar: React.FC<{ side: 'left' | 'right' }> = ({ side }) => {
  const { ui, toggleSidebar, toggleInspector } = useFlowStudioStore();
  
  const isOpen = side === 'left' ? ui.sidebarOpen : ui.inspectorOpen;
  const toggle = side === 'left' ? toggleSidebar : toggleInspector;

  return (
    <motion.aside
      initial={false}
      animate={{ width: isOpen ? 320 : 0 }}
      transition={{ duration: 0.2 }}
      className={cn(
        "h-full bg-white dark:bg-slate-800 border-gray-200 dark:border-slate-700 overflow-hidden flex flex-col",
        side === 'left' ? "border-r" : "border-l"
      )}
    >
      {isOpen && (
        <div className="flex-1 overflow-hidden">
          {side === 'left' ? (
            <NodeLibrary />
          ) : (
            <div className="p-4">
              <h3 className="font-semibold text-gray-900 dark:text-white mb-4">Properties</h3>
              <p className="text-sm text-gray-500">Select a node to view properties</p>
            </div>
          )}
        </div>
      )}
    </motion.aside>
  );
};

// ============================================================
// Sidebar Toggle Button
// ============================================================

const SidebarToggle: React.FC<{ side: 'left' | 'right' }> = ({ side }) => {
  const { ui, toggleSidebar, toggleInspector } = useFlowStudioStore();
  
  const isOpen = side === 'left' ? ui.sidebarOpen : ui.inspectorOpen;
  const toggle = side === 'left' ? toggleSidebar : toggleInspector;

  const Icon = side === 'left'
    ? (isOpen ? PanelLeftClose : PanelLeftOpen)
    : (isOpen ? PanelRightClose : PanelRightOpen);

  return (
    <button
      onClick={toggle}
      className={cn(
        "absolute top-4 z-10 p-2 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-gray-200 dark:border-slate-700",
        "hover:bg-gray-50 dark:hover:bg-slate-700 transition-colors",
        side === 'left' ? "left-4" : "right-4"
      )}
      title={`${isOpen ? 'Close' : 'Open'} ${side} panel`}
    >
      <Icon className="w-4 h-4" />
    </button>
  );
};

// ============================================================
// Main Page Component
// ============================================================

export default function FlowStudioPage() {
  const { newWorkflow, workflow } = useFlowStudioStore();

  // Initialize new workflow on mount
  useEffect(() => {
    if (!workflow) {
      newWorkflow();
    }
  }, [workflow, newWorkflow]);

  return (
    <Protected>
      <div className="space-y-4">
        <PageHeader
          title="Flow Studio"
          subtitle="Construa workflows visuais com nós e conexões."
          breadcrumbs={[
            { label: 'Workflows', href: '/workflows' },
            { label: 'Flow Studio' },
          ]}
        />

        <div className="h-screen flex flex-col bg-gray-50 dark:bg-slate-900">
          <Header />
          
          <div className="flex-1 flex overflow-hidden relative">
            {/* Left Sidebar */}
            <Sidebar side="left" />
            
            {/* Canvas */}
            <main className="flex-1 relative">
              <SidebarToggle side="left" />
              <SidebarToggle side="right" />
              <FlowCanvas />
            </main>
            
            {/* Right Sidebar - Inspector */}
            <Sidebar side="right" />
          </div>
        </div>
      </div>
    </Protected>
  );
}
