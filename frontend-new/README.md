# AI Search Platform - Frontend

A modern, neutral AI-powered document search platform built with Next.js 14, TypeScript, and Tailwind CSS.

## Features

- **Hybrid Search**: Combines TF-IDF, BM25, and Transformer models
- **Real-time Results**: Sub-2 second response times
- **Modern UI**: Clean, professional interface inspired by ChatGPT
- **TypeScript**: Full type safety across the application
- **Responsive**: Mobile-first design with Tailwind CSS

## Tech Stack

- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS + shadcn/ui
- **Icons**: Lucide React
- **HTTP Client**: Fetch API with custom client
- **Deployment**: Vercel-ready

## Quick Start

### Prerequisites
- Node.js 18+ 
- npm or yarn
- Backend API running on port 8000

### Installation

```bash
# Clone and navigate
cd frontend-new

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Update API URL in .env.local if needed
NEXT_PUBLIC_API_URL=http://localhost:8000

# Start development server
npm run dev
```

### Available Scripts

```bash
# Development
npm run dev          # Start dev server on http://localhost:3000

# Production
npm run build        # Build for production
npm run start        # Start production server

# Code Quality
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript compiler
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NODE_ENV` | Environment | `development` |

## Project Structure

```
frontend-new/
├── app/                    # Next.js App Router
│   ├── globals.css        # Global styles
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Homepage
├── components/            # Reusable components
│   ├── ui/               # Base UI components (shadcn/ui)
│   └── search-interface.tsx
├── hooks/                # Custom React hooks
├── lib/                  # Utilities and configurations
│   ├── api.ts           # API client
│   └── utils.ts         # Helper functions
├── public/              # Static assets
└── tailwind.config.js   # Tailwind configuration
```

## API Integration

The frontend communicates with the backend via a custom TypeScript client:

```typescript
import { apiClient } from '@/lib/api'

// Search documents
const results = await apiClient.search({
  query: "search term",
  method: "hybrid",
  top_k: 10
})

// Upload document
const upload = await apiClient.uploadDocument(file)

// Check system status
const status = await apiClient.getSystemStatus()
```

## Deployment

### Vercel (Recommended)

1. **Connect Repository**:
   ```bash
   # Push to GitHub
   git add .
   git commit -m "Ready for deployment"
   git push
   ```

2. **Deploy on Vercel**:
   - Go to [vercel.com](https://vercel.com)
   - Import your GitHub repository
   - Configure environment variables:
     - `NEXT_PUBLIC_API_URL`: Your backend URL
   - Deploy

3. **Environment Variables in Vercel**:
   ```
   NEXT_PUBLIC_API_URL=https://your-backend-domain.com
   NODE_ENV=production
   ```

### Other Platforms

The app is also compatible with:
- Netlify
- AWS Amplify
- Railway
- Render

## Configuration

### Tailwind Customization

Edit `tailwind.config.js` to customize colors and styles:

```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        system: {
          primary: "#1f2937",    // Professional dark gray
          secondary: "#6b7280",  // Medium gray
          accent: "#3b82f6",     // Neutral blue
        }
      }
    }
  }
}
```

### API Client Configuration

Edit `lib/api.ts` to modify API behavior:

```typescript
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
```

## Performance Optimizations

- **Next.js 14**: Latest performance improvements
- **Dynamic Imports**: Lazy loading for components
- **Image Optimization**: Built-in Next.js optimization
- **Bundle Analysis**: Run `npm run build` for insights

## Security Features

- **CSP Headers**: Content Security Policy
- **XSS Protection**: Built-in Next.js protections
- **HTTPS Enforcement**: Production redirects
- **Environment Validation**: Runtime checks

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with proper TypeScript typing
4. Test thoroughly
5. Submit a pull request

## License

Proprietary - All rights reserved

## Support

For technical support or questions:
- Check the [backend API documentation](http://localhost:8000/docs)
- Review the [deployment guide](#deployment)
- Contact the development team