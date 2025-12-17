"use client";
import React from "react";
import Link from "next/link";

interface EmptyStateProps {
  icon: string;
  title: string;
  description: string;
  action?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
  suggestions?: string[];
  secondaryAction?: {
    label: string;
    href?: string;
    onClick?: () => void;
  };
}

export default function EmptyState({
  icon,
  title,
  description,
  action,
  suggestions,
  secondaryAction
}: EmptyStateProps) {
  const ActionButton = action?.href ? Link : "button";

  return (
    <div className="flex flex-col items-center justify-center text-center py-16 px-4">
      {/* Icon */}
      <div className="w-24 h-24 mb-6 rounded-3xl bg-gradient-to-br from-blue-100 to-purple-100 dark:from-slate-800 dark:to-slate-700 flex items-center justify-center shadow-lg shadow-blue-500/10">
        <span className="text-5xl">{icon}</span>
      </div>

      {/* Title */}
      <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">
        {title}
      </h3>

      {/* Description */}
      <p className="text-gray-600 dark:text-gray-400 max-w-md mb-8">
        {description}
      </p>

      {/* Actions */}
      {action && (
        <div className="flex gap-3">
          <ActionButton
            href={action.href || "#"}
            onClick={action.onClick}
            className="px-6 py-3 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-xl font-medium hover:opacity-90 transition-opacity shadow-lg shadow-blue-500/25 flex items-center gap-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            {action.label}
          </ActionButton>
          {secondaryAction && (
            <ActionButton
              href={secondaryAction.href || "#"}
              onClick={secondaryAction.onClick}
              className="px-6 py-3 bg-gray-100 dark:bg-slate-800 text-gray-700 dark:text-gray-300 rounded-xl font-medium hover:bg-gray-200 dark:hover:bg-slate-700 transition-colors"
            >
              {secondaryAction.label}
            </ActionButton>
          )}
        </div>
      )}

      {/* Suggestions */}
      {suggestions && suggestions.length > 0 && (
        <div className="mt-8 w-full max-w-md">
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-4">
            💡 Sugestões:
          </p>
          <div className="space-y-2">
            {suggestions.map((suggestion, idx) => (
              <div
                key={idx}
                className="flex items-start gap-3 p-3 bg-gray-50 dark:bg-slate-800 rounded-xl text-left"
              >
                <div className="w-6 h-6 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 flex items-center justify-center flex-shrink-0 text-xs font-medium">
                  {idx + 1}
                </div>
                <p className="text-sm text-gray-700 dark:text-gray-300 flex-1">
                  {suggestion}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
