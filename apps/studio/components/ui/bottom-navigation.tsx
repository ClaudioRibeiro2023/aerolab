"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence, useMotionValue, useTransform, PanInfo } from "framer-motion";
import { useRouter, usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Bot,
  Users,
  Workflow,
  MessageSquare,
  Plus,
  Settings,
  Database,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

interface NavItem {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: string;
}

interface QuickAction {
  id: string;
  label: string;
  icon: React.ReactNode;
  href: string;
  color: string;
}

// ============================================================
// NAVIGATION ITEMS
// ============================================================

const NAV_ITEMS: NavItem[] = [
  { id: "dashboard", label: "Dashboard", icon: <LayoutDashboard className="w-5 h-5" />, href: "/dashboard" },
  { id: "agents", label: "Agentes", icon: <Bot className="w-5 h-5" />, href: "/agents" },
  { id: "add", label: "Novo", icon: <Plus className="w-6 h-6" />, href: "" }, // Special action button
  { id: "teams", label: "Times", icon: <Users className="w-5 h-5" />, href: "/teams" },
  { id: "chat", label: "Chat", icon: <MessageSquare className="w-5 h-5" />, href: "/chat" },
];

const QUICK_ACTIONS: QuickAction[] = [
  { id: "agent", label: "Novo Agente", icon: <Bot className="w-5 h-5" />, href: "/agents/new", color: "bg-blue-500" },
  { id: "team", label: "Novo Time", icon: <Users className="w-5 h-5" />, href: "/teams/new", color: "bg-purple-500" },
  { id: "workflow", label: "Workflow", icon: <Workflow className="w-5 h-5" />, href: "/workflows/builder", color: "bg-emerald-500" },
  { id: "domain", label: "Domínio", icon: <Database className="w-5 h-5" />, href: "/domains", color: "bg-amber-500" },
];

// ============================================================
// BOTTOM NAVIGATION
// ============================================================

interface BottomNavigationProps {
  className?: string;
}

export function BottomNavigation({ className }: BottomNavigationProps) {
  const router = useRouter();
  const pathname = usePathname();
  const [showQuickActions, setShowQuickActions] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Check if mobile
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768);
    };
    
    checkMobile();
    window.addEventListener("resize", checkMobile);
    return () => window.removeEventListener("resize", checkMobile);
  }, []);

  // Don't render on desktop
  if (!isMobile) return null;

  const handleNavClick = (item: NavItem) => {
    if (item.id === "add") {
      setShowQuickActions(true);
    } else {
      router.push(item.href);
    }
  };

  const handleQuickAction = (action: QuickAction) => {
    setShowQuickActions(false);
    router.push(action.href);
  };

  return (
    <>
      {/* Quick Actions Modal */}
      <AnimatePresence>
        {showQuickActions && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
            onClick={() => setShowQuickActions(false)}
          >
            <motion.div
              initial={{ y: "100%" }}
              animate={{ y: 0 }}
              exit={{ y: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 300 }}
              className="absolute bottom-0 left-0 right-0 bg-slate-900 rounded-t-3xl p-6 pb-10"
              onClick={(e) => e.stopPropagation()}
            >
              {/* Handle bar */}
              <div className="w-12 h-1 bg-slate-700 rounded-full mx-auto mb-6" />

              {/* Header */}
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white">Criar Novo</h3>
                <button
                  onClick={() => setShowQuickActions(false)}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Actions Grid */}
              <div className="grid grid-cols-2 gap-4">
                {QUICK_ACTIONS.map((action) => (
                  <motion.button
                    key={action.id}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => handleQuickAction(action)}
                    className="flex flex-col items-center gap-3 p-4 bg-slate-800/50 rounded-2xl border border-slate-700"
                  >
                    <div className={cn("p-3 rounded-xl", action.color)}>
                      {action.icon}
                    </div>
                    <span className="text-sm font-medium text-white">{action.label}</span>
                  </motion.button>
                ))}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Bottom Navigation Bar */}
      <motion.nav
        initial={{ y: 100 }}
        animate={{ y: 0 }}
        className={cn(
          "fixed bottom-0 left-0 right-0 z-50",
          "bg-slate-900/95 backdrop-blur-xl border-t border-slate-800",
          "safe-area-pb",
          className
        )}
      >
        <div className="flex items-center justify-around px-2 py-2">
          {NAV_ITEMS.map((item) => {
            const isActive = pathname === item.href;
            const isAddButton = item.id === "add";

            return (
              <motion.button
                key={item.id}
                whileTap={{ scale: 0.9 }}
                onClick={() => handleNavClick(item)}
                className={cn(
                  "flex flex-col items-center gap-1 py-2 px-3 rounded-xl transition-colors",
                  isAddButton
                    ? "relative -mt-6"
                    : isActive
                    ? "text-blue-400"
                    : "text-slate-500"
                )}
              >
                {isAddButton ? (
                  <div className="w-14 h-14 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/30">
                    <Plus className="w-7 h-7 text-white" />
                  </div>
                ) : (
                  <>
                    <motion.div
                      animate={isActive ? { scale: 1.1 } : { scale: 1 }}
                    >
                      {item.icon}
                    </motion.div>
                    <span className="text-[10px] font-medium">{item.label}</span>
                    {isActive && (
                      <motion.div
                        layoutId="activeIndicator"
                        className="absolute -bottom-1 w-1 h-1 rounded-full bg-blue-400"
                      />
                    )}
                  </>
                )}
              </motion.button>
            );
          })}
        </div>
      </motion.nav>
    </>
  );
}

