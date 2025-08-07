'use client'

import React, { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Loader2, Copy, AlertCircle } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card } from './ui/card'

interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  results?: any[]
  error?: boolean
}

export function ModernChatUI() {
  const [messages, setMessages] = useState<Message[]>([
    {
      id: '1',
      type: 'assistant',
      content: '¡Hola! Soy tu asistente de IA del MINEDU. Puedo ayudarte a buscar información en documentos administrativos y educativos. ¿Qué necesitas saber?',
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input,
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    const currentQuery = input
    setInput('')
    setIsLoading(true)

    try {
      console.log('🔍 Enviando búsqueda al backend:', currentQuery)
      
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: currentQuery,
          method: 'hybrid',
          top_k: 5
        })
      })

      console.log('📡 Respuesta del servidor:', response.status)

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Error ${response.status}: ${errorText}`)
      }

      const data = await response.json()
      console.log('📊 Datos recibidos:', data)

      let assistantContent = ''
      if (data.results && data.results.length > 0) {
        assistantContent = `He encontrado ${data.results.length} resultado${data.results.length > 1 ? 's' : ''} relevante${data.results.length > 1 ? 's' : ''} para tu consulta:\n\n`
        
        // Mostrar el resultado principal
        const topResult = data.results[0]
        assistantContent += `📄 **Resultado principal** (${(topResult.score * 100).toFixed(1)}% relevancia):\n\n`
        assistantContent += topResult.content.substring(0, 400)
        if (topResult.content.length > 400) {
          assistantContent += '...'
        }
        
        if (data.results.length > 1) {
          assistantContent += `\n\n📋 Encontré ${data.results.length - 1} resultado${data.results.length > 2 ? 's' : ''} adicional${data.results.length > 2 ? 'es' : ''} que también podrían ser útiles.`
        }
        
        assistantContent += `\n\n⚡ Búsqueda procesada en ${(data.processing_time * 1000).toFixed(0)}ms usando el método ${data.method.toUpperCase()}.`
      } else {
        assistantContent = `No encontré resultados específicos para "${currentQuery}". \n\nTe sugiero:\n• Usar términos más generales\n• Verificar la ortografía\n• Probar con sinónimos\n\n¿Te gustaría reformular tu pregunta?`
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: assistantContent,
        timestamp: new Date(),
        results: data.results || []
      }

      setMessages(prev => [...prev, assistantMessage])

    } catch (error) {
      console.error('❌ Error en la búsqueda:', error)
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'assistant',
        content: `❌ **Error de conexión**\n\nNo pude procesar tu consulta. Detalles técnicos:\n• ${error instanceof Error ? error.message : 'Error desconocido'}\n• Backend: http://localhost:8000\n\nPor favor:\n1. Verifica que el backend esté corriendo\n2. Revisa la consola del navegador (F12)\n3. Intenta nuevamente`,
        timestamp: new Date(),
        error: true
      }

      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
  }

  const quickQuestions = [
    "¿Cuál es el monto máximo para viáticos?",
    "¿Qué documentos requiere la solicitud de licencia?", 
    "¿Cuál es el procedimiento para declaración jurada?",
    "¿Cuánto tiempo antes debo solicitar permisos?"
  ]

  return (
    <div className="flex flex-col h-[80vh] max-w-5xl mx-auto bg-white rounded-xl shadow-2xl overflow-hidden border">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-blue-800 text-white p-6">
        <div className="flex items-center gap-4">
          <div className="bg-white/20 p-3 rounded-full">
            <Bot className="h-8 w-8" />
          </div>
          <div>
            <h1 className="text-2xl font-bold">Asistente MINEDU IA</h1>
            <p className="text-blue-100 text-sm">Sistema de búsqueda híbrida inteligente • Conectado</p>
          </div>
          <div className="ml-auto">
            <div className="bg-green-400 w-3 h-3 rounded-full animate-pulse"></div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-gradient-to-b from-gray-50 to-white">
        {messages.map((message) => (
          <div
            key={message.id}
            className={`flex gap-4 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            {message.type === 'assistant' && (
              <div className="flex-shrink-0 mt-1">
                <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                  message.error ? 'bg-red-500' : 'bg-blue-600'
                }`}>
                  {message.error ? (
                    <AlertCircle className="h-5 w-5 text-white" />
                  ) : (
                    <Bot className="h-5 w-5 text-white" />
                  )}
                </div>
              </div>
            )}
            
            <div className={`max-w-[75%] ${message.type === 'user' ? 'order-first' : ''}`}>
              <div
                className={`p-4 rounded-2xl shadow-sm ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white ml-auto rounded-br-md'
                    : message.error
                    ? 'bg-red-50 text-red-900 border border-red-200'
                    : 'bg-white text-gray-800 border border-gray-200 rounded-bl-md'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </div>
                
                {/* Results preview for assistant messages */}
                {message.results && message.results.length > 1 && (
                  <div className="mt-4 pt-4 border-t border-gray-100">
                    <p className="text-xs font-medium text-gray-600 mb-3">
                      📋 Resultados adicionales encontrados:
                    </p>
                    <div className="space-y-2">
                      {message.results.slice(1, 4).map((result, index) => (
                        <div key={index} className="bg-gray-50 p-3 rounded-lg text-xs">
                          <div className="flex justify-between items-start mb-1">
                            <span className="font-medium text-gray-700">
                              Resultado {index + 2}
                            </span>
                            <span className="text-blue-600 font-medium">
                              {(result.score * 100).toFixed(1)}%
                            </span>
                          </div>
                          <p className="text-gray-600 leading-relaxed">
                            {result.content.substring(0, 150)}...
                          </p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex items-center justify-between mt-3 pt-3 border-t border-gray-100/50">
                  <span className="text-xs text-gray-500">
                    {message.timestamp.toLocaleTimeString('es-ES', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                  {message.type === 'assistant' && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => copyToClipboard(message.content)}
                      className="h-6 px-2 text-xs text-gray-500 hover:text-gray-700"
                    >
                      <Copy className="h-3 w-3 mr-1" />
                      Copiar
                    </Button>
                  )}
                </div>
              </div>
            </div>

            {message.type === 'user' && (
              <div className="flex-shrink-0 mt-1">
                <div className="w-10 h-10 bg-gray-600 rounded-full flex items-center justify-center">
                  <User className="h-5 w-5 text-white" />
                </div>
              </div>
            )}
          </div>
        ))}

        {/* Loading indicator */}
        {isLoading && (
          <div className="flex gap-4 justify-start">
            <div className="flex-shrink-0 mt-1">
              <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="h-5 w-5 text-white" />
              </div>
            </div>
            <div className="bg-white p-4 rounded-2xl rounded-bl-md shadow-sm border border-gray-200">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                <span className="text-sm text-gray-600">Procesando tu consulta...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Actions (only show if no messages yet) */}
      {messages.length === 1 && (
        <div className="px-6 py-4 bg-gray-50 border-t">
          <p className="text-sm font-medium text-gray-700 mb-3">
            💡 Preguntas frecuentes:
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {quickQuestions.map((question, index) => (
              <Button
                key={index}
                variant="outline"
                size="sm"
                onClick={() => setInput(question)}
                className="text-left justify-start h-auto p-3 text-xs hover:bg-blue-50 hover:border-blue-300"
                disabled={isLoading}
              >
                <span className="truncate">{question}</span>
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Input Area */}
      <div className="p-6 bg-white border-t border-gray-200">
        <div className="flex gap-3">
          <div className="flex-1 relative">
            <Input
              ref={inputRef}
              placeholder="Escribe tu pregunta sobre documentos MINEDU..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="h-12 pr-12 text-base border-gray-300 focus:border-blue-500 focus:ring-blue-500 rounded-xl"
            />
            {input && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setInput('')}
                className="absolute right-2 top-1/2 -translate-y-1/2 h-8 w-8 p-0 text-gray-400 hover:text-gray-600"
              >
                ×
              </Button>
            )}
          </div>
          <Button
            onClick={sendMessage}
            disabled={isLoading || !input.trim()}
            className="h-12 px-6 bg-blue-600 hover:bg-blue-700 text-white rounded-xl font-medium"
          >
            {isLoading ? (
              <Loader2 className="h-5 w-5 animate-spin" />
            ) : (
              <Send className="h-5 w-5" />
            )}
          </Button>
        </div>
        
        <p className="text-xs text-gray-500 mt-2 text-center">
          Presiona Enter para enviar • Tu consulta se procesará usando IA híbrida
        </p>
      </div>
    </div>
  )
}