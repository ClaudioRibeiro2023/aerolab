"use client";

import React, { useState } from 'react';
import { Info, ChevronUp, Package, Clock, Sparkles, CheckCircle } from 'lucide-react';
import { 
  PLATFORM_VERSION, 
  PLATFORM_BUILD, 
  getLatestUpdate,
  MODULE_VERSIONS,
  CHANGELOG,
  formatDate,
  ModuleVersion,
  ChangelogEntry
} from '@/lib/version';

export function VersionFooter() {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="border-t border-gray-700 bg-gray-900/50">
      {/* Collapsed Footer */}
      <button
        onClick={() => setExpanded(!expanded)}
        className="w-full px-4 py-2 flex items-center justify-between text-xs text-gray-400 hover:text-gray-200 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Package className="w-3 h-3" />
          <span>AGNO Platform v{PLATFORM_VERSION}</span>
          <span className="text-gray-600">|</span>
          <Clock className="w-3 h-3" />
          <span>{getLatestUpdate()}</span>
        </div>
        <ChevronUp className={`w-4 h-4 transition-transform ${expanded ? 'rotate-180' : ''}`} />
      </button>

      {/* Expanded Panel */}
      {expanded && (
        <div className="px-4 pb-4 border-t border-gray-800">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            {/* Modules */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Package className="w-4 h-4 text-blue-400" />
                Módulos
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {MODULE_VERSIONS.map((module) => (
                  <ModuleItem key={module.name} module={module} />
                ))}
              </div>
            </div>

            {/* Changelog */}
            <div>
              <h4 className="text-sm font-semibold text-white mb-3 flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-yellow-400" />
                Últimas Atualizações
              </h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {CHANGELOG.slice(0, 5).map((entry, idx) => (
                  <ChangelogItem key={idx} entry={entry} />
                ))}
              </div>
            </div>
          </div>

          {/* Build Info */}
          <div className="mt-4 pt-3 border-t border-gray-800 flex items-center justify-between text-xs text-gray-500">
            <span>Build: {PLATFORM_BUILD}</span>
            <span>© 2024 AGNO Platform</span>
          </div>
        </div>
      )}
    </div>
  );
}

function ModuleItem({ module }: { module: ModuleVersion }) {
  const statusColors = {
    stable: 'bg-green-500/20 text-green-400',
    beta: 'bg-yellow-500/20 text-yellow-400',
    alpha: 'bg-red-500/20 text-red-400'
  };

  return (
    <div className="flex items-center justify-between p-2 rounded bg-gray-800/50 hover:bg-gray-800 transition-colors">
      <div className="flex items-center gap-2">
        <CheckCircle className="w-3 h-3 text-green-400" />
        <span className="text-sm text-gray-200">{module.name}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className={`px-2 py-0.5 rounded text-xs ${statusColors[module.status]}`}>
          v{module.version}
        </span>
      </div>
    </div>
  );
}

function ChangelogItem({ entry }: { entry: ChangelogEntry }) {
  const typeColors = {
    feature: 'bg-blue-500/20 text-blue-400',
    fix: 'bg-red-500/20 text-red-400',
    improvement: 'bg-green-500/20 text-green-400',
    breaking: 'bg-orange-500/20 text-orange-400'
  };

  const typeLabels = {
    feature: 'Novo',
    fix: 'Fix',
    improvement: 'Melhoria',
    breaking: 'Breaking'
  };

  return (
    <div className="p-2 rounded bg-gray-800/50 text-xs">
      <div className="flex items-center gap-2 mb-1">
        <span className={`px-1.5 py-0.5 rounded ${typeColors[entry.type]}`}>
          {typeLabels[entry.type]}
        </span>
        <span className="text-gray-400">{entry.module}</span>
        <span className="text-gray-600 ml-auto">{entry.date}</span>
      </div>
      <p className="text-gray-300 truncate">{entry.description}</p>
    </div>
  );
}

export default VersionFooter;
