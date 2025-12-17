import "./globals.css";
import React from "react";
import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import QueryProvider from "../providers/QueryProvider";
import { ThemeProvider } from "../providers/ThemeProvider";
import AppLayout from "../components/AppLayout";
import CommandPalette from "../components/CommandPalette";
import OnboardingWizard from "../components/OnboardingWizard";
import { Toaster } from "sonner";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  metadataBase: new URL(process.env.NEXT_PUBLIC_BASE_URL || "https://agno-multi-agent.netlify.app"),
  title: {
    default: "Agno Platform",
    template: "%s | Agno",
  },
  description: "Plataforma Multi-Agente de IA - Orquestre agentes inteligentes, automatize workflows e potencialize sua equipe com IA.",
  keywords: ["IA", "Agentes", "Multi-Agente", "Automação", "Workflow", "RAG", "LLM", "ChatGPT", "Claude"],
  authors: [{ name: "Agno Team" }],
  creator: "Agno",
  publisher: "Agno",
  robots: "index, follow",
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon.ico", sizes: "32x32" },
    ],
    apple: "/apple-touch-icon.png",
  },
  manifest: "/manifest.json",
  openGraph: {
    type: "website",
    locale: "pt_BR",
    url: "https://agno-multi-agent.netlify.app",
    siteName: "Agno Platform",
    title: "Agno Platform - Plataforma Multi-Agente de IA",
    description: "Orquestre agentes inteligentes, automatize workflows e potencialize sua equipe com IA.",
    images: [{ url: "/og-image.png", width: 1200, height: 630, alt: "Agno Platform" }],
  },
  twitter: {
    card: "summary_large_image",
    title: "Agno Platform",
    description: "Plataforma Multi-Agente de IA",
    images: ["/og-image.png"],
  },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#ffffff" },
    { media: "(prefers-color-scheme: dark)", color: "#0f172a" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="pt-br" className={inter.className} suppressHydrationWarning>
      <body className="min-h-screen bg-gray-50 dark:bg-slate-900 text-gray-900 dark:text-gray-100 antialiased transition-colors">
        <ThemeProvider>
          <QueryProvider>
            <Toaster richColors position="top-right" />
            <CommandPalette />
            <OnboardingWizard />
            <AppLayout>{children}</AppLayout>
          </QueryProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
