"use client";

import React from "react";
import { motion, HTMLMotionProps } from "framer-motion";
import { cn } from "@/lib/utils";

interface GlassCardProps extends HTMLMotionProps<"div"> {
  children: React.ReactNode;
  className?: string;
  hoverEffect?: boolean;
  glowColor?: "blue" | "purple" | "pink" | "emerald";
  variant?: "light" | "dark";
}

const glowColors = {
  blue: "hover:shadow-glow hover:border-blue-500/30",
  purple: "hover:shadow-glow-purple hover:border-purple-500/30",
  pink: "hover:shadow-glow-pink hover:border-pink-500/30",
  emerald: "hover:shadow-[0_0_40px_rgba(16,185,129,0.3)] hover:border-emerald-500/30",
};

export function GlassCard({
  children,
  className,
  hoverEffect = true,
  glowColor = "blue",
  variant = "dark",
  ...props
}: GlassCardProps) {
  const baseStyles = variant === "dark"
    ? "bg-slate-900/40 border-white/10"
    : "bg-white/10 border-white/20";

  return (
    <motion.div
      className={cn(
        "relative overflow-hidden rounded-2xl backdrop-blur-xl border transition-all duration-500",
        baseStyles,
        hoverEffect && glowColors[glowColor],
        hoverEffect && "hover:-translate-y-1",
        className
      )}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      {...props}
    >
      {/* Gradient Overlay on Hover */}
      {hoverEffect && (
        <div className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-500/5 via-purple-500/5 to-pink-500/5" />
        </div>
      )}
      
      {/* Content */}
      <div className="relative z-10">{children}</div>
    </motion.div>
  );
}

export default GlassCard;
