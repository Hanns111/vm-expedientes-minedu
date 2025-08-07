"""
Cadena RAG semántica avanzada usando LangChain
Reemplaza las respuestas hardcoded con retrieval real
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import json
import re

try:
    from langchain.chains import RetrievalQA
    from langchain.prompts import PromptTemplate
    from langchain.schema import Document
    from langchain.callbacks.manager import CallbackManagerForChainRun
    from langchain.memory import ConversationBufferWindowMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Imports locales
from ..hybrid.hybrid_search import HybridSearch

logger = logging.getLogger(__name__)

class SemanticRAGChain:
    """
    Cadena RAG semántica que integra el sistema híbrido existente
    con LangChain para eliminar respuestas hardcoded
    """

    def __init__(self,
                 chunks_path: Optional[Path] = None,
                 use_memory: bool = True):

        self.chunks_path = chunks_path or Path("data/processed/chunks.json")
        self.use_memory = use_memory

        # Sistema híbrido existente (ya probado y funcional)
        self.hybrid_search = HybridSearch(
            bm25_vectorstore_path="data/vectorstores/bm25.pkl",
            tfidf_vectorstore_path="data/vectorstores/tfidf.pkl",
            transformer_vectorstore_path="data/vectorstores/transformers.pkl"
        )

        # Template de prompts para respuestas legales
        self.prompt_template = self._create_legal_prompt_template()

        # Memoria conversacional
        self.memory = ConversationBufferWindowMemory(
            k=5,  # Últimas 5 interacciones
            memory_key="chat_history",
            return_messages=True
        ) if use_memory else None

        # Cargar documentos
        self.documents = self._load_documents()

        logger.info(f"📚 SemanticRAGChain inicializado con {len(self.documents)} documentos")

    def _create_legal_prompt_template(self) -> str:
        """Crear template optimizado para consultas legales"""
        return """Eres un asistente especializado en normativa del Ministerio de Educación del Perú.

CONTEXTO NORMATIVO:
{context}

HISTORIAL DE CONVERSACIÓN:
{chat_history}

CONSULTA DEL USUARIO:
{question}

INSTRUCCIONES:
1. Responde basándote ÚNICAMENTE en el contexto normativo proporcionado
2. Cita específicamente las fuentes (directivas, artículos, numerales)
3. Si mencionas montos, especifica la normativa exacta
4. Si no encuentras información suficiente, indícalo claramente
5. Usa formato profesional apropiado para consultas gubernamentales

RESPUESTA:"""

    def _load_documents(self) -> List[Document]:
        """Cargar documentos desde chunks.json"""
        try:
            if not self.chunks_path.exists():
                logger.warning(f"Archivo de chunks no encontrado: {self.chunks_path}")
                return []

            with open(self.chunks_path, 'r', encoding='utf-8') as f:
                chunks_data = json.load(f)

            documents = []

            # Convertir chunks a formato LangChain Document
            if isinstance(chunks_data, list):
                chunks = chunks_data
            elif isinstance(chunks_data, dict) and 'chunks' in chunks_data:
                chunks = chunks_data['chunks']
            else:
                logger.error("Formato de chunks no reconocido")
                return []

            for chunk in chunks:
                if isinstance(chunk, dict) and 'content' in chunk:
                    doc = Document(
                        page_content=chunk['content'],
                        metadata={
                            'source': chunk.get('source', 'Unknown'),
                            'chunk_id': chunk.get('id', ''),
                            'chunk_index': chunk.get('chunk_index', 0)
                        }
                    )
                    documents.append(doc)

            logger.info(f"✅ Cargados {len(documents)} documentos")
            return documents

        except Exception as e:
            logger.error(f"Error cargando documentos: {e}")
            return []

    def search_and_generate(self,
                          query: str,
                          max_docs: int = 5) -> Dict[str, Any]:
        """
        Buscar documentos relevantes y generar respuesta
        ESTE MÉTODO REEMPLAZA LAS RESPUESTAS HARDCODED
        """
        try:
            # 1. Búsqueda híbrida (reutiliza sistema existente probado)
            search_results = self.hybrid_search.search(
                query=query,
                top_k=max_docs
            )

            if not search_results:
                return {
                    "answer": "No se encontraron documentos relevantes para responder su consulta. Por favor, reformule su pregunta o consulte directamente las normativas vigentes.",
                    "sources": [],
                    "confidence": 0.0,
                    "method": "semantic_rag_no_results"
                }

            # 2. Preparar contexto para el prompt
            context_docs = []
            sources_info = []

            for doc in search_results[:max_docs]:
                context_docs.append(f"Fuente: {doc.get('source', 'Unknown')}\nContenido: {doc.get('content', '')}")
                sources_info.append({
                    'source': doc.get('source', 'Unknown'),
                    'content': doc.get('content', '')[:200] + '...',
                    'score': doc.get('score', 0.0)
                })

            context = "\n\n".join(context_docs)

            # 3. Preparar historial de conversación
            chat_history = ""
            if self.memory:
                try:
                    history = self.memory.load_memory_variables({})
                    chat_history = str(history.get('chat_history', ''))
                except:
                    chat_history = ""

            # 4. Generar respuesta usando template
            # Por ahora usamos un LLM simple simulado, en producción sería OpenAI/Anthropic
            response = self._generate_response_with_context(
                query=query,
                context=context,
                chat_history=chat_history
            )

            # 5. Guardar en memoria si está habilitada
            if self.memory:
                try:
                    self.memory.save_context(
                        inputs={"question": query},
                        outputs={"answer": response}
                    )
                except Exception as e:
                    logger.warning(f"Error guardando en memoria: {e}")

            return {
                "answer": response,
                "sources": sources_info,
                "confidence": 0.8,  # Confianza fija por ahora
                "method": "semantic_rag_langchain",
                "documents_found": len(search_results)
            }

        except Exception as e:
            logger.error(f"Error en search_and_generate: {e}")
            return {
                "answer": f"Error procesando la consulta: {str(e)}",
                "sources": [],
                "confidence": 0.0,
                "method": "semantic_rag_error"
            }

    def _generate_response_with_context(self,
                                      query: str,
                                      context: str,
                                      chat_history: str) -> str:
        """
        Generar respuesta basada en contexto
        NOTA: En producción esto usaría un LLM real (OpenAI, Anthropic, etc.)
        Por ahora implementamos lógica rule-based inteligente
        """

        # Análisis de la query para determinar tipo de respuesta
        query_lower = query.lower()

        # Buscar montos específicos en el contexto
        montos_encontrados = re.findall(r's/\s*(\d+(?:\.\d+)?)', context.lower())

        # Detectar tipo de consulta
        if any(keyword in query_lower for keyword in ['monto', 'máximo', 'cuánto', 'precio']):
            if montos_encontrados:
                monto_principal = montos_encontrados[0]

                # Buscar fuente específica
                fuente_match = re.search(r'fuente:\s*([^\n]+)', context, re.IGNORECASE)
                fuente = fuente_match.group(1) if fuente_match else "normativa vigente"

                response = f"""Según la {fuente}, el monto establecido es de S/ {monto_principal}.