// ============================================================
// SWIPEABLE BOTTOM SHEET
// ============================================================

interface BottomSheetProps {
  isOpen: boolean;
  onClose: () => void;
  children: React.ReactNode;
  title?: string;
}

export function BottomSheet({ isOpen, onClose, children, title }: BottomSheetProps) {
  const y = useMotionValue(0);
  const opacity = useTransform(y, [0, 300], [1, 0]);

  const handleDragEnd = (_: unknown, info: PanInfo) => {
    if (info.offset.y > 100 || info.velocity.y > 500) {
      onClose();
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] bg-black/60 backdrop-blur-sm"
          onClick={onClose}
        >
          <motion.div
            initial={{ y: "100%" }}
            animate={{ y: 0 }}
            exit={{ y: "100%" }}
            transition={{ type: "spring", damping: 25, stiffness: 300 }}
            drag="y"
            dragConstraints={{ top: 0 }}
            dragElastic={0.2}
            onDragEnd={handleDragEnd}
            style={{ y, opacity }}
            className="absolute bottom-0 left-0 right-0 max-h-[90vh] bg-slate-900 rounded-t-3xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Handle */}
            <div className="sticky top-0 z-10 bg-slate-900 pt-3 pb-4">
              <div className="w-12 h-1 bg-slate-700 rounded-full mx-auto" />
              {title && (
                <h3 className="text-lg font-semibold text-white text-center mt-4">{title}</h3>
              )}
            </div>

            {/* Content */}
            <div className="px-6 pb-10 overflow-y-auto">
              {children}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ============================================================
// FLOATING ACTION BUTTON
// ============================================================

interface FABProps {
  onClick?: () => void;
  icon?: React.ReactNode;
  className?: string;
}

export function FloatingActionButton({
  onClick,
  icon = <Plus className="w-6 h-6" />,
  className,
}: FABProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.1 }}
      whileTap={{ scale: 0.9 }}
      onClick={onClick}
      className={cn(
        "fixed bottom-24 right-6 z-40 w-14 h-14 rounded-full",
        "bg-gradient-to-br from-blue-500 to-purple-600",
        "flex items-center justify-center shadow-lg shadow-blue-500/30",
        "text-white",
        className
      )}
    >
      {icon}
    </motion.button>
  );
}

export default {
  BottomNavigation,
  BottomSheet,
  FloatingActionButton,
};
