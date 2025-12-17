"use client";
import React from "react";
import Link from "next/link";
import { useAuth } from "../store/auth";
import { Button } from "./ui/button";

export default function NavBar() {
  const { token, username, role, logout } = useAuth();
  const appName = process.env.NEXT_PUBLIC_APP_NAME || "Agno Agents UI";
  return (
    <header className="border-b bg-white">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link href="/" className="font-semibold">
            {appName}
          </Link>
          {token && (
            <nav className="text-sm text-gray-600 hidden sm:flex gap-3">
              <Link href="/dashboard">Dashboard</Link>
              <Link href="/agents">Agents</Link>
              <Link href="/teams">Teams</Link>
              <Link href="/workflows">Workflows</Link>
              <Link href="/editor">Editor</Link>
              <Link href="/rag/query">RAG Query</Link>
              <Link href="/rag/collections">RAG Collections</Link>
              {role === "admin" && <Link href="/rag/ingest">RAG Ingest</Link>}
              <Link href="/hitl">HITL</Link>
            </nav>
          )}
        </div>
        <div className="flex items-center gap-2 text-sm">
          {token ? (
            <>
              <span className="hidden sm:inline text-gray-600">{username} · {role}</span>
              <Button variant="outline" onClick={logout}>Sair</Button>
            </>
          ) : (
            <Link href="/">Entrar</Link>
          )}
        </div>
      </div>
    </header>
  );
}
