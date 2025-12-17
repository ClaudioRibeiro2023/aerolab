"use client";

import React from "react";
import Link from "next/link";

export type BreadcrumbItem = {
  label: string;
  href?: string;
};

interface PageHeaderProps {
  title: string;
  subtitle?: string;
  breadcrumbs?: BreadcrumbItem[];
  leadingAction?: React.ReactNode;
  rightActions?: React.ReactNode;
}

export function PageHeader({
  title,
  subtitle,
  breadcrumbs,
  leadingAction,
  rightActions,
}: PageHeaderProps) {
  return (
    <div className="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div className="flex items-start gap-3">
        {leadingAction && <div className="mt-1 flex-shrink-0">{leadingAction}</div>}
        <div>
          {breadcrumbs && breadcrumbs.length > 0 && (
            <nav className="mb-1 text-xs text-gray-400 dark:text-slate-500">
              <ol className="flex flex-wrap items-center gap-1">
                {breadcrumbs.map((bc, index) => {
                  const isLast = index === breadcrumbs.length - 1;
                  return (
                    <li key={`${bc.label}-${index}`} className="flex items-center gap-1">
                      {bc.href && !isLast ? (
                        <Link href={bc.href} className="hover:text-blue-500">
                          {bc.label}
                        </Link>
                      ) : (
                        <span
                          className={
                            isLast ? "font-medium text-gray-700 dark:text-gray-200" : undefined
                          }
                        >
                          {bc.label}
                        </span>
                      )}
                      {!isLast && (
                        <span className="text-gray-500 dark:text-slate-600">/</span>
                      )}
                    </li>
                  );
                })}
              </ol>
            </nav>
          )}
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">{title}</h1>
          {subtitle && (
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">{subtitle}</p>
          )}
        </div>
      </div>
      {rightActions && (
        <div className="flex items-center gap-3">{rightActions}</div>
      )}
    </div>
  );
}
