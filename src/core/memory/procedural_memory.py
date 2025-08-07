"""
Memoria procedimental - Fase 4
Maneja procedimientos y flujos de trabajo
"""
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class ProcedureStatus(Enum):
    """Estados de procedimientos"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class ProcedureStep:
    """Paso de un procedimiento"""
    step_id: str
    description: str
    required_inputs: List[str]
    expected_outputs: List[str]
    estimated_duration: int  # minutos
    status: ProcedureStatus = ProcedureStatus.PENDING

@dataclass
class Procedure:
    """Procedimiento completo"""
    procedure_id: str
    name: str
    description: str
    steps: List[ProcedureStep]
    category: str
    created_at: datetime
    last_executed: Optional[datetime] = None

class ProceduralMemoryManager:
    """
    Gestor de memoria procedimental para sistemas RAG
    """
    
    def __init__(self):
        self.procedures: Dict[str, Procedure] = {}
        self.execution_history: List[Dict[str, Any]] = []
        logger.info("⚙️ ProceduralMemoryManager inicializado")
    
    def add_procedure(self, procedure_id: str, name: str, 
                     description: str, steps: List[ProcedureStep],
                     category: str = "general") -> None:
        """Agregar un procedimiento"""
        procedure = Procedure(
            procedure_id=procedure_id,
            name=name,
            description=description,
            steps=steps,
            category=category,
            created_at=datetime.now()
        )
        self.procedures[procedure_id] = procedure
    
    def get_procedure(self, procedure_id: str) -> Optional[Procedure]:
        """Obtener un procedimiento por ID"""
        return self.procedures.get(procedure_id)
    
    def search_procedures(self, query: str, category: str = None) -> List[Procedure]:
        """Buscar procedimientos por query"""
        query_lower = query.lower()
        results = []
        
        for procedure in self.procedures.values():
            if category and procedure.category != category:
                continue
                
            if (query_lower in procedure.name.lower() or 
                query_lower in procedure.description.lower()):
                results.append(procedure)
        
        return results
    
    def execute_procedure(self, procedure_id: str, 
                         inputs: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simular ejecución de procedimiento"""
        procedure = self.get_procedure(procedure_id)
        if not procedure:
            return {"error": "Procedure not found"}
        
        # Simular ejecución
        execution_record = {
            "procedure_id": procedure_id,
            "executed_at": datetime.now(),
            "inputs": inputs or {},
            "status": "completed",
            "duration_minutes": sum(step.estimated_duration for step in procedure.steps)
        }
        
        self.execution_history.append(execution_record)
        procedure.last_executed = datetime.now()
        
        return {
            "success": True,
            "procedure_name": procedure.name,
            "steps_executed": len(procedure.steps),
            "total_duration": execution_record["duration_minutes"]
        }
    
    def get_procedure_categories(self) -> List[str]:
        """Obtener categorías de procedimientos"""
        categories = set(proc.category for proc in self.procedures.values())
        return list(categories)
    
    def get_execution_stats(self) -> Dict[str, Any]:
        """Estadísticas de ejecución"""
        total_executions = len(self.execution_history)
        avg_duration = (
            sum(exec["duration_minutes"] for exec in self.execution_history) / total_executions
            if total_executions > 0 else 0
        )
        
        return {
            "total_procedures": len(self.procedures),
            "total_executions": total_executions,
            "avg_execution_duration": avg_duration,
            "categories": len(self.get_procedure_categories())
        } 