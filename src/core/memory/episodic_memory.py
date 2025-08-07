"""
Memoria Episódica Avanzada
Gestiona experiencias pasadas, patrones de consulta y contexto temporal
"""
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import hashlib

# Para similaridad semántica
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

logger = logging.getLogger(__name__)

class EpisodeType(Enum):
    """Tipos de episodios de memoria"""
    QUERY_RESPONSE = "query_response"
    CALCULATION = "calculation"
    PROCEDURE_INQUIRY = "procedure_inquiry"
    LEGAL_CONSULTATION = "legal_consultation"
    ERROR_RESOLUTION = "error_resolution"
    CONTEXT_CLARIFICATION = "context_clarification"

@dataclass
class MemoryEpisode:
    """Episodio individual de memoria"""
    episode_id: str
    session_id: str
    episode_type: EpisodeType
    query: str
    response: str
    context: Dict[str, Any]
    confidence: float
    timestamp: datetime
    tags: List[str]
    success: bool
    reasoning_chain: List[str]
    related_episodes: List[str]
    metadata: Dict[str, Any]

@dataclass
class EpisodicSearchResult:
    """Resultado de búsqueda en memoria episódica"""
    relevant_episodes: List[MemoryEpisode]
    similarity_scores: List[float]
    context_summary: str
    pattern_detected: Optional[str]
    total_episodes: int

