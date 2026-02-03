/** @type {import('next').NextConfig} */

// URL du backend - localhost:8000 en production (même conteneur)
const backendUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const nextConfig = {
  // Output standalone for Docker
  output: 'standalone',
  // Proxy API calls to backend
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${backendUrl}/:path*`,
      },
      {
        source: '/auth/:path*',
        destination: `${backendUrl}/auth/:path*`,
      },
      {
        source: '/concours/:path*',
        destination: `${backendUrl}/concours/:path*`,
      },
      {
        source: '/concours',
        destination: `${backendUrl}/concours`,
      },
      {
        source: '/health',
        destination: `${backendUrl}/health`,
      },
      {
        source: '/stats/:path*',
        destination: `${backendUrl}/stats/:path*`,
      },
      {
        source: '/calendar/:path*',
        destination: `${backendUrl}/calendar/:path*`,
      },
      {
        source: '/subscriptions/:path*',
        destination: `${backendUrl}/subscriptions/:path*`,
      },
      {
        source: '/subscriptions',
        destination: `${backendUrl}/subscriptions`,
      },
      {
        source: '/debug/:path*',
        destination: `${backendUrl}/debug/:path*`,
      },
      {
        source: '/test-:channel',
        destination: `${backendUrl}/test-:channel`,
      },
      {
        source: '/profile',
        destination: `${backendUrl}/profile`,
      },
    ]
  },
  // Service worker headers
  async headers() {
    return [
      {
        source: '/sw.js',
        headers: [
          { key: 'Service-Worker-Allowed', value: '/' },
        ],
      },
    ]
  },
}

module.exports = nextConfig
