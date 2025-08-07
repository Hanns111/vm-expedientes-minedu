"""
Sistema de concordancia normativa entre fuentes
Encuentra relaciones entre ley → reglamento → directiva → jurisprudencia
"""
import logging
import re
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass
from datetime import datetime, date
import numpy as np
from pathlib import Path
import json

# Para embeddings y similaridad
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class RelatedNorm:
    """Norma relacionada con metadatos de relación"""
    norm_id: str
    norm_name: str
    article: str
    content: str
    relation_type: str  # "hierarchical", "temporal", "thematic", "contradictory"
    similarity_score: float
    legal_hierarchy: int  # 1=Constitución, 2=Ley, 3=Reglamento, 4=Directiva, 5=Jurisprudencia
    publication_date: Optional[date]
    validity_status: str  # "vigente", "derogada", "modificada"

@dataclass
class NormativeRelation:
    """Relación específica entre dos normas"""
    source_norm: str
    target_norm: str
    relation_type: str
    confidence: float
    explanation: str
    detected_patterns: List[str]

class NormativeConcordance:
    """
    Sistema de concordancia normativa usando embeddings y análisis semántico
    Encuentra relaciones entre diferentes fuentes normativas
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path(__file__).parent / "data"
        self.data_path.mkdir(exist_ok=True)
        
        # Modelo de embeddings (gratuito)
        self.embeddings_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("✅ Modelo de embeddings cargado para concordancia")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar modelo de embeddings: {e}")
        
        # Jerarquía normativa
        self.legal_hierarchy = {
            "constitución": 1,
            "ley": 2,
            "decreto ley": 2,
            "decreto legislativo": 2,
            "decreto supremo": 3,
            "reglamento": 3,
            "resolución suprema": 4,
            "resolución ministerial": 4,
            "directiva": 4,
            "resolución directoral": 5,
            "jurisprudencia": 6,
            "precedente": 6
        }
        
        # Patrones de relación
        self.relation_patterns = {
            "hierarchical": [
                r"en aplicación de la ley",
                r"reglamento de la ley",
                r"de conformidad con",
                r"en cumplimiento de",
                r"desarrollo de la ley"
            ],
            "temporal": [
                r"modifica",
                r"deroga", 
                r"sustituye",
                r"actualiza",
                r"reemplaza"
            ],
            "thematic": [
                r"viáticos",
                r"gastos de viaje",
                r"comisión de servicio",
                r"movilidad",
                r"alimentación"
            ],
            "contradictory": [
                r"excepto",
                r"salvo",
                r"no obstante",
                r"sin perjuicio",
                r"a diferencia de"
            ]
        }
        
        # Cache de embeddings
        self.embeddings_cache = {}
        
        logger.info("📋 NormativeConcordance inicializado")
    
    def find_related_norms(
        self, 
        source_article: str,
        source_norm: str,
        corpus_norms: List[Dict[str, Any]],
        max_results: int = 10
    ) -> List[RelatedNorm]:
        """
        Encontrar normas relacionadas a un artículo específico
        
        Args:
            source_article: Texto del artículo fuente
            source_norm: Nombre de la norma fuente
            corpus_norms: Lista de normas disponibles
            max_results: Máximo número de resultados
        
        Returns:
            Lista de normas relacionadas ordenadas por relevancia
        """
        try:
            related_norms = []
            
            # 1. Búsqueda por patrones explícitos
            pattern_matches = self._find_pattern_relations(source_article, corpus_norms)
            
            # 2. Búsqueda por embeddings semánticos
            if self.embeddings_model:
                semantic_matches = self._find_semantic_relations(source_article, corpus_norms)
            else:
                semantic_matches = []
            
            # 3. Búsqueda por jerarquía normativa
            hierarchical_matches = self._find_hierarchical_relations(source_norm, corpus_norms)
            
            # 4. Combinar y rankear resultados
            all_matches = pattern_matches + semantic_matches + hierarchical_matches
            
            # Eliminar duplicados y ordenar por score
            seen = set()
            unique_matches = []
            for match in all_matches:
                if match.norm_id not in seen:
                    seen.add(match.norm_id)
                    unique_matches.append(match)
            
            # Ordenar por similarity_score descendente
            unique_matches.sort(key=lambda x: x.similarity_score, reverse=True)
            
            return unique_matches[:max_results]
            
        except Exception as e:
            logger.error(f"❌ Error encontrando normas relacionadas: {e}")
            return []
    
    def _find_pattern_relations(
        self, 
        source_article: str, 
        corpus_norms: List[Dict[str, Any]]
    ) -> List[RelatedNorm]:
        """Encontrar relaciones por patrones explícitos"""
        matches = []
        source_lower = source_article.lower()
        
        for norm in corpus_norms:
            content = norm.get('content', '').lower()
            norm_name = norm.get('name', '')
            
            # Buscar patrones en cada categoría
            for relation_type, patterns in self.relation_patterns.items():
                pattern_score = 0
                detected_patterns = []
                
                for pattern in patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        pattern_score += 1
                        detected_patterns.append(pattern)
                
                if pattern_score > 0:
                    # Calcular score basado en número de patrones
                    similarity_score = min(pattern_score / len(patterns), 1.0)
                    
                    hierarchy = self._get_norm_hierarchy(norm_name)
                    
                    related_norm = RelatedNorm(
                        norm_id=norm.get('id', ''),
                        norm_name=norm_name,
                        article=norm.get('article', ''),
                        content=norm.get('content', ''),
                        relation_type=relation_type,
                        similarity_score=similarity_score,
                        legal_hierarchy=hierarchy,
                        publication_date=self._parse_date(norm.get('date')),
                        validity_status=norm.get('status', 'vigente')
                    )
                    matches.append(related_norm)
        
        return matches
    
    def _find_semantic_relations(
        self, 
        source_article: str, 
        corpus_norms: List[Dict[str, Any]]
    ) -> List[RelatedNorm]:
        """Encontrar relaciones por similaridad semántica"""
        if not self.embeddings_model:
            return []
        
        matches = []
        
        try:
            # Obtener embedding del artículo fuente
            source_embedding = self._get_embedding(source_article)
            
            for norm in corpus_norms:
                content = norm.get('content', '')
                if not content:
                    continue
                
                # Obtener embedding del contenido
                content_embedding = self._get_embedding(content)
                
                # Calcular similaridad coseno
                similarity = self._cosine_similarity(source_embedding, content_embedding)
                
                # Solo incluir si similaridad es significativa
                if similarity > 0.3:
                    hierarchy = self._get_norm_hierarchy(norm.get('name', ''))
                    
                    related_norm = RelatedNorm(
                        norm_id=norm.get('id', ''),
                        norm_name=norm.get('name', ''),
                        article=norm.get('article', ''),
                        content=content,
                        relation_type="thematic",
                        similarity_score=similarity,
                        legal_hierarchy=hierarchy,
                        publication_date=self._parse_date(norm.get('date')),
                        validity_status=norm.get('status', 'vigente')
                    )
                    matches.append(related_norm)
        
        except Exception as e:
            logger.error(f"❌ Error en búsqueda semántica: {e}")
        
        return matches
    
    def _find_hierarchical_relations(
        self, 
        source_norm: str, 
        corpus_norms: List[Dict[str, Any]]
    ) -> List[RelatedNorm]:
        """Encontrar relaciones por jerarquía normativa"""
        matches = []
        source_hierarchy = self._get_norm_hierarchy(source_norm)
        
        for norm in corpus_norms:
            norm_name = norm.get('name', '')
            norm_hierarchy = self._get_norm_hierarchy(norm_name)
            
            # Buscar relaciones jerárquicas
            relation_type = "hierarchical"
            similarity_score = 0.0
            
            if norm_hierarchy < source_hierarchy:
                # Norma superior (ley vs reglamento)
                similarity_score = 0.7
                relation_type = "hierarchical_superior"
            elif norm_hierarchy > source_hierarchy:
                # Norma inferior (reglamento vs directiva)
                similarity_score = 0.6
                relation_type = "hierarchical_inferior"
            elif norm_hierarchy == source_hierarchy:
                # Mismo nivel (ley vs ley)
                similarity_score = 0.5
                relation_type = "hierarchical_equal"
            
            if similarity_score > 0:
                related_norm = RelatedNorm(
                    norm_id=norm.get('id', ''),
                    norm_name=norm_name,
                    article=norm.get('article', ''),
                    content=norm.get('content', ''),
                    relation_type=relation_type,
                    similarity_score=similarity_score,
                    legal_hierarchy=norm_hierarchy,
                    publication_date=self._parse_date(norm.get('date')),
                    validity_status=norm.get('status', 'vigente')
                )
                matches.append(related_norm)
        
        return matches
    
    def _get_embedding(self, text: str) -> np.ndarray:
        """Obtener embedding con cache"""
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        # Limitar longitud del texto
        text = text[:512]  # Límite para modelos sentence-transformers
        
        embedding = self.embeddings_model.encode(text)
        self.embeddings_cache[text] = embedding
        
        return embedding
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calcular similaridad coseno"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)
    
    def _get_norm_hierarchy(self, norm_name: str) -> int:
        """Determinar jerarquía de una norma"""
        norm_lower = norm_name.lower()
        
        for norm_type, hierarchy in self.legal_hierarchy.items():
            if norm_type in norm_lower:
                return hierarchy
        
        return 7  # Jerarquía por defecto (más baja)
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parsear fecha de string"""
        if not date_str:
            return None
        
        try:
            # Intentar diferentes formatos
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                try:
                    return datetime.strptime(date_str, fmt).date()
                except ValueError:
                    continue
            return None
        except Exception:
            return None
    
    def analyze_normative_network(
        self, 
        corpus_norms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analizar la red completa de relaciones normativas"""
        try:
            network_analysis = {
                "total_norms": len(corpus_norms),
                "hierarchy_distribution": {},
                "temporal_coverage": {},
                "relation_matrix": {},
                "isolated_norms": [],
                "central_norms": [],
                "analysis_date": datetime.now().isoformat()
            }
            
            # Distribución por jerarquía
            for norm in corpus_norms:
                hierarchy = self._get_norm_hierarchy(norm.get('name', ''))
                hierarchy_name = self._get_hierarchy_name(hierarchy)
                network_analysis["hierarchy_distribution"][hierarchy_name] = \
                    network_analysis["hierarchy_distribution"].get(hierarchy_name, 0) + 1
            
            # Cobertura temporal
            for norm in corpus_norms:
                year = self._extract_year(norm.get('date', ''))
                if year:
                    network_analysis["temporal_coverage"][str(year)] = \
                        network_analysis["temporal_coverage"].get(str(year), 0) + 1
            
            # Identificar normas centrales (más referencias)
            norm_references = {}
            for norm in corpus_norms:
                norm_id = norm.get('id', norm.get('name', ''))
                
                # Contar referencias en otras normas
                reference_count = 0
                for other_norm in corpus_norms:
                    if norm_id != other_norm.get('id', other_norm.get('name', '')):
                        content = other_norm.get('content', '').lower()
                        if norm_id.lower() in content:
                            reference_count += 1
                
                norm_references[norm_id] = reference_count
            
            # Top 5 normas más referenciadas
            sorted_refs = sorted(norm_references.items(), key=lambda x: x[1], reverse=True)
            network_analysis["central_norms"] = [
                {"norm": norm, "references": count} 
                for norm, count in sorted_refs[:5]
            ]
            
            # Normas aisladas (sin referencias)
            network_analysis["isolated_norms"] = [
                norm for norm, count in sorted_refs if count == 0
            ]
            
            return network_analysis
            
        except Exception as e:
            logger.error(f"❌ Error analizando red normativa: {e}")
            return {"error": str(e)}
    
    def _get_hierarchy_name(self, hierarchy: int) -> str:
        """Obtener nombre de jerarquía"""
        hierarchy_names = {
            1: "Constitución",
            2: "Ley", 
            3: "Reglamento",
            4: "Resolución/Directiva",
            5: "Resolución Directoral",
            6: "Jurisprudencia",
            7: "Otros"
        }
        return hierarchy_names.get(hierarchy, "Otros")
    
    def _extract_year(self, date_str: str) -> Optional[int]:
        """Extraer año de string de fecha"""
        if not date_str:
            return None
        
        year_match = re.search(r'(19|20)\d{2}', date_str)
        if year_match:
            return int(year_match.group())
        
        return None
    
    def find_normative_conflicts(
        self, 
        corpus_norms: List[Dict[str, Any]]
    ) -> List[NormativeRelation]:
        """Detectar posibles conflictos entre normas"""
        conflicts = []
        
        try:
            for i, norm1 in enumerate(corpus_norms):
                for j, norm2 in enumerate(corpus_norms[i+1:], i+1):
                    
                    content1 = norm1.get('content', '').lower()
                    content2 = norm2.get('content', '').lower()
                    
                    # Buscar indicadores de conflicto
                    conflict_indicators = [
                        ("contradictory_amounts", self._detect_amount_conflicts(content1, content2)),
                        ("contradictory_procedures", self._detect_procedure_conflicts(content1, content2)),
                        ("temporal_conflicts", self._detect_temporal_conflicts(norm1, norm2))
                    ]
                    
                    for conflict_type, confidence in conflict_indicators:
                        if confidence > 0.6:
                            conflict = NormativeRelation(
                                source_norm=norm1.get('name', ''),
                                target_norm=norm2.get('name', ''),
                                relation_type=conflict_type,
                                confidence=confidence,
                                explanation=f"Posible conflicto detectado: {conflict_type}",
                                detected_patterns=[conflict_type]
                            )
                            conflicts.append(conflict)
            
            return conflicts
            
        except Exception as e:
            logger.error(f"❌ Error detectando conflictos: {e}")
            return []
    
    def _detect_amount_conflicts(self, content1: str, content2: str) -> float:
        """Detectar conflictos en montos"""
        # Buscar patrones de montos
        amount_pattern = r's/\s*(\d+(?:\.\d+)?)'
        
        amounts1 = re.findall(amount_pattern, content1, re.IGNORECASE)
        amounts2 = re.findall(amount_pattern, content2, re.IGNORECASE)
        
        if amounts1 and amounts2:
            # Si hay montos diferentes para conceptos similares
            return 0.7 if set(amounts1) != set(amounts2) else 0.0
        
        return 0.0
    
    def _detect_procedure_conflicts(self, content1: str, content2: str) -> float:
        """Detectar conflictos en procedimientos"""
        # Buscar indicadores de procedimientos diferentes
        procedure_indicators = [
            "días hábiles", "días calendario", "plazo", "término",
            "autorización", "aprobación", "visto bueno"
        ]
        
        conflicts = 0
        for indicator in procedure_indicators:
            if indicator in content1 and indicator in content2:
                # Buscar contexto diferente alrededor del indicador
                conflicts += 1
        
        return min(conflicts / len(procedure_indicators), 1.0)
    
    def _detect_temporal_conflicts(self, norm1: Dict, norm2: Dict) -> float:
        """Detectar conflictos temporales"""
        date1 = self._parse_date(norm1.get('date'))
        date2 = self._parse_date(norm2.get('date'))
        
        if date1 and date2:
            # Si una norma posterior contradice una anterior
            status1 = norm1.get('status', 'vigente')
            status2 = norm2.get('status', 'vigente')
            
            if status1 == 'vigente' and status2 == 'vigente' and abs((date1 - date2).days) < 30:
                return 0.8  # Normas muy cercanas en tiempo, posible conflicto
        
        return 0.0
    
    def get_concordance_summary(self) -> Dict[str, Any]:
        """Resumen del sistema de concordancia"""
        return {
            "status": "operational",
            "embeddings_available": EMBEDDINGS_AVAILABLE,
            "model_loaded": self.embeddings_model is not None,
            "hierarchy_levels": len(self.legal_hierarchy),
            "relation_types": list(self.relation_patterns.keys()),
            "cache_size": len(self.embeddings_cache),
            "features": {
                "pattern_matching": True,
                "semantic_similarity": EMBEDDINGS_AVAILABLE,
                "hierarchical_analysis": True,
                "conflict_detection": True,
                "network_analysis": True
            }
        }