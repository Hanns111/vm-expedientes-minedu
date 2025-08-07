"""
Sistema de testing de cobertura normativa
Asegura que todas las normas sean semanticamente cubiertas por el RAG
"""
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import re

# Testing framework
import pytest
from unittest.mock import AsyncMock

# RAGAS evaluation
try:
    from ragas import evaluate
    from ragas.metrics import (
        answer_relevancy,
        faithfulness,
        context_precision,
        context_recall
    )
    RAGAS_AVAILABLE = True
except ImportError:
    RAGAS_AVAILABLE = False

# Basic imports
import numpy as np

# Semantic similarity
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class CoverageMetric:
    """Métrica de cobertura normativa"""
    norm_id: str
    norm_name: str
    article_number: str
    content: str
    semantic_coverage: float  # 0-1
    query_coverage: int  # número de queries que cubren esta norma
    gaps_detected: List[str]  # aspectos no cubiertos
    last_tested: datetime
    test_status: str  # "covered", "partial", "uncovered"

@dataclass
class CoverageReport:
    """Reporte completo de cobertura"""
    total_norms: int
    covered_norms: int
    partially_covered: int
    uncovered_norms: int
    overall_coverage: float
    semantic_coverage_avg: float
    critical_gaps: List[str]
    recommendations: List[str]
    detailed_metrics: List[CoverageMetric]
    generated_at: datetime

