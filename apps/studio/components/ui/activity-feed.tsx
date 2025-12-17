"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Bot,
  Users,
  Workflow,
  MessageSquare,
  Settings,
  Database,
  Zap,
  Clock,
  ChevronDown,
  RefreshCw,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "../Badge";

// ============================================================
// TYPES
// ============================================================

interface ActivityItem {
  id: string;
  type: "agent" | "team" | "workflow" | "chat" | "settings" | "domain" | "system";
  action: string;
  description: string;
  user?: {
    name: string;
    avatar?: string;
  };
  metadata?: Record<string, string | number>;
  timestamp: Date;
  isNew?: boolean;
}

// ============================================================
// ICONS
// ============================================================

const ACTIVITY_ICONS: Record<ActivityItem["type"], React.ReactNode> = {
  agent: <Bot className="w-4 h-4" />,
  team: <Users className="w-4 h-4" />,
  workflow: <Workflow className="w-4 h-4" />,
  chat: <MessageSquare className="w-4 h-4" />,
  settings: <Settings className="w-4 h-4" />,
  domain: <Database className="w-4 h-4" />,
  system: <Zap className="w-4 h-4" />,
};

const ACTIVITY_COLORS: Record<ActivityItem["type"], string> = {
  agent: "bg-blue-500/20 text-blue-400",
  team: "bg-purple-500/20 text-purple-400",
  workflow: "bg-emerald-500/20 text-emerald-400",
  chat: "bg-amber-500/20 text-amber-400",
  settings: "bg-slate-500/20 text-slate-400",
  domain: "bg-pink-500/20 text-pink-400",
  system: "bg-cyan-500/20 text-cyan-400",
};

// ============================================================
// ACTIVITY ITEM COMPONENT
// ============================================================

interface ActivityItemCardProps {
  activity: ActivityItem;
}

function ActivityItemCard({ activity }: ActivityItemCardProps) {
  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return "agora";
    if (minutes < 60) return `${minutes}m`;
    if (hours < 24) return `${hours}h`;
    return `${days}d`;
  };

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20 }}
      className={cn(
        "flex gap-3 p-3 rounded-xl transition-colors",
        activity.isNew ? "bg-blue-500/5" : "hover:bg-slate-800/50"
      )}
    >
      {/* Icon */}
      <div className={cn("p-2 rounded-lg", ACTIVITY_COLORS[activity.type])}>
        {ACTIVITY_ICONS[activity.type]}
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          {activity.user && (
            <span className="text-sm font-medium text-white">
              {activity.user.name}
            </span>
          )}
          <span className="text-sm text-slate-400">{activity.action}</span>
          {activity.isNew && (
            <Badge variant="primary" className="text-[10px] px-1.5 py-0.5">
              NOVO
            </Badge>
          )}
        </div>
        <p className="text-sm text-slate-500 truncate">{activity.description}</p>
      </div>

      {/* Time */}
      <div className="flex items-center gap-1 text-xs text-slate-500">
        <Clock className="w-3 h-3" />
        {formatTime(activity.timestamp)}
      </div>
    </motion.div>
  );
}

// ============================================================
// ACTIVITY FEED
// ============================================================

interface ActivityFeedProps {
  activities?: ActivityItem[];
  className?: string;
  maxItems?: number;
  title?: string;
  showLoadMore?: boolean;
  onLoadMore?: () => void;
  onRefresh?: () => void;
  isLoading?: boolean;
}

