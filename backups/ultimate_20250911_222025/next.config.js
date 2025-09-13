/**
 * Sophia sophia-intel-app Next.js configuration
 * - Adds no-cache headers to avoid stale UI assets during active development
 * - Keep minimal to avoid conflicts with existing setup
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable standalone output for Docker multi-stage builds
  output: 'standalone',
  experimental: {
    // Ensure PWA SW can control all pages quickly in dev/prod
    swcMinify: true,
  },
  
  async headers() {
    return [
      {
        source: '/:path*',
        headers: [
          { key: 'Cache-Control', value: 'no-cache, no-store, must-revalidate' },
          { key: 'Pragma', value: 'no-cache' },
          { key: 'Expires', value: '0' },
        ],
      },
    ]
  },
  async rewrites() {
    // Proxy /api/* to the backend in dev/server mode.
    // Default points to localhost for native dev; override with API_BASE_URL (e.g., http://bridge:8003) inside Docker.
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8000'
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/:path*`,
      },
      {
        // Proxy WebSocket paths to API as well (Next dev server supports WS upgrade)
        source: '/ws/:path*',
        destination: `${apiBase}/ws/:path*`,
      },
    ]
  },
}

module.exports = nextConfig;
