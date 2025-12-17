"use client";
import { create } from "zustand";

type Role = "admin" | "user";

type AuthState = {
  token: string | null;
  role: Role | null;
  username: string | null;
  isHydrated: boolean;
  setAuth: (token: string, role: Role, username: string) => void;
  logout: () => void;
  hydrate: () => void;
};

// Função helper para carregar do localStorage
const getInitialState = () => {
  if (typeof window === "undefined") {
    return { token: null, role: null, username: null };
  }
  
  const token = localStorage.getItem("access_token");
  const role = (localStorage.getItem("role") as Role | null);
  const username = localStorage.getItem("username");
  
  return { token, role, username };
};

export const useAuth = create<AuthState>((set) => ({
  ...getInitialState(),
  isHydrated: false,
  setAuth: (token, role, username) => {
    if (typeof window !== "undefined") {
      localStorage.setItem("access_token", token);
      localStorage.setItem("role", role);
      localStorage.setItem("username", username);
    }
    set({ token, role, username, isHydrated: true });
  },
  logout: () => {
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
      localStorage.removeItem("role");
      localStorage.removeItem("username");
    }
    set({ token: null, role: null, username: null, isHydrated: true });
  },
  hydrate: () => {
    const state = getInitialState();
    set({ ...state, isHydrated: true });
  },
}));
