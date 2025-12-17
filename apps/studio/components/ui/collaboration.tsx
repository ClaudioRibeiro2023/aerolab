"use client";

import React, { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

// ============================================================
// TYPES
// ============================================================

interface User {
  id: string;
  name: string;
  avatar?: string;
  color: string;
  cursor?: { x: number; y: number };
  status: "online" | "away" | "busy";
}

interface PresenceState {
  users: User[];
  currentUser: User | null;
}

// ============================================================
// PRESENCE AVATARS
// ============================================================

interface PresenceAvatarsProps {
  users: User[];
  maxVisible?: number;
  className?: string;
  size?: "sm" | "md" | "lg";
}

const sizes = {
  sm: "w-6 h-6 text-xs",
  md: "w-8 h-8 text-sm",
  lg: "w-10 h-10 text-base",
};

export function PresenceAvatars({
  users,
  maxVisible = 5,
  className,
  size = "md",
}: PresenceAvatarsProps) {
  const visibleUsers = users.slice(0, maxVisible);
  const remainingCount = users.length - maxVisible;

  return (
    <div className={cn("flex -space-x-2", className)}>
      <AnimatePresence mode="popLayout">
        {visibleUsers.map((user) => (
          <motion.div
            key={user.id}
            initial={{ opacity: 0, scale: 0.5, x: -20 }}
            animate={{ opacity: 1, scale: 1, x: 0 }}
            exit={{ opacity: 0, scale: 0.5, x: 20 }}
            className="relative"
            title={`${user.name} - ${user.status}`}
          >
            <div
              className={cn(
                "rounded-full flex items-center justify-center font-semibold text-white border-2 border-slate-900",
                sizes[size]
              )}
              style={{ backgroundColor: user.color }}
            >
              {user.avatar ? (
                <img
                  src={user.avatar}
                  alt={user.name}
                  className="w-full h-full rounded-full object-cover"
                />
              ) : (
                user.name.charAt(0).toUpperCase()
              )}
            </div>
            
            {/* Status indicator */}
            <span
              className={cn(
                "absolute bottom-0 right-0 w-2.5 h-2.5 rounded-full border-2 border-slate-900",
                user.status === "online" && "bg-green-500",
                user.status === "away" && "bg-yellow-500",
                user.status === "busy" && "bg-red-500"
              )}
            />
          </motion.div>
        ))}
      </AnimatePresence>
      
      {remainingCount > 0 && (
        <div
          className={cn(
            "rounded-full flex items-center justify-center font-semibold bg-slate-700 text-white border-2 border-slate-900",
            sizes[size]
          )}
        >
          +{remainingCount}
        </div>
      )}
    </div>
  );
}

// ============================================================
// LIVE CURSORS
// ============================================================

interface LiveCursorsProps {
  users: User[];
  className?: string;
}

export function LiveCursors({ users, className }: LiveCursorsProps) {
  return (
    <div className={cn("fixed inset-0 pointer-events-none z-50", className)}>
      <AnimatePresence>
        {users.map((user) =>
          user.cursor ? (
            <motion.div
              key={user.id}
              className="absolute"
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{
                opacity: 1,
                scale: 1,
                x: user.cursor.x,
                y: user.cursor.y,
              }}
              exit={{ opacity: 0, scale: 0.5 }}
              transition={{ type: "spring", damping: 30, stiffness: 500 }}
            >
              {/* Cursor */}
              <svg
                width="24"
                height="24"
                viewBox="0 0 24 24"
                fill={user.color}
                className="drop-shadow-md"
              >
                <path d="M5.65376 12.456H0.380127L10.5765 0.0568848V23.9432L5.65376 12.456Z" />
              </svg>
              
              {/* Name label */}
              <div
                className="absolute left-4 top-4 px-2 py-1 rounded text-xs font-medium text-white whitespace-nowrap"
                style={{ backgroundColor: user.color }}
              >
                {user.name}
              </div>
            </motion.div>
          ) : null
        )}
      </AnimatePresence>
    </div>
  );
}

// ============================================================
// TYPING INDICATOR
// ============================================================

interface TypingIndicatorProps {
  users: string[];
  className?: string;
}

