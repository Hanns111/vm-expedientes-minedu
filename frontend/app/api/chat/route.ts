import { openai } from '@ai-sdk/openai'
import { streamText } from 'ai'

export async function POST(req: Request) {
  try {
    const { messages } = await req.json()

    // Validate messages
    if (!messages || !Array.isArray(messages)) {
      return new Response('Invalid messages format', { status: 400 })
    }

    const result = await streamText({
      model: openai('gpt-4-turbo'),
      messages,
      system: `Eres un asistente especializado en documentos gubernamentales del Ministerio de Educación (MINEDU) del Perú. 

Tu expertise incluye:
- Directivas administrativas y normativas educativas
- Procedimientos para viáticos y declaraciones juradas
- Montos máximos y límites para gastos administrativos
- Requisitos documentarios para trámites
- Plazos y tiempos de procesamiento
- Regulaciones específicas del sector educación

Instrucciones:
- Responde de manera precisa y profesional
- Si no tienes información específica, indica claramente las limitaciones
- Proporciona referencias a normativas cuando sea posible
- Usa un tono formal pero accesible
- Estructura tus respuestas de manera clara y ordenada
- Si la pregunta no está relacionada con temas gubernamentales/educativos, redirige cortésmente al tema

Recuerda que estás ayudando con información administrativa importante que debe ser precisa.`,
      temperature: 0.1,
      maxTokens: 1000,
    })

    return result.toAIStreamResponse()
  } catch (error) {
    console.error('Chat API Error:', error)
    return new Response('Internal Server Error', { status: 500 })
  }
}