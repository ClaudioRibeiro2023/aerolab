"use client";

import React, { useState, useEffect, createContext, useContext, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Trophy, Star, Zap, Target, Award, Crown, Flame, Gift } from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

interface Achievement {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  points: number;
  unlockedAt?: Date;
  progress?: number;
  maxProgress?: number;
  category: "beginner" | "intermediate" | "advanced" | "expert";
}

interface UserStats {
  level: number;
  xp: number;
  xpToNextLevel: number;
  totalPoints: number;
  streak: number;
  achievements: string[];
}

interface GamificationContextValue {
  stats: UserStats;
  achievements: Achievement[];
  addXP: (amount: number) => void;
  unlockAchievement: (id: string) => void;
  showLevelUp: boolean;
  showAchievement: Achievement | null;
}

// ============================================================
// ACHIEVEMENTS
// ============================================================

const ACHIEVEMENTS: Achievement[] = [
  {
    id: "first-agent",
    name: "Primeiro Agente",
    description: "Crie seu primeiro agente de IA",
    icon: <Star className="w-5 h-5" />,
    points: 100,
    category: "beginner",
  },
  {
    id: "team-leader",
    name: "Líder de Equipe",
    description: "Crie um time com 3 ou mais agentes",
    icon: <Crown className="w-5 h-5" />,
    points: 250,
    category: "intermediate",
  },
  {
    id: "workflow-master",
    name: "Mestre dos Fluxos",
    description: "Crie 5 workflows automatizados",
    icon: <Zap className="w-5 h-5" />,
    points: 500,
    category: "advanced",
  },
  {
    id: "streak-7",
    name: "Semana de Fogo",
    description: "Use a plataforma por 7 dias seguidos",
    icon: <Flame className="w-5 h-5" />,
    points: 300,
    category: "intermediate",
  },
  {
    id: "domain-explorer",
    name: "Explorador de Domínios",
    description: "Use agentes de 5 domínios diferentes",
    icon: <Target className="w-5 h-5" />,
    points: 400,
    category: "advanced",
  },
  {
    id: "power-user",
    name: "Power User",
    description: "Alcance o nível 10",
    icon: <Trophy className="w-5 h-5" />,
    points: 1000,
    category: "expert",
  },
];

// ============================================================
// CONTEXT
// ============================================================

const GamificationContext = createContext<GamificationContextValue | null>(null);

export function useGamification() {
  const context = useContext(GamificationContext);
  if (!context) {
    throw new Error("useGamification must be used within GamificationProvider");
  }
  return context;
}

// ============================================================
// PROVIDER
// ============================================================

export function GamificationProvider({ children }: { children: React.ReactNode }) {
  const [stats, setStats] = useState<UserStats>({
    level: 1,
    xp: 0,
    xpToNextLevel: 100,
    totalPoints: 0,
    streak: 0,
    achievements: [],
  });
  const [showLevelUp, setShowLevelUp] = useState(false);
  const [showAchievement, setShowAchievement] = useState<Achievement | null>(null);

  // Load from localStorage
  useEffect(() => {
    const saved = localStorage.getItem("agno-gamification");
    if (saved) {
      setStats(JSON.parse(saved));
    }
  }, []);

  // Save to localStorage
  useEffect(() => {
    localStorage.setItem("agno-gamification", JSON.stringify(stats));
  }, [stats]);

  const addXP = useCallback((amount: number) => {
    setStats((prev) => {
      let newXP = prev.xp + amount;
      let newLevel = prev.level;
      let newXPToNext = prev.xpToNextLevel;

      // Level up check
      while (newXP >= newXPToNext) {
        newXP -= newXPToNext;
        newLevel++;
        newXPToNext = Math.floor(newXPToNext * 1.5); // Increase XP needed
        setShowLevelUp(true);
        setTimeout(() => setShowLevelUp(false), 3000);
      }

      return {
        ...prev,
        xp: newXP,
        level: newLevel,
        xpToNextLevel: newXPToNext,
        totalPoints: prev.totalPoints + amount,
      };
    });
  }, []);

  const unlockAchievement = useCallback((id: string) => {
    const achievement = ACHIEVEMENTS.find((a) => a.id === id);
    if (!achievement) return;

    setStats((prev) => {
      if (prev.achievements.includes(id)) return prev;

      setShowAchievement(achievement);
      setTimeout(() => setShowAchievement(null), 4000);

      return {
        ...prev,
        achievements: [...prev.achievements, id],
        totalPoints: prev.totalPoints + achievement.points,
      };
    });
  }, []);

  const achievements = ACHIEVEMENTS.map((a) => ({
    ...a,
    unlockedAt: stats.achievements.includes(a.id) ? new Date() : undefined,
  }));

  return (
    <GamificationContext.Provider
      value={{
        stats,
        achievements,
        addXP,
        unlockAchievement,
        showLevelUp,
        showAchievement,
      }}
    >
      {children}
      <LevelUpNotification show={showLevelUp} level={stats.level} />
      <AchievementNotification achievement={showAchievement} />
    </GamificationContext.Provider>
  );
}

// ============================================================
// LEVEL UP NOTIFICATION
// ============================================================