export function TypingIndicator({ users, className }: TypingIndicatorProps) {
  if (users.length === 0) return null;

  const text =
    users.length === 1
      ? `${users[0]} está digitando...`
      : users.length === 2
      ? `${users[0]} e ${users[1]} estão digitando...`
      : `${users.length} pessoas estão digitando...`;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: 10 }}
      className={cn("flex items-center gap-2 text-sm text-slate-400", className)}
    >
      <div className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-1.5 h-1.5 rounded-full bg-slate-400"
            animate={{ y: [0, -4, 0] }}
            transition={{
              duration: 0.6,
              repeat: Infinity,
              delay: i * 0.1,
            }}
          />
        ))}
      </div>
      <span>{text}</span>
    </motion.div>
  );
}

// ============================================================
// COLLABORATION BANNER
// ============================================================

interface CollaborationBannerProps {
  users: User[];
  documentName: string;
  className?: string;
}

export function CollaborationBanner({
  users,
  documentName,
  className,
}: CollaborationBannerProps) {
  const onlineUsers = users.filter((u) => u.status === "online");

  return (
    <div
      className={cn(
        "flex items-center justify-between px-4 py-2 bg-slate-800/50 backdrop-blur-sm border-b border-slate-700",
        className
      )}
    >
      <div className="flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm text-slate-300">
            {onlineUsers.length} online
          </span>
        </div>
        <span className="text-slate-600">|</span>
        <span className="text-sm text-slate-400">{documentName}</span>
      </div>
      
      <PresenceAvatars users={onlineUsers} size="sm" />
    </div>
  );
}

// ============================================================
// COLLABORATION PROVIDER (Simulated - can be replaced with Liveblocks)
// ============================================================

interface CollaborationContextValue {
  users: User[];
  currentUser: User | null;
  updateCursor: (x: number, y: number) => void;
  setStatus: (status: User["status"]) => void;
}

const CollaborationContext = React.createContext<CollaborationContextValue | null>(null);

export function useCollaboration() {
  const context = React.useContext(CollaborationContext);
  if (!context) {
    throw new Error("useCollaboration must be used within CollaborationProvider");
  }
  return context;
}

interface CollaborationProviderProps {
  children: React.ReactNode;
  roomId: string;
  userName?: string;
}

// Simulated collaboration - replace with Liveblocks for production
export function CollaborationProvider({
  children,
  roomId,
  userName = "Anônimo",
}: CollaborationProviderProps) {
  const [users, setUsers] = useState<User[]>([]);
  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    // Simulated user join
    const colors = ["#3B82F6", "#8B5CF6", "#EC4899", "#10B981", "#F59E0B"];
    const user: User = {
      id: `user-${Date.now()}`,
      name: userName,
      color: colors[Math.floor(Math.random() * colors.length)],
      status: "online",
    };
    
    setCurrentUser(user);
    setUsers([user]);
    
    // Simulate other users joining (demo)
    const demoUsers: User[] = [
      { id: "demo-1", name: "Maria", color: "#EC4899", status: "online" },
      { id: "demo-2", name: "João", color: "#10B981", status: "away" },
    ];
    
    const timeout = setTimeout(() => {
      setUsers((prev) => [...prev, ...demoUsers]);
    }, 2000);
    
    return () => clearTimeout(timeout);
  }, [userName, roomId]);

  const updateCursor = useCallback((x: number, y: number) => {
    if (!currentUser) return;
    setCurrentUser((prev) => prev ? { ...prev, cursor: { x, y } } : null);
  }, [currentUser]);

  const setStatus = useCallback((status: User["status"]) => {
    if (!currentUser) return;
    setCurrentUser((prev) => prev ? { ...prev, status } : null);
    setUsers((prev) =>
      prev.map((u) => (u.id === currentUser.id ? { ...u, status } : u))
    );
  }, [currentUser]);

  return (
    <CollaborationContext.Provider
      value={{ users, currentUser, updateCursor, setStatus }}
    >
      {children}
    </CollaborationContext.Provider>
  );
}

export default {
  PresenceAvatars,
  LiveCursors,
  TypingIndicator,
  CollaborationBanner,
  CollaborationProvider,
  useCollaboration,
};
