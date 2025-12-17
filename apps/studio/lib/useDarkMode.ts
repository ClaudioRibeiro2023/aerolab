"use client";

import { useState, useEffect, useCallback } from "react";

type Theme = "light" | "dark" | "system";

const STORAGE_KEY = "agno_theme";

/**
 * Hook para gerenciar dark mode com persistência
 * 
 * Features:
 * - Persiste preferência no localStorage
 * - Suporta tema do sistema (prefers-color-scheme)
 * - Toggle rápido entre light/dark
 */
export function useDarkMode() {
  const [theme, setThemeState] = useState<Theme>(() => {
    if (typeof window === "undefined") {
      return "system";
    }
    const savedTheme = window.localStorage.getItem(STORAGE_KEY) as Theme | null;
    return savedTheme || "system";
  });
  const [isDark, setIsDark] = useState(false);
  const [isHydrated, setIsHydrated] = useState(false);

  // Detectar preferência do sistema
  const getSystemPreference = useCallback((): boolean => {
    if (typeof window === "undefined") return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  }, []);

  // Aplicar tema ao documento
  const applyTheme = useCallback((dark: boolean) => {
    if (typeof document === "undefined") return;
    
    if (dark) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    setIsDark(dark);
  }, []);

  // Aplicar tema sempre que a preferência mudar
  useEffect(() => {
    const effectiveDark = theme === "system" ? getSystemPreference() : theme === "dark";
    applyTheme(effectiveDark);
    setIsHydrated(true);
  }, [theme, applyTheme, getSystemPreference]);

  // Escutar mudanças na preferência do sistema
  useEffect(() => {
    if (theme !== "system") return;
    if (typeof window === "undefined") return;

    const mediaQuery = window.matchMedia("(prefers-color-scheme: dark)");

    const handleChange = (e: MediaQueryListEvent) => {
      applyTheme(e.matches);
    };

    mediaQuery.addEventListener("change", handleChange);
    return () => mediaQuery.removeEventListener("change", handleChange);
  }, [theme, applyTheme]);

  // Definir tema
  const setTheme = useCallback((newTheme: Theme) => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(STORAGE_KEY, newTheme);
    }
    setThemeState(newTheme);
  }, []);

  // Toggle rápido
  const toggleDarkMode = useCallback(() => {
    const newDark = !isDark;
    setTheme(newDark ? "dark" : "light");
  }, [isDark, setTheme]);

  // Ciclar entre light -> dark -> system
  const cycleTheme = useCallback(() => {
    const cycle: Theme[] = ["light", "dark", "system"];
    const currentIndex = cycle.indexOf(theme);
    const nextIndex = (currentIndex + 1) % cycle.length;
    setTheme(cycle[nextIndex]);
  }, [theme, setTheme]);

  return {
    theme,
    isDark,
    isHydrated,
    setTheme,
    toggleDarkMode,
    cycleTheme,
  };
}

/**
 * Inicializador de dark mode para evitar flash
 * Adicione este script inline no <head> do layout
 */
export const darkModeInitScript = `
(function() {
  try {
    var theme = localStorage.getItem('${STORAGE_KEY}');
    var isDark = theme === 'dark' || 
      (theme !== 'light' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (isDark) {
      document.documentElement.classList.add('dark');
    }
  } catch (e) {}
})();
`;