class EpisodicMemoryManager:
    """
    Gestor de memoria episódica para RAG contextual
    Mantiene experiencias pasadas y detecta patrones de consulta
    """
    
    def __init__(self, 
                 memory_dir: Optional[Path] = None,
                 max_episodes_per_session: int = 100,
                 similarity_threshold: float = 0.7):
        
        self.memory_dir = memory_dir or Path(__file__).parent / "episodic_storage"
        self.memory_dir.mkdir(exist_ok=True)
        
        self.max_episodes_per_session = max_episodes_per_session
        self.similarity_threshold = similarity_threshold
        
        # Modelo de embeddings para similaridad
        self.embeddings_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("✅ Modelo de embeddings cargado para memoria episódica")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar modelo de embeddings: {e}")
        
        # Cache de episodios en memoria
        self.episodes_cache: Dict[str, List[MemoryEpisode]] = {}
        
        # Índice de embeddings
        self.embeddings_index: Dict[str, np.ndarray] = {}
        
        # Patrones detectados
        self.detected_patterns: Dict[str, Dict[str, Any]] = {}
        
        # Cargar episodios existentes
        self._load_existing_episodes()
        
        logger.info(f"🧠 EpisodicMemoryManager inicializado - {len(self.episodes_cache)} sesiones")
    
    async def store_episode(self, 
                          session_id: str, 
                          episode: Dict[str, Any]) -> str:
        """
        Almacenar nuevo episodio de memoria
        
        Args:
            session_id: ID de sesión
            episode: Datos del episodio
            
        Returns:
            ID del episodio creado
        """
        try:
            # Generar ID único para el episodio
            episode_id = self._generate_episode_id(session_id, episode)
            
            # Crear objeto MemoryEpisode
            memory_episode = MemoryEpisode(
                episode_id=episode_id,
                session_id=session_id,
                episode_type=self._detect_episode_type(episode),
                query=episode.get("query", ""),
                response=episode.get("response", ""),
                context=episode.get("context", {}),
                confidence=episode.get("confidence", 0.0),
                timestamp=datetime.now(),
                tags=self._extract_tags(episode),
                success=episode.get("success", True),
                reasoning_chain=episode.get("reasoning_chain", []),
                related_episodes=[],
                metadata=episode.get("metadata", {})
            )
            
            # Añadir a cache
            if session_id not in self.episodes_cache:
                self.episodes_cache[session_id] = []
            
            self.episodes_cache[session_id].append(memory_episode)
            
            # Mantener límite de episodios por sesión
            if len(self.episodes_cache[session_id]) > self.max_episodes_per_session:
                self.episodes_cache[session_id] = self.episodes_cache[session_id][-self.max_episodes_per_session:]
            
            # Generar embedding si es posible
            if self.embeddings_model:
                await self._generate_episode_embedding(memory_episode)
            
            # Detectar episodios relacionados
            await self._find_related_episodes(memory_episode)
            
            # Guardar persistentemente
            await self._save_episode_to_disk(memory_episode)
            
            # Actualizar patrones
            await self._update_patterns(memory_episode)
            
            logger.info(f"🧠 Episodio guardado: {episode_id} en sesión {session_id}")
            return episode_id
            
        except Exception as e:
            logger.error(f"❌ Error guardando episodio: {e}")
            raise
    
    async def retrieve_relevant_episodes(self, 
                                       query: str, 
                                       session_id: str,
                                       max_episodes: int = 5,
                                       include_other_sessions: bool = True) -> Dict[str, Any]:
        """
        Recuperar episodios relevantes para una consulta
        
        Args:
            query: Consulta actual
            session_id: ID de sesión actual
            max_episodes: Máximo episodios a retornar
            include_other_sessions: Incluir episodios de otras sesiones
            
        Returns:
            Episodios relevantes con contexto
        """
        try:
            relevant_episodes = []
            similarity_scores = []
            
            # 1. Buscar en sesión actual
            session_episodes = self.episodes_cache.get(session_id, [])
            current_session_results = await self._search_episodes_by_similarity(
                query, session_episodes, max_episodes // 2
            )
            
            relevant_episodes.extend(current_session_results["episodes"])
            similarity_scores.extend(current_session_results["scores"])
            
            # 2. Buscar en otras sesiones si está habilitado
            if include_other_sessions:
                other_episodes = []
                for sid, episodes in self.episodes_cache.items():
                    if sid != session_id:
                        other_episodes.extend(episodes)
                
                other_session_results = await self._search_episodes_by_similarity(
                    query, other_episodes, max_episodes - len(relevant_episodes)
                )
                
                relevant_episodes.extend(other_session_results["episodes"])
                similarity_scores.extend(other_session_results["scores"])
            
            # 3. Generar resumen de contexto
            context_summary = self._generate_context_summary(relevant_episodes)
            
            # 4. Detectar patrón si existe
            pattern_detected = self._detect_query_pattern(query, relevant_episodes)
            
            return {
                "episodes": [asdict(ep) for ep in relevant_episodes],
                "similarity_scores": similarity_scores,
                "context_summary": context_summary,
                "pattern_detected": pattern_detected,
                "total_episodes": len(relevant_episodes),
                "session_episodes": len(session_episodes),
                "relevant_context": len(relevant_episodes) > 0
            }
            
        except Exception as e:
            logger.error(f"❌ Error recuperando episodios: {e}")
            return {
                "episodes": [],
                "similarity_scores": [],
                "context_summary": "",
                "pattern_detected": None,
                "total_episodes": 0,
                "session_episodes": 0,
                "relevant_context": False
            }
    
    async def _search_episodes_by_similarity(self, 
                                           query: str, 
                                           episodes: List[MemoryEpisode],
                                           max_results: int) -> Dict[str, Any]:
        """Buscar episodios por similaridad semántica"""
        
        if not self.embeddings_model or not episodes:
            return {"episodes": [], "scores": []}
        
        try:
            # Generar embedding de la query
            query_embedding = self.embeddings_model.encode(query)
            
            # Calcular similaridades
            similarities = []
            for episode in episodes:
                episode_embedding = self.embeddings_index.get(episode.episode_id)
                
                if episode_embedding is not None:
                    similarity = self._cosine_similarity(query_embedding, episode_embedding)
                    similarities.append((episode, similarity))
                else:
                    # Generar embedding si no existe
                    episode_text = f"{episode.query} {episode.response}"
                    episode_embedding = self.embeddings_model.encode(episode_text)
                    self.embeddings_index[episode.episode_id] = episode_embedding
                    
                    similarity = self._cosine_similarity(query_embedding, episode_embedding)
                    similarities.append((episode, similarity))
            
            # Filtrar por umbral y ordenar
            relevant = [(ep, score) for ep, score in similarities 
                       if score >= self.similarity_threshold]
            relevant.sort(key=lambda x: x[1], reverse=True)
            
            # Tomar top resultados
            top_results = relevant[:max_results]
            
            return {
                "episodes": [ep for ep, _ in top_results],
                "scores": [score for _, score in top_results]
            }
            
        except Exception as e:
            logger.error(f"❌ Error en búsqueda por similaridad: {e}")
            return {"episodes": [], "scores": []}
    
    def _generate_episode_id(self, session_id: str, episode: Dict[str, Any]) -> str:
        """Generar ID único para episodio"""
        content = f"{session_id}_{episode.get('query', '')}_{datetime.now().isoformat()}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def _detect_episode_type(self, episode: Dict[str, Any]) -> EpisodeType:
        """Detectar tipo de episodio basado en contenido"""
        query = episode.get("query", "").lower()
        
        if any(keyword in query for keyword in ["monto", "calcular", "cuánto", "s/"]):
            return EpisodeType.CALCULATION
        elif any(keyword in query for keyword in ["procedimiento", "cómo", "pasos", "requisito"]):
            return EpisodeType.PROCEDURE_INQUIRY
        elif any(keyword in query for keyword in ["legal", "artículo", "ley", "decreto"]):
            return EpisodeType.LEGAL_CONSULTATION
        elif "error" in episode.get("response", "").lower():
            return EpisodeType.ERROR_RESOLUTION
        else:
            return EpisodeType.QUERY_RESPONSE
    
    def _extract_tags(self, episode: Dict[str, Any]) -> List[str]:
        """Extraer tags del episodio"""
        tags = []
        
        query = episode.get("query", "").lower()
        response = episode.get("response", "").lower()
        
        # Tags temáticos
        if any(word in query for word in ["viático", "viáticos"]):
            tags.append("viaticos")
        
        if any(word in query for word in ["procedimiento", "trámite"]):
            tags.append("procedimientos")
        
        if any(word in query for word in ["monto", "calcular", "s/"]):
            tags.append("calculos")
        
        if any(word in query for word in ["ley", "decreto", "directiva"]):
            tags.append("normativa")
        
        # Tags de éxito
        if episode.get("confidence", 0) > 0.8:
            tags.append("high_confidence")
        
        if episode.get("success", True):
            tags.append("successful")
        
        return tags
    
    async def _generate_episode_embedding(self, episode: MemoryEpisode):
        """Generar embedding para episodio"""
        if not self.embeddings_model:
            return
        
        try:
            episode_text = f"{episode.query} {episode.response}"
            embedding = self.embeddings_model.encode(episode_text)
            self.embeddings_index[episode.episode_id] = embedding
            
        except Exception as e:
            logger.error(f"❌ Error generando embedding: {e}")
    
    async def _find_related_episodes(self, episode: MemoryEpisode):
        """Encontrar episodios relacionados"""
        try:
            # Buscar episodios similares en todas las sesiones
            all_episodes = []
            for episodes in self.episodes_cache.values():
                all_episodes.extend(episodes)
            
            # Excluir el episodio actual
            all_episodes = [ep for ep in all_episodes if ep.episode_id != episode.episode_id]
            
            # Buscar similares
            similar_results = await self._search_episodes_by_similarity(
                episode.query, all_episodes, 3
            )
            
            # Actualizar episodios relacionados
            episode.related_episodes = [ep.episode_id for ep in similar_results["episodes"]]
            
        except Exception as e:
            logger.error(f"❌ Error encontrando episodios relacionados: {e}")
    
    async def _save_episode_to_disk(self, episode: MemoryEpisode):
        """Guardar episodio a disco"""
        try:
            session_file = self.memory_dir / f"session_{episode.session_id}.json"
            
            # Cargar episodios existentes
            episodes_data = []
            if session_file.exists():
                with open(session_file, 'r', encoding='utf-8') as f:
                    episodes_data = json.load(f)
            
            # Añadir nuevo episodio
            episode_dict = asdict(episode)
            episode_dict["timestamp"] = episode.timestamp.isoformat()
            episode_dict["episode_type"] = episode.episode_type.value
            
            episodes_data.append(episode_dict)
            
            # Mantener límite
            if len(episodes_data) > self.max_episodes_per_session:
                episodes_data = episodes_data[-self.max_episodes_per_session:]
            
            # Guardar
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(episodes_data, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"❌ Error guardando episodio a disco: {e}")
    
    def _load_existing_episodes(self):
        """Cargar episodios existentes desde disco"""
        try:
            for session_file in self.memory_dir.glob("session_*.json"):
                session_id = session_file.stem.replace("session_", "")
                
                with open(session_file, 'r', encoding='utf-8') as f:
                    episodes_data = json.load(f)
                
                episodes = []
                for ep_data in episodes_data:
                    try:
                        episode = MemoryEpisode(
                            episode_id=ep_data["episode_id"],
                            session_id=ep_data["session_id"],
                            episode_type=EpisodeType(ep_data["episode_type"]),
                            query=ep_data["query"],
                            response=ep_data["response"],
                            context=ep_data["context"],
                            confidence=ep_data["confidence"],
                            timestamp=datetime.fromisoformat(ep_data["timestamp"]),
                            tags=ep_data["tags"],
                            success=ep_data["success"],
                            reasoning_chain=ep_data["reasoning_chain"],
                            related_episodes=ep_data["related_episodes"],
                            metadata=ep_data["metadata"]
                        )
                        episodes.append(episode)
                    except Exception as e:
                        logger.warning(f"Error cargando episodio: {e}")
                
                self.episodes_cache[session_id] = episodes
            
        except Exception as e:
            logger.error(f"❌ Error cargando episodios existentes: {e}")
    
    async def _update_patterns(self, episode: MemoryEpisode):
        """Actualizar patrones detectados"""
        try:
            # Analizar patrones por tipo de episodio
            episode_type = episode.episode_type.value
            
            if episode_type not in self.detected_patterns:
                self.detected_patterns[episode_type] = {
                    "count": 0,
                    "common_queries": [],
                    "success_rate": 0.0,
                    "avg_confidence": 0.0
                }
            
            pattern = self.detected_patterns[episode_type]
            pattern["count"] += 1
            
            # Actualizar queries comunes
            if episode.query not in pattern["common_queries"]:
                pattern["common_queries"].append(episode.query)
                if len(pattern["common_queries"]) > 10:
                    pattern["common_queries"] = pattern["common_queries"][-10:]
            
            # Actualizar métricas
            all_episodes = [ep for episodes in self.episodes_cache.values() 
                          for ep in episodes if ep.episode_type == episode.episode_type]
            
            if all_episodes:
                pattern["success_rate"] = sum(1 for ep in all_episodes if ep.success) / len(all_episodes)
                pattern["avg_confidence"] = sum(ep.confidence for ep in all_episodes) / len(all_episodes)
            
        except Exception as e:
            logger.error(f"❌ Error actualizando patrones: {e}")
    
    def _generate_context_summary(self, episodes: List[MemoryEpisode]) -> str:
        """Generar resumen de contexto de episodios"""
        if not episodes:
            return "No hay contexto episódico relevante"
        
        # Agrupar por tipo
        by_type = {}
        for episode in episodes:
            episode_type = episode.episode_type.value
            if episode_type not in by_type:
                by_type[episode_type] = []
            by_type[episode_type].append(episode)
        
        # Generar resumen
        summary_parts = []
        for episode_type, type_episodes in by_type.items():
            avg_confidence = sum(ep.confidence for ep in type_episodes) / len(type_episodes)
            summary_parts.append(f"{len(type_episodes)} {episode_type} (confianza: {avg_confidence:.2f})")
        
        return f"Contexto: {', '.join(summary_parts)}"
    
    def _detect_query_pattern(self, query: str, episodes: List[MemoryEpisode]) -> Optional[str]:
        """Detectar patrón en la consulta basado en episodios previos"""
        if not episodes:
            return None
        
        query_lower = query.lower()
        
        # Detectar patrones comunes
        for pattern_name, pattern_data in self.detected_patterns.items():
            common_queries = pattern_data.get("common_queries", [])
            
            for common_query in common_queries:
                if self._queries_similar(query_lower, common_query.lower()):
                    return f"Patrón detectado: {pattern_name} (consulta similar previa)"
        
        return None
    
    def _queries_similar(self, query1: str, query2: str) -> bool:
        """Verificar si dos consultas son similares"""
        # Implementación simple basada en keywords comunes
        words1 = set(query1.split())
        words2 = set(query2.split())
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        similarity = len(intersection) / len(union) if union else 0
        return similarity > 0.5
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcular similaridad coseno"""
        if not EMBEDDINGS_AVAILABLE:
            return 0.0
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de memoria episódica"""
        total_episodes = sum(len(episodes) for episodes in self.episodes_cache.values())
        
        return {
            "total_sessions": len(self.episodes_cache),
            "total_episodes": total_episodes,
            "embeddings_available": EMBEDDINGS_AVAILABLE,
            "embeddings_indexed": len(self.embeddings_index),
            "patterns_detected": len(self.detected_patterns),
            "pattern_summary": self.detected_patterns,
            "memory_dir": str(self.memory_dir),
            "max_episodes_per_session": self.max_episodes_per_session,
            "similarity_threshold": self.similarity_threshold
        }

# Instancia global
global_episodic_memory = EpisodicMemoryManager()