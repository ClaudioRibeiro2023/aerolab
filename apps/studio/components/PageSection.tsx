"use client";

import React from "react";

interface PageSectionProps {
  title?: string;
  subtitle?: string;
  rightActions?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export function PageSection({
  title,
  subtitle,
  rightActions,
  children,
  className,
}: PageSectionProps) {
  return (
    <section className={className}>
      {(title || subtitle || rightActions) && (
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            {title && (
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h2>
            )}
            {subtitle && (
              <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
            )}
          </div>
          {rightActions && <div className="flex items-center gap-2">{rightActions}</div>}
        </div>
      )}
      <div className="rounded-2xl border border-gray-100 bg-white p-6 dark:border-slate-700 dark:bg-slate-800">
        {children}
      </div>
    </section>
  );
}
