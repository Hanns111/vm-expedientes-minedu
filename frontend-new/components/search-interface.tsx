"use client"

import { useState, useCallback } from 'react'
import { Search, Filter, Clock, Target, FileText, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useAPI, type SearchResponse, type SearchRequest, formatSearchTime, highlightText, truncateContent } from '@/lib/api'
import { useToast } from '@/hooks/use-toast'

interface SearchInterfaceProps {
  onResults?: (results: SearchResponse) => void
}

export function SearchInterface({ onResults }: SearchInterfaceProps) {
  const [query, setQuery] = useState('')
  const [isSearching, setIsSearching] = useState(false)
  const [results, setResults] = useState<SearchResponse | null>(null)
  const [searchMethod, setSearchMethod] = useState<SearchRequest['method']>('hybrid')
  const [error, setError] = useState<string | null>(null)
  
  const api = useAPI()
  const { toast } = useToast()

  const handleSearch = useCallback(async () => {
    if (!query.trim()) {
      toast({
        title: "Error",
        description: "Por favor ingresa una consulta",
        variant: "destructive"
      })
      return
    }

    setIsSearching(true)
    setError(null)
    
    try {
      const searchRequest: SearchRequest = {
        query: query.trim(),
        method: searchMethod,
        top_k: 10,
        fusion_method: 'weighted'
      }
      
      const response = await api.search(searchRequest)
      setResults(response)
      onResults?.(response)
      
      toast({
        title: "Búsqueda completada",
        description: `Se encontraron ${response.total_results} resultados en ${formatSearchTime(response.processing_time)}`,
        variant: "success"
      })
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Error desconocido en la búsqueda'
      setError(errorMessage)
      toast({
        title: "Error en la búsqueda",
        description: errorMessage,
        variant: "destructive"
      })
    } finally {
      setIsSearching(false)
    }
  }, [query, searchMethod, api, onResults, toast])

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
      handleSearch()
    }
  }

  const exampleQueries = [
    "What is the maximum amount for travel allowances in service commissions?",
    "What documents are required for ticket requests?",
    "What is the procedure to authorize trips abroad?",
    "How long before should I request travel allowances?"
  ]

  const methodDescriptions = {
    hybrid: "Combines multiple techniques (TF-IDF + BM25 + Transformers) for maximum precision",
    bm25: "Fast search based on statistical relevance, ideal for specific queries",
    tfidf: "Classic vector search, excellent for thematic matches",
    transformers: "Advanced semantic search using language models"
  }

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="w-5 h-5" />
            Intelligent Document Search
          </CardTitle>
          <CardDescription>
            Use our hybrid AI system to find precise information in complex documents
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Query Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Query</label>
            <Textarea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={handleKeyPress}
              placeholder="Enter your query here... (Use Ctrl+Enter to search)"
              className="min-h-[100px] resize-none"
              disabled={isSearching}
            />
            <p className="text-xs text-gray-500">
              💡 Tip: Be specific in your query for better results
            </p>
          </div>

          {/* Search Method Selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium flex items-center gap-2">
              <Filter className="w-4 h-4" />
              Search Method
            </label>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2">
              {(Object.keys(methodDescriptions) as Array<keyof typeof methodDescriptions>).map((method) => (
                <Button
                  key={method}
                  variant={searchMethod === method ? "system" : "outline"}
                  size="sm"
                  onClick={() => setSearchMethod(method)}
                  disabled={isSearching}
                  className="justify-start text-left h-auto p-3"
                >
                  <div>
                    <div className="font-medium text-xs uppercase tracking-wider">
                      {method}
                    </div>
                    <div className="text-xs opacity-75 mt-1 leading-tight">
                      {method === 'hybrid' && "Recommended"}
                      {method === 'bm25' && "Fast"}
                      {method === 'tfidf' && "Classic"}
                      {method === 'transformers' && "Semantic"}
                    </div>
                  </div>
                </Button>
              ))}
            </div>
            <p className="text-xs text-gray-600">
              {methodDescriptions[searchMethod]}
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button 
              onClick={handleSearch}
              disabled={isSearching || !query.trim()}
              className="flex-1 h-12"
              variant="system"
            >
              {isSearching ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Searching...
                </>
              ) : (
                <>
                  <Search className="w-5 h-5 mr-2" />
                  Search with AI
                </>
              )}
            </Button>
          </div>

          {/* Example Queries */}
          <div className="space-y-2">
            <label className="text-sm font-medium">Example queries:</label>
            <div className="flex flex-wrap gap-2">
              {exampleQueries.map((example, i) => (
                <Button
                  key={i}
                  variant="outline"
                  size="sm"
                  onClick={() => setQuery(example)}
                  disabled={isSearching}
                  className="text-xs h-auto py-2 px-3 text-left"
                >
                  {truncateContent(example, 60)}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="w-5 h-5" />
              <span className="font-medium">Error en la búsqueda</span>
            </div>
            <p className="text-red-600 mt-2">{error}</p>
          </CardContent>
        </Card>
      )}

      {/* Results Display */}
      {results && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Target className="w-5 h-5" />
                Resultados de Búsqueda
              </span>
              <div className="flex items-center gap-4 text-sm text-gray-600">
                <span className="flex items-center gap-1">
                  <Clock className="w-4 h-4" />
                  {formatSearchTime(results.processing_time)}
                </span>
                <span className="bg-minedu-primary text-white px-2 py-1 rounded text-xs">
                  {results.total_results} resultados
                </span>
              </div>
            </CardTitle>
            <CardDescription>
              Método: {results.method.toUpperCase()} • Consulta: "{results.query}"
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {results.results.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>No se encontraron resultados para tu consulta.</p>
                <p className="text-sm mt-2">Intenta con palabras clave diferentes o usa el método híbrido.</p>
              </div>
            ) : (
              results.results.map((result, index) => (
                <Card key={index} className="border-l-4 border-l-minedu-primary">
                  <CardContent className="p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="bg-minedu-primary text-white text-xs px-2 py-1 rounded">
                          #{index + 1}
                        </span>
                        <span className="text-sm text-gray-600">
                          Score: {(result.score * 100).toFixed(1)}%
                        </span>
                      </div>
                      {result.metadata.source_document && (
                        <div className="text-xs text-gray-500">
                          📄 {result.metadata.source_document}
                          {result.metadata.page_number && ` (pág. ${result.metadata.page_number})`}
                        </div>
                      )}
                    </div>
                    <div 
                      className="text-sm leading-relaxed"
                      dangerouslySetInnerHTML={{ 
                        __html: highlightText(result.content, results.query) 
                      }}
                    />
                    {result.metadata.section && (
                      <div className="mt-2 text-xs text-gray-500">
                        📍 Sección: {result.metadata.section}
                      </div>
                    )}
                  </CardContent>
                </Card>
              ))
            )}
          </CardContent>
        </Card>
      )}
    </div>
  )
}