"""
Gestor de memoria conversacional para RAG
Maneja el historial de conversaciones
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

try:
    from langchain.memory import ConversationBufferWindowMemory
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)

class ConversationalMemoryManager:
    """
    Gestor de memoria conversacional para el sistema RAG
    """
    
    def __init__(self, window_size: int = 5):
        self.window_size = window_size
        self.conversations = {}
        self.current_session_id = None
        
        if LANGCHAIN_AVAILABLE:
            self.memory = ConversationBufferWindowMemory(
                k=window_size,
                memory_key="chat_history",
                return_messages=True
            )
        else:
            self.memory = None
            
        logger.info(f"💭 ConversationalMemoryManager inicializado (ventana: {window_size})")
    
    def add_exchange(self, user_input: str, ai_response: str, session_id: str = "default"):
        """Agregar intercambio a la memoria"""
        if session_id not in self.conversations:
            self.conversations[session_id] = []
        
        exchange = {
            "timestamp": datetime.now(),
            "user": user_input,
            "ai": ai_response
        }
        
        self.conversations[session_id].append(exchange)
        
        # Mantener solo los últimos N intercambios
        if len(self.conversations[session_id]) > self.window_size:
            self.conversations[session_id] = self.conversations[session_id][-self.window_size:]
    
    def get_history(self, session_id: str = "default") -> List[Dict[str, Any]]:
        """Obtener historial de conversación"""
        return self.conversations.get(session_id, [])
    
    def clear_session(self, session_id: str = "default"):
        """Limpiar sesión específica"""
        if session_id in self.conversations:
            del self.conversations[session_id]
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas de memoria"""
        return {
            "active_sessions": len(self.conversations),
            "window_size": self.window_size,
            "langchain_available": LANGCHAIN_AVAILABLE,
            "total_exchanges": sum(len(conv) for conv in self.conversations.values())
        } 