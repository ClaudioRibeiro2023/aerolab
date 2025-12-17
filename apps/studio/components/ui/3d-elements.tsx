"use client";

import React, { useRef, useState, Suspense } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

// ============================================================
// 3D CARD EFFECT (CSS-based, no Three.js needed for basic use)
// ============================================================

interface Card3DProps {
  children: React.ReactNode;
  className?: string;
  containerClassName?: string;
}

export function Card3D({ children, className, containerClassName }: Card3DProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [rotateX, setRotateX] = useState(0);
  const [rotateY, setRotateY] = useState(0);

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!containerRef.current) return;

    const rect = containerRef.current.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const mouseX = e.clientX - centerX;
    const mouseY = e.clientY - centerY;

    const rotateXValue = (mouseY / (rect.height / 2)) * -10;
    const rotateYValue = (mouseX / (rect.width / 2)) * 10;

    setRotateX(rotateXValue);
    setRotateY(rotateYValue);
  };

  const handleMouseLeave = () => {
    setRotateX(0);
    setRotateY(0);
  };

  return (
    <div
      ref={containerRef}
      className={cn("perspective-1000", containerClassName)}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
    >
      <motion.div
        className={cn(
          "relative preserve-3d transition-transform duration-200 ease-out",
          className
        )}
        animate={{
          rotateX,
          rotateY,
        }}
        transition={{ type: "spring", stiffness: 300, damping: 30 }}
      >
        {children}
      </motion.div>
    </div>
  );
}

// ============================================================
// 3D FLOATING ELEMENT
// ============================================================

interface FloatingElement3DProps {
  children: React.ReactNode;
  className?: string;
  amplitude?: number;
  duration?: number;
}

export function FloatingElement3D({
  children,
  className,
  amplitude = 10,
  duration = 3,
}: FloatingElement3DProps) {
  return (
    <motion.div
      className={cn("relative", className)}
      animate={{
        y: [-amplitude, amplitude, -amplitude],
        rotateX: [-2, 2, -2],
        rotateY: [-2, 2, -2],
      }}
      transition={{
        duration,
        repeat: Infinity,
        ease: "easeInOut",
      }}
      style={{
        transformStyle: "preserve-3d",
        perspective: "1000px",
      }}
    >
      {children}
    </motion.div>
  );
}

// ============================================================
// 3D ROTATING CUBE
// ============================================================

interface RotatingCubeProps {
  size?: number;
  className?: string;
  faces?: {
    front?: React.ReactNode;
    back?: React.ReactNode;
    left?: React.ReactNode;
    right?: React.ReactNode;
    top?: React.ReactNode;
    bottom?: React.ReactNode;
  };
}

export function RotatingCube({ size = 100, className, faces }: RotatingCubeProps) {
  const halfSize = size / 2;

  return (
    <div
      className={cn("relative preserve-3d", className)}
      style={{
        width: size,
        height: size,
        transformStyle: "preserve-3d",
        animation: "spin-slow 10s linear infinite",
      }}
    >
      {/* Front */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-500/80 to-purple-600/80 backdrop-blur-sm border border-white/20 rounded-lg"
        style={{ transform: `translateZ(${halfSize}px)` }}
      >
        {faces?.front || "F"}
      </div>

      {/* Back */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-purple-500/80 to-pink-600/80 backdrop-blur-sm border border-white/20 rounded-lg"
        style={{ transform: `rotateY(180deg) translateZ(${halfSize}px)` }}
      >
        {faces?.back || "B"}
      </div>

      {/* Left */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-cyan-500/80 to-blue-600/80 backdrop-blur-sm border border-white/20 rounded-lg"
        style={{ transform: `rotateY(-90deg) translateZ(${halfSize}px)` }}
      >
        {faces?.left || "L"}
      </div>

      {/* Right */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-pink-500/80 to-red-600/80 backdrop-blur-sm border border-white/20 rounded-lg"
        style={{ transform: `rotateY(90deg) translateZ(${halfSize}px)` }}
      >
        {faces?.right || "R"}
      </div>

      {/* Top */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-emerald-500/80 to-teal-600/80 backdrop-blur-sm border border-white/20 rounded-lg"
        style={{ transform: `rotateX(90deg) translateZ(${halfSize}px)` }}
      >
        {faces?.top || "T"}
      </div>

      {/* Bottom */}
      <div
        className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-amber-500/80 to-orange-600/80 backdrop-blur-sm border border-white/20 rounded-lg"
        style={{ transform: `rotateX(-90deg) translateZ(${halfSize}px)` }}
      >
        {faces?.bottom || "Bo"}
      </div>
    </div>
  );
}

// ============================================================
// 3D LOGO SCENE
// ============================================================

export function Logo3D({ className }: { className?: string }) {
  return (
    <div className={cn("perspective-1000", className)}>
      <FloatingElement3D amplitude={5} duration={4}>
        <div
          className="relative w-24 h-24 preserve-3d"
          style={{ transformStyle: "preserve-3d" }}
        >
          {/* Main face */}
          <div
            className="absolute inset-0 flex items-center justify-center bg-gradient-to-br from-blue-600 to-purple-600 rounded-2xl shadow-2xl shadow-blue-500/30"
            style={{ transform: "translateZ(20px)" }}
          >
            <span className="text-4xl font-bold text-white">A</span>
          </div>
          
          {/* Depth layer */}
          <div
            className="absolute inset-0 bg-gradient-to-br from-blue-800 to-purple-800 rounded-2xl"
            style={{ transform: "translateZ(0px)" }}
          />
          
          {/* Back layer */}
          <div
            className="absolute inset-0 bg-gradient-to-br from-blue-900 to-purple-900 rounded-2xl"
            style={{ transform: "translateZ(-20px)" }}
          />
        </div>
      </FloatingElement3D>
    </div>
  );
}

// ============================================================
// PARALLAX CONTAINER
// ============================================================

interface ParallaxContainerProps {
  children: React.ReactNode;
  className?: string;
  layers?: {
    content: React.ReactNode;
    depth: number;
    className?: string;
  }[];
}

export function ParallaxContainer({
  children,
  className,
  layers = [],
}: ParallaxContainerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    
    const rect = containerRef.current.getBoundingClientRect();
    const x = (e.clientX - rect.left - rect.width / 2) / rect.width;
    const y = (e.clientY - rect.top - rect.height / 2) / rect.height;
    
    setMousePosition({ x, y });
  };

  return (
    <div
      ref={containerRef}
      className={cn("relative overflow-hidden", className)}
      onMouseMove={handleMouseMove}
      onMouseLeave={() => setMousePosition({ x: 0, y: 0 })}
    >
      {/* Parallax Layers */}
      {layers.map((layer, index) => (
        <motion.div
          key={index}
          className={cn("absolute inset-0", layer.className)}
          animate={{
            x: mousePosition.x * layer.depth * 20,
            y: mousePosition.y * layer.depth * 20,
          }}
          transition={{ type: "spring", stiffness: 150, damping: 20 }}
        >
          {layer.content}
        </motion.div>
      ))}
      
      {/* Main Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}

export default {
  Card3D,
  FloatingElement3D,
  RotatingCube,
  Logo3D,
  ParallaxContainer,
};
