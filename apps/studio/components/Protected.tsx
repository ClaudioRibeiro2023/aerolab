"use client";
import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "../store/auth";

export default function Protected({ children }: { children: React.ReactNode }) {
  const { token, isHydrated, hydrate } = useAuth();
  const router = useRouter();
  const [isReady, setIsReady] = useState(false);

  // Hidratar estado do auth
  useEffect(() => {
    if (!isHydrated) {
      hydrate();
    } else {
      setIsReady(true);
    }
  }, [isHydrated, hydrate]);

  // Verificar token (só após hidratação)
  useEffect(() => {
    if (isHydrated && !token && typeof window !== "undefined") {
      router.replace("/");
    }
  }, [token, router, isHydrated]);

  // Mostrar loading enquanto hidrata
  if (!isReady || !isHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!token) return null;
  return <>{children}</>;
}
