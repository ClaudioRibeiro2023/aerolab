"use client";
import React, { useState, useEffect, useCallback } from "react";

interface Notification {
  id: string;
  type: "success" | "info" | "warning" | "error";
  title: string;
  message?: string;
  timestamp: Date;
  read: boolean;
  action?: { label: string; href: string };
}

const Icons = {
  bell: (<svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" /></svg>),
  check: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>),
  info: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  warning: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" /></svg>),
  error: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>),
  x: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>),
  trash: (<svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" /></svg>),
};

const typeStyles = {
  success: { bg: "bg-green-100 dark:bg-green-900/30", icon: "text-green-600 dark:text-green-400", iconEl: Icons.check },
  info: { bg: "bg-blue-100 dark:bg-blue-900/30", icon: "text-blue-600 dark:text-blue-400", iconEl: Icons.info },
  warning: { bg: "bg-orange-100 dark:bg-orange-900/30", icon: "text-orange-600 dark:text-orange-400", iconEl: Icons.warning },
  error: { bg: "bg-red-100 dark:bg-red-900/30", icon: "text-red-600 dark:text-red-400", iconEl: Icons.error },
};

// Sample notifications - in real app, these would come from an API/WebSocket
const sampleNotifications: Notification[] = [
  { id: "1", type: "success", title: "Workflow concluído", message: "O workflow 'Data Pipeline' foi executado com sucesso", timestamp: new Date(Date.now() - 1000 * 60 * 2), read: false },
  { id: "2", type: "info", title: "Novo agente disponível", message: "O agente 'Code Assistant' foi adicionado ao sistema", timestamp: new Date(Date.now() - 1000 * 60 * 15), read: false, action: { label: "Ver agente", href: "/agents" } },
  { id: "3", type: "warning", title: "Rate limit próximo", message: "Você usou 80% do limite de requisições diárias", timestamp: new Date(Date.now() - 1000 * 60 * 60), read: true },
  { id: "4", type: "success", title: "Documento indexado", message: "3 novos documentos foram adicionados à coleção RAG", timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2), read: true },
  { id: "5", type: "info", title: "Atualização disponível", message: "Nova versão do Agno Platform está disponível", timestamp: new Date(Date.now() - 1000 * 60 * 60 * 5), read: true },
];

function formatTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const minutes = Math.floor(diff / 60000);
  const hours = Math.floor(diff / 3600000);
  const days = Math.floor(diff / 86400000);

  if (minutes < 1) return "Agora";
  if (minutes < 60) return `${minutes}min atrás`;
  if (hours < 24) return `${hours}h atrás`;
  return `${days}d atrás`;
}

export default function NotificationCenter() {
  const [isOpen, setIsOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>(sampleNotifications);

  const unreadCount = notifications.filter(n => !n.read).length;

  const markAsRead = (id: string) => {
    setNotifications(notifications.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const markAllAsRead = () => {
    setNotifications(notifications.map(n => ({ ...n, read: true })));
  };

  const deleteNotification = (id: string) => {
    setNotifications(notifications.filter(n => n.id !== id));
  };

  const clearAll = () => {
    setNotifications([]);
  };

  // Close on click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      const target = e.target as HTMLElement;
      if (isOpen && !target.closest("[data-notification-center]")) {
        setIsOpen(false);
      }
    };
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, [isOpen]);

  return (
    <div className="relative" data-notification-center>
      {/* Bell button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
        title="Notificações"
        aria-label="Notificações"
      >
        {Icons.bell}
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 text-white text-xs font-bold rounded-full flex items-center justify-center">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {/* Dropdown */}
      {isOpen && (
        <div className="absolute right-0 top-full mt-2 w-96 bg-white dark:bg-slate-800 rounded-2xl shadow-2xl border border-gray-100 dark:border-slate-700 overflow-hidden z-50 animate-slide-down">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100 dark:border-slate-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">Notificações</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={markAllAsRead}
                  className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Marcar todas como lidas
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={clearAll}
                  className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  title="Limpar todas"
                >
                  {Icons.trash}
                </button>
              )}
            </div>
          </div>

          {/* Notifications list */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="py-12 text-center text-gray-400">
                <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-gray-100 dark:bg-slate-700 flex items-center justify-center">
                  {Icons.bell}
                </div>
                <p>Nenhuma notificação</p>
              </div>
            ) : (
              notifications.map((notification) => {
                const style = typeStyles[notification.type];
                return (
                  <div
                    key={notification.id}
                    className={`flex gap-3 px-4 py-3 border-b border-gray-50 dark:border-slate-700/50 hover:bg-gray-50 dark:hover:bg-slate-700/50 transition-colors ${
                      !notification.read ? "bg-blue-50/50 dark:bg-blue-900/10" : ""
                    }`}
                    onClick={() => markAsRead(notification.id)}
                  >
                    <div className={`flex-shrink-0 w-8 h-8 rounded-lg ${style.bg} ${style.icon} flex items-center justify-center`}>
                      {style.iconEl}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className={`text-sm font-medium ${!notification.read ? "text-gray-900 dark:text-white" : "text-gray-700 dark:text-gray-300"}`}>
                          {notification.title}
                        </p>
                        <button
                          onClick={(e) => { e.stopPropagation(); deleteNotification(notification.id); }}
                          className="flex-shrink-0 p-1 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
                          title="Remover"
                        >
                          {Icons.x}
                        </button>
                      </div>
                      {notification.message && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
                          {notification.message}
                        </p>
                      )}
                      <div className="flex items-center justify-between mt-1">
                        <span className="text-xs text-gray-400">
                          {formatTime(notification.timestamp)}
                        </span>
                        {notification.action && (
                          <a
                            href={notification.action.href}
                            className="text-xs text-blue-600 dark:text-blue-400 hover:underline"
                            onClick={(e) => e.stopPropagation()}
                          >
                            {notification.action.label} →
                          </a>
                        )}
                      </div>
                    </div>
                    {!notification.read && (
                      <div className="flex-shrink-0 w-2 h-2 mt-2 bg-blue-500 rounded-full" />
                    )}
                  </div>
                );
              })
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-100 dark:border-slate-700 text-center">
              <button className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
                Ver histórico completo
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
