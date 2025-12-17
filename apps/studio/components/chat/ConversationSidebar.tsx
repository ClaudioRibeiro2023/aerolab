"use client";

import React, { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useChatStore, type Conversation } from "../../store/chat";

interface ConversationSidebarProps {
  isOpen: boolean;
  onClose: () => void;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
}

interface ConversationItemProps {
  conv: Conversation;
  isActive: boolean;
  isEditing: boolean;
  editTitle: string;
  onSelect: (id: string) => void;
  onDelete: (e: React.MouseEvent, id: string) => void;
  onPin: (e: React.MouseEvent, id: string) => void;
  onStartEdit: (e: React.MouseEvent, conv: Conversation) => void;
  onEditChange: (value: string) => void;
  onSaveTitle: (id: string) => void;
  onCancelEdit: () => void;
}

function ConversationItem({
  conv,
  isActive,
  isEditing,
  editTitle,
  onSelect,
  onDelete,
  onPin,
  onStartEdit,
  onEditChange,
  onSaveTitle,
  onCancelEdit,
}: ConversationItemProps) {
  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      onClick={() => onSelect(conv.id)}
      className={`group relative flex items-center gap-2 px-3 py-2.5 rounded-lg cursor-pointer transition-all ${
        isActive
          ? "bg-blue-600/20 border border-blue-500/30"
          : "hover:bg-slate-800/50"
      }`}
    >
      <div
        className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
          isActive ? "bg-blue-600 text-white" : "bg-slate-700 text-slate-400"
        }`}
      >
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
          />
        </svg>
      </div>

      <div className="flex-1 min-w-0">
        {isEditing ? (
          <input
            type="text"
            value={editTitle}
            onChange={(e) => onEditChange(e.target.value)}
            onBlur={() => onSaveTitle(conv.id)}
            onKeyDown={(e) => {
              if (e.key === "Enter") onSaveTitle(conv.id);
              if (e.key === "Escape") onCancelEdit();
            }}
            onClick={(e) => e.stopPropagation()}
            autoFocus
            placeholder="Nome da conversa"
            className="w-full bg-slate-700 text-white text-sm px-2 py-1 rounded border border-blue-500 focus:outline-none"
          />
        ) : (
          <>
            <p className="text-sm font-medium text-slate-200 truncate">{conv.title}</p>
            <p className="text-xs text-slate-500 truncate">
              {conv.agentName || "Chat"} • {conv.messages.length} msg
            </p>
          </>
        )}
      </div>

      <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {conv.pinned && <span className="text-yellow-500 text-xs">📌</span>}
        <button
          onClick={(e) => onPin(e, conv.id)}
          className="p-1 text-slate-500 hover:text-yellow-500 rounded"
          title={conv.pinned ? "Desafixar" : "Fixar"}
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
          </svg>
        </button>
        <button
          onClick={(e) => onStartEdit(e, conv)}
          className="p-1 text-slate-500 hover:text-blue-400 rounded"
          title="Renomear"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
          </svg>
        </button>
        <button
          onClick={(e) => onDelete(e, conv.id)}
          className="p-1 text-slate-500 hover:text-red-400 rounded"
          title="Excluir"
        >
          <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>
    </motion.div>
  );
}


export default function ConversationSidebar({
  isOpen,
  onClose,
  onSelectConversation,
  onNewConversation,
}: ConversationSidebarProps) {
  const {
    conversations,
    activeConversationId,
    setActiveConversation,
    deleteConversation,
    togglePin,
    updateConversationTitle,
  } = useChatStore();

  const [searchQuery, setSearchQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState("");

  // Group conversations
  const { pinned, today, yesterday, older } = useMemo(() => {
    const now = new Date();
    const todayStart = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterdayStart = new Date(todayStart.getTime() - 24 * 60 * 60 * 1000);

    const allConversations = Object.values(conversations)
      .filter((c) => !c.archived)
      .filter((c) =>
        searchQuery
          ? c.title.toLowerCase().includes(searchQuery.toLowerCase())
          : true
      )
      .sort((a, b) => new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime());

    return {
      pinned: allConversations.filter((c) => c.pinned),
      today: allConversations.filter(
        (c) => !c.pinned && new Date(c.updatedAt) >= todayStart
      ),
      yesterday: allConversations.filter(
        (c) =>
          !c.pinned &&
          new Date(c.updatedAt) >= yesterdayStart &&
          new Date(c.updatedAt) < todayStart
      ),
      older: allConversations.filter(
        (c) => !c.pinned && new Date(c.updatedAt) < yesterdayStart
      ),
    };
  }, [conversations, searchQuery]);

  const handleSelect = (id: string) => {
    setActiveConversation(id);
    onSelectConversation(id);
  };

  const handleDelete = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    if (confirm("Excluir esta conversa?")) {
      deleteConversation(id);
    }
  };

  const handlePin = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    togglePin(id);
  };

  const startEditing = (e: React.MouseEvent, conv: Conversation) => {
    e.stopPropagation();
    setEditingId(conv.id);
    setEditTitle(conv.title);
  };

  const saveTitle = (id: string) => {
    if (editTitle.trim()) {
      updateConversationTitle(id, editTitle.trim());
    }
    setEditingId(null);
  };

  const renderSection = (title: string, icon: string, items: Conversation[]) => {
    if (items.length === 0) return null;

    return (
      <div className="mb-4">
        <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider px-3 mb-2 flex items-center gap-2">
          <span>{icon}</span>
          {title}
          <span className="text-slate-600">({items.length})</span>
        </h3>
        <div className="space-y-1">
          <AnimatePresence>
            {items.map((conv) => (
              <ConversationItem
                key={conv.id}
                conv={conv}
                isActive={conv.id === activeConversationId}
                isEditing={editingId === conv.id}
                editTitle={editTitle}
                onSelect={handleSelect}
                onDelete={handleDelete}
                onPin={handlePin}
                onStartEdit={startEditing}
                onEditChange={setEditTitle}
                onSaveTitle={saveTitle}
                onCancelEdit={() => setEditingId(null)}
              />
            ))}
          </AnimatePresence>
        </div>
      </div>
    );
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          />

          {/* Sidebar */}
          <motion.div
            initial={{ x: -320 }}
            animate={{ x: 0 }}
            exit={{ x: -320 }}
            transition={{ type: "spring", damping: 25, stiffness: 200 }}
            className="fixed left-0 top-0 bottom-0 w-80 bg-slate-900 border-r border-slate-800 z-50 flex flex-col"
          >
            {/* Header */}
            <div className="p-4 border-b border-slate-800">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-white">Conversas</h2>
                <button
                  onClick={onClose}
                  className="p-2 text-slate-400 hover:text-white hover:bg-slate-800 rounded-lg transition-colors lg:hidden"
                >
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* New Conversation Button */}
              <button
                onClick={onNewConversation}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Nova Conversa
              </button>

              {/* Search */}
              <div className="mt-3 relative">
                <svg
                  className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                <input
                  type="text"
                  placeholder="Buscar conversas..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
                />
              </div>
            </div>

            {/* Conversations List */}
            <div className="flex-1 overflow-y-auto p-3">
              {Object.keys(conversations).length === 0 ? (
                <div className="text-center py-8">
                  <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-slate-800 flex items-center justify-center">
                    <svg className="w-8 h-8 text-slate-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                      />
                    </svg>
                  </div>
                  <p className="text-slate-400 text-sm">Nenhuma conversa ainda</p>
                  <p className="text-slate-500 text-xs mt-1">
                    Clique em "Nova Conversa" para começar
                  </p>
                </div>
              ) : (
                <>
                  {renderSection("Fixadas", "📌", pinned)}
                  {renderSection("Hoje", "📅", today)}
                  {renderSection("Ontem", "🕐", yesterday)}
                  {renderSection("Anteriores", "📁", older)}
                </>
              )}
            </div>

            {/* Footer */}
            <div className="p-3 border-t border-slate-800">
              <div className="flex items-center justify-between text-xs text-slate-500">
                <span>{Object.keys(conversations).length} conversas</span>
                <span>
                  {Object.values(conversations).reduce(
                    (acc, c) => acc + c.messages.length,
                    0
                  )}{" "}
                  mensagens
                </span>
              </div>
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