Esta información se basa en la documentación normativa oficial del Ministerio de Educación.

Para consultas específicas sobre su caso particular, recomendamos verificar con el área administrativa correspondiente, ya que pueden existir excepciones o actualizaciones recientes no reflejadas en esta consulta.

Fuente: {fuente}"""
            else:
                response = f"""Basándome en la documentación disponible, no se encontró un monto específico que responda directamente a su consulta sobre "{query}".

Le recomiendo:
1. Consultar directamente las normativas más recientes
2. Contactar al área administrativa competente
3. Revisar si existen directivas específicas para su caso

La información puede variar según el tipo de servidor, destino, y normativa específica aplicable."""

        elif any(keyword in query_lower for keyword in ['procedimiento', 'cómo', 'requisito', 'solicitar']):
            response = f"""Según la normativa consultada, para su consulta sobre "{query}":

{self._extract_procedural_info(context)}

IMPORTANTE: Esta información se basa en la documentación disponible. Para procedimientos específicos, verifique:
- Las directivas más recientes de su entidad
- Los requisitos particulares de su caso
- Las actualizaciones normativas vigentes

Recomendamos confirmar estos pasos con el área administrativa correspondiente."""

        else:
            # Respuesta general basada en contexto
            response = f"""Basándome en la normativa del Ministerio de Educación consultada:

{self._extract_relevant_info(context, query)}

Esta respuesta se fundamenta en la documentación oficial disponible. Para información más específica o casos particulares, recomendamos consultar directamente las fuentes normativas o contactar al área administrativa competente.

NOTA: La normativa puede tener actualizaciones o casos especiales no cubiertos en esta consulta general."""

        return response

    def _extract_procedural_info(self, context: str) -> str:
        """Extraer información de procedimientos del contexto"""
        lines = context.split('\n')
        procedural_lines = []

        for line in lines:
            if any(keyword in line.lower() for keyword in
                   ['solicitar', 'presentar', 'requisito', 'documento', 'plazo', 'autorización']):
                cleaned_line = line.strip()
                if len(cleaned_line) > 20:  # Filtrar líneas muy cortas
                    procedural_lines.append(f"• {cleaned_line}")

        if procedural_lines:
            return '\n'.join(procedural_lines[:5])  # Máximo 5 puntos
        else:
            return "Se requiere revisar la normativa específica para obtener los procedimientos detallados."

    def _extract_relevant_info(self, context: str, query: str) -> str:
        """Extraer información más relevante del contexto"""
        # Implementación simple que toma las primeras líneas sustanciales
        lines = context.split('\n')
        relevant_lines = []

        query_keywords = query.lower().split()

        for line in lines:
            line_clean = line.strip()
            if len(line_clean) > 30:  # Líneas sustanciales
                # Verificar si contiene keywords de la query
                if any(keyword in line_clean.lower() for keyword in query_keywords):
                    relevant_lines.append(line_clean)
                elif len(relevant_lines) < 3:  # Incluir contexto general
                    relevant_lines.append(line_clean)

        if relevant_lines:
            return '\n\n'.join(relevant_lines[:3])  # Máximo 3 párrafos
        else:
            return "La información específica requiere consulta directa de las normativas correspondientes."

    def get_chain_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de la cadena"""
        return {
            "documents_loaded": len(self.documents),
            "memory_enabled": self.memory is not None,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "hybrid_search_status": "active",
            "chunks_file": str(self.chunks_path),
            "chunks_exists": self.chunks_path.exists()
        }

# Instancia global (comentada para evitar problemas en import)
# global_semantic_rag = SemanticRAGChain() 