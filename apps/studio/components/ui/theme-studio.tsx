"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Palette, Download, Upload, Check, Copy, RefreshCw, X, Save, Eye } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

interface ThemeColors {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
  foreground: string;
  muted: string;
  border: string;
}

interface CustomTheme {
  id: string;
  name: string;
  colors: ThemeColors;
  createdAt: Date;
}

// ============================================================
// PRESET THEMES
// ============================================================

const PRESET_THEMES: Record<string, ThemeColors> = {
  default: {
    primary: "#3b82f6",
    secondary: "#8b5cf6",
    accent: "#ec4899",
    background: "#0f172a",
    foreground: "#f8fafc",
    muted: "#64748b",
    border: "#334155",
  },
  ocean: {
    primary: "#06b6d4",
    secondary: "#0ea5e9",
    accent: "#22d3ee",
    background: "#0c1222",
    foreground: "#e0f2fe",
    muted: "#7dd3fc",
    border: "#164e63",
  },
  forest: {
    primary: "#10b981",
    secondary: "#059669",
    accent: "#34d399",
    background: "#0d1912",
    foreground: "#ecfdf5",
    muted: "#6ee7b7",
    border: "#065f46",
  },
  sunset: {
    primary: "#f97316",
    secondary: "#ea580c",
    accent: "#fbbf24",
    background: "#1c1412",
    foreground: "#fff7ed",
    muted: "#fdba74",
    border: "#9a3412",
  },
  lavender: {
    primary: "#a855f7",
    secondary: "#9333ea",
    accent: "#c084fc",
    background: "#1a1425",
    foreground: "#faf5ff",
    muted: "#d8b4fe",
    border: "#581c87",
  },
  rose: {
    primary: "#ec4899",
    secondary: "#db2777",
    accent: "#f472b6",
    background: "#1c1218",
    foreground: "#fdf2f8",
    muted: "#f9a8d4",
    border: "#9d174d",
  },
};

// ============================================================
// COLOR PICKER
// ============================================================

interface ColorPickerProps {
  label: string;
  value: string;
  onChange: (color: string) => void;
}

function ColorPicker({ label, value, onChange }: ColorPickerProps) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="space-y-2">
      <label className="text-sm text-slate-400">{label}</label>
      <div className="flex items-center gap-2">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="w-10 h-10 rounded-lg border border-slate-700 overflow-hidden"
          style={{ backgroundColor: value }}
        />
        <input
          type="text"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="flex-1 px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white text-sm font-mono"
        />
        <button
          onClick={() => navigator.clipboard.writeText(value)}
          className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
          title="Copiar"
        >
          <Copy className="w-4 h-4" />
        </button>
      </div>
      
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="overflow-hidden"
          >
            <input
              type="color"
              value={value}
              onChange={(e) => onChange(e.target.value)}
              className="w-full h-24 cursor-pointer"
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// THEME PREVIEW
// ============================================================

interface ThemePreviewProps {
  colors: ThemeColors;
  className?: string;
}

function ThemePreview({ colors, className }: ThemePreviewProps) {
  return (
    <div
      className={cn("rounded-xl overflow-hidden border", className)}
      style={{ borderColor: colors.border, backgroundColor: colors.background }}
    >
      {/* Header */}
      <div
        className="p-4 flex items-center justify-between"
        style={{ borderBottom: `1px solid ${colors.border}` }}
      >
        <div className="flex items-center gap-2">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: colors.primary }}
          >
            <span className="text-white font-bold text-sm">A</span>
          </div>
          <span style={{ color: colors.foreground }} className="font-semibold">
            AGNO
          </span>
        </div>
        <div className="flex gap-2">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: colors.accent }}
          />
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: colors.secondary }}
          />
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: colors.primary }}
          />
        </div>
      </div>

      {/* Content */}
      <div className="p-4 space-y-3">
        <div
          className="h-4 rounded"
          style={{ backgroundColor: colors.muted, width: "60%", opacity: 0.3 }}
        />
        <div
          className="h-3 rounded"
          style={{ backgroundColor: colors.muted, width: "80%", opacity: 0.2 }}
        />
        <div className="flex gap-2 mt-4">
          <div
            className="px-4 py-2 rounded-lg text-white text-sm"
            style={{ backgroundColor: colors.primary }}
          >
            Primário
          </div>
          <div
            className="px-4 py-2 rounded-lg text-sm"
            style={{
              backgroundColor: "transparent",
              border: `1px solid ${colors.border}`,
              color: colors.foreground,
            }}
          >
            Secundário
          </div>
        </div>
      </div>
    </div>
  );
}

