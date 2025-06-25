import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { MessageSquare, Settings, BookOpen } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            🏛️ Sistema de IA Gubernamental
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Plataforma híbrida de IA para procesamiento de documentos gubernamentales
            con Next.js, FastAPI y Multi-LLM Router
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-6 w-6 text-blue-600" />
                Chat IA
              </CardTitle>
              <CardDescription>
                Interfaz de chat con streaming usando Vercel AI SDK
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/chat">
                <Button className="w-full">
                  Iniciar Chat
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="h-6 w-6 text-green-600" />
                Administración
              </CardTitle>
              <CardDescription>
                Dashboard para gestionar plugins, modelos y métricas
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Link href="/admin">
                <Button variant="outline" className="w-full">
                  Panel Admin
                </Button>
              </Link>
            </CardContent>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-6 w-6 text-purple-600" />
                Documentación
              </CardTitle>
              <CardDescription>
                Guías de uso y documentación técnica
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Button variant="secondary" className="w-full">
                Ver Docs
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="mt-16 text-center">
          <div className="inline-flex items-center gap-4 bg-white rounded-lg px-6 py-3 shadow-md">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse"></div>
              <span className="text-sm font-medium">Sistema Activo</span>
            </div>
            <div className="text-sm text-gray-500">|</div>
            <div className="text-sm text-gray-600">
              Frontend: Next.js 14 | Backend: FastAPI | AI: Multi-LLM Router
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}