export function ActivityFeed({
  activities = [],
  className,
  maxItems = 10,
  title = "Atividade Recente",
  showLoadMore = true,
  onLoadMore,
  onRefresh,
  isLoading = false,
}: ActivityFeedProps) {
  const [filter, setFilter] = useState<ActivityItem["type"] | "all">("all");
  const [isExpanded, setIsExpanded] = useState(true);

  const filteredActivities =
    filter === "all"
      ? activities
      : activities.filter((a) => a.type === filter);

  const displayedActivities = filteredActivities.slice(0, maxItems);

  return (
    <div className={cn("bg-slate-900/50 rounded-xl border border-slate-800", className)}>
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-slate-800">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-2"
        >
          <h3 className="font-semibold text-white">{title}</h3>
          <motion.div animate={{ rotate: isExpanded ? 0 : -90 }}>
            <ChevronDown className="w-4 h-4 text-slate-400" />
          </motion.div>
        </button>

        <div className="flex items-center gap-2">
          {onRefresh && (
            <button
              onClick={onRefresh}
              disabled={isLoading}
              className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg disabled:opacity-50"
              title="Atualizar"
            >
              <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
            </button>
          )}
        </div>
      </div>

      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0 }}
            animate={{ height: "auto" }}
            exit={{ height: 0 }}
            className="overflow-hidden"
          >
            {/* Filters */}
            <div className="flex gap-1 p-2 overflow-x-auto border-b border-slate-800">
              {["all", "agent", "team", "workflow", "chat", "domain"].map((type) => (
                <button
                  key={type}
                  onClick={() => setFilter(type as typeof filter)}
                  className={cn(
                    "px-3 py-1 rounded-full text-xs font-medium transition-colors whitespace-nowrap",
                    filter === type
                      ? "bg-blue-600 text-white"
                      : "bg-slate-800 text-slate-400 hover:text-white"
                  )}
                >
                  {type === "all" ? "Todos" : type.charAt(0).toUpperCase() + type.slice(1)}
                </button>
              ))}
            </div>

            {/* Activities List */}
            <div className="p-2 space-y-1 max-h-[400px] overflow-y-auto">
              {displayedActivities.length > 0 ? (
                <AnimatePresence mode="popLayout">
                  {displayedActivities.map((activity) => (
                    <ActivityItemCard key={activity.id} activity={activity} />
                  ))}
                </AnimatePresence>
              ) : (
                <div className="py-8 text-center text-slate-500">
                  <Zap className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>Nenhuma atividade encontrada</p>
                </div>
              )}
            </div>

            {/* Load More */}
            {showLoadMore && filteredActivities.length > maxItems && (
              <div className="p-3 border-t border-slate-800">
                <button
                  onClick={onLoadMore}
                  className="w-full py-2 text-sm text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors"
                >
                  Ver mais ({filteredActivities.length - maxItems} restantes)
                </button>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// ACTIVITY FEED HOOK (Simulated real-time)
// ============================================================

export function useActivityFeed() {
  const [activities, setActivities] = useState<ActivityItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  // Simulate initial load
  useEffect(() => {
    const initialActivities: ActivityItem[] = [
      {
        id: "1",
        type: "agent",
        action: "criou",
        description: "Agente de Suporte ao Cliente",
        user: { name: "Maria Silva" },
        timestamp: new Date(Date.now() - 5 * 60000),
        isNew: true,
      },
      {
        id: "2",
        type: "team",
        action: "atualizou",
        description: "Time de Vendas - adicionou 2 agentes",
        user: { name: "João Santos" },
        timestamp: new Date(Date.now() - 15 * 60000),
      },
      {
        id: "3",
        type: "workflow",
        action: "executou",
        description: "Pipeline de Análise de Dados",
        user: { name: "Ana Costa" },
        timestamp: new Date(Date.now() - 30 * 60000),
      },
      {
        id: "4",
        type: "chat",
        action: "enviou",
        description: "128 mensagens processadas",
        user: { name: "Sistema" },
        timestamp: new Date(Date.now() - 60 * 60000),
      },
      {
        id: "5",
        type: "domain",
        action: "configurou",
        description: "Domínio Financeiro com 5 ferramentas",
        user: { name: "Carlos Lima" },
        timestamp: new Date(Date.now() - 2 * 3600000),
      },
      {
        id: "6",
        type: "system",
        action: "atualizou",
        description: "Sistema atualizado para v5.0",
        timestamp: new Date(Date.now() - 3 * 3600000),
      },
    ];

    setActivities(initialActivities);
  }, []);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000));
    
    // Add a new random activity
    const newActivity: ActivityItem = {
      id: `new-${Date.now()}`,
      type: ["agent", "team", "workflow", "chat"][Math.floor(Math.random() * 4)] as ActivityItem["type"],
      action: "atualizou",
      description: "Nova atividade simulada",
      user: { name: "Usuário" },
      timestamp: new Date(),
      isNew: true,
    };

    setActivities((prev) => [newActivity, ...prev.map((a) => ({ ...a, isNew: false }))]);
    setIsLoading(false);
  }, []);

  const loadMore = useCallback(() => {
    // Simulate loading more
    const moreActivities: ActivityItem[] = [
      {
        id: `more-${Date.now()}-1`,
        type: "agent",
        action: "criou",
        description: "Agente adicional",
        user: { name: "Usuário" },
        timestamp: new Date(Date.now() - 24 * 3600000),
      },
      {
        id: `more-${Date.now()}-2`,
        type: "workflow",
        action: "executou",
        description: "Workflow antigo",
        user: { name: "Sistema" },
        timestamp: new Date(Date.now() - 48 * 3600000),
      },
    ];

    setActivities((prev) => [...prev, ...moreActivities]);
  }, []);

  return {
    activities,
    isLoading,
    refresh,
    loadMore,
  };
}

export default {
  ActivityFeed,
  useActivityFeed,
};
