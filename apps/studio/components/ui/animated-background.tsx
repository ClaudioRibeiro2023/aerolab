"use client";

import React, { useEffect, useRef } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

// ============================================================
// ANIMATED GRID PATTERN
// ============================================================

interface AnimatedGridPatternProps {
  className?: string;
  numSquares?: number;
  maxOpacity?: number;
  duration?: number;
}

export function AnimatedGridPattern({
  className,
  numSquares = 30,
  maxOpacity = 0.1,
  duration = 3,
}: AnimatedGridPatternProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  
  return (
    <div ref={containerRef} className={cn("absolute inset-0 overflow-hidden", className)}>
      <svg className="absolute inset-0 w-full h-full">
        <defs>
          <pattern
            id="grid-pattern"
            width="40"
            height="40"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M 40 0 L 0 0 0 40"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
              className="text-slate-700"
            />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#grid-pattern)" />
      </svg>
      
      {/* Animated Squares */}
      {Array.from({ length: numSquares }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-10 h-10 bg-blue-500"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          initial={{ opacity: 0 }}
          animate={{
            opacity: [0, maxOpacity, 0],
          }}
          transition={{
            duration,
            delay: Math.random() * duration,
            repeat: Infinity,
            repeatDelay: Math.random() * 2,
          }}
        />
      ))}
    </div>
  );
}

// ============================================================
// PARTICLES
// ============================================================

interface ParticlesProps {
  className?: string;
  quantity?: number;
  color?: string;
}

export function Particles({
  className,
  quantity = 50,
  color = "#3b82f6",
}: ParticlesProps) {
  return (
    <div className={cn("absolute inset-0 overflow-hidden", className)}>
      {Array.from({ length: quantity }).map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 rounded-full"
          style={{
            backgroundColor: color,
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            y: [0, -30, 0],
            opacity: [0.2, 0.8, 0.2],
            scale: [1, 1.5, 1],
          }}
          transition={{
            duration: 3 + Math.random() * 2,
            delay: Math.random() * 2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      ))}
    </div>
  );
}

// ============================================================
// SPOTLIGHT
// ============================================================

interface SpotlightProps {
  className?: string;
  fill?: string;
}

export function Spotlight({ className, fill = "white" }: SpotlightProps) {
  return (
    <motion.svg
      className={cn(
        "animate-spotlight pointer-events-none absolute z-[1] h-[169%] w-[138%] lg:w-[84%] opacity-0",
        className
      )}
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 3787 2842"
      fill="none"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 1 }}
    >
      <g filter="url(#filter)">
        <ellipse
          cx="1924.71"
          cy="273.501"
          rx="1924.71"
          ry="273.501"
          transform="matrix(-0.822377 -0.568943 -0.568943 0.822377 3631.88 2291.09)"
          fill={fill}
          fillOpacity="0.21"
        />
      </g>
      <defs>
        <filter
          id="filter"
          x="0.860352"
          y="0.838989"
          width="3785.16"
          height="2840.26"
          filterUnits="userSpaceOnUse"
          colorInterpolationFilters="sRGB"
        >
          <feFlood floodOpacity="0" result="BackgroundImageFix" />
          <feBlend mode="normal" in="SourceGraphic" in2="BackgroundImageFix" result="shape" />
          <feGaussianBlur stdDeviation="151" result="effect1_foregroundBlur" />
        </filter>
      </defs>
    </motion.svg>
  );
}

// ============================================================
// BORDER BEAM
// ============================================================

interface BorderBeamProps {
  className?: string;
  size?: number;
  duration?: number;
  delay?: number;
  colorFrom?: string;
  colorTo?: string;
}

export function BorderBeam({
  className,
  size = 200,
  duration = 12,
  delay = 0,
  colorFrom = "#3b82f6",
  colorTo = "#8b5cf6",
}: BorderBeamProps) {
  return (
    <div
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden rounded-[inherit]",
        className
      )}
    >
      <div
        className="absolute inset-0"
        style={{
          background: `linear-gradient(90deg, ${colorFrom}, ${colorTo})`,
          mask: `conic-gradient(from calc(var(--angle, 0deg)), transparent 80%, white)`,
          WebkitMask: `conic-gradient(from calc(var(--angle, 0deg)), transparent 80%, white)`,
          animation: `border-beam ${duration}s linear infinite`,
          animationDelay: `${delay}s`,
        }}
      />
    </div>
  );
}

// ============================================================
// GRADIENT ORB
// ============================================================

interface GradientOrbProps {
  className?: string;
  color?: "blue" | "purple" | "pink" | "emerald";
}

const orbColors = {
  blue: "from-blue-500/30 to-blue-600/10",
  purple: "from-purple-500/30 to-purple-600/10",
  pink: "from-pink-500/30 to-pink-600/10",
  emerald: "from-emerald-500/30 to-emerald-600/10",
};

export function GradientOrb({ className, color = "blue" }: GradientOrbProps) {
  return (
    <motion.div
      className={cn(
        "absolute w-96 h-96 rounded-full blur-3xl",
        `bg-gradient-to-br ${orbColors[color]}`,
        className
      )}
      animate={{
        scale: [1, 1.1, 1],
        opacity: [0.5, 0.8, 0.5],
      }}
      transition={{
        duration: 8,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />
  );
}

export default {
  AnimatedGridPattern,
  Particles,
  Spotlight,
  BorderBeam,
  GradientOrb,
};