function LevelUpNotification({ show, level }: { show: boolean; level: number }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, scale: 0.5, y: 50 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.5, y: -50 }}
          className="fixed inset-0 z-[200] flex items-center justify-center pointer-events-none"
        >
          <div className="relative">
            {/* Glow effect */}
            <motion.div
              className="absolute inset-0 bg-gradient-to-r from-yellow-400 to-amber-500 rounded-full blur-3xl"
              animate={{ scale: [1, 1.5, 1], opacity: [0.5, 0.8, 0.5] }}
              transition={{ duration: 2, repeat: Infinity }}
            />
            
            <div className="relative bg-gradient-to-br from-yellow-500 to-amber-600 p-8 rounded-3xl text-center">
              <motion.div
                animate={{ rotate: [0, 10, -10, 0] }}
                transition={{ duration: 0.5, repeat: 3 }}
              >
                <Crown className="w-16 h-16 text-white mx-auto mb-4" />
              </motion.div>
              <h2 className="text-3xl font-bold text-white mb-2">Level Up!</h2>
              <p className="text-5xl font-black text-white">{level}</p>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ============================================================
// ACHIEVEMENT NOTIFICATION
// ============================================================

function AchievementNotification({ achievement }: { achievement: Achievement | null }) {
  return (
    <AnimatePresence>
      {achievement && (
        <motion.div
          initial={{ opacity: 0, x: 100 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: 100 }}
          className="fixed top-20 right-4 z-[100] w-80"
        >
          <div className="bg-gradient-to-r from-purple-600 to-pink-600 rounded-xl p-4 shadow-xl">
            <div className="flex items-center gap-4">
              <div className="p-3 bg-white/20 rounded-xl">
                <Award className="w-8 h-8 text-white" />
              </div>
              <div>
                <p className="text-xs text-white/80 uppercase tracking-wider">Conquista Desbloqueada!</p>
                <h3 className="text-lg font-bold text-white">{achievement.name}</h3>
                <p className="text-sm text-white/80">{achievement.description}</p>
              </div>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ============================================================
// XP BAR COMPONENT
// ============================================================

interface XPBarProps {
  className?: string;
  showLevel?: boolean;
}

export function XPBar({ className, showLevel = true }: XPBarProps) {
  const { stats } = useGamification();
  const progress = (stats.xp / stats.xpToNextLevel) * 100;

  return (
    <div className={cn("space-y-1", className)}>
      {showLevel && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-slate-400">Nível {stats.level}</span>
          <span className="text-slate-500">
            {stats.xp}/{stats.xpToNextLevel} XP
          </span>
        </div>
      )}
      <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
        <motion.div
          className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
          initial={{ width: 0 }}
          animate={{ width: `${progress}%` }}
          transition={{ duration: 0.5, ease: "easeOut" }}
        />
      </div>
    </div>
  );
}

// ============================================================
// ACHIEVEMENTS GRID
// ============================================================

export function AchievementsGrid({ className }: { className?: string }) {
  const { achievements } = useGamification();

  const categories = {
    beginner: "Iniciante",
    intermediate: "Intermediário",
    advanced: "Avançado",
    expert: "Expert",
  };

  return (
    <div className={cn("space-y-6", className)}>
      {Object.entries(categories).map(([key, label]) => {
        const categoryAchievements = achievements.filter(
          (a) => a.category === key
        );
        if (categoryAchievements.length === 0) return null;

        return (
          <div key={key}>
            <h3 className="text-sm font-medium text-slate-400 mb-3">{label}</h3>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
              {categoryAchievements.map((achievement) => (
                <AchievementCard key={achievement.id} achievement={achievement} />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AchievementCard({ achievement }: { achievement: Achievement }) {
  const isUnlocked = !!achievement.unlockedAt;

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className={cn(
        "p-4 rounded-xl border transition-colors",
        isUnlocked
          ? "bg-gradient-to-br from-purple-500/10 to-pink-500/10 border-purple-500/30"
          : "bg-slate-800/50 border-slate-700 opacity-60"
      )}
    >
      <div className="flex items-center gap-3 mb-2">
        <div
          className={cn(
            "p-2 rounded-lg",
            isUnlocked ? "bg-purple-500/20 text-purple-400" : "bg-slate-700 text-slate-500"
          )}
        >
          {achievement.icon}
        </div>
        <div>
          <h4 className="font-medium text-white text-sm">{achievement.name}</h4>
          <p className="text-xs text-slate-400">+{achievement.points} pts</p>
        </div>
      </div>
      <p className="text-xs text-slate-500">{achievement.description}</p>
    </motion.div>
  );
}

// ============================================================
// STREAK COUNTER
// ============================================================

export function StreakCounter({ className }: { className?: string }) {
  const { stats } = useGamification();

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <div className="p-2 bg-orange-500/20 rounded-lg">
        <Flame className="w-5 h-5 text-orange-400" />
      </div>
      <div>
        <p className="text-2xl font-bold text-white">{stats.streak}</p>
        <p className="text-xs text-slate-400">dias seguidos</p>
      </div>
    </div>
  );
}

// ============================================================
// POINTS DISPLAY
// ============================================================

export function PointsDisplay({ className }: { className?: string }) {
  const { stats } = useGamification();

  return (
    <div className={cn("flex items-center gap-2", className)}>
      <Gift className="w-5 h-5 text-yellow-400" />
      <span className="text-lg font-bold text-white">
        {stats.totalPoints.toLocaleString()}
      </span>
      <span className="text-sm text-slate-400">pontos</span>
    </div>
  );
}

export default {
  GamificationProvider,
  useGamification,
  XPBar,
  AchievementsGrid,
  StreakCounter,
  PointsDisplay,
};
