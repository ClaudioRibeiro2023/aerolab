"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import api from "../lib/api";
import { useAuth } from "../store/auth";
import { toast } from "sonner";

export default function HomePage() {
  const { token, setAuth } = useAuth();
  const router = useRouter();
  const [uname, setUname] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== "undefined" && !token) {
      const t = localStorage.getItem("access_token");
      const r = (localStorage.getItem("role") as "admin" | "user" | null) || null;
      const u = localStorage.getItem("username");
      if (t && r && u) setAuth(t, r, u);
    }
  }, [token, setAuth]);

  useEffect(() => {
    if (token) {
      router.replace("/dashboard");
    }
  }, [token, router]);

  const onLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.post("/auth/login", { username: uname });
      const t = res.data.access_token as string;
      const rl = (res.data.role as "admin" | "user") ?? "user";
      setAuth(t, rl, uname);
      toast.success("Login realizado com sucesso!");
      router.replace("/dashboard");
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Falha no login");
      toast.error(err?.response?.data?.detail || "Falha no login");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex">
      {/* Left Side - Branding */}
      <div className="hidden lg:flex lg:w-1/2 bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 p-12 flex-col justify-between">
        <div>
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center backdrop-blur-sm">
              <span className="text-white font-bold text-xl">AL</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-white">AeroLab</h1>
              <p className="text-blue-200 text-sm">AI Platform</p>
            </div>
          </div>
        </div>
        
        <div className="space-y-6">
          <h2 className="text-4xl font-bold text-white leading-tight">
            Plataforma de<br />Agentes de IA
          </h2>
          <p className="text-blue-100 text-lg max-w-md">
            Crie, gerencie e orquestre agentes de inteligência artificial para automatizar seus processos.
          </p>
          
          <div className="grid grid-cols-2 gap-4 pt-4">
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-white">25+</div>
              <div className="text-blue-200 text-sm">Ferramentas</div>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-white">6</div>
              <div className="text-blue-200 text-sm">Domínios</div>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-white">9+</div>
              <div className="text-blue-200 text-sm">APIs Integradas</div>
            </div>
            <div className="bg-white/10 rounded-xl p-4 backdrop-blur-sm">
              <div className="text-3xl font-bold text-white">∞</div>
              <div className="text-blue-200 text-sm">Possibilidades</div>
            </div>
          </div>
        </div>
        
        <div className="text-blue-200 text-sm">
          © 2025 AeroLab. Todos os direitos reservados.
        </div>
      </div>

      {/* Right Side - Login Form */}
      <div className="flex-1 flex items-center justify-center p-8 bg-gray-50">
        <div className="w-full max-w-md">
          {/* Mobile Logo */}
          <div className="lg:hidden flex items-center justify-center gap-3 mb-8">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/25">
              <span className="text-white font-bold text-xl">AL</span>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">AeroLab</h1>
              <p className="text-gray-500 text-sm">AI Platform</p>
            </div>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8 border border-gray-100">
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900">Bem-vindo</h2>
              <p className="text-gray-500 mt-2">Entre para acessar a plataforma</p>
            </div>

            <form onSubmit={onLogin} className="space-y-6">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-2">
                  Usuário
                </label>
                <input
                  id="username"
                  type="text"
                  value={uname}
                  onChange={(e) => setUname(e.target.value)}
                  required
                  placeholder="admin"
                  className="input-modern"
                />
              </div>

              {error && (
                <div className="bg-red-50 text-red-600 px-4 py-3 rounded-xl text-sm flex items-center gap-2">
                  <svg className="w-5 h-5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="btn-primary w-full"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Entrando...
                  </span>
                ) : (
                  "Entrar"
                )}
              </button>
            </form>

            <div className="mt-6 pt-6 border-t border-gray-100">
              <p className="text-center text-sm text-gray-500">
                Use <span className="font-medium text-gray-700">admin</span> para acesso administrativo
              </p>
            </div>
          </div>

          <p className="text-center text-xs text-gray-400 mt-6">
            Conectado à API: {process.env.NEXT_PUBLIC_API_URL || process.env.NEXT_PUBLIC_AGENTOS_API_BASE || "localhost"}
          </p>
        </div>
      </div>
    </div>
  );
}
