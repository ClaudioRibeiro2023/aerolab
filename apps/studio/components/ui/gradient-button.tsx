"use client";

import React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

interface GradientButtonProps extends HTMLMotionProps<"button"> {
  children: React.ReactNode;
  className?: string;
  variant?: "primary" | "secondary" | "accent" | "ghost";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  disabled?: boolean;
}

const variants = {
  primary: "bg-gradient-to-r from-blue-600 via-blue-500 to-indigo-600 text-white shadow-lg shadow-blue-500/25",
  secondary: "bg-gradient-to-r from-slate-700 to-slate-800 text-white shadow-lg shadow-slate-500/25",
  accent: "bg-gradient-to-r from-purple-600 via-purple-500 to-pink-600 text-white shadow-lg shadow-purple-500/25",
  ghost: "bg-transparent text-slate-300 hover:bg-slate-800/50",
};

const sizes = {
  sm: "px-4 py-2 text-sm rounded-lg",
  md: "px-6 py-3 text-sm rounded-xl",
  lg: "px-8 py-4 text-base rounded-xl",
};

export function GradientButton({
  children,
  className,
  variant = "primary",
  size = "md",
  loading = false,
  disabled = false,
  ...props
}: GradientButtonProps) {
  return (
    <motion.button
      className={cn(
        "relative overflow-hidden font-semibold transition-all duration-300",
        "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variants[variant],
        sizes[size],
        className
      )}
      whileHover={!disabled ? { scale: 1.02 } : undefined}
      whileTap={!disabled ? { scale: 0.98 } : undefined}
      disabled={disabled || loading}
      {...props}
    >
      {/* Shine Effect */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent"
        initial={{ x: "-100%" }}
        whileHover={{ x: "100%" }}
        transition={{ duration: 0.6 }}
      />
      
      {/* Content */}
      <span className="relative z-10 flex items-center justify-center gap-2">
        {loading && (
          <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
        )}
        {children}
      </span>
    </motion.button>
  );
}

export default GradientButton;