// ============================================================
// THEME STUDIO PANEL
// ============================================================

interface ThemeStudioProps {
  isOpen: boolean;
  onClose: () => void;
  onApplyTheme?: (colors: ThemeColors) => void;
}

export function ThemeStudio({ isOpen, onClose, onApplyTheme }: ThemeStudioProps) {
  const [colors, setColors] = useState<ThemeColors>(PRESET_THEMES.default);
  const [savedThemes, setSavedThemes] = useState<CustomTheme[]>([]);
  const [themeName, setThemeName] = useState("");

  // Load saved themes
  useEffect(() => {
    const saved = localStorage.getItem("agno-custom-themes");
    if (saved) {
      setSavedThemes(JSON.parse(saved));
    }
  }, []);

  const updateColor = useCallback((key: keyof ThemeColors, value: string) => {
    setColors((prev) => ({ ...prev, [key]: value }));
  }, []);

  const applyPreset = useCallback((presetKey: string) => {
    setColors(PRESET_THEMES[presetKey]);
  }, []);

  const saveTheme = useCallback(() => {
    if (!themeName.trim()) return;

    const newTheme: CustomTheme = {
      id: `theme-${Date.now()}`,
      name: themeName,
      colors,
      createdAt: new Date(),
    };

    const updated = [...savedThemes, newTheme];
    setSavedThemes(updated);
    localStorage.setItem("agno-custom-themes", JSON.stringify(updated));
    setThemeName("");
  }, [themeName, colors, savedThemes]);

  const deleteTheme = useCallback((id: string) => {
    const updated = savedThemes.filter((t) => t.id !== id);
    setSavedThemes(updated);
    localStorage.setItem("agno-custom-themes", JSON.stringify(updated));
  }, [savedThemes]);

  const exportTheme = useCallback(() => {
    const data = JSON.stringify(colors, null, 2);
    const blob = new Blob([data], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "agno-theme.json";
    a.click();
    URL.revokeObjectURL(url);
  }, [colors]);

  const importTheme = useCallback(() => {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json";
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;

      try {
        const text = await file.text();
        const imported = JSON.parse(text);
        setColors(imported);
      } catch {
        console.error("Failed to import theme");
      }
    };
    input.click();
  }, []);

  const randomize = useCallback(() => {
    const randomColor = () =>
      `#${Math.floor(Math.random() * 16777215).toString(16).padStart(6, "0")}`;

    setColors({
      primary: randomColor(),
      secondary: randomColor(),
      accent: randomColor(),
      background: `#${Math.floor(Math.random() * 0x222222).toString(16).padStart(6, "0")}`,
      foreground: "#f8fafc",
      muted: randomColor(),
      border: randomColor(),
    });
  }, []);

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
          onClick={onClose}
        >
          <motion.div
            initial={{ scale: 0.95, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.95, y: 20 }}
            className="w-full max-w-4xl max-h-[90vh] bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-slate-800">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-500/20 rounded-lg">
                  <Palette className="w-5 h-5 text-purple-400" />
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-white">Theme Studio</h2>
                  <p className="text-sm text-slate-400">Personalize as cores da plataforma</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="flex flex-col md:flex-row gap-6 p-6 overflow-y-auto max-h-[calc(90vh-200px)]">
              {/* Left: Color Editors */}
              <div className="flex-1 space-y-6">
                {/* Presets */}
                <div>
                  <h3 className="text-sm font-medium text-slate-400 mb-3">Temas Predefinidos</h3>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(PRESET_THEMES).map(([key, preset]) => (
                      <button
                        key={key}
                        onClick={() => applyPreset(key)}
                        className="flex items-center gap-2 px-3 py-1.5 bg-slate-800 hover:bg-slate-700 rounded-lg text-sm text-white capitalize"
                      >
                        <div
                          className="w-4 h-4 rounded-full"
                          style={{ backgroundColor: preset.primary }}
                        />
                        {key}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Color Pickers */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <ColorPicker
                    label="Primária"
                    value={colors.primary}
                    onChange={(v) => updateColor("primary", v)}
                  />
                  <ColorPicker
                    label="Secundária"
                    value={colors.secondary}
                    onChange={(v) => updateColor("secondary", v)}
                  />
                  <ColorPicker
                    label="Accent"
                    value={colors.accent}
                    onChange={(v) => updateColor("accent", v)}
                  />
                  <ColorPicker
                    label="Background"
                    value={colors.background}
                    onChange={(v) => updateColor("background", v)}
                  />
                  <ColorPicker
                    label="Foreground"
                    value={colors.foreground}
                    onChange={(v) => updateColor("foreground", v)}
                  />
                  <ColorPicker
                    label="Border"
                    value={colors.border}
                    onChange={(v) => updateColor("border", v)}
                  />
                </div>

                {/* Actions */}
                <div className="flex flex-wrap gap-2">
                  <button
                    onClick={randomize}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Aleatório
                  </button>
                  <button
                    onClick={importTheme}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm"
                  >
                    <Upload className="w-4 h-4" />
                    Importar
                  </button>
                  <button
                    onClick={exportTheme}
                    className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg text-sm"
                  >
                    <Download className="w-4 h-4" />
                    Exportar
                  </button>
                </div>

                {/* Save Theme */}
                <div className="flex gap-2">
                  <input
                    type="text"
                    placeholder="Nome do tema..."
                    value={themeName}
                    onChange={(e) => setThemeName(e.target.value)}
                    className="flex-1 px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
                  />
                  <button
                    onClick={saveTheme}
                    disabled={!themeName.trim()}
                    className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white rounded-lg"
                  >
                    <Save className="w-4 h-4" />
                    Salvar
                  </button>
                </div>

                {/* Saved Themes */}
                {savedThemes.length > 0 && (
                  <div>
                    <h3 className="text-sm font-medium text-slate-400 mb-3">Meus Temas</h3>
                    <div className="space-y-2">
                      {savedThemes.map((theme) => (
                        <div
                          key={theme.id}
                          className="flex items-center justify-between p-3 bg-slate-800 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <div
                              className="w-6 h-6 rounded-full"
                              style={{ backgroundColor: theme.colors.primary }}
                            />
                            <span className="text-white">{theme.name}</span>
                          </div>
                          <div className="flex gap-1">
                            <button
                              onClick={() => setColors(theme.colors)}
                              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-700 rounded"
                              title="Aplicar"
                            >
                              <Check className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => deleteTheme(theme.id)}
                              className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-700 rounded"
                              title="Excluir"
                            >
                              <X className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Right: Preview */}
              <div className="w-full md:w-80">
                <h3 className="text-sm font-medium text-slate-400 mb-3 flex items-center gap-2">
                  <Eye className="w-4 h-4" />
                  Preview
                </h3>
                <ThemePreview colors={colors} />
              </div>
            </div>

            {/* Footer */}
            <div className="flex items-center justify-end gap-3 p-6 border-t border-slate-800">
              <button
                onClick={onClose}
                className="px-4 py-2 text-slate-400 hover:text-white"
              >
                Cancelar
              </button>
              <button
                onClick={() => {
                  onApplyTheme?.(colors);
                  onClose();
                }}
                className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg"
              >
                <Check className="w-4 h-4" />
                Aplicar Tema
              </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default ThemeStudio;
