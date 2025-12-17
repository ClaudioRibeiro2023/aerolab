"use client";

import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

// ============================================================
// GRADIENT MESH BACKGROUND
// ============================================================

interface GradientMeshProps {
  className?: string;
  variant?: "aurora" | "sunset" | "ocean" | "forest" | "cosmic" | "custom";
  animated?: boolean;
  intensity?: "subtle" | "medium" | "strong";
  customColors?: string[];
}

const VARIANTS = {
  aurora: ["#00d4ff", "#7c3aed", "#f0abfc", "#22d3ee"],
  sunset: ["#f97316", "#ec4899", "#8b5cf6", "#f59e0b"],
  ocean: ["#0ea5e9", "#3b82f6", "#6366f1", "#06b6d4"],
  forest: ["#10b981", "#059669", "#34d399", "#14b8a6"],
  cosmic: ["#1e3a5f", "#3b82f6", "#8b5cf6", "#ec4899"],
  custom: [],
};

const INTENSITY = {
  subtle: 0.15,
  medium: 0.3,
  strong: 0.5,
};

export function GradientMesh({
  className,
  variant = "cosmic",
  animated = true,
  intensity = "medium",
  customColors,
}: GradientMeshProps) {
  const colors = variant === "custom" && customColors ? customColors : VARIANTS[variant];
  const opacity = INTENSITY[intensity];

  return (
    <div className={cn("absolute inset-0 overflow-hidden", className)}>
      {/* Base gradient */}
      <div 
        className="absolute inset-0"
        style={{
          background: `linear-gradient(135deg, ${colors[0]}20 0%, transparent 50%)`,
        }}
      />

      {/* Animated blobs */}
      {colors.map((color, i) => (
        <motion.div
          key={i}
          className="absolute rounded-full blur-3xl"
          style={{
            background: color,
            opacity,
            width: `${30 + i * 10}%`,
            height: `${30 + i * 10}%`,
          }}
          initial={{
            x: `${20 + i * 20}%`,
            y: `${10 + i * 25}%`,
          }}
          animate={animated ? {
            x: [`${20 + i * 20}%`, `${40 + i * 15}%`, `${20 + i * 20}%`],
            y: [`${10 + i * 25}%`, `${30 + i * 20}%`, `${10 + i * 25}%`],
            scale: [1, 1.2, 1],
          } : undefined}
          transition={{
            duration: 15 + i * 5,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}

      {/* Noise texture overlay */}
      <div 
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.65' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
        }}
      />
    </div>
  );
}

// ============================================================
// ANIMATED GRADIENT BORDER
// ============================================================

interface GradientBorderProps {
  children: React.ReactNode;
  className?: string;
  borderWidth?: number;
  colors?: string[];
  animated?: boolean;
}

export function GradientBorder({
  children,
  className,
  borderWidth = 2,
  colors = ["#3b82f6", "#8b5cf6", "#ec4899", "#3b82f6"],
  animated = true,
}: GradientBorderProps) {
  return (
    <div className={cn("relative p-[2px] rounded-2xl", className)}>
      {/* Gradient border */}
      <motion.div
        className="absolute inset-0 rounded-2xl"
        style={{
          background: `linear-gradient(135deg, ${colors.join(", ")})`,
          backgroundSize: "300% 300%",
          padding: borderWidth,
        }}
        animate={animated ? {
          backgroundPosition: ["0% 0%", "100% 100%", "0% 0%"],
        } : undefined}
        transition={{
          duration: 5,
          repeat: Infinity,
          ease: "linear",
        }}
      />
      
      {/* Content */}
      <div className="relative bg-slate-900 rounded-2xl">
        {children}
      </div>
    </div>
  );
}

// ============================================================
// SPOTLIGHT GRADIENT
// ============================================================

interface SpotlightGradientProps {
  className?: string;
  color?: string;
  size?: number;
}

export function SpotlightGradient({
  className,
  color = "#3b82f6",
  size = 400,
}: SpotlightGradientProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [position, setPosition] = React.useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      setPosition({
        x: e.clientX - rect.left,
        y: e.clientY - rect.top,
      });
    };

    const container = containerRef.current;
    container?.addEventListener("mousemove", handleMouseMove);
    return () => container?.removeEventListener("mousemove", handleMouseMove);
  }, []);

  return (
    <div ref={containerRef} className={cn("absolute inset-0 overflow-hidden", className)}>
      <div
        className="pointer-events-none absolute transition-opacity duration-300"
        style={{
          background: `radial-gradient(${size}px circle at ${position.x}px ${position.y}px, ${color}30, transparent 80%)`,
          width: "100%",
          height: "100%",
        }}
      />
    </div>
  );
}

export default {
  GradientMesh,
  GradientBorder,
  SpotlightGradient,
};
