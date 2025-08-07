"""
Sistema de Memoria Episódica Avanzada - Fase 4: RAGC
Memoria conversacional, episódica, semántica y procedimental
"""

from .episodic_memory import EpisodicMemoryManager, EpisodeType
from .conversational_memory import ConversationalMemoryManager
from .semantic_memory import SemanticMemoryManager
from .procedural_memory import ProceduralMemoryManager

__all__ = [
    'EpisodicMemoryManager',
    'ConversationalMemoryManager',
    'SemanticMemoryManager', 
    'ProceduralMemoryManager',
    'EpisodeType'
]