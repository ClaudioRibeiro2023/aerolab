"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";

interface FloatingInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
  icon?: React.ReactNode;
}

export function FloatingInput({
  label,
  error,
  icon,
  className,
  ...props
}: FloatingInputProps) {
  const [focused, setFocused] = useState(false);
  const [hasValue, setHasValue] = useState(!!props.value || !!props.defaultValue);

  return (
    <div className="relative group">
      {/* Icon */}
      {icon && (
        <div className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-blue-400 transition-colors">
          {icon}
        </div>
      )}
      
      {/* Input */}
      <input
        className={cn(
          "peer w-full px-4 pt-6 pb-2 bg-slate-800/50 border-2 border-slate-700 rounded-xl",
          "text-white placeholder-transparent",
          "focus:border-blue-500 focus:ring-4 focus:ring-blue-500/20 focus:outline-none",
          "transition-all duration-300",
          icon && "pl-12",
          error && "border-red-500 focus:border-red-500 focus:ring-red-500/20",
          className
        )}
        placeholder={label}
        onFocus={() => setFocused(true)}
        onBlur={(e) => {
          setFocused(false);
          setHasValue(!!e.target.value);
        }}
        onChange={(e) => setHasValue(!!e.target.value)}
        {...props}
      />
      
      {/* Floating Label */}
      <label
        className={cn(
          "absolute left-4 transition-all duration-300 pointer-events-none",
          icon && "left-12",
          focused || hasValue
            ? "top-2 text-xs text-blue-400"
            : "top-1/2 -translate-y-1/2 text-base text-slate-400",
          error && (focused || hasValue) && "text-red-400"
        )}
      >
        {label}
      </label>
      
      {/* Animated Bottom Border */}
      <motion.div
        className={cn(
          "absolute bottom-0 left-1/2 h-0.5 bg-gradient-to-r from-blue-500 to-purple-500",
          error && "from-red-500 to-red-400"
        )}
        initial={{ width: 0, x: "-50%" }}
        animate={{
          width: focused ? "100%" : 0,
          left: focused ? 0 : "50%",
          x: focused ? 0 : "-50%",
        }}
        transition={{ duration: 0.3 }}
      />
      
      {/* Error Message */}
      {error && (
        <motion.p
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-2 text-sm text-red-400"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
}

export default FloatingInput;
