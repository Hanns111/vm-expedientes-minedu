'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Search, Clock, Target, Copy, ChevronDown, Sparkles, FileText, Zap } from 'lucide-react'
import { Card, CardContent } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { useToast } from '../hooks/use-toast'
import { apiClient, SearchResponse, formatSearchTime } from '../lib/api'

interface Message {
  id: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  searchResults?: SearchResponse
  isLoading?: boolean
}

interface QuickAction {
  icon: React.ReactNode
  label: string
  query: string
  color: string
}

export function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'system',
      content: '¡Hola! Soy el asistente de IA del MINEDU. Puedo ayudarte a buscar información en documentos administrativos y educativos. ¿En qué puedo asistirte hoy?',
      timestamp: new Date()
    }
  ])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [searchMethod, setSearchMethod] = useState<'hybrid' | 'bm25' | 'tfidf' | 'transformers'>('hybrid')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const { toast } = useToast()

  // Acciones rápidas para MINEDU
  const quickActions: QuickAction[] = [
    {
      icon: <FileText className="h-4 w-4" />,
      label: "Viáticos",
      query: "¿Cuál es el monto máximo para viáticos?",
      color: "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100"
    },
    {
      icon: <Target className="h-4 w-4" />,
      label: "Procedimientos",
      query: "¿Cuál es el procedimiento para declaración jurada?",
      color: "bg-green-50 text-green-700 border-green-200 hover:bg-green-100"
    },
    {
      icon: <Clock className="h-4 w-4" />,
      label: "Tiempos",
      query: "¿Cuánto tiempo antes debo solicitar permisos?",
      color: "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100"
    },
    {
      icon: <Search className="h-4 w-4" />,
      label: "Documentos",
      query: "¿Qué documentos requiere la solicitud de licencia?",
      color: "bg-orange-50 text-orange-700 border-orange-200 hover:bg-orange-100"
    }
  ]

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async (message: string = inputValue) => {
    if (!message.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: message,
      timestamp: new Date()
    }

    const loadingMessage: Message = {
      id: (Date.now() + 1).toString(),
      type: 'assistant',
      content: 'Buscando información...',
      timestamp: new Date(),
      isLoading: true
    }

    setMessages(prev => [...prev, userMessage, loadingMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      const startTime = Date.now()
      const response = await apiClient.hybridSearch(message, { method: searchMethod })
      const endTime = Date.now()

      // Crear respuesta formateada
      let responseContent = ''
      if (response.results.length > 0) {
        responseContent = `Encontré ${response.results.length} resultado${response.results.length > 1 ? 's' : ''} relevante${response.results.length > 1 ? 's' : ''} para tu consulta sobre "${message}".\n\n`
        
        if (response.results.length > 0) {
          const topResult = response.results[0]
          responseContent += `**Resultado principal:**\n${topResult.content.slice(0, 300)}${topResult.content.length > 300 ? '...' : ''}\n\n`
          responseContent += `📊 *Puntuación: ${(topResult.score * 100).toFixed(1)}% | Método: ${response.method.toUpperCase()} | Tiempo: ${formatSearchTime(response.processing_time * 1000)}*`
        }
      } else {
        responseContent = `No encontré resultados específicos para "${message}". Puedes intentar reformular tu pregunta o usar términos más generales. ¿Te gustaría que busque algo relacionado?`
      }

      const assistantMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: 'assistant',
        content: responseContent,
        timestamp: new Date(),
        searchResults: response
      }

      setMessages(prev => prev.slice(0, -1).concat(assistantMessage))

      toast({
        title: "Búsqueda completada",
        description: `${response.results.length} resultados en ${formatSearchTime((endTime - startTime))}`
      })

    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 2).toString(),
        type: 'assistant',
        content: `❌ Lo siento, hubo un error al procesar tu consulta: ${error instanceof Error ? error.message : 'Error desconocido'}. Por favor, inténtalo nuevamente.`,
        timestamp: new Date()
      }

      setMessages(prev => prev.slice(0, -1).concat(errorMessage))
      
      toast({
        title: "Error en la búsqueda",
        description: "Hubo un problema al conectar con el servidor",
        variant: "destructive"
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleQuickAction = (action: QuickAction) => {
    handleSendMessage(action.query)
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    toast({
      title: "Copiado",
      description: "El contenido se ha copiado al portapapeles"
    })
  }

  return (
    <div className="flex flex-col h-[80vh] max-w-4xl mx-auto bg-white rounded-lg shadow-lg overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-4">
        <div className="flex items-center gap-3">
          <div className="bg-white/20 p-2 rounded-lg">
            <Bot className="h-6 w-6" />
          </div>
          <div>
            <h2 className="text-lg font-semibold">Asistente MINEDU IA</h2>
            <p className="text-blue-100 text-sm">Sistema de búsqueda híbrida • {searchMethod.toUpperCase()}</p>
          </div>
          <div className="ml-auto flex gap-2">
            {(['hybrid', 'bm25', 'tfidf', 'transformers'] as const).map((method) => (
              <Button
                key={method}
                variant={searchMethod === method ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setSearchMethod(method)}
                className={`text-xs ${searchMethod === method ? 'bg-white/20 text-white' : 'text-blue-100 hover:bg-white/10'}`}
              >
                {method.toUpperCase()}
              </Button>
            ))}
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type !== 'user' && (
              <div className="flex-shrink-0">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                  message.type === 'system' ? 'bg-gray-400' : 'bg-blue-600'
                }`}>
                  {message.type === 'system' ? <Sparkles className="h-4 w-4 text-white" /> : <Bot className="h-4 w-4 text-white" />}
                </div>
              </div>
            )}
            
            <div className={`max-w-[70%] ${message.type === 'user' ? 'order-first' : ''}`}>
              <div
                className={`p-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white ml-auto'
                    : message.type === 'system'
                    ? 'bg-gray-100 text-gray-800'
                    : 'bg-white text-gray-800 shadow-sm border'
                }`}
              >
                {message.isLoading ? (
                  <div className="flex items-center gap-2">
                    <div className="flex gap-1">
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                      <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                    </div>
                    <span className="text-sm text-gray-600">Buscando información...</span>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="whitespace-pre-wrap text-sm leading-relaxed">
                      {message.content}
                    </div>
                    
                    {message.type !== 'user' && (
                      <div className="flex items-center gap-2 pt-2 border-t border-gray-100">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => copyToClipboard(message.content)}
                          className="h-7 px-2 text-xs"
                        >
                          <Copy className="h-3 w-3 mr-1" />
                          Copiar
                        </Button>
                        <span className="text-xs text-gray-500">
                          {message.timestamp.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' })}
                        </span>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Results Preview for Assistant Messages */}
              {message.searchResults && message.searchResults.results.length > 0 && (
                <div className="mt-3 space-y-2">
                  <div className="text-xs font-medium text-gray-600 flex items-center gap-1">
                    <FileText className="h-3 w-3" />
                    Resultados detallados ({message.searchResults.results.length})
                  </div>
                  
                  {message.searchResults.results.slice(0, 3).map((result, index) => (
                    <Card key={index} className="border-l-4 border-l-blue-500 bg-white/80">
                      <CardContent className="p-3">
                        <div className="flex items-start justify-between gap-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className={`px-2 py-1 text-xs rounded ${
                                result.score >= 0.8 ? 'bg-green-100 text-green-800' :
                                result.score >= 0.6 ? 'bg-yellow-100 text-yellow-800' :
                                'bg-red-100 text-red-800'
                              }`}>
                                {(result.score * 100).toFixed(1)}%
                              </span>
                              {result.metadata.source_document && (
                                <span className="text-xs text-gray-500">
                                  📄 {result.metadata.source_document}
                                </span>
                              )}
                            </div>
                            <p className="text-xs text-gray-700 leading-relaxed">
                              {result.content.slice(0, 200)}...
                            </p>
                          </div>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => copyToClipboard(result.content)}
                            className="h-6 w-6 p-0"
                          >
                            <Copy className="h-3 w-3" />
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                  
                  {message.searchResults.results.length > 3 && (
                    <p className="text-xs text-gray-500 text-center">
                      ... y {message.searchResults.results.length - 3} resultados más
                    </p>
                  )}
                </div>
              )}
            </div>

            {message.type === 'user' && (
              <div className="flex-shrink-0">
                <div className="w-8 h-8 rounded-full bg-gray-600 flex items-center justify-center">
                  <User className="h-4 w-4 text-white" />
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions */}
      {messages.length <= 1 && (
        <div className="p-4 bg-white border-t">
          <p className="text-sm text-gray-600 mb-3">Consultas frecuentes:</p>
          <div className="grid grid-cols-2 gap-2">
            {quickActions.map((action, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => handleQuickAction(action)}
                className={`text-left justify-start h-auto p-3 ${action.color}`}
                disabled={isLoading}
              >
                <div className="flex items-center gap-2">
                  {action.icon}
                  <div>
                    <div className="text-xs font-medium">{action.label}</div>
                    <div className="text-xs opacity-75">{action.query.slice(0, 30)}...</div>
                  </div>
                </div>
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-4 bg-white border-t">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              placeholder="Escribe tu pregunta sobre documentos MINEDU..."
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="pr-12"
            />
            {inputValue && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInputValue('')}
                className="absolute right-1 top-1/2 -translate-y-1/2 h-6 w-6 p-0"
              >
                ×
              </Button>
            )}
          </div>
          <Button
            onClick={() => handleSendMessage()}
            disabled={isLoading || !inputValue.trim()}
            className="bg-blue-600 hover:bg-blue-700"
            size="icon"
          >
            {isLoading ? (
              <div className="h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>
    </div>
  )
}