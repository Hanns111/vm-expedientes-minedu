"use client"

import { useState } from 'react'
import { Search, FileText, Shield, BarChart3, Upload, MessageSquare, Home, Database, Activity } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { HybridSearchUI } from '@/components/HybridSearchUI'
import { DocumentUploader } from '@/components/DocumentUploader'
import { MetricsDashboard } from '@/components/MetricsDashboard'

export default function HomePage() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [activeTab, setActiveTab] = useState<'home' | 'search' | 'upload' | 'metrics'>('home')

  const handleSearch = async () => {
    if (!query.trim()) return
    
    setIsSearching(true)
    // TODO: Implementar búsqueda con API
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsSearching(false)
  }

  const features = [
    {
      icon: Search,
      title: "Hybrid Intelligent Search",
      description: "System combining TF-IDF, BM25 and Transformers with 94.2% accuracy",
      color: "text-blue-600"
    },
    {
      icon: FileText,
      title: "Document Processing",
      description: "Advanced OCR and entity extraction for complex documents",
      color: "text-green-600"
    },
    {
      icon: Shield,
      title: "Enterprise Security",
      description: "ISO27001 and NIST compliance with sensitive data protection",
      color: "text-purple-600"
    },
    {
      icon: BarChart3,
      title: "Analytics & Metrics",
      description: "Complete dashboard with real-time performance analysis",
      color: "text-orange-600"
    }
  ]

  const stats = [
    { label: "System Accuracy", value: "94.2%", color: "text-green-600" },
    { label: "Documents Processed", value: "10,000+", color: "text-blue-600" },
    { label: "Daily Queries", value: "500+", color: "text-purple-600" },
    { label: "Response Time", value: "<2s", color: "text-orange-600" }
  ]

  return (
    <div className="min-h-screen">
      {/* Header */}
      <header className="border-b bg-white sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gray-900 rounded-lg flex items-center justify-center">
              <Search className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">AI Search</h1>
              <p className="text-sm text-gray-600">Hybrid Document Platform</p>
            </div>
          </div>
          <nav className="hidden md:flex space-x-2">
            <Button 
              variant={activeTab === 'home' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('home')}
              className="flex items-center gap-2"
            >
              <Home className="w-4 h-4" />
              Inicio
            </Button>
            <Button 
              variant={activeTab === 'search' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('search')}
              className="flex items-center gap-2"
            >
              <Search className="w-4 h-4" />
              Búsqueda
            </Button>
            <Button 
              variant={activeTab === 'upload' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('upload')}
              className="flex items-center gap-2"
            >
              <Upload className="w-4 h-4" />
              Documentos
            </Button>
            <Button 
              variant={activeTab === 'metrics' ? 'default' : 'ghost'}
              onClick={() => setActiveTab('metrics')}
              className="flex items-center gap-2"
            >
              <BarChart3 className="w-4 h-4" />
              Métricas
            </Button>
          </nav>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8">
        {/* Contenido condicional basado en la tab activa */}
        {activeTab === 'home' && (
          <>
            {/* Hero Section */}
            <section className="text-center mb-16">
              <div className="max-w-4xl mx-auto">
                <h2 className="text-4xl md:text-6xl font-bold mb-6 text-gray-900">
                  Sistema de IA MINEDU
                </h2>
                <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
                  Plataforma avanzada de IA con tecnología de búsqueda híbrida. 
                  Encuentra información precisa en documentos complejos con 94.2% de precisión.
                </p>
                
                {/* Search Bar */}
                <div className="max-w-2xl mx-auto mb-8">
                  <div className="flex gap-3">
                    <div className="flex-1">
                      <Textarea
                        placeholder="¿Cuál es el monto máximo para viáticos en comisiones de servicio?"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        className="min-h-[120px] text-base"
                      />
                    </div>
                  </div>
                  <div className="flex gap-3 mt-4">
                    <Button 
                      onClick={() => setActiveTab('search')}
                      className="flex-1 h-12 bg-blue-600 hover:bg-blue-700"
                    >
                      <Search className="w-5 h-5 mr-2" />
                      Buscar con IA
                    </Button>
                    <Button 
                      variant="outline" 
                      className="h-12"
                      onClick={() => setActiveTab('upload')}
                    >
                      <Upload className="w-5 h-5 mr-2" />
                      Subir Documento
                    </Button>
                  </div>
                </div>

                {/* Quick Examples */}
                <div className="flex flex-wrap gap-2 justify-center">
                  <span className="text-sm text-gray-500">Ejemplos:</span>
                  {[
                    "¿Cuál es el procedimiento para solicitar viáticos?",
                    "Montos máximos para comisiones de servicio",
                    "Documentos requeridos para procedimientos"
                  ].map((example, i) => (
                    <Button
                      key={i}
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        setQuery(example)
                        setActiveTab('search')
                      }}
                      className="text-xs"
                    >
                      {example}
                    </Button>
                  ))}
                </div>
              </div>
            </section>

            {/* Stats Section */}
            <section className="mb-16">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
                {stats.map((stat, i) => (
                  <Card key={i} className="text-center">
                    <CardContent className="p-6">
                      <div className={`text-3xl font-bold ${stat.color} mb-2`}>
                        {stat.value}
                      </div>
                      <div className="text-sm text-gray-600">{stat.label}</div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* Features Section */}
            <section className="mb-16">
              <div className="text-center mb-12">
                <h3 className="text-3xl font-bold mb-4 text-gray-900">Tecnología Avanzada para Gobierno</h3>
                <p className="text-lg text-gray-600 max-w-2xl mx-auto">
                  Nuestro sistema híbrido combina múltiples técnicas de IA para entregar 
                  máxima precisión en recuperación de información y análisis de documentos.
                </p>
              </div>
              
              <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                {features.map((feature, i) => (
                  <Card key={i} className="group hover:shadow-lg transition-shadow duration-200">
                    <CardHeader className="text-center">
                      <div className={`w-16 h-16 mx-auto rounded-full bg-gray-100 flex items-center justify-center mb-4`}>
                        <feature.icon className={`w-8 h-8 ${feature.color}`} />
                      </div>
                      <CardTitle className="text-lg">{feature.title}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <CardDescription className="text-center">
                        {feature.description}
                      </CardDescription>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </section>

            {/* CTA Section */}
            <section className="text-center">
              <Card className="max-w-4xl mx-auto bg-gradient-to-r from-blue-600 to-purple-600 text-white">
                <CardContent className="p-12">
                  <h3 className="text-3xl font-bold mb-4">
                    ¿Listo para mejorar la eficiencia de tu organización?
                  </h3>
                  <p className="text-xl mb-8 opacity-90">
                    Únete a las organizaciones que confían en nuestra tecnología 
                    para gestión inteligente y análisis de documentos.
                  </p>
                  <div className="flex gap-4 justify-center">
                    <Button 
                      variant="outline" 
                      size="lg" 
                      className="bg-white text-gray-900 hover:bg-gray-100"
                      onClick={() => setActiveTab('search')}
                    >
                      <MessageSquare className="w-5 h-5 mr-2" />
                      Probar Sistema
                    </Button>
                    <Button 
                      variant="outline" 
                      size="lg" 
                      className="bg-transparent border-white text-white hover:bg-white/10"
                      onClick={() => setActiveTab('metrics')}
                    >
                      Ver Métricas
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </section>
          </>
        )}

        {/* Búsqueda Híbrida */}
        {activeTab === 'search' && (
          <div className="py-8">
            <HybridSearchUI />
          </div>
        )}

        {/* Subida de Documentos */}
        {activeTab === 'upload' && (
          <div className="py-8">
            <DocumentUploader />
          </div>
        )}

        {/* Dashboard de Métricas */}
        {activeTab === 'metrics' && (
          <div className="py-8">
            <MetricsDashboard />
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-20 border-t bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-gray-600">
            <p>© 2024 AI Search Platform - Hybrid Document System. All rights reserved.</p>
            <p className="text-sm mt-2">Advanced AI Technology | Powered by Hybrid Intelligence</p>
          </div>
        </div>
      </footer>
    </div>
  )
}