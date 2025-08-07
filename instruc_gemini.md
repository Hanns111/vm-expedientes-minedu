 Reporte Completo del Estado del Proyecto MINEDU - Sistema RAG Híbrido

  Resumen Ejecutivo

  Estamos trabajando en un sistema de búsqueda híbrida para documentos gubernamentales del MINEDU
  que combina múltiples métodos de retrieval (BM25, TF-IDF, Transformers). El proyecto tiene una
  arquitectura compleja con backend FastAPI y frontend Next.js, pero enfrenta problemas críticos de
  integración.

  Estado Actual del Proyecto

  ✅ Componentes Funcionales

  1. Sistema de búsqueda híbrida independiente: demo_secure.py funciona perfectamente
  2. Vectorstores generados: BM25, TF-IDF y Transformers en /data/vectorstores/
  3. Frontend moderno: Interfaz ChatGPT-style completamente implementada
  4. Arquitectura de seguridad: Sistema completo de validación y protección

  ❌ Problemas Críticos Identificados

  1. Problema Principal: Desconexión Backend-Frontend

  - Síntoma: Frontend muestra respuestas mock/fallback en lugar de búsquedas reales
  - Ubicación: /backend/src/main.py líneas 22-31
  - Error específico: No module named 'src' al importar HybridSearch

  2. Problemas de Importación en Backend

  # Error en backend/src/main.py
  from core.hybrid.hybrid_search import HybridSearch  # FALLA

  Causa raíz: El backend está en /backend/src/ pero intenta importar desde /src/core/hybrid/

  3. Inconsistencia en Rutas de Importación

  - demo_secure.py usa: sys.path.append(str(Path(__file__).parent / "src")) ✅ FUNCIONA
  - backend/src/main.py usa: sys.path.insert(0, str(project_root / "src")) ❌ FALLA

  4. Puerto de API Incorrecto

  - Backend corriendo en puerto 8001
  - Frontend apuntando a puerto 8000 (parcialmente corregido)

  Arquitectura del Sistema

  Estructura de Directorios

  vm-expedientes-minedu/
  ├── src/                          # Sistema principal de búsqueda
  │   ├── core/
  │   │   ├── hybrid/
  │   │   │   └── hybrid_search.py  # Clase principal ✅
  │   │   └── retrieval/            # Retrievers ✅
  │   └── ...
  ├── backend/                      # API FastAPI
  │   └── src/
  │       └── main.py              # Endpoint problemático ❌
  ├── frontend-new/                 # Interfaz Next.js
  │   └── app/
  │       └── page.tsx             # Chat interface ✅
  └── data/
      └── vectorstores/            # Índices generados ✅

  Flujo de Datos Esperado

  1. Usuario escribe consulta en frontend
  2. Frontend envía POST a /api/chat
  3. Backend usa HybridSearch para buscar
  4. Retorna respuesta con información real de documentos

  Flujo Actual (Problemático)

  1. Usuario escribe consulta ✅
  2. Frontend envía POST ✅
  3. Backend usa respuestas fallback/mock ❌
  4. Usuario recibe información genérica sin valor ❌

  Detalles Técnicos de los Problemas

  Error de Importación

  ⚠️ Hybrid search not available: No module named 'src'
  Project root: /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu
  Src path added: /mnt/c/Users/hanns/Documents/proyectos/vm-expedientes-minedu/src

  Configuración de Paths

  # En backend/src/main.py (PROBLEMÁTICO)
  project_root = Path(__file__).parent.parent.parent  # Correcto
  src_path = project_root / "src"                     # Correcto
  sys.path.insert(0, str(src_path))                   # Debería funcionar pero no funciona

  Dependencias de HybridSearch

  # En src/core/hybrid/hybrid_search.py
  from ..retrieval.bm25_retriever import BM25Retriever
  from ..retrieval.tfidf_retriever import TFIDFRetriever
  from ..retrieval.transformer_retriever import TransformerRetriever

  Evidencia de Funcionalidad

  Demo Independiente Funciona

  python demo_secure.py "¿Cuál es el monto máximo para viáticos?"
  # Retorna respuesta detallada con información real

  Respuesta Real Esperada

  📋 RESPUESTA SOBRE DECLARACIÓN JURADA DE VIÁTICOS:
  🏛️ LIMA (Capital): Hasta S/ 45.00 soles por día
  🌄 REGIONES (Provincias): Hasta S/ 30.00 soles por día
  📖 NUMERAL DE REFERENCIA: 8.4.17 - Declaración Jurada de Gastos

  Respuesta Actual del Frontend

  📋 SISTEMA EN MODO BÁSICO
  ⚠️ El sistema de búsqueda avanzada no está disponible temporalmente.
  💡 INFORMACIÓN GENERAL DE VIÁTICOS MINEDU:
  • Ministros de Estado: S/ 380.00 diarios

  Requerimientos del Usuario

  1. Interfaz ChatGPT-Style ✅ COMPLETADO

  - Colores y diseño similar a ChatGPT
  - Modo oscuro/claro
  - Animaciones y typing indicators
  - Sin referencias a MINEDU en la interfaz

  2. Respuestas Funcionales ❌ PENDIENTE CRÍTICO

  - Respuestas basadas en documentos reales
  - Información útil para el sector tributario
  - Sistema escalable a otros dominios

  3. Funcionalidad Completa ❌ BLOQUEADO

  - Chat end-to-end funcional
  - Búsqueda híbrida integrada
  - Respuestas contextualizadas

  Próximos Pasos Requeridos

  Prioridad Alta

  1. Resolver importación de HybridSearch en backend
  2. Conectar sistema de búsqueda real
  3. Verificar respuestas end-to-end

  Prioridad Media

  4. Optimizar rendimiento
  5. Testing completo
  6. Documentación de deployment

  Contexto de Desarrollo

  Tecnologías Utilizadas

  - Backend: FastAPI, Python 3.x, Uvicorn
  - Frontend: Next.js, React, TypeScript, Tailwind CSS
  - Búsqueda: BM25, TF-IDF, Sentence Transformers
  - Seguridad: Sistema gubernamental (ISO27001, NIST)

  Archivos Clave Modificados

  1. /backend/src/main.py - API endpoints y lógica principal
  2. /frontend-new/app/page.tsx - Interfaz de chat
  3. /src/core/hybrid/hybrid_search.py - Motor de búsqueda
  4. /demo_secure.py - Referencia funcional

  Estado de Testing

  - ✅ demo_secure.py - Funciona perfectamente
  - ✅ Frontend UI - Interfaz completa y responsive
  - ❌ Integración backend-frontend - Completamente rota
  - ❌ API endpoints - Retornan mock data

  Objetivo Final

  Un sistema web funcional donde usuarios puedan hacer consultas sobre viáticos y recibir respuestas     
   precisas extraídas de documentos oficiales del MINEDU, con interfaz moderna tipo ChatGPT,
  escalable a otros sectores como tributario.

  Estado: 70% completado, bloqueado por problema de importación crítico.
