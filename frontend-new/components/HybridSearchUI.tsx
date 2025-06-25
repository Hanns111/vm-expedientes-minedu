'use client'

import React, { useState, useEffect } from 'react'
import { Search, Clock, Target, Layers, Filter, Copy, ExternalLink } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { useToast } from '../hooks/use-toast'
import { apiClient, SearchResponse, SearchResult, formatSearchTime, highlightText, truncateContent } from '../lib/api'

interface SearchHistory {
  query: string
  timestamp: string
  method: string
  resultsCount: number
  processingTime: number
}

export function HybridSearchUI() {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [searchResults, setSearchResults] = useState<SearchResponse | null>(null)
  const [searchMethod, setSearchMethod] = useState<'hybrid' | 'bm25' | 'tfidf' | 'transformers'>('hybrid')
  const [searchHistory, setSearchHistory] = useState<SearchHistory[]>([])
  const { toast } = useToast()

  // Consultas de ejemplo para MINEDU
  const exampleQueries = [
    "¿Cuál es el monto máximo para viáticos?",
    "¿Qué documentos requiere la solicitud de licencia?",
    "¿Cuál es el procedimiento para declaración jurada?",
    "¿Cuánto tiempo antes debo solicitar permisos?",
    "Monto máximo para gastos de representación"
  ]

  const performSearch = async (searchQuery: string = query) => {
    if (!searchQuery.trim()) {
      toast({
        title: "Query vacío",
        description: "Por favor ingresa una consulta para buscar.",
        variant: "destructive",
      })
      return
    }

    setIsSearching(true)
    
    try {
      const startTime = Date.now()
      let response: SearchResponse

      // Ejecutar búsqueda según el método seleccionado
      switch (searchMethod) {
        case 'hybrid':
          response = await apiClient.hybridSearch(searchQuery)
          break
        case 'bm25':
          const bm25Results = await apiClient.search({ query: searchQuery, method: 'bm25' })
          response = bm25Results
          break
        case 'tfidf':
          const tfidfResults = await apiClient.search({ query: searchQuery, method: 'tfidf' })
          response = tfidfResults
          break
        case 'transformers':
          const transformerResults = await apiClient.search({ query: searchQuery, method: 'transformers' })
          response = transformerResults
          break
        default:
          response = await apiClient.hybridSearch(searchQuery)
      }

      const endTime = Date.now()
      const processingTime = endTime - startTime

      setSearchResults(response)
      
      // Agregar a historial
      const historyEntry: SearchHistory = {
        query: searchQuery,
        timestamp: new Date().toLocaleString(),
        method: searchMethod,
        resultsCount: response.results.length,
        processingTime: response.processing_time || processingTime / 1000
      }
      
      setSearchHistory(prev => [historyEntry, ...prev.slice(0, 9)]) // Mantener solo 10 entradas

      toast({
        title: "Búsqueda completada",
        description: `${response.results.length} resultados encontrados en ${formatSearchTime(response.processing_time * 1000 || processingTime)}.`,
      })

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido'
      toast({
        title: "Error en la búsqueda",
        description: errorMessage,
        variant: "destructive",
      })
      setSearchResults(null)
    } finally {
      setIsSearching(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      performSearch()
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: "Copiado",
      description: "El contenido se ha copiado al portapapeles.",
    })
  }

  const getMethodBadgeColor = (method: string) => {
    switch (method) {
      case 'hybrid':
        return 'bg-purple-100 text-purple-800 border-purple-200'
      case 'bm25':
        return 'bg-blue-100 text-blue-800 border-blue-200'
      case 'tfidf':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'transformers':
        return 'bg-orange-100 text-orange-800 border-orange-200'
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-50'
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-50'
    return 'text-red-600 bg-red-50'
  }

  return (
    <div className="w-full max-w-6xl mx-auto space-y-6">
      {/* Interfaz de búsqueda */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-6 w-6" />
            Búsqueda Híbrida MINEDU
          </CardTitle>
          <CardDescription>
            Sistema de búsqueda inteligente con IA para documentos administrativos
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-4">
          {/* Selector de método de búsqueda */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-medium">Método:</span>
            {(['hybrid', 'bm25', 'tfidf', 'transformers'] as const).map((method) => (
              <Button
                key={method}
                variant={searchMethod === method ? "default" : "outline"}
                size="sm"
                onClick={() => setSearchMethod(method)}
                className={`text-xs ${searchMethod === method ? 'bg-blue-600' : ''}`}
              >
                {method.toUpperCase()}
              </Button>
            ))}
          </div>

          {/* Campo de búsqueda */}
          <div className="flex gap-2">
            <Textarea
              placeholder="Ej: ¿Cuál es el monto máximo para viáticos de funcionarios?"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={handleKeyPress}
              className="min-h-[80px] resize-none"
              disabled={isSearching}
            />
            <Button
              onClick={() => performSearch()}
              disabled={isSearching || !query.trim()}
              className="bg-blue-600 hover:bg-blue-700 px-6"
            >
              {isSearching ? (
                <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
              ) : (
                <Search className="h-4 w-4" />
              )}
            </Button>
          </div>

          {/* Consultas de ejemplo */}
          <div className="space-y-2">
            <p className="text-sm font-medium text-gray-700">Consultas de ejemplo:</p>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.map((exampleQuery, index) => (
                <Button
                  key={index}
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setQuery(exampleQuery)
                    performSearch(exampleQuery)
                  }}
                  className="text-xs text-blue-600 border-blue-200 hover:bg-blue-50"
                  disabled={isSearching}
                >
                  {truncateContent(exampleQuery, 50)}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Resultados de búsqueda */}
      {searchResults && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5" />
                Resultados ({searchResults.total_results})
              </CardTitle>
              <div className="flex items-center gap-2">
                <span className={`px-2 py-1 text-xs rounded-md border ${getMethodBadgeColor(searchResults.method)}`}>
                  {searchResults.method.toUpperCase()}
                </span>
                <span className="text-sm text-gray-500">
                  {formatSearchTime(searchResults.processing_time * 1000)}
                </span>
              </div>
            </div>
            <CardDescription>
              Consulta: "{searchResults.query}"
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {searchResults.results.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Search className="h-12 w-12 mx-auto mb-4 opacity-50" />
                <p>No se encontraron resultados para esta consulta.</p>
                <p className="text-sm">Prueba con diferentes términos o utiliza otro método de búsqueda.</p>
              </div>
            ) : (
              <div className="space-y-4">
                {searchResults.results.map((result, index) => (
                  <Card key={index} className="border-l-4 border-l-blue-500">
                    <CardContent className="pt-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className={`px-2 py-1 text-xs rounded-md ${getScoreColor(result.score)}`}>
                              Score: {(result.score * 100).toFixed(1)}%
                            </span>
                            {result.metadata.source_document && (
                              <span className="text-xs text-gray-500">
                                📄 {result.metadata.source_document}
                              </span>
                            )}
                            {result.metadata.page_number && (
                              <span className="text-xs text-gray-500">
                                Página {result.metadata.page_number}
                              </span>
                            )}
                          </div>
                          
                          <div 
                            className="text-gray-800 leading-relaxed"
                            dangerouslySetInnerHTML={{ 
                              __html: highlightText(truncateContent(result.content, 400), searchResults.query) 
                            }}
                          />
                          
                          {result.metadata.section && (
                            <div className="mt-2 text-xs text-gray-600">
                              Sección: {result.metadata.section}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex flex-col gap-1">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(result.content)}
                            title="Copiar contenido"
                          >
                            <Copy className="h-4 w-4" />
                          </Button>
                          {result.metadata.chunk_id && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => copyToClipboard(result.metadata.chunk_id)}
                              title="Copiar ID del fragmento"
                            >
                              <ExternalLink className="h-4 w-4" />
                            </Button>
                          )}
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Historial de búsquedas */}
      {searchHistory.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Historial de Búsquedas
            </CardTitle>
          </CardHeader>
          
          <CardContent>
            <div className="space-y-2">
              {searchHistory.map((entry, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer transition-colors"
                  onClick={() => {
                    setQuery(entry.query)
                    setSearchMethod(entry.method as any)
                  }}
                >
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {truncateContent(entry.query, 60)}
                    </p>
                    <p className="text-xs text-gray-500">
                      {entry.timestamp} • {entry.resultsCount} resultados • {formatSearchTime(entry.processingTime * 1000)}
                    </p>
                  </div>
                  <span className={`px-2 py-1 text-xs rounded-md border ${getMethodBadgeColor(entry.method)}`}>
                    {entry.method.toUpperCase()}
                  </span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}