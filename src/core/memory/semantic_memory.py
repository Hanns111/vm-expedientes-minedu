"""
Memoria semántica - Fase 4
Maneja conceptos y relaciones semánticas
"""
import logging
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class SemanticConcept:
    """Concepto semántico"""
    name: str
    description: str
    related_concepts: List[str]
    confidence: float
    last_accessed: datetime

@dataclass
class SemanticRelation:
    """Relación semántica entre conceptos"""
    concept_a: str
    concept_b: str
    relation_type: str
    strength: float

class SemanticMemoryManager:
    """
    Gestor de memoria semántica para RAG avanzado
    """
    
    def __init__(self):
        self.concepts: Dict[str, SemanticConcept] = {}
        self.relations: List[SemanticRelation] = []
        self.concept_clusters: Dict[str, Set[str]] = {}
        logger.info("🔗 SemanticMemoryManager inicializado")
    
    def add_concept(self, name: str, description: str, 
                   related_concepts: List[str] = None) -> None:
        """Agregar concepto semántico"""
        concept = SemanticConcept(
            name=name,
            description=description,
            related_concepts=related_concepts or [],
            confidence=1.0,
            last_accessed=datetime.now()
        )
        self.concepts[name] = concept
    
    def add_relation(self, concept_a: str, concept_b: str, 
                    relation_type: str, strength: float = 1.0) -> None:
        """Agregar relación semántica"""
        relation = SemanticRelation(
            concept_a=concept_a,
            concept_b=concept_b,
            relation_type=relation_type,
            strength=strength
        )
        self.relations.append(relation)
    
    def get_related_concepts(self, concept_name: str, 
                           max_depth: int = 2) -> List[str]:
        """Obtener conceptos relacionados"""
        if concept_name not in self.concepts:
            return []
        
        related = set()
        to_explore = [(concept_name, 0)]
        explored = set()
        
        while to_explore and len(related) < 20:  # Limitar resultados
            current, depth = to_explore.pop(0)
            if current in explored or depth >= max_depth:
                continue
                
            explored.add(current)
            
            # Agregar conceptos directamente relacionados
            if current in self.concepts:
                for rel_concept in self.concepts[current].related_concepts:
                    if rel_concept not in explored:
                        related.add(rel_concept)
                        if depth < max_depth - 1:
                            to_explore.append((rel_concept, depth + 1))
        
        return list(related)
    
    def find_semantic_clusters(self, min_cluster_size: int = 2) -> Dict[str, Set[str]]:
        """Encontrar clusters semánticos"""
        clusters = {}
        processed = set()
        
        for concept_name in self.concepts:
            if concept_name in processed:
                continue
                
            related = self.get_related_concepts(concept_name, max_depth=1)
            if len(related) >= min_cluster_size:
                cluster_key = f"cluster_{len(clusters)}"
                clusters[cluster_key] = {concept_name} | set(related)
                processed.update(clusters[cluster_key])
        
        self.concept_clusters = clusters
        return clusters
    
    def get_concept_by_similarity(self, query: str) -> List[str]:
        """Buscar conceptos por similitud textual básica"""
        query_lower = query.lower()
        matches = []
        
        for concept_name, concept in self.concepts.items():
            # Similitud básica por palabras clave
            if (query_lower in concept_name.lower() or 
                query_lower in concept.description.lower()):
                matches.append(concept_name)
        
        return matches[:10]  # Limitar resultados
    
    def update_concept_access(self, concept_name: str) -> None:
        """Actualizar última vez que se accedió al concepto"""
        if concept_name in self.concepts:
            self.concepts[concept_name].last_accessed = datetime.now()
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Estadísticas de memoria semántica"""
        return {
            "total_concepts": len(self.concepts),
            "total_relations": len(self.relations),
            "concept_clusters": len(self.concept_clusters),
            "avg_relations_per_concept": (
                len(self.relations) / len(self.concepts) 
                if self.concepts else 0
            )
        } 