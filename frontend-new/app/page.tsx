"use client"

import { useState, useRef, useEffect } from 'react'
import { Send, MessageSquare, FileText, Search, Settings, Plus, Moon, Sun } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
  sources?: Array<{
    title: string
    excerpt: string
    confidence: number
  }>
}

interface ChatResponse {
  response: string
  conversation_id: string
  timestamp: string
  sources: Array<{
    title: string
    excerpt: string
    confidence: number
  }>
  processing_time: number
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isDark, setIsDark] = useState(false)
  
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = inputRef.current.scrollHeight + 'px'
    }
  }, [input])

  // Toggle dark mode
  useEffect(() => {
    if (isDark) {
      document.documentElement.classList.add('dark')
    } else {
      document.documentElement.classList.remove('dark')
    }
  }, [isDark])

  const sendMessage = async () => {
    if (!input.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: input.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInput('')
    setIsLoading(true)

    try {
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          ...(conversationId && { conversation_id: conversationId })
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to send message')
      }

      const data: ChatResponse = await response.json()
      
      setConversationId(data.conversation_id)

      const aiMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: data.response,
        timestamp: new Date(),
        sources: data.sources
      }

      setMessages(prev => [...prev, aiMessage])
    } catch (error) {
      console.error('Error sending message:', error)
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: 'Lo siento, hubo un error al procesar tu mensaje. Por favor, inténtalo de nuevo.',
        timestamp: new Date()
      }
      
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const startNewChat = () => {
    setMessages([])
    setConversationId(null)
    setInput('')
  }

  const examplePrompts = [
    "¿Cuál es el monto máximo para viáticos en comisiones de servicio?",
    "¿Qué documentos se requieren para solicitar viáticos?",
    "¿Cuál es el procedimiento para autorizar viajes al extranjero?",
    "¿Cuánto tiempo antes debo solicitar los viáticos?"
  ]

  return (
    <div className={`chat-container flex h-screen ${isDark ? 'dark' : ''}`}>
      {/* Sidebar */}
      <div className="chat-sidebar">
        <div className="p-4">
          <Button 
            onClick={startNewChat}
            className="w-full flex items-center gap-2 justify-start bg-gray-800 hover:bg-gray-700 text-white border border-gray-600"
          >
            <Plus className="w-4 h-4" />
            Nueva conversación
          </Button>
        </div>
        
        <div className="px-4 pb-4">
          <div className="text-xs text-gray-400 uppercase tracking-wide mb-2">Conversaciones recientes</div>
          <div className="space-y-2">
            <div className="text-sm text-gray-300 p-2 rounded hover:bg-gray-800 cursor-pointer truncate">
              Consulta sobre viáticos
            </div>
            <div className="text-sm text-gray-300 p-2 rounded hover:bg-gray-800 cursor-pointer truncate">
              Documentos requeridos
            </div>
            <div className="text-sm text-gray-300 p-2 rounded hover:bg-gray-800 cursor-pointer truncate">
              Procedimiento de autorización
            </div>
          </div>
        </div>

        <div className="mt-auto p-4 border-t border-gray-700">
          <Button
            onClick={() => setIsDark(!isDark)}
            variant="ghost"
            size="sm"
            className="w-full flex items-center gap-2 justify-start text-gray-300 hover:text-white hover:bg-gray-800"
          >
            {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            {isDark ? 'Modo claro' : 'Modo oscuro'}
          </Button>
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="chat-main">
        {/* Header */}
        <div className="chat-header p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 bg-[#10a37f] rounded-full flex items-center justify-center">
                <MessageSquare className="w-4 h-4 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-gray-900 dark:text-gray-100">
                  Asistente Inteligente
                </h1>
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Búsqueda avanzada de documentos
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="ghost" size="sm">
                <Search className="w-4 h-4" />
              </Button>
              <Button variant="ghost" size="sm">
                <Settings className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Messages */}
        <div className="chat-messages scrollbar-thin">
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center px-4">
              <div className="w-16 h-16 bg-[#10a37f] rounded-full flex items-center justify-center mb-6">
                <MessageSquare className="w-8 h-8 text-white" />
              </div>
              <h2 className="text-2xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
                ¿En qué puedo ayudarte?
              </h2>
              <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-md">
                Especialista en análisis de documentos y consultas normativas.
                Encuentra información precisa y confiable al instante.
              </p>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
                {examplePrompts.map((prompt, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="text-left h-auto py-3 px-4 whitespace-normal"
                    onClick={() => setInput(prompt)}
                  >
                    <div className="text-sm leading-relaxed">{prompt}</div>
                  </Button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((message) => (
                <div key={message.id} className="fade-in">
                  <div className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={message.type === 'user' ? 'message-user' : 'message-ai'}>
                      <div className="whitespace-pre-wrap leading-relaxed">
                        {message.content}
                      </div>
                      
                      {message.sources && message.sources.length > 0 && (
                        <div className="mt-4 space-y-2">
                          <div className="text-xs font-medium text-gray-600 dark:text-gray-400">
                            Fuentes consultadas:
                          </div>
                          {message.sources.map((source, index) => (
                            <div key={index} className="source-citation">
                              <div className="source-title">{source.title}</div>
                              <div className="source-excerpt">{source.excerpt}</div>
                              <div className="flex items-center justify-between mt-2">
                                <div className="confidence-badge">
                                  {Math.round(source.confidence * 100)}% relevancia
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
              
              {isLoading && (
                <div className="flex justify-start">
                  <div className="message-ai">
                    <div className="typing-indicator">
                      <div className="loading-dots">
                        <div className="loading-dot" style={{ animationDelay: '0ms' }}></div>
                        <div className="loading-dot" style={{ animationDelay: '150ms' }}></div>
                        <div className="loading-dot" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <span className="text-sm">Pensando...</span>
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="chat-input-container">
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="Escribe tu mensaje aquí..."
                className="input-modern min-h-[50px] max-h-32"
                disabled={isLoading}
                rows={1}
              />
              <Button
                onClick={sendMessage}
                disabled={!input.trim() || isLoading}
                className="btn-send absolute right-2 bottom-2"
              >
                <Send className="w-4 h-4" />
              </Button>
            </div>
            
            <div className="flex items-center justify-between mt-2 text-xs text-gray-500 dark:text-gray-400">
              <div>
                Presiona Enter para enviar, Shift+Enter para nueva línea
              </div>
              <div className="flex items-center gap-4">
                <span>
                  {input.length > 0 && `${input.length} caracteres`}
                </span>
                {isLoading && (
                  <span className="flex items-center gap-1">
                    <div className="w-2 h-2 bg-[#10a37f] rounded-full animate-pulse"></div>
                    Procesando...
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}