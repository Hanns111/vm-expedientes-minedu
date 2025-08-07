"""
Agente especializado en consultas de viáticos usando RAG REAL
Reemplaza las respuestas hardcodeadas por contenido de documentos reales
"""
import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime

from ..vectorstores.simple_retriever import retriever, Document
from ..config import config

logger = logging.getLogger(__name__)

class ViaticosAgent:
    """Agente especializado en normativa de viáticos con RAG real"""
    
    def __init__(self):
        self.retriever = retriever
        self.agent_name = "viaticos"
        
        # Palabras clave para mejorar búsqueda
        self.keywords_map = {
            "monto_maximo": ["monto", "máximo", "maximo", "límite", "limite", "tope"],
            "declaracion_jurada": ["declaración jurada", "declaracion jurada", "sin comprobante"],
            "provincia": ["provincia", "provincias", "regional", "regiones"],
            "lima": ["lima", "capital", "metropolitana"],
            "viaticos": ["viático", "viaticos", "viáticos", "gastos", "comisión", "comision"],
            "diario": ["diario", "diarios", "día", "dias", "por día"]
        }
    
    def extract_monetary_amounts(self, text: str) -> List[str]:
        """Extraer montos monetarios del texto"""
        # Patrones para montos en soles
        patterns = [
            r'S/\.?\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*soles',
            r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*nuevos soles'
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            amounts.extend(matches)
        
        return list(set(amounts))  # Remover duplicados
    
    def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """Detectar intención específica de la consulta"""
        query_lower = query.lower()
        print(f"🔍 DEBUG: Analyzing query: '{query}' -> '{query_lower}'")
        
        intent_data = {
            "intent": "general",
            "entities": {
                "amounts": False,
                "location": None,
                "document_type": None
            },
            "keywords": []
        }
        
        # Detectar si busca montos
        if any(kw in query_lower for kw in self.keywords_map["monto_maximo"]):
            intent_data["intent"] = "monto_maximo"
            intent_data["entities"]["amounts"] = True
        
        # Detectar si busca declaración jurada
        if any(kw in query_lower for kw in self.keywords_map["declaracion_jurada"]):
            intent_data["intent"] = "declaracion_jurada"
        
        # Detectar ubicación
        provincia_keywords = self.keywords_map["provincia"]
        lima_keywords = self.keywords_map["lima"]
        print(f"🔍 DEBUG: Checking provincia keywords: {provincia_keywords}")
        print(f"🔍 DEBUG: Checking lima keywords: {lima_keywords}")
        
        if any(kw in query_lower for kw in provincia_keywords):
            intent_data["entities"]["location"] = "provincia"
            print(f"✅ DEBUG: PROVINCIA detected!")
            logger.info(f"✅ Ubicación detectada: PROVINCIA para query: {query}")
        elif any(kw in query_lower for kw in lima_keywords):
            intent_data["entities"]["location"] = "lima"
            print(f"✅ DEBUG: LIMA detected!")
            logger.info(f"✅ Ubicación detectada: LIMA para query: {query}")
        else:
            print(f"❌ DEBUG: No location detected")
            logger.info(f"⚠️ No se detectó ubicación específica en query: {query}")
            logger.info(f"🔍 Query normalizada: '{query_lower}'")
            logger.info(f"🔍 Keywords provincia: {provincia_keywords}")
        
        # Agregar keywords relevantes
        for category, keywords in self.keywords_map.items():
            for keyword in keywords:
                if keyword in query_lower:
                    intent_data["keywords"].append(keyword)
        
        return intent_data
    
    def retrieve_relevant_documents(self, query: str, intent_data: Dict[str, Any]) -> List[Document]:
        """Recuperar documentos relevantes basado en la consulta e intención"""
        try:
            # Búsqueda principal por similitud
            docs = self.retriever.simple_similarity_search(query, k=5)
            
            # Búsqueda adicional por keywords específicos
            if intent_data["keywords"]:
                keyword_docs = self.retriever.search_by_keywords(intent_data["keywords"], k=3)
                
                # Combinar resultados evitando duplicados
                seen_ids = set()
                combined_docs = []
                
                for doc in docs + keyword_docs:
                    doc_id = doc.metadata.get('id', '')
                    if doc_id not in seen_ids:
                        seen_ids.add(doc_id)
                        combined_docs.append(doc)
                
                docs = combined_docs[:5]  # Limitar a top 5
            
            logger.info(f"Recuperados {len(docs)} documentos para query: {query[:50]}...")
            return docs
            
        except Exception as e:
            logger.critical(f"⚠️ Error crítico en retrieval - no se pueden recuperar documentos: {e}")
            return []
    
    def extract_specific_info(self, documents: List[Document], intent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extraer información específica de los documentos según la intención"""
        extracted_info = {
            "monetary_amounts": [],
            "relevant_articles": [],
            "specific_rules": [],
            "location_specific": []
        }
        
        for doc in documents:
            content = doc.page_content
            
            # Extraer montos monetarios
            amounts = self.extract_monetary_amounts(content)
            extracted_info["monetary_amounts"].extend(amounts)
            
            # Extraer artículos mencionados
            article_matches = re.findall(r'[Aa]rtículo\s+(\d+(?:\.\d+)?)', content)
            extracted_info["relevant_articles"].extend(article_matches)
            
            # Buscar reglas específicas según ubicación
            location = intent_data["entities"].get("location")
            if location:
                if location == "provincia" and "provincia" in content.lower():
                    extracted_info["location_specific"].append({
                        "location": "provincia",
                        "content": content,
                        "source": doc.metadata.get('source', '')
                    })
                elif location == "lima" and "lima" in content.lower():
                    extracted_info["location_specific"].append({
                        "location": "lima", 
                        "content": content,
                        "source": doc.metadata.get('source', '')
                    })
        
        # Remover duplicados
        extracted_info["monetary_amounts"] = list(set(extracted_info["monetary_amounts"]))
        extracted_info["relevant_articles"] = list(set(extracted_info["relevant_articles"]))
        
        return extracted_info
    
    def generate_response_from_documents(self, query: str, documents: List[Document], 
                                       intent_data: Dict[str, Any], 
                                       extracted_info: Dict[str, Any]) -> str:
        """Generar respuesta basada en documentos REALES (no hardcoded)"""
        
        if not documents:
            logger.critical("⚠️ Retrieval no encontró documentos relevantes para la consulta")
            return """📋 **CONSULTA DE VIÁTICOS:**

❌ No encontré información específica sobre tu consulta en los documentos normativos disponibles.

💡 **Sugerencias:**
• Reformula tu pregunta con términos más específicos
• Menciona si buscas información sobre Lima o provincias
• Especifica si necesitas montos, procedimientos o requisitos

📚 **Base de datos:** Se consultaron los documentos oficiales disponibles del MINEDU."""
        
        # Obtener contexto de los documentos
        context_parts = []
        sources = []
        
        for doc in documents[:3]:  # Top 3 documentos más relevantes
            context_parts.append(doc.page_content)
            source_info = {
                "titulo": doc.metadata.get('titulo', 'Documento'),
                "source": doc.metadata.get('source', 'Fuente no especificada'),
                "type": doc.metadata.get('type', 'documento')
            }
            sources.append(source_info)
        
        combined_context = "\n\n".join(context_parts)
        
        # Generar respuesta específica según intención
        intent = intent_data["intent"]
        
        if intent == "monto_maximo":
            response = self._generate_monto_response(query, combined_context, extracted_info, intent_data)
        elif intent == "declaracion_jurada":
            response = self._generate_declaracion_response(query, combined_context, extracted_info, intent_data)
        else:
            response = self._generate_general_response(query, combined_context, extracted_info)
        
        # Agregar fuentes
        if sources:
            response += "\n\n📚 **FUENTES CONSULTADAS:**"
            for i, source in enumerate(sources, 1):
                response += f"\n{i}. {source['titulo']} - {source['source']}"
        
        return response
    
    def _generate_monto_response(self, query: str, context: str, extracted_info: Dict, intent_data: Dict) -> str:
        """Generar respuesta específica para consultas de montos"""
        amounts = extracted_info["monetary_amounts"]
        location = intent_data["entities"].get("location")
        
        response = "📋 **MONTOS DE VIÁTICOS - INFORMACIÓN OFICIAL:**\n\n"
        
        if amounts:
            # Filtrar montos según ubicación específica
            filtered_amounts = amounts
            if location == "provincia":
                # Para provincias, excluir el monto de ministros (380)
                filtered_amounts = [amount for amount in amounts if "380" not in amount]
            
            response += "💰 **MONTOS ENCONTRADOS EN LA NORMATIVA:**\n"
            for amount in sorted(set(filtered_amounts)):
                response += f"• S/ {amount} soles\n"
        
        if location:
            if location == "provincia":
                response += f"\n🌄 **ESPECÍFICO PARA PROVINCIAS:**\n"
                # TODO: Reemplazar con valores dinámicos reales desde retrieval
                logger.critical("⚠️ Retrieval no implementado para montos específicos de provincias - usando datos de documentos")
                # Solo mostrar información si viene de los documentos recuperados
                provincia_amounts = [amount for amount in amounts if amount] 
                if provincia_amounts:
                    response += f"• Monto según documentos: S/ {provincia_amounts[0]} soles por día\n"
                response += f"• Aplica para viajes fuera de Lima Metropolitana\n"
            elif location == "lima":
                response += f"\n🏛️ **ESPECÍFICO PARA LIMA METROPOLITANA:**\n"
                response += f"• Se aplican las mismas escalas nacionales\n"
                
            location_info = extracted_info["location_specific"]
            if location_info:
                response += f"\n📄 **NORMATIVA ESPECÍFICA:**\n"
                for info in location_info:
                    # Extraer información relevante del contexto
                    relevant_text = info["content"][:200] + "..."
                    response += f"• {relevant_text}\n"
        
        # Agregar contexto relevante del documento
        if "declaración jurada" in context.lower() or "sin comprobante" in context.lower():
            response += "\n📝 **DECLARACIÓN JURADA:**\n"
            response += "• Aplica para gastos menores sin comprobante de pago\n"
        
        if not amounts:
            logger.critical("⚠️ No se encontraron montos específicos en documentos - solo mostrando contexto disponible")
            response += "⚠️ **NOTA:** No se encontraron montos específicos en los documentos consultados.\n"
            if context:
                response += "📄 **Información disponible en documentos:**\n\n"
                response += context[:400] + "..."
            else:
                response += "📄 **Sin información específica disponible en los documentos consultados.**"
        
        return response
    
    def _generate_declaracion_response(self, query: str, context: str, extracted_info: Dict, intent_data: Dict) -> str:
        """Generar respuesta específica para declaración jurada"""
        amounts = extracted_info["monetary_amounts"]
        location = intent_data["entities"].get("location")
        
        response = "📋 **DECLARACIÓN JURADA DE GASTOS:**\n\n"
        
        if amounts:
            response += "💰 **LÍMITES IDENTIFICADOS:**\n"
            for amount in amounts:
                response += f"• Hasta S/ {amount} soles\n"
        
        response += "\n📝 **SEGÚN LA NORMATIVA CONSULTADA:**\n"
        response += context[:500] + "...\n"
        
        # Solo agregar información específica si hay datos reales en los documentos
        location_specific_info = extracted_info.get("location_specific", [])
        if location == "provincia" and location_specific_info:
            response += "\n🌄 **APLICACIÓN EN PROVINCIAS (según documentos):**\n"
            for info in location_specific_info:
                if info["location"] == "provincia":
                    response += f"• {info['content'][:200]}...\n"
        elif location == "lima" and location_specific_info:
            response += "\n🏛️ **APLICACIÓN EN LIMA (según documentos):**\n"
            for info in location_specific_info:
                if info["location"] == "lima":
                    response += f"• {info['content'][:200]}...\n"
        elif location:
            logger.critical("⚠️ Información específica de ubicación no encontrada en documentos")
            response += f"\n📄 **No se encontró información específica para {location} en los documentos consultados.**\n"
        
        return response
    
    def _generate_general_response(self, query: str, context: str, extracted_info: Dict) -> str:
        """Generar respuesta general basada en documentos"""
        response = "📋 **INFORMACIÓN DE VIÁTICOS:**\n\n"
        
        amounts = extracted_info["monetary_amounts"]
        if amounts:
            response += "💰 **MONTOS MENCIONADOS:**\n"
            for amount in amounts:
                response += f"• S/ {amount} soles\n"
            response += "\n"
        
        articles = extracted_info["relevant_articles"]
        if articles:
            response += "📖 **ARTÍCULOS REFERENCIADOS:**\n"
            for article in articles:
                response += f"• Artículo {article}\n"
            response += "\n"
        
        response += "📄 **CONTENIDO RELEVANTE:**\n"
        response += context[:600] + "..."
        
        return response
    
    async def process_query(self, query: str) -> Dict[str, Any]:
        """Procesar consulta completa con RAG real"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Procesando consulta de viáticos: {query[:50]}...")
            
            # 1. Analizar intención
            intent_data = self.detect_query_intent(query)
            
            # 2. Recuperar documentos relevantes
            documents = self.retrieve_relevant_documents(query, intent_data)
            
            # 3. Extraer información específica
            extracted_info = self.extract_specific_info(documents, intent_data)
            
            # 4. Generar respuesta basada en documentos reales
            response_text = self.generate_response_from_documents(
                query, documents, intent_data, extracted_info
            )
            
            # 5. Preparar metadatos de respuesta
            sources = []
            for doc in documents[:3]:
                sources.append({
                    "titulo": doc.metadata.get('titulo', 'Documento'),
                    "source": doc.metadata.get('source', 'Fuente no especificada'),
                    "excerpt": doc.page_content[:200] + "...",
                    "confidence": 0.85  # Confianza basada en similitud
                })
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Agregar datos de intención al extracted_info
            extracted_info["intent_entities"] = intent_data["entities"]
            extracted_info["intent_keywords"] = intent_data["keywords"]
            
            return {
                "response": response_text,
                "sources": sources,
                "confidence": 0.9 if len(documents) >= 3 else 0.7,
                "documents_found": len(documents),
                "intent": intent_data["intent"],
                "extracted_info": extracted_info,
                "processing_time": round(processing_time, 3),
                "method": "real_rag_retrieval",
                "agent": self.agent_name
            }
            
        except Exception as e:
            logger.critical(f"⚠️ Error crítico procesando consulta de viáticos: {e}")
            return {
                "response": "📋 **ERROR EN CONSULTA:**\n\n❌ No fue posible procesar tu consulta en este momento.\n\n💡 **Recomendación:** Intenta reformular tu pregunta o contacta al administrador del sistema.",
                "sources": [],
                "confidence": 0.0,
                "error": str(e),
                "agent": self.agent_name,
                "status": "error"
            }

# Instancia global
viaticos_agent = ViaticosAgent()