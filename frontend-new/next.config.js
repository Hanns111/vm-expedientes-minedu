/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    appDir: true,
  },
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: process.env.NODE_ENV === 'development' 
          ? 'http://localhost:8000/:path*'
          : process.env.NEXT_PUBLIC_API_URL + '/:path*'
      }
    ]
  }
}

module.exports = nextConfig