"use client";

import React, { useState, useEffect, createContext, useContext, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle, Undo2 } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

type ToastType = "success" | "error" | "warning" | "info";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
  duration?: number;
  action?: {
    label: string;
    onClick: () => void;
  };
  undoable?: boolean;
  onUndo?: () => void;
  progress?: boolean;
}

interface ToastContextValue {
  toasts: Toast[];
  addToast: (toast: Omit<Toast, "id">) => string;
  removeToast: (id: string) => void;
  success: (title: string, options?: Partial<Toast>) => string;
  error: (title: string, options?: Partial<Toast>) => string;
  warning: (title: string, options?: Partial<Toast>) => string;
  info: (title: string, options?: Partial<Toast>) => string;
}

// ============================================================
// CONTEXT
// ============================================================

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within ToastProvider");
  }
  return context;
}

// ============================================================
// PROVIDER
// ============================================================

interface ToastProviderProps {
  children: React.ReactNode;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left" | "top-center" | "bottom-center";
  maxToasts?: number;
}

export function ToastProvider({
  children,
  position = "bottom-right",
  maxToasts = 5,
}: ToastProviderProps) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2)}`;
    setToasts((prev) => {
      const newToasts = [...prev, { ...toast, id }];
      // Limit max toasts
      if (newToasts.length > maxToasts) {
        return newToasts.slice(-maxToasts);
      }
      return newToasts;
    });
    return id;
  }, [maxToasts]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const success = useCallback((title: string, options?: Partial<Toast>) => {
    return addToast({ type: "success", title, duration: 4000, ...options });
  }, [addToast]);

  const error = useCallback((title: string, options?: Partial<Toast>) => {
    return addToast({ type: "error", title, duration: 6000, ...options });
  }, [addToast]);

  const warning = useCallback((title: string, options?: Partial<Toast>) => {
    return addToast({ type: "warning", title, duration: 5000, ...options });
  }, [addToast]);

  const info = useCallback((title: string, options?: Partial<Toast>) => {
    return addToast({ type: "info", title, duration: 4000, ...options });
  }, [addToast]);

  const positionClasses = {
    "top-right": "top-4 right-4",
    "top-left": "top-4 left-4",
    "bottom-right": "bottom-4 right-4",
    "bottom-left": "bottom-4 left-4",
    "top-center": "top-4 left-1/2 -translate-x-1/2",
    "bottom-center": "bottom-4 left-1/2 -translate-x-1/2",
  };

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, warning, info }}>
      {children}
      
      {/* Toast Container */}
      <div className={cn("fixed z-[100] flex flex-col gap-2", positionClasses[position])}>
        <AnimatePresence mode="popLayout">
          {toasts.map((toast) => (
            <ToastItem key={toast.id} toast={toast} onDismiss={() => removeToast(toast.id)} />
          ))}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

// ============================================================
// TOAST ITEM
// ============================================================

interface ToastItemProps {
  toast: Toast;
  onDismiss: () => void;
}

const icons = {
  success: CheckCircle,
  error: AlertCircle,
  warning: AlertTriangle,
  info: Info,
};

const colors = {
  success: {
    bg: "bg-emerald-500/10",
    border: "border-emerald-500/20",
    icon: "text-emerald-400",
    progress: "bg-emerald-500",
  },
  error: {
    bg: "bg-red-500/10",
    border: "border-red-500/20",
    icon: "text-red-400",
    progress: "bg-red-500",
  },
  warning: {
    bg: "bg-amber-500/10",
    border: "border-amber-500/20",
    icon: "text-amber-400",
    progress: "bg-amber-500",
  },
  info: {
    bg: "bg-blue-500/10",
    border: "border-blue-500/20",
    icon: "text-blue-400",
    progress: "bg-blue-500",
  },
};

function ToastItem({ toast, onDismiss }: ToastItemProps) {
  const [progress, setProgress] = useState(100);
  const [isPaused, setIsPaused] = useState(false);
  const duration = toast.duration || 4000;

  useEffect(() => {
    if (isPaused || !toast.progress) return;

    const interval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev - (100 / (duration / 100));
        if (newProgress <= 0) {
          onDismiss();
          return 0;
        }
        return newProgress;
      });
    }, 100);

    return () => clearInterval(interval);
  }, [duration, isPaused, toast.progress, onDismiss]);

  // Auto dismiss without progress bar
  useEffect(() => {
    if (toast.progress) return;
    
    const timeout = setTimeout(onDismiss, duration);
    return () => clearTimeout(timeout);
  }, [duration, toast.progress, onDismiss]);

  const Icon = icons[toast.type];
  const colorScheme = colors[toast.type];

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 50, scale: 0.9 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.2 } }}
      className={cn(
        "relative w-80 overflow-hidden rounded-xl border backdrop-blur-xl",
        colorScheme.bg,
        colorScheme.border
      )}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      <div className="flex items-start gap-3 p-4">
        {/* Icon */}
        <Icon className={cn("w-5 h-5 mt-0.5 flex-shrink-0", colorScheme.icon)} />
        
        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className="font-medium text-white text-sm">{toast.title}</p>
          {toast.description && (
            <p className="mt-1 text-sm text-slate-400">{toast.description}</p>
          )}
          
          {/* Actions */}
          {(toast.action || toast.undoable) && (
            <div className="flex items-center gap-2 mt-3">
              {toast.action && (
                <button
                  onClick={() => {
                    toast.action?.onClick();
                    onDismiss();
                  }}
                  className="text-sm font-medium text-blue-400 hover:text-blue-300"
                >
                  {toast.action.label}
                </button>
              )}
              {toast.undoable && toast.onUndo && (
                <button
                  onClick={() => {
                    toast.onUndo?.();
                    onDismiss();
                  }}
                  className="flex items-center gap-1 text-sm font-medium text-slate-400 hover:text-white"
                >
                  <Undo2 className="w-3 h-3" />
                  Desfazer
                </button>
              )}
            </div>
          )}
        </div>
        
        {/* Close button */}
        <button
          onClick={onDismiss}
          className="p-1 text-slate-400 hover:text-white hover:bg-white/10 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      
      {/* Progress bar */}
      {toast.progress && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-white/10">
          <motion.div
            className={cn("h-full", colorScheme.progress)}
            initial={{ width: "100%" }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.1 }}
          />
        </div>
      )}
    </motion.div>
  );
}

// ============================================================
// SIMPLE TOAST FUNCTION (for non-context usage)
// ============================================================

let toastQueue: Toast[] = [];
let toastListeners: ((toasts: Toast[]) => void)[] = [];

export const toast = {
  success: (title: string, options?: Partial<Omit<Toast, "id" | "type">>) => {
    const id = `toast-${Date.now()}`;
    const newToast: Toast = { id, type: "success", title, duration: 4000, ...options };
    toastQueue = [...toastQueue, newToast];
    toastListeners.forEach((listener) => listener(toastQueue));
    setTimeout(() => {
      toastQueue = toastQueue.filter((t) => t.id !== id);
      toastListeners.forEach((listener) => listener(toastQueue));
    }, newToast.duration);
    return id;
  },
  error: (title: string, options?: Partial<Omit<Toast, "id" | "type">>) => {
    const id = `toast-${Date.now()}`;
    const newToast: Toast = { id, type: "error", title, duration: 6000, ...options };
    toastQueue = [...toastQueue, newToast];
    toastListeners.forEach((listener) => listener(toastQueue));
    setTimeout(() => {
      toastQueue = toastQueue.filter((t) => t.id !== id);
      toastListeners.forEach((listener) => listener(toastQueue));
    }, newToast.duration);
    return id;
  },
  info: (title: string, options?: Partial<Omit<Toast, "id" | "type">>) => {
    const id = `toast-${Date.now()}`;
    const newToast: Toast = { id, type: "info", title, duration: 4000, ...options };
    toastQueue = [...toastQueue, newToast];
    toastListeners.forEach((listener) => listener(toastQueue));
    setTimeout(() => {
      toastQueue = toastQueue.filter((t) => t.id !== id);
      toastListeners.forEach((listener) => listener(toastQueue));
    }, newToast.duration);
    return id;
  },
  warning: (title: string, options?: Partial<Omit<Toast, "id" | "type">>) => {
    const id = `toast-${Date.now()}`;
    const newToast: Toast = { id, type: "warning", title, duration: 5000, ...options };
    toastQueue = [...toastQueue, newToast];
    toastListeners.forEach((listener) => listener(toastQueue));
    setTimeout(() => {
      toastQueue = toastQueue.filter((t) => t.id !== id);
      toastListeners.forEach((listener) => listener(toastQueue));
    }, newToast.duration);
    return id;
  },
};

export default {
  ToastProvider,
  useToast,
  toast,
};
