"use client";

import { useEffect, useState, useCallback } from "react";

interface PerformanceMetrics {
  fcp: number | null;
  lcp: number | null;
  fid: number | null;
  cls: number | null;
  ttfb: number | null;
  memoryUsage: number | null;
  connectionType: string | null;
}

interface PerformanceMonitorProps {
  enabled?: boolean;
  showOverlay?: boolean;
}

export function usePerformanceMetrics() {
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fcp: null,
    lcp: null,
    fid: null,
    cls: null,
    ttfb: null,
    memoryUsage: null,
    connectionType: null,
  });

  useEffect(() => {
    if (typeof window === "undefined") return;

    // First Contentful Paint
    const paintObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        if (entry.name === "first-contentful-paint") {
          setMetrics((prev) => ({ ...prev, fcp: entry.startTime }));
        }
      }
    });

    // Largest Contentful Paint
    const lcpObserver = new PerformanceObserver((list) => {
      const entries = list.getEntries();
      const lastEntry = entries[entries.length - 1];
      setMetrics((prev) => ({ ...prev, lcp: lastEntry.startTime }));
    });

    // First Input Delay
    const fidObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const fidEntry = entry as PerformanceEventTiming;
        setMetrics((prev) => ({ ...prev, fid: fidEntry.processingStart - fidEntry.startTime }));
      }
    });

    // Cumulative Layout Shift
    let clsValue = 0;
    const clsObserver = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        const layoutShift = entry as PerformanceEntry & { hadRecentInput: boolean; value: number };
        if (!layoutShift.hadRecentInput) {
          clsValue += layoutShift.value;
          setMetrics((prev) => ({ ...prev, cls: clsValue }));
        }
      }
    });

    try {
      paintObserver.observe({ entryTypes: ["paint"] });
      lcpObserver.observe({ entryTypes: ["largest-contentful-paint"] });
      fidObserver.observe({ entryTypes: ["first-input"] });
      clsObserver.observe({ entryTypes: ["layout-shift"] });
    } catch (e) {
      console.warn("Performance Observer not supported:", e);
    }

    // Navigation timing
    const navEntry = performance.getEntriesByType("navigation")[0] as PerformanceNavigationTiming;
    if (navEntry) {
      setMetrics((prev) => ({ ...prev, ttfb: navEntry.responseStart - navEntry.requestStart }));
    }

    // Memory usage (Chrome only)
    const memoryInfo = (performance as Performance & { memory?: { usedJSHeapSize: number } }).memory;
    if (memoryInfo) {
      setMetrics((prev) => ({ ...prev, memoryUsage: memoryInfo.usedJSHeapSize / 1048576 }));
    }

    // Connection type
    const connection = (navigator as Navigator & { connection?: { effectiveType: string } }).connection;
    if (connection) {
      setMetrics((prev) => ({ ...prev, connectionType: connection.effectiveType }));
    }

    return () => {
      paintObserver.disconnect();
      lcpObserver.disconnect();
      fidObserver.disconnect();
      clsObserver.disconnect();
    };
  }, []);

  return metrics;
}

export default function PerformanceMonitor({ enabled = true, showOverlay = false }: PerformanceMonitorProps) {
  const metrics = usePerformanceMetrics();
  const [isVisible, setIsVisible] = useState(showOverlay);

  const reportMetrics = useCallback(() => {
    if (typeof window === "undefined") return;
    
    // Log to console in development
    if (process.env.NODE_ENV === "development") {
      console.log("📊 Performance Metrics:", metrics);
    }

    // Could send to analytics endpoint
    // fetch('/api/metrics', { method: 'POST', body: JSON.stringify(metrics) });
  }, [metrics]);

  useEffect(() => {
    if (enabled && metrics.lcp !== null) {
      reportMetrics();
    }
  }, [enabled, metrics.lcp, reportMetrics]);

  // Keyboard shortcut to toggle overlay (Ctrl+Shift+P)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.ctrlKey && e.shiftKey && e.key === "P") {
        e.preventDefault();
        setIsVisible((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  if (!enabled || !isVisible) return null;

  const getScoreColor = (value: number | null, thresholds: { good: number; poor: number }) => {
    if (value === null) return "text-gray-400";
    if (value <= thresholds.good) return "text-green-400";
    if (value <= thresholds.poor) return "text-yellow-400";
    return "text-red-400";
  };

  return (
    <div className="fixed bottom-4 right-4 z-50 bg-slate-900/95 backdrop-blur-sm border border-slate-700 rounded-xl p-4 text-xs font-mono shadow-xl">
      <div className="flex items-center justify-between mb-3">
        <span className="text-white font-semibold">📊 Performance</span>
        <button
          onClick={() => setIsVisible(false)}
          className="text-slate-400 hover:text-white"
        >
          ✕
        </button>
      </div>
      <div className="space-y-1.5">
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">FCP:</span>
          <span className={getScoreColor(metrics.fcp, { good: 1800, poor: 3000 })}>
            {metrics.fcp?.toFixed(0) ?? "—"} ms
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">LCP:</span>
          <span className={getScoreColor(metrics.lcp, { good: 2500, poor: 4000 })}>
            {metrics.lcp?.toFixed(0) ?? "—"} ms
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">FID:</span>
          <span className={getScoreColor(metrics.fid, { good: 100, poor: 300 })}>
            {metrics.fid?.toFixed(0) ?? "—"} ms
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">CLS:</span>
          <span className={getScoreColor(metrics.cls, { good: 0.1, poor: 0.25 })}>
            {metrics.cls?.toFixed(3) ?? "—"}
          </span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-slate-400">TTFB:</span>
          <span className={getScoreColor(metrics.ttfb, { good: 800, poor: 1800 })}>
            {metrics.ttfb?.toFixed(0) ?? "—"} ms
          </span>
        </div>
        {metrics.memoryUsage && (
          <div className="flex justify-between gap-4">
            <span className="text-slate-400">Memory:</span>
            <span className="text-blue-400">{metrics.memoryUsage.toFixed(1)} MB</span>
          </div>
        )}
        {metrics.connectionType && (
          <div className="flex justify-between gap-4">
            <span className="text-slate-400">Network:</span>
            <span className="text-purple-400">{metrics.connectionType}</span>
          </div>
        )}
      </div>
      <div className="mt-3 pt-2 border-t border-slate-700 text-slate-500 text-center">
        Ctrl+Shift+P para toggle
      </div>
    </div>
  );
}
