"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface BentoGridProps {
  children: React.ReactNode;
  className?: string;
}

export function BentoGrid({ children, className }: BentoGridProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-[minmax(180px,auto)]",
        className
      )}
    >
      {children}
    </div>
  );
}

interface BentoGridItemProps {
  className?: string;
  title: string;
  description?: string;
  header?: React.ReactNode;
  icon?: React.ReactNode;
  onClick?: () => void;
}

export function BentoGridItem({
  className,
  title,
  description,
  header,
  icon,
  onClick,
}: BentoGridItemProps) {
  return (
    <motion.div
      className={cn(
        "group relative overflow-hidden rounded-2xl",
        "bg-slate-900/50 backdrop-blur-sm border border-slate-800",
        "hover:border-slate-700 hover:shadow-xl hover:shadow-blue-500/5",
        "transition-all duration-500 cursor-pointer",
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      whileHover={{ y: -4 }}
      onClick={onClick}
    >
      {/* Background Gradient on Hover */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
      
      {/* Header */}
      {header && (
        <div className="relative h-32 overflow-hidden">
          {header}
        </div>
      )}
      
      {/* Content */}
      <div className="relative p-6">
        {/* Icon */}
        {icon && (
          <div className="mb-3 w-10 h-10 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/25">
            {icon}
          </div>
        )}
        
        {/* Title */}
        <h3 className="text-lg font-semibold text-white group-hover:text-blue-400 transition-colors">
          {title}
        </h3>
        
        {/* Description */}
        {description && (
          <p className="mt-2 text-sm text-slate-400 line-clamp-2">
            {description}
          </p>
        )}
      </div>
      
      {/* Shine Effect */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent pointer-events-none"
        initial={{ x: "-100%" }}
        whileHover={{ x: "100%" }}
        transition={{ duration: 0.8 }}
      />
    </motion.div>
  );
}

export default BentoGrid;
