'use client'

import { useChat } from 'ai/react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent } from '@/components/ui/card'
import { Send, Bot, User, ArrowLeft } from 'lucide-react'
import Link from 'next/link'

export default function ChatPage() {
  const { messages, input, handleInputChange, handleSubmit, isLoading } = useChat({
    api: '/api/chat',
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto max-w-4xl p-4">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-center gap-4 mb-6">
            <Link href="/">
              <Button variant="outline" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Inicio
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold">Chat con IA Gubernamental</h1>
              <p className="text-gray-600">
                Asistente especializado en documentos y procedimientos gubernamentales
              </p>
            </div>
          </div>
          
          {/* Messages Container */}
          <div className="space-y-4 min-h-[500px] max-h-[500px] overflow-y-auto bg-white rounded-lg p-4 shadow-lg">
            {messages.length === 0 && (
              <div className="flex flex-col items-center justify-center h-full text-center space-y-4">
                <Bot className="h-16 w-16 text-blue-500" />
                <div>
                  <h3 className="text-lg font-semibold">¡Hola! Soy tu asistente de IA</h3>
                  <p className="text-gray-600">
                    Puedes preguntarme sobre documentos gubernamentales, procedimientos administrativos,
                    y cualquier tema relacionado con la gestión pública.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-md">
                  <Button variant="outline" size="sm" className="text-xs">
                    ¿Cuál es el monto máximo para viáticos?
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs">
                    ¿Qué documentos requiere una solicitud?
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs">
                    Procedimiento para declaración jurada
                  </Button>
                  <Button variant="outline" size="sm" className="text-xs">
                    ¿Cuánto tiempo antes debo solicitar?
                  </Button>
                </div>
              </div>
            )}
            
            {messages.map((message) => (
              <Card 
                key={message.id} 
                className={`${message.role === 'user' ? 'ml-12 bg-blue-50' : 'mr-12 bg-green-50'}`}
              >
                <CardContent className="p-4">
                  <div className="flex items-start space-x-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm ${
                      message.role === 'user' ? 'bg-blue-500' : 'bg-green-500'
                    }`}>
                      {message.role === 'user' ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
                    </div>
                    <div className="flex-1">
                      <p className="text-sm text-muted-foreground mb-1 font-medium">
                        {message.role === 'user' ? 'Usuario' : 'Asistente IA'}
                      </p>
                      <div className="prose prose-sm max-w-none">
                        {message.content}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
            
            {isLoading && (
              <Card className="mr-12 bg-green-50">
                <CardContent className="p-4">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 rounded-full bg-green-500 flex items-center justify-center">
                      <Bot className="h-4 w-4 text-white" />
                    </div>
                    <div className="flex items-center space-x-2">
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce"></div>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                      <div className="w-2 h-2 bg-green-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                      <span className="text-sm text-green-600">Procesando...</span>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Input Form */}
          <form onSubmit={handleSubmit} className="flex space-x-2">
            <Input
              value={input}
              onChange={handleInputChange}
              placeholder="Escribe tu pregunta sobre documentos gubernamentales..."
              disabled={isLoading}
              className="flex-1 h-12 text-base"
            />
            <Button type="submit" disabled={isLoading || !input.trim()} className="h-12 px-6">
              <Send className="h-4 w-4" />
            </Button>
          </form>
          
          {/* Info Footer */}
          <div className="text-center text-sm text-gray-500 bg-white rounded-lg p-3">
            💡 <strong>Tip:</strong> Soy especialista en documentos del MINEDU. 
            Puedes preguntarme sobre montos, procedimientos, requisitos y plazos.
          </div>
        </div>
      </div>
    </div>
  )
}