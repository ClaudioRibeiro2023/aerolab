"use client";

import React from "react";

interface ToggleCardProps {
  label: string;
  description?: string;
  enabled: boolean;
  onToggle: (value: boolean) => void;
}

export function ToggleCard({ label, description, enabled, onToggle }: ToggleCardProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(!enabled)}
      className="flex w-full items-center justify-between rounded-xl bg-gray-50 p-4 text-left transition-colors dark:bg-slate-900"
    >
      <div>
        <p className="font-medium text-gray-900 dark:text-white">{label}</p>
        {description && (
          <p className="text-xs text-gray-500 dark:text-gray-400">{description}</p>
        )}
      </div>
      <span
        className={`inline-flex h-6 w-12 items-center rounded-full transition-colors ${
          enabled ? "bg-blue-500" : "bg-gray-300 dark:bg-slate-600"
        }`}
      >
        <span
          className={`h-5 w-5 transform rounded-full bg-white shadow transition-transform ${
            enabled ? "translate-x-6" : "translate-x-0.5"
          }`}
        />
      </span>
    </button>
  );
}
