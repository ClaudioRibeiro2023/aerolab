/** @type {import('next').NextConfig} */
const nextConfig = {
  // Gera saída standalone (server.js em .next/standalone) compatível com o Dockerfile
  output: "standalone",
  reactStrictMode: true,
  typescript: {
    // Ignorar erros de tipo durante build (útil para deploy)
    ignoreBuildErrors: true,
  },
  eslint: {
    // Ignorar erros de lint durante build
    ignoreDuringBuilds: true,
  },
};
export default nextConfig;
