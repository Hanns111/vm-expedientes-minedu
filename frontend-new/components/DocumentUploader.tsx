'use client'

import React, { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { Upload, File, CheckCircle, AlertCircle, X, FileText } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { Textarea } from './ui/textarea'
import { useToast } from '../hooks/use-toast'
import { apiClient, DocumentUploadResponse } from '../lib/api'

interface UploadedFile {
  id: string
  file: File
  title?: string
  description?: string
  status: 'pending' | 'uploading' | 'completed' | 'error'
  response?: DocumentUploadResponse
  error?: string
  progress?: number
}

export function DocumentUploader() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const { toast } = useToast()

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      id: Math.random().toString(36).substr(2, 9),
      file,
      status: 'pending'
    }))
    
    setFiles(prev => [...prev, ...newFiles])
    
    toast({
      title: `${acceptedFiles.length} archivo(s) agregado(s)`,
      description: "Configura los detalles y haz clic en 'Procesar' para subirlos.",
    })
  }, [toast])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt']
    },
    multiple: true,
    maxFileSize: 50 * 1024 * 1024 // 50MB
  })

  const updateFile = (id: string, updates: Partial<UploadedFile>) => {
    setFiles(prev => prev.map(file => 
      file.id === id ? { ...file, ...updates } : file
    ))
  }

  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(file => file.id !== id))
  }

  const uploadFile = async (file: UploadedFile) => {
    try {
      updateFile(file.id, { status: 'uploading', progress: 0 })
      
      const response = await apiClient.uploadDocument(file.file, {
        title: file.title,
        description: file.description
      })
      
      updateFile(file.id, { 
        status: 'completed', 
        response,
        progress: 100 
      })
      
      toast({
        title: "Documento procesado exitosamente",
        description: `${file.file.name} se ha cargado y procesado correctamente.`,
      })
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Error desconocido'
      updateFile(file.id, { 
        status: 'error', 
        error: errorMessage 
      })
      
      toast({
        title: "Error al procesar documento",
        description: errorMessage,
        variant: "destructive",
      })
    }
  }

  const uploadAllFiles = async () => {
    setIsUploading(true)
    const pendingFiles = files.filter(f => f.status === 'pending')
    
    for (const file of pendingFiles) {
      await uploadFile(file)
    }
    
    setIsUploading(false)
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getStatusIcon = (status: UploadedFile['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'error':
        return <AlertCircle className="h-5 w-5 text-red-500" />
      case 'uploading':
        return <div className="h-5 w-5 animate-spin rounded-full border-2 border-blue-500 border-t-transparent" />
      default:
        return <File className="h-5 w-5 text-gray-500" />
    }
  }

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="h-6 w-6" />
          Procesador de Documentos MINEDU
        </CardTitle>
        <CardDescription>
          Sube documentos administrativos para procesamiento con IA. 
          Formatos soportados: PDF, DOC, DOCX, TXT (máx. 50MB)
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {/* Área de drop */}
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors
            ${isDragActive 
              ? 'border-blue-500 bg-blue-50' 
              : 'border-gray-300 hover:border-gray-400 hover:bg-gray-50'
            }
          `}
        >
          <input {...getInputProps()} />
          <Upload className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          {isDragActive ? (
            <p className="text-blue-600 font-medium">
              Suelta los archivos aquí...
            </p>
          ) : (
            <div>
              <p className="text-gray-600 font-medium mb-2">
                Arrastra y suelta documentos aquí, o haz clic para seleccionar
              </p>
              <p className="text-sm text-gray-500">
                PDF, DOC, DOCX, TXT hasta 50MB cada uno
              </p>
            </div>
          )}
        </div>

        {/* Lista de archivos */}
        {files.length > 0 && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-semibold">
                Documentos ({files.length})
              </h3>
              {files.some(f => f.status === 'pending') && (
                <Button 
                  onClick={uploadAllFiles}
                  disabled={isUploading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {isUploading ? 'Procesando...' : 'Procesar Todos'}
                </Button>
              )}
            </div>

            <div className="space-y-3">
              {files.map((file) => (
                <Card key={file.id} className="p-4">
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0 mt-1">
                      {getStatusIcon(file.status)}
                    </div>
                    
                    <div className="flex-1 space-y-3">
                      <div className="flex items-start justify-between">
                        <div>
                          <h4 className="font-medium text-gray-900">
                            {file.file.name}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {formatFileSize(file.file.size)}
                          </p>
                        </div>
                        
                        {file.status === 'pending' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => removeFile(file.id)}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        )}
                      </div>

                      {file.status === 'pending' && (
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Título (opcional)
                            </label>
                            <Input
                              placeholder="Ej: Directiva de Viáticos 2024"
                              value={file.title || ''}
                              onChange={(e) => updateFile(file.id, { title: e.target.value })}
                            />
                          </div>
                          <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">
                              Descripción (opcional)
                            </label>
                            <Textarea
                              placeholder="Descripción del documento..."
                              value={file.description || ''}
                              onChange={(e) => updateFile(file.id, { description: e.target.value })}
                              rows={2}
                            />
                          </div>
                        </div>
                      )}

                      {file.status === 'uploading' && file.progress !== undefined && (
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                            style={{ width: `${file.progress}%` }}
                          />
                        </div>
                      )}

                      {file.status === 'completed' && file.response && (
                        <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                          <div className="flex items-center gap-2 text-green-800">
                            <CheckCircle className="h-4 w-4" />
                            <span className="font-medium">Procesado exitosamente</span>
                          </div>
                          <div className="mt-2 text-sm text-green-700">
                            <p>ID: {file.response.document_id}</p>
                            <p>Fragmentos generados: {file.response.chunks_generated || 'N/A'}</p>
                            <p>Tiempo: {file.response.processing_time?.toFixed(2) || 'N/A'}s</p>
                          </div>
                        </div>
                      )}

                      {file.status === 'error' && (
                        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                          <div className="flex items-center gap-2 text-red-800">
                            <AlertCircle className="h-4 w-4" />
                            <span className="font-medium">Error al procesar</span>
                          </div>
                          <p className="mt-1 text-sm text-red-700">{file.error}</p>
                          <Button
                            variant="outline"
                            size="sm"
                            className="mt-2"
                            onClick={() => uploadFile(file)}
                          >
                            Reintentar
                          </Button>
                        </div>
                      )}

                      {file.status === 'pending' && (
                        <Button
                          onClick={() => uploadFile(file)}
                          disabled={isUploading}
                          size="sm"
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          Procesar Documento
                        </Button>
                      )}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}