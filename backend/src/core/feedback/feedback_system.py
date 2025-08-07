"""
Sistema de feedback y rating para mejora continua del RAG
Integra con PostgreSQL existente para análisis de calidad
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from pydantic import BaseModel, validator

from ..database.repositories import UnitOfWork
from ..database.models import QueryLog, User

class FeedbackRequest(BaseModel):
    """Request model para feedback del usuario"""
    query_log_id: UUID
    rating: int  # 1-5 stars
    feedback_text: Optional[str] = None
    feedback_type: str = "quality"  # quality, relevance, completeness
    improvement_suggestions: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Rating must be between 1 and 5')
        return v
    
    @validator('feedback_type')
    def validate_feedback_type(cls, v):
        allowed_types = ['quality', 'relevance', 'completeness', 'accuracy', 'speed']
        if v not in allowed_types:
            raise ValueError(f'Feedback type must be one of: {allowed_types}')
        return v

class FeedbackAnalytics(BaseModel):
    """Analytics del sistema de feedback"""
    average_rating: float
    total_feedback_count: int
    rating_distribution: Dict[int, int]
    common_issues: List[Dict[str, Any]]
    improvement_areas: List[str]
    monthly_trend: List[Dict[str, Any]]

class FeedbackSystem:
    """Sistema de feedback y mejora continua"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def submit_feedback(
        self,
        user_id: UUID,
        feedback_request: FeedbackRequest
    ) -> Dict[str, Any]:
        """Enviar feedback del usuario"""
        async with UnitOfWork(self.session) as uow:
            try:
                # Verificar que el query_log existe y pertenece al usuario
                query_log = await uow.queries.get_by_id(feedback_request.query_log_id)
                if not query_log or query_log.user_id != user_id:
                    raise ValueError("Query log not found or access denied")
                
                # Crear registro de feedback usando SystemMetrics
                feedback_data = {
                    "metric_name": "user_feedback",
                    "value": float(feedback_request.rating),
                    "metric_type": "gauge",
                    "labels": {
                        "query_log_id": str(feedback_request.query_log_id),
                        "user_id": str(user_id),
                        "feedback_type": feedback_request.feedback_type,
                        "query_method": query_log.method,
                        "agent_used": query_log.agent_used,
                        "feedback_text": feedback_request.feedback_text,
                        "improvement_suggestions": feedback_request.improvement_suggestions,
                        "original_confidence": query_log.confidence_score,
                        "processing_time": query_log.processing_time,
                        "used_fallback": query_log.used_fallback
                    }
                }
                
                await uow.metrics.record_metric(**feedback_data)
                
                # Log de auditoría
                await uow.audit.log_action(
                    user_id=user_id,
                    action="submit_feedback",
                    resource="query_feedback",
                    resource_id=str(feedback_request.query_log_id),
                    ip_address="system",
                    user_agent="feedback_system",
                    endpoint="/api/feedback",
                    method="POST",
                    status_code=200,
                    response_time=0.1,
                    details={
                        "rating": feedback_request.rating,
                        "feedback_type": feedback_request.feedback_type,
                        "has_text_feedback": bool(feedback_request.feedback_text),
                        "has_suggestions": bool(feedback_request.improvement_suggestions)
                    }
                )
                
                await uow.commit()
                
                return {
                    "success": True,
                    "feedback_id": str(uuid4()),
                    "message": "Feedback submitted successfully",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
            except Exception as e:
                await uow.rollback()
                raise e
    
    async def get_feedback_analytics(
        self,
        days: int = 30,
        user_id: Optional[UUID] = None
    ) -> FeedbackAnalytics:
        """Obtener analytics del feedback"""
        async with UnitOfWork(self.session) as uow:
            try:
                # Fecha límite
                since = datetime.now(timezone.utc) - timedelta(days=days)
                
                # Query base para feedback
                feedback_metrics = await uow.metrics.get_latest_metrics(
                    metric_name="user_feedback",
                    hours=days * 24
                )
                
                if not feedback_metrics:
                    return FeedbackAnalytics(
                        average_rating=0.0,
                        total_feedback_count=0,
                        rating_distribution={},
                        common_issues=[],
                        improvement_areas=[],
                        monthly_trend=[]
                    )
                
                # Calcular métricas
                ratings = [m.value for m in feedback_metrics]
                total_count = len(ratings)
                average_rating = sum(ratings) / total_count if total_count > 0 else 0.0
                
                # Distribución de ratings
                rating_distribution = {}
                for rating in range(1, 6):
                    rating_distribution[rating] = len([r for r in ratings if int(r) == rating])
                
                # Identificar problemas comunes (ratings bajos)
                low_rating_feedback = [
                    m for m in feedback_metrics 
                    if m.value <= 2.0 and m.labels.get("feedback_text")
                ]
                
                common_issues = []
                for feedback in low_rating_feedback[:10]:  # Top 10 issues
                    common_issues.append({
                        "rating": feedback.value,
                        "feedback_text": feedback.labels.get("feedback_text", ""),
                        "feedback_type": feedback.labels.get("feedback_type", ""),
                        "method": feedback.labels.get("query_method", ""),
                        "agent": feedback.labels.get("agent_used", ""),
                        "timestamp": feedback.timestamp.isoformat()
                    })
                
                # Áreas de mejora basadas en feedback
                improvement_areas = []
                
                # Analizar por método
                method_ratings = {}
                for m in feedback_metrics:
                    method = m.labels.get("query_method", "unknown")
                    if method not in method_ratings:
                        method_ratings[method] = []
                    method_ratings[method].append(m.value)
                
                for method, ratings in method_ratings.items():
                    avg_rating = sum(ratings) / len(ratings)
                    if avg_rating < 3.5:
                        improvement_areas.append(f"Método '{method}' - Rating promedio: {avg_rating:.2f}")
                
                # Analizar por agente
                agent_ratings = {}
                for m in feedback_metrics:
                    agent = m.labels.get("agent_used", "unknown")
                    if agent not in agent_ratings:
                        agent_ratings[agent] = []
                    agent_ratings[agent].append(m.value)
                
                for agent, ratings in agent_ratings.items():
                    avg_rating = sum(ratings) / len(ratings)
                    if avg_rating < 3.5:
                        improvement_areas.append(f"Agente '{agent}' - Rating promedio: {avg_rating:.2f}")
                
                # Tendencia mensual (últimos 6 meses)
                monthly_trend = []
                for month_offset in range(6):
                    month_start = datetime.now(timezone.utc).replace(day=1) - timedelta(days=30 * month_offset)
                    month_end = month_start + timedelta(days=30)
                    
                    month_feedback = [
                        m for m in feedback_metrics 
                        if month_start <= m.timestamp <= month_end
                    ]
                    
                    if month_feedback:
                        month_ratings = [m.value for m in month_feedback]
                        monthly_trend.append({
                            "month": month_start.strftime("%Y-%m"),
                            "average_rating": sum(month_ratings) / len(month_ratings),
                            "feedback_count": len(month_ratings)
                        })
                
                monthly_trend.reverse()  # Orden cronológico
                
                return FeedbackAnalytics(
                    average_rating=round(average_rating, 2),
                    total_feedback_count=total_count,
                    rating_distribution=rating_distribution,
                    common_issues=common_issues,
                    improvement_areas=improvement_areas,
                    monthly_trend=monthly_trend
                )
                
            except Exception as e:
                raise e
    
    async def get_quality_insights(self) -> Dict[str, Any]:
        """Obtener insights de calidad para mejora del sistema"""
        async with UnitOfWork(self.session) as uow:
            try:
                # Obtener feedback reciente
                recent_feedback = await uow.metrics.get_latest_metrics(
                    metric_name="user_feedback",
                    hours=24 * 7  # última semana
                )
                
                if not recent_feedback:
                    return {"insights": "Insufficient data for analysis"}
                
                insights = {
                    "total_feedback_this_week": len(recent_feedback),
                    "average_rating_this_week": sum(m.value for m in recent_feedback) / len(recent_feedback),
                    "quality_trends": {},
                    "recommendations": []
                }
                
                # Análisis por confianza del sistema vs rating del usuario
                confidence_vs_rating = []
                for feedback in recent_feedback:
                    original_confidence = feedback.labels.get("original_confidence")
                    if original_confidence:
                        confidence_vs_rating.append({
                            "system_confidence": float(original_confidence),
                            "user_rating": feedback.value,
                            "difference": feedback.value - float(original_confidence) * 5  # Normalizar confidence a escala 1-5
                        })
                
                # Recomendaciones basadas en análisis
                if confidence_vs_rating:
                    avg_difference = sum(item["difference"] for item in confidence_vs_rating) / len(confidence_vs_rating)
                    
                    if avg_difference < -1:
                        insights["recommendations"].append("Sistema sobreconfidente - calibrar confianza hacia abajo")
                    elif avg_difference > 1:
                        insights["recommendations"].append("Sistema subconfidente - hay oportunidad de mejorar confianza")
                
                # Análisis de métodos con bajo rating
                low_rating_methods = {}
                for feedback in recent_feedback:
                    if feedback.value <= 2:
                        method = feedback.labels.get("query_method", "unknown")
                        low_rating_methods[method] = low_rating_methods.get(method, 0) + 1
                
                if low_rating_methods:
                    worst_method = max(low_rating_methods.items(), key=lambda x: x[1])
                    insights["recommendations"].append(f"Revisar método '{worst_method[0]}' - {worst_method[1]} ratings bajos")
                
                insights["quality_trends"] = {
                    "confidence_calibration": avg_difference if confidence_vs_rating else 0,
                    "low_rating_methods": low_rating_methods
                }
                
                return insights
                
            except Exception as e:
                return {"error": str(e)}

# Funciones de utilidad para FastAPI endpoints
async def submit_user_feedback(
    user_id: UUID,
    feedback_request: FeedbackRequest,
    session: AsyncSession
) -> Dict[str, Any]:
    """Endpoint helper para enviar feedback"""
    feedback_system = FeedbackSystem(session)
    return await feedback_system.submit_feedback(user_id, feedback_request)

async def get_system_feedback_analytics(
    session: AsyncSession,
    days: int = 30
) -> FeedbackAnalytics:
    """Endpoint helper para obtener analytics"""
    feedback_system = FeedbackSystem(session)
    return await feedback_system.get_feedback_analytics(days=days)

async def get_system_quality_insights(session: AsyncSession) -> Dict[str, Any]:
    """Endpoint helper para obtener insights de calidad"""
    feedback_system = FeedbackSystem(session)
    return await feedback_system.get_quality_insights()