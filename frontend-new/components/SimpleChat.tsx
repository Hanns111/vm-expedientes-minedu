'use client'

import React, { useState } from 'react'
import { Send, Bot, User } from 'lucide-react'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Card, CardContent } from './ui/card'

export function SimpleChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: '¡Hola! Soy el asistente de IA del MINEDU. ¿En qué puedo ayudarte?'
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const sendMessage = async () => {
    if (!input.trim()) return

    // Añadir mensaje del usuario
    const userMessage = {
      id: Date.now(),
      type: 'user',
      text: input
    }
    
    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setIsLoading(true)

    try {
      // Llamar al backend
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: currentInput,
          method: 'hybrid',
          top_k: 5
        })
      })

      if (!response.ok) {
        throw new Error('Error en la búsqueda')
      }

      const data = await response.json()
      
      // Crear respuesta del bot
      let botResponse = `Encontré ${data.results.length} resultados para "${currentInput}":\n\n`
      
      if (data.results.length > 0) {
        const topResult = data.results[0]
        botResponse += `📄 **Resultado principal:**\n${topResult.content.substring(0, 300)}...\n\n`
        botResponse += `📊 Puntuación: ${(topResult.score * 100).toFixed(1)}%`
      } else {
        botResponse = `No encontré resultados para "${currentInput}". Intenta con otros términos.`
      }

      const botMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: botResponse
      }

      setMessages(prev => [...prev, botMessage])

    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        type: 'bot',
        text: `❌ Error: ${error.message}. Verifica que el backend esté corriendo en http://localhost:8000`
      }
      setMessages(prev => [...prev, errorMessage])
    }

    setIsLoading(false)
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      sendMessage()
    }
  }

  return (
    <div className="max-w-4xl mx-auto">
      <Card className="h-[600px] flex flex-col">
        {/* Header */}
        <div className="bg-blue-600 text-white p-4 rounded-t-lg">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <Bot className="h-6 w-6" />
            Chat MINEDU IA - FUNCIONANDO
          </h2>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              {message.type === 'bot' && (
                <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <Bot className="h-4 w-4 text-white" />
                </div>
              )}
              
              <div
                className={`max-w-[70%] p-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-white text-gray-800 shadow-sm'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm">
                  {message.text}
                </div>
              </div>

              {message.type === 'user' && (
                <div className="w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <User className="h-4 w-4 text-white" />
                </div>
              )}
            </div>
          ))}

          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="h-4 w-4 text-white" />
              </div>
              <div className="bg-white p-3 rounded-lg shadow-sm">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                  <div className="w-2 h-2 bg-blue-600 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input */}
        <div className="p-4 border-t bg-white">
          <div className="flex gap-2">
            <Input
              placeholder="Pregunta sobre viáticos, procedimientos, etc..."
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={isLoading}
              className="text-base"
            />
            <Button 
              onClick={sendMessage}
              disabled={isLoading || !input.trim()}
              className="bg-blue-600 hover:bg-blue-700"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
          
          {/* Quick buttons */}
          <div className="mt-3 flex flex-wrap gap-2">
            {[
              "¿Cuál es el monto máximo para viáticos?",
              "Procedimiento para solicitar licencia",
              "Documentos requeridos para trámites"
            ].map((example, i) => (
              <Button
                key={i}
                variant="outline"
                size="sm"
                onClick={() => setInput(example)}
                className="text-xs"
                disabled={isLoading}
              >
                {example}
              </Button>
            ))}
          </div>
        </div>
      </Card>
    </div>
  )
}