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
  // Proxy API requests to backend
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    return [
      {
        source: "/api/:path*",
        destination: `${apiUrl}/:path*`,
      },
    ];
  },
};
export default nextConfig;