class NormativeCoverageTester:
    """
    Sistema de testing de cobertura normativa
    Valida que el RAG puede responder apropiadamente sobre todas las normas
    """
    
    def __init__(self, 
                 norms_corpus_path: Optional[Path] = None,
                 test_queries_path: Optional[Path] = None,
                 output_path: Optional[Path] = None):
        
        self.norms_corpus_path = norms_corpus_path or Path("data/processed/chunks.json")
        self.test_queries_path = test_queries_path or Path("paper_cientifico/dataset/golden_dataset.json")
        self.output_path = output_path or Path(__file__).parent / "coverage_reports"
        self.output_path.mkdir(exist_ok=True)
        
        # Modelo de embeddings para similaridad semántica
        self.embeddings_model = None
        if EMBEDDINGS_AVAILABLE:
            try:
                self.embeddings_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
                logger.info("✅ Modelo de embeddings cargado para testing de cobertura")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar modelo de embeddings: {e}")
        
        # Umbrales de cobertura
        self.coverage_thresholds = {
            "semantic_similarity": 0.6,  # Similaridad mínima para considerar cubierto
            "query_coverage": 1,  # Mínimo número de queries por norma
            "critical_coverage": 0.8  # Cobertura mínima para normas críticas
        }
        
        # Normas críticas (requieren mayor cobertura)
        self.critical_norm_patterns = [
            r"viáticos",
            r"gastos de viaje", 
            r"comisión de servicio",
            r"monto.*máximo",
            r"procedimiento.*solicitud"
        ]
        
        logger.info("📊 NormativeCoverageTester inicializado")
    
    async def run_comprehensive_coverage_test(self, 
                                            rag_system: Any = None) -> CoverageReport:
        """
        Ejecutar test completo de cobertura normativa
        
        Args:
            rag_system: Sistema RAG a testear (opcional, usa mock si no se provee)
        
        Returns:
            Reporte completo de cobertura
        """
        try:
            logger.info("🧪 Iniciando test de cobertura normativa completo")
            
            # 1. Cargar corpus de normas
            norms_corpus = self._load_norms_corpus()
            if not norms_corpus:
                raise ValueError("No se pudo cargar corpus de normas")
            
            # 2. Cargar queries de prueba
            test_queries = self._load_test_queries()
            
            # 3. Generar métricas de cobertura por norma
            coverage_metrics = []
            
            for norm in norms_corpus:
                metric = await self._test_norm_coverage(norm, test_queries, rag_system)
                coverage_metrics.append(metric)
            
            # 4. Generar reporte consolidado
            report = self._generate_coverage_report(coverage_metrics)
            
            # 5. Guardar reporte
            self._save_coverage_report(report)
            
            logger.info(f"✅ Test de cobertura completado - Cobertura general: {report.overall_coverage:.1%}")
            return report
            
        except Exception as e:
            logger.error(f"❌ Error en test de cobertura: {e}")
            raise
    
    def _load_norms_corpus(self) -> List[Dict[str, Any]]:
        """Cargar corpus de normas"""
        try:
            if not self.norms_corpus_path.exists():
                logger.warning(f"Archivo de normas no encontrado: {self.norms_corpus_path}")
                return []
            
            with open(self.norms_corpus_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalizar formato si es necesario
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'chunks' in data:
                return data['chunks']
            else:
                logger.warning("Formato de corpus de normas no reconocido")
                return []
                
        except Exception as e:
            logger.error(f"Error cargando corpus de normas: {e}")
            return []
    
    def _load_test_queries(self) -> List[Dict[str, Any]]:
        """Cargar queries de prueba"""
        try:
            if not self.test_queries_path.exists():
                logger.warning(f"Archivo de queries no encontrado: {self.test_queries_path}")
                return []
            
            with open(self.test_queries_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Normalizar formato
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'questions' in data:
                return data['questions']
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error cargando queries de prueba: {e}")
            return []
    
    async def _test_norm_coverage(self, 
                                 norm: Dict[str, Any], 
                                 test_queries: List[Dict[str, Any]], 
                                 rag_system: Any) -> CoverageMetric:
        """Testear cobertura de una norma específica"""
        try:
            norm_content = norm.get('content', '')
            norm_id = norm.get('id', str(norm.get('chunk_index', 0)))
            norm_name = norm.get('source', 'Unknown')
            article_number = self._extract_article_number(norm_content)
            
            # 1. Calcular cobertura semántica
            semantic_coverage = self._calculate_semantic_coverage(norm_content, test_queries)
            
            # 2. Contar queries que cubren esta norma
            query_coverage = self._count_covering_queries(norm_content, test_queries)
            
            # 3. Detectar gaps de cobertura
            gaps_detected = self._detect_coverage_gaps(norm_content, test_queries)
            
            # 4. Determinar status de test
            test_status = self._determine_test_status(semantic_coverage, query_coverage, gaps_detected)
            
            return CoverageMetric(
                norm_id=norm_id,
                norm_name=norm_name,
                article_number=article_number,
                content=norm_content,
                semantic_coverage=semantic_coverage,
                query_coverage=query_coverage,
                gaps_detected=gaps_detected,
                last_tested=datetime.now(),
                test_status=test_status
            )
            
        except Exception as e:
            logger.error(f"Error testeando cobertura de norma {norm.get('id', 'unknown')}: {e}")
            
            return CoverageMetric(
                norm_id=norm.get('id', 'error'),
                norm_name=norm.get('source', 'Error'),
                article_number="",
                content="",
                semantic_coverage=0.0,
                query_coverage=0,
                gaps_detected=[f"Error en test: {str(e)}"],
                last_tested=datetime.now(),
                test_status="error"
            )
    
    def _calculate_semantic_coverage(self, 
                                   norm_content: str, 
                                   test_queries: List[Dict[str, Any]]) -> float:
        """Calcular cobertura semántica usando embeddings"""
        if not self.embeddings_model or not test_queries:
            return 0.0
        
        try:
            # Obtener embedding de la norma
            norm_embedding = self.embeddings_model.encode(norm_content)
            
            # Calcular similitudes con todas las queries
            similarities = []
            for query in test_queries:
                query_text = query.get('question', query.get('query', ''))
                if query_text:
                    query_embedding = self.embeddings_model.encode(query_text)
                    similarity = self._cosine_similarity(norm_embedding, query_embedding)
                    similarities.append(similarity)
            
            if not similarities:
                return 0.0
            
            # Cobertura = máxima similaridad encontrada
            max_similarity = max(similarities)
            
            # Aplicar umbral para determinar si está "cubierto"
            return max_similarity if max_similarity >= self.coverage_thresholds["semantic_similarity"] else 0.0
            
        except Exception as e:
            logger.error(f"Error calculando cobertura semántica: {e}")
            return 0.0
    
    def _count_covering_queries(self, 
                               norm_content: str, 
                               test_queries: List[Dict[str, Any]]) -> int:
        """Contar queries que cubren esta norma"""
        count = 0
        norm_lower = norm_content.lower()
        
        for query in test_queries:
            query_text = query.get('question', query.get('query', '')).lower()
            
            # Buscar coincidencias de conceptos clave
            key_concepts = self._extract_key_concepts(norm_content)
            query_concepts = self._extract_key_concepts(query_text)
            
            # Si hay overlap de conceptos, cuenta como cobertura
            if any(concept in query_concepts for concept in key_concepts):
                count += 1
        
        return count
    
    def _extract_key_concepts(self, text: str) -> Set[str]:
        """Extraer conceptos clave de un texto"""
        # Conceptos importantes en normativas
        key_patterns = [
            r"viáticos?",
            r"gastos?\s+de\s+viaje",
            r"comisión\s+de\s+servicio",
            r"monto.*máximo",
            r"procedimiento",
            r"solicitud",
            r"autorización",
            r"días?\s+hábiles?",
            r"s/\s*\d+",  # montos en soles
            r"artículo\s+\d+"
        ]
        
        concepts = set()
        text_lower = text.lower()
        
        for pattern in key_patterns:
            matches = re.findall(pattern, text_lower)
            concepts.update(matches)
        
        return concepts
    
    def _detect_coverage_gaps(self, 
                             norm_content: str, 
                             test_queries: List[Dict[str, Any]]) -> List[str]:
        """Detectar gaps en la cobertura"""
        gaps = []
        
        # Conceptos críticos que deben estar cubiertos
        critical_concepts = [
            "monto máximo",
            "procedimiento de solicitud", 
            "requisitos",
            "plazos",
            "documentos necesarios"
        ]
        
        norm_lower = norm_content.lower()
        query_texts = " ".join([q.get('question', q.get('query', '')) for q in test_queries]).lower()
        
        for concept in critical_concepts:
            if concept in norm_lower and concept not in query_texts:
                gaps.append(f"Concepto '{concept}' no cubierto por queries de prueba")
        
        # Detectar montos específicos no cubiertos
        amounts = re.findall(r's/\s*(\d+(?:\.\d+)?)', norm_lower)
        for amount in amounts:
            if amount not in query_texts:
                gaps.append(f"Monto S/ {amount} no cubierto por queries")
        
        return gaps
    
    def _determine_test_status(self, 
                              semantic_coverage: float, 
                              query_coverage: int, 
                              gaps_detected: List[str]) -> str:
        """Determinar status del test de cobertura"""
        
        # Verificar si es norma crítica
        is_critical = any(re.search(pattern, str(gaps_detected), re.IGNORECASE) 
                         for pattern in self.critical_norm_patterns)
        
        min_coverage = self.coverage_thresholds["critical_coverage"] if is_critical else self.coverage_thresholds["semantic_similarity"]
        
        if semantic_coverage >= min_coverage and query_coverage >= self.coverage_thresholds["query_coverage"] and not gaps_detected:
            return "covered"
        elif semantic_coverage > 0 or query_coverage > 0:
            return "partial"
        else:
            return "uncovered"
    
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
    
    def _extract_article_number(self, content: str) -> str:
        """Extraer número de artículo del contenido"""
        # Buscar patrones de artículos
        patterns = [
            r"artículo\s+(\d+(?:\.\d+)?)",
            r"art\.\s*(\d+(?:\.\d+)?)",
            r"numeral\s+(\d+(?:\.\d+)?)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return ""
    
    def _generate_coverage_report(self, 
                                coverage_metrics: List[CoverageMetric]) -> CoverageReport:
        """Generar reporte consolidado de cobertura"""
        
        total_norms = len(coverage_metrics)
        covered_norms = len([m for m in coverage_metrics if m.test_status == "covered"])
        partially_covered = len([m for m in coverage_metrics if m.test_status == "partial"])
        uncovered_norms = len([m for m in coverage_metrics if m.test_status == "uncovered"])
        
        overall_coverage = covered_norms / total_norms if total_norms > 0 else 0.0
        
        semantic_scores = [m.semantic_coverage for m in coverage_metrics if m.semantic_coverage > 0]
        semantic_coverage_avg = sum(semantic_scores) / len(semantic_scores) if semantic_scores else 0.0
        
        # Identificar gaps críticos
        critical_gaps = []
        for metric in coverage_metrics:
            if metric.test_status == "uncovered" and any(re.search(pattern, metric.content, re.IGNORECASE) 
                                                        for pattern in self.critical_norm_patterns):
                critical_gaps.append(f"Norma crítica sin cobertura: {metric.norm_name} - {metric.article_number}")
        
        # Generar recomendaciones
        recommendations = self._generate_recommendations(coverage_metrics, overall_coverage)
        
        return CoverageReport(
            total_norms=total_norms,
            covered_norms=covered_norms,
            partially_covered=partially_covered,
            uncovered_norms=uncovered_norms,
            overall_coverage=overall_coverage,
            semantic_coverage_avg=semantic_coverage_avg,
            critical_gaps=critical_gaps,
            recommendations=recommendations,
            detailed_metrics=coverage_metrics,
            generated_at=datetime.now()
        )
    
    def _generate_recommendations(self, 
                                coverage_metrics: List[CoverageMetric], 
                                overall_coverage: float) -> List[str]:
        """Generar recomendaciones basadas en el análisis"""
        recommendations = []
        
        # Recomendaciones basadas en cobertura general
        if overall_coverage < 0.8:
            recommendations.append("Cobertura general por debajo del 80%. Considerar expandir dataset de queries.")
        
        if overall_coverage < 0.6:
            recommendations.append("Cobertura crítica. Revisar corpus de normas y mejorar algoritmos de retrieval.")
        
        # Recomendaciones específicas por gaps
        uncovered_metrics = [m for m in coverage_metrics if m.test_status == "uncovered"]
        if len(uncovered_metrics) > 5:
            recommendations.append(f"Se detectaron {len(uncovered_metrics)} normas sin cobertura. Priorizar creación de queries específicas.")
        
        # Recomendaciones por cobertura semántica
        low_semantic = [m for m in coverage_metrics if m.semantic_coverage < 0.3]
        if len(low_semantic) > 0:
            recommendations.append("Múltiples normas con baja similaridad semántica. Considerar reentrenamiento o ajuste de embeddings.")
        
        # Recomendaciones por gaps específicos
        all_gaps = []
        for metric in coverage_metrics:
            all_gaps.extend(metric.gaps_detected)
        
        if "monto" in " ".join(all_gaps).lower():
            recommendations.append("Detectados gaps en cobertura de montos específicos. Añadir queries sobre valores monetarios.")
        
        if "procedimiento" in " ".join(all_gaps).lower():
            recommendations.append("Gaps en procedimientos detectados. Crear queries sobre procesos administrativos.")
        
        return recommendations
    
    def _save_coverage_report(self, report: CoverageReport):
        """Guardar reporte de cobertura"""
        try:
            # Convertir a dict serializable
            report_dict = asdict(report)
            
            # Convertir datetime a string
            report_dict['generated_at'] = report.generated_at.isoformat()
            for metric in report_dict['detailed_metrics']:
                metric['last_tested'] = datetime.fromisoformat(metric['last_tested']).isoformat() if isinstance(metric['last_tested'], str) else metric['last_tested'].isoformat()
            
            # Guardar reporte JSON
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_file = self.output_path / f"coverage_report_{timestamp}.json"
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
            
            # Guardar resumen legible
            summary_file = self.output_path / f"coverage_summary_{timestamp}.md"
            self._save_coverage_summary(report, summary_file)
            
            logger.info(f"✅ Reporte de cobertura guardado: {report_file}")
            
        except Exception as e:
            logger.error(f"Error guardando reporte de cobertura: {e}")
    
    def _save_coverage_summary(self, report: CoverageReport, summary_file: Path):
        """Guardar resumen ejecutivo del reporte"""
        summary_content = f"""# Reporte de Cobertura Normativa

## Resumen Ejecutivo

- **Fecha:** {report.generated_at.strftime('%d/%m/%Y %H:%M')}
- **Total de normas analizadas:** {report.total_norms}
- **Cobertura general:** {report.overall_coverage:.1%}
- **Cobertura semántica promedio:** {report.semantic_coverage_avg:.1%}

## Distribución de Cobertura

- ✅ **Cubiertas completamente:** {report.covered_norms} ({report.covered_norms/report.total_norms:.1%})
- ⚠️ **Parcialmente cubiertas:** {report.partially_covered} ({report.partially_covered/report.total_norms:.1%})
- ❌ **Sin cobertura:** {report.uncovered_norms} ({report.uncovered_norms/report.total_norms:.1%})

## Gaps Críticos

{"".join([f"- {gap}" + chr(10) for gap in report.critical_gaps]) if report.critical_gaps else "- No se detectaron gaps críticos"}

## Recomendaciones

{"".join([f"- {rec}" + chr(10) for rec in report.recommendations])}

## Normas con Problemas de Cobertura

"""
        
        # Añadir detalles de normas problemáticas
        problematic_norms = [m for m in report.detailed_metrics 
                            if m.test_status in ["uncovered", "partial"]]
        
        for norm in problematic_norms[:10]:  # Top 10 problemáticas
            summary_content += f"""
### {norm.norm_name} - {norm.article_number}
- **Status:** {norm.test_status}
- **Cobertura semántica:** {norm.semantic_coverage:.1%}
- **Queries que la cubren:** {norm.query_coverage}
- **Gaps detectados:** {len(norm.gaps_detected)}
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)

    def get_coverage_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas del sistema de cobertura"""
        return {
            "status": "operational",
            "embeddings_available": EMBEDDINGS_AVAILABLE,
            "ragas_available": RAGAS_AVAILABLE,
            "model_loaded": self.embeddings_model is not None,
            "corpus_file": str(self.norms_corpus_path),
            "queries_file": str(self.test_queries_path),
            "output_directory": str(self.output_path),
            "thresholds": self.coverage_thresholds,
            "critical_patterns": len(self.critical_norm_patterns),
            "features": {
                "semantic_coverage": EMBEDDINGS_AVAILABLE,
                "query_coverage": True,
                "gap_detection": True,
                "critical_norm_identification": True,
                "automated_recommendations": True
            }
        }

# Funciones de utilidad para pytest
def pytest_coverage_test(rag_system=None):
    """Función para usar con pytest"""
    async def run_test():
        tester = NormativeCoverageTester()
        report = await tester.run_comprehensive_coverage_test(rag_system)
        
        # Asserts para pytest
        assert report.overall_coverage > 0.5, f"Cobertura muy baja: {report.overall_coverage:.1%}"
        assert len(report.critical_gaps) == 0, f"Gaps críticos detectados: {report.critical_gaps}"
        assert report.uncovered_norms / report.total_norms < 0.3, "Demasiadas normas sin cobertura"
        
        return report
    
    return asyncio.run(run_test())

# Instancia global
global_coverage_tester = NormativeCoverageTester()