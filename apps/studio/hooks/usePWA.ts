"use client";

import { useState, useEffect, useCallback } from "react";

// ============================================================
// TYPES
// ============================================================

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

interface PWAState {
  isInstalled: boolean;
  isInstallable: boolean;
  isOnline: boolean;
  isStandalone: boolean;
  serviceWorkerStatus: "pending" | "registered" | "error" | "unsupported";
}

// ============================================================
// PWA HOOK
// ============================================================

export function usePWA() {
  const [state, setState] = useState<PWAState>({
    isInstalled: false,
    isInstallable: false,
    isOnline: true,
    isStandalone: false,
    serviceWorkerStatus: "pending",
  });

  const [installPrompt, setInstallPrompt] = useState<BeforeInstallPromptEvent | null>(null);

  // Check if running in standalone mode (PWA)
  useEffect(() => {
    const isStandalone =
      window.matchMedia("(display-mode: standalone)").matches ||
      (window.navigator as unknown as { standalone: boolean }).standalone === true;

    setState((prev) => ({ ...prev, isStandalone, isInstalled: isStandalone }));
  }, []);

  // Register service worker
  useEffect(() => {
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker
        .register("/sw.js")
        .then((registration) => {
          console.log("[PWA] Service Worker registered:", registration.scope);
          setState((prev) => ({ ...prev, serviceWorkerStatus: "registered" }));

          // Check for updates
          registration.addEventListener("updatefound", () => {
            const newWorker = registration.installing;
            if (newWorker) {
              newWorker.addEventListener("statechange", () => {
                if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
                  console.log("[PWA] New version available!");
                  // You could show a notification here
                }
              });
            }
          });
        })
        .catch((error) => {
          console.error("[PWA] Service Worker registration failed:", error);
          setState((prev) => ({ ...prev, serviceWorkerStatus: "error" }));
        });
    } else {
      setState((prev) => ({ ...prev, serviceWorkerStatus: "unsupported" }));
    }
  }, []);

  // Handle install prompt
  useEffect(() => {
    const handleBeforeInstallPrompt = (e: Event) => {
      e.preventDefault();
      setInstallPrompt(e as BeforeInstallPromptEvent);
      setState((prev) => ({ ...prev, isInstallable: true }));
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);

    return () => {
      window.removeEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    };
  }, []);

  // Handle app installed
  useEffect(() => {
    const handleAppInstalled = () => {
      setInstallPrompt(null);
      setState((prev) => ({ ...prev, isInstalled: true, isInstallable: false }));
    };

    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  // Handle online/offline status
  useEffect(() => {
    const handleOnline = () => setState((prev) => ({ ...prev, isOnline: true }));
    const handleOffline = () => setState((prev) => ({ ...prev, isOnline: false }));

    window.addEventListener("online", handleOnline);
    window.addEventListener("offline", handleOffline);

    // Set initial state
    setState((prev) => ({ ...prev, isOnline: navigator.onLine }));

    return () => {
      window.removeEventListener("online", handleOnline);
      window.removeEventListener("offline", handleOffline);
    };
  }, []);

  // Install the PWA
  const install = useCallback(async () => {
    if (!installPrompt) return false;

    await installPrompt.prompt();
    const { outcome } = await installPrompt.userChoice;

    if (outcome === "accepted") {
      setInstallPrompt(null);
      setState((prev) => ({ ...prev, isInstalled: true, isInstallable: false }));
      return true;
    }

    return false;
  }, [installPrompt]);

  // Request notification permission
  const requestNotificationPermission = useCallback(async () => {
    if (!("Notification" in window)) return "unsupported";
    
    const permission = await Notification.requestPermission();
    return permission;
  }, []);

  // Check for updates
  const checkForUpdates = useCallback(async () => {
    if ("serviceWorker" in navigator) {
      const registration = await navigator.serviceWorker.getRegistration();
      if (registration) {
        await registration.update();
        return true;
      }
    }
    return false;
  }, []);

  return {
    ...state,
    install,
    requestNotificationPermission,
    checkForUpdates,
  };
}

export default usePWA;
