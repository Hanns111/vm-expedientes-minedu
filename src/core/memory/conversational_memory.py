"""
Gestor de memoria conversacional - Fase 4
Maneja la memoria a corto y largo plazo de conversaciones
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class ConversationTurn:
    """Un turno de conversación"""
    user_input: str
    ai_response: str
    timestamp: datetime
    confidence: float
    context: Dict[str, Any]

class ConversationalMemoryManager:
    """
    Gestor de memoria conversacional para sistemas RAG
    """
    
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self.conversations: Dict[str, List[ConversationTurn]] = {}
        self.active_sessions: Dict[str, datetime] = {}
        logger.info("🧠 ConversationalMemoryManager inicializado")
    
    def add_turn(self, session_id: str, user_input: str, ai_response: str, 
                 confidence: float = 1.0, context: Dict[str, Any] = None) -> None:
        """Agregar un turno de conversación"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
            
        turn = ConversationTurn(
            user_input=user_input,
            ai_response=ai_response,
            timestamp=datetime.now(),
            confidence=confidence,
            context=context or {}
        )
        
        self.conversations[session_id].append(turn)
        self.active_sessions[session_id] = datetime.now()
        
        # Mantener solo los últimos N turnos
        if len(self.conversations[session_id]) > self.max_turns:
            self.conversations[session_id] = self.conversations[session_id][-self.max_turns:]
    
    def get_conversation_history(self, session_id: str) -> List[ConversationTurn]:
        """Obtener historial de conversación"""
        return self.conversations.get(session_id, [])
    
    def get_recent_context(self, session_id: str, num_turns: int = 3) -> str:
        """Obtener contexto reciente como string"""
        history = self.get_conversation_history(session_id)
        recent = history[-num_turns:] if history else []
        
        context_parts = []
        for turn in recent:
            context_parts.append(f"Usuario: {turn.user_input}")
            context_parts.append(f"Asistente: {turn.ai_response}")
        
        return "\n".join(context_parts)
    
    def clear_session(self, session_id: str) -> None:
        """Limpiar sesión"""
        if session_id in self.conversations:
            del self.conversations[session_id]
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Estadísticas de memoria"""
        total_turns = sum(len(conv) for conv in self.conversations.values())
        return {
            "active_sessions": len(self.active_sessions),
            "total_conversations": len(self.conversations),
            "total_turns": total_turns,
            "max_turns_per_session": self.max_turns
        } 