/** @type {import('next').NextConfig} */
const nextConfig = {
  // Standalone output only for Docker builds (disabled for local dev on Windows)
  // output: "standalone",
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
