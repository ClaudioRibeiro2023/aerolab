"use client";

import React from "react";
import clsx from "clsx";

export type BadgeVariant =
  | "primary"
  | "success"
  | "warning"
  | "error"
  | "info"
  | "neutral";

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

export function Badge({ variant = "neutral", className, children, ...rest }: BadgeProps) {
  const variantClasses: Record<BadgeVariant, string> = {
    primary: "badge badge-primary",
    success: "badge badge-success",
    warning: "badge badge-warning",
    error: "badge badge-error",
    info: "badge bg-sky-100 text-sky-800 dark:bg-sky-900/30 dark:text-sky-300",
    neutral: "badge bg-gray-100 text-gray-700 dark:bg-slate-700 dark:text-gray-200",
  };

  return (
    <span className={clsx(variantClasses[variant], className)} {...rest}>
      {children}
    </span>
  );
}
