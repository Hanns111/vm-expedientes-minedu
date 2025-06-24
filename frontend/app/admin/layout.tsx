import { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Panel de Administración - Sistema de IA Gubernamental',
  description: 'Dashboard para gestionar plugins, modelos y configuración del sistema',
}

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-background">
      <header className="border-b">
        <div className="container mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Panel de Administración</h1>
        </div>
      </header>
      <main className="container mx-auto px-4 py-8">
        {children}
      </main>
    </div>
  )
}