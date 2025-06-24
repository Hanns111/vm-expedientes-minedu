'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Button } from '@/components/ui/button'
import { RefreshCw, Activity, Cpu, Database } from 'lucide-react'

interface Plugin {
  id: string
  name: string
  description: string
  enabled: boolean
  capabilities: string[]
  metrics: {
    total_requests: number
    success_rate: number
    avg_latency: number
    errors_last_hour: number
  }
}

interface Model {
  model_name: string
  display_name: string
  description: string
  enabled: boolean
  provider: string
  cost_per_1k_tokens: number
  metrics: {
    total_requests: number
    total_tokens: number
    avg_latency: number
    success_rate: number
  }
}

export default function AdminDashboard() {
  const [plugins, setPlugins] = useState<Plugin[]>([])
  const [models, setModels] = useState<Model[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)
    try {
      const [pluginsRes, modelsRes] = await Promise.all([
        fetch('http://localhost:8000/api/admin/plugins'),
        fetch('http://localhost:8000/api/admin/models')
      ])

      if (pluginsRes.ok) setPlugins(await pluginsRes.json())
      if (modelsRes.ok) setModels(await modelsRes.json())
    } catch (error) {
      console.error('Error loading data:', error)
      setError('Error conectando con el backend. Asegúrate de que esté ejecutándose en puerto 8000.')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin" />
        <span className="ml-2 text-lg">Cargando dashboard...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-64 space-y-4">
        <div className="text-red-500 text-center">
          <Database className="h-12 w-12 mx-auto mb-2" />
          <p className="text-lg font-semibold">Error de Conexión</p>
          <p className="text-sm">{error}</p>
        </div>
        <Button onClick={loadData} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          Reintentar
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Panel de Administración</h1>
          <p className="text-muted-foreground">
            Gestiona plugins, modelos y monitorea el sistema
          </p>
        </div>
        <Button onClick={loadData} variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Actualizar
        </Button>
      </div>

      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Plugins Activos</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{plugins.filter(p => p.enabled).length}</div>
            <p className="text-xs text-muted-foreground">
              de {plugins.length} total
            </p>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Modelos LLM</CardTitle>
            <Cpu className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{models.filter(m => m.enabled).length}</div>
            <p className="text-xs text-muted-foreground">
              modelos habilitados
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Requests Totales</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {plugins.reduce((sum, p) => sum + p.metrics.total_requests, 0)}
            </div>
            <p className="text-xs text-muted-foreground">
              en plugins
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Tokens Procesados</CardTitle>
            <Database className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {models.reduce((sum, m) => sum + m.metrics.total_tokens, 0).toLocaleString()}
            </div>
            <p className="text-xs text-muted-foreground">
              por modelos LLM
            </p>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="plugins" className="space-y-4">
        <TabsList>
          <TabsTrigger value="plugins">Plugins ({plugins.length})</TabsTrigger>
          <TabsTrigger value="models">Modelos LLM ({models.length})</TabsTrigger>
        </TabsList>

        <TabsContent value="plugins" className="space-y-4">
          <div className="grid gap-4">
            {plugins.map((plugin) => (
              <Card key={plugin.id}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">{plugin.name}</CardTitle>
                      <CardDescription>{plugin.description}</CardDescription>
                    </div>
                    <div className="flex items-center space-x-4">
                      <div className="flex space-x-2">
                        {plugin.capabilities.map((cap) => (
                          <Badge key={cap} variant="secondary">
                            {cap.replace('_', ' ')}
                          </Badge>
                        ))}
                      </div>
                      <Switch checked={plugin.enabled} />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="font-medium">Requests</p>
                      <p className="text-muted-foreground">{plugin.metrics.total_requests}</p>
                    </div>
                    <div>
                      <p className="font-medium">Success Rate</p>
                      <p className="text-muted-foreground">{plugin.metrics.success_rate}%</p>
                    </div>
                    <div>
                      <p className="font-medium">Latencia Avg</p>
                      <p className="text-muted-foreground">{plugin.metrics.avg_latency}ms</p>
                    </div>
                    <div>
                      <p className="font-medium">Errores (1h)</p>
                      <p className="text-muted-foreground">{plugin.metrics.errors_last_hour}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>

        <TabsContent value="models" className="space-y-4">
          <div className="grid gap-4">
            {models.map((model) => (
              <Card key={model.model_name}>
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <div>
                      <CardTitle className="text-lg">{model.display_name}</CardTitle>
                      <CardDescription>{model.description}</CardDescription>
                    </div>
                    <div className="flex items-center space-x-4">
                      <Badge variant="outline">{model.provider}</Badge>
                      <Badge variant={model.cost_per_1k_tokens === 0 ? "secondary" : "default"}>
                        ${model.cost_per_1k_tokens}/1K tokens
                      </Badge>
                      <Switch checked={model.enabled} />
                    </div>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-4 text-sm">
                    <div>
                      <p className="font-medium">Requests</p>
                      <p className="text-muted-foreground">{model.metrics.total_requests}</p>
                    </div>
                    <div>
                      <p className="font-medium">Tokens</p>
                      <p className="text-muted-foreground">{model.metrics.total_tokens.toLocaleString()}</p>
                    </div>
                    <div>
                      <p className="font-medium">Latencia</p>
                      <p className="text-muted-foreground">{model.metrics.avg_latency}ms</p>
                    </div>
                    <div>
                      <p className="font-medium">Success Rate</p>
                      <p className="text-muted-foreground">{model.metrics.success_rate}%</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}