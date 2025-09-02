import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  devIndicators: false,
  async rewrites() {
    // In development, proxy /api/* to the backend server
    const apiBase = process.env.API_BASE_URL || 'http://localhost:8003'
    return [
      {
        source: '/api/:path*',
        destination: `${apiBase}/:path*`
      }
    ]
  }
}

export default nextConfig
