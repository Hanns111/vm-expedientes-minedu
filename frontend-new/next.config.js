/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    domains: ['localhost'],
  },
  async rewrites() {
    return [
      {
        source: '/api/backend/:path*',
        destination: process.env.NODE_ENV === 'development' 
          ? 'http://localhost:8001/:path*'
          : process.env.NEXT_PUBLIC_API_URL + '/:path*'
      }
    ]
  }
}

module.exports = nextConfig