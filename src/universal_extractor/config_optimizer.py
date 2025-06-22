#!/usr/bin/env python3
"""
Config Optimizer - Auto-configuración Universal para Extracción
==============================================================

Optimizador inteligente que auto-configura parámetros de extracción
basado en características del documento y aprendizaje histórico.
"""

import logging
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, asdict, field
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class DocumentProfile:
    """Perfil de características de documento"""
    file_hash: str
    file_size_mb: float
    page_count: int
    text_density: float
    image_density: float
    table_indicators: int
    scan_quality: float
    document_type: str
    language: str = "es"
    creation_date: datetime = field(default_factory=datetime.now)

@dataclass
class ExtractionConfig:
    """Configuración optimizada para extracción"""
    # Configuración Camelot
    camelot_flavor: str = "lattice"
    camelot_line_scale: int = 40
    camelot_process_background: bool = True
    camelot_confidence_threshold: float = 0.7
    
    # Configuración PDFPlumber
    pdfplumber_snap_tolerance: int = 3
    pdfplumber_join_tolerance: int = 3
    pdfplumber_edge_min_length: int = 3
    
    # Configuración OpenCV
    opencv_enable_preprocessing: bool = False
    opencv_kernel_size: Tuple[int, int] = (3, 3)
    opencv_adaptive_threshold: bool = True
    opencv_enhance_contrast: bool = False
    
    # Configuración general
    max_extraction_time: int = 30  # segundos
    enable_fallback_methods: bool = True
    confidence_threshold: float = 0.8
    max_tables_per_page: int = 10
    
    # Configuración de detección de entidades
    money_confidence_threshold: float = 0.6
    numeral_confidence_threshold: float = 0.7
    enable_pattern_learning: bool = True
    
    # Metadatos de configuración
    config_source: str = "auto"
    optimization_score: float = 0.0
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class OptimizationRule:
    """Regla de optimización"""
    name: str
    condition: str  # Condición en Python evaluable
    action: Dict[str, Any]  # Cambios a aplicar
    priority: int = 1
    confidence: float = 0.8
    usage_count: int = 0
    success_rate: float = 0.0

class ConfigOptimizer:
    """
    Optimizador de configuración que aprende automáticamente los mejores
    parámetros para diferentes tipos de documentos legales.
    
    Características:
    - Análisis automático de características del documento
    - Reglas de optimización adaptativas
    - Aprendizaje de configuraciones exitosas
    - Cache de configuraciones por tipo de documento
    - Métricas de rendimiento y feedback loop
    """
    
    def __init__(self, cache_dir: str = "data/optimization_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Reglas de optimización
        self.optimization_rules = self._initialize_base_rules()
        self.learned_rules: List[OptimizationRule] = []
        
        # Cache de configuraciones
        self.config_cache: Dict[str, ExtractionConfig] = {}
        self.document_profiles: Dict[str, DocumentProfile] = {}
        
        # Historial de optimizaciones
        self.optimization_history: List[Dict[str, Any]] = []
        
        # Métricas de rendimiento
        self.performance_metrics = {
            'total_optimizations': 0,
            'successful_optimizations': 0,
            'average_improvement': 0.0,
            'rules_learned': 0,
            'cache_hits': 0
        }
        
        # Cargar datos persistentes
        self._load_optimization_data()
        
        logger.info(f"ConfigOptimizer initialized with {len(self.optimization_rules)} base rules")
    
    def optimize_config_for_document(self, pdf_path: str, 
                                   document_type: Optional[str] = None) -> ExtractionConfig:
        """
        Optimizar configuración automáticamente para un documento específico.
        
        Args:
            pdf_path: Ruta al documento PDF
            document_type: Tipo de documento (opcional, se detecta automáticamente)
            
        Returns:
            Configuración optimizada
        """
        start_time = time.time()
        
        # 1. Generar perfil del documento
        doc_profile = self._analyze_document_profile(pdf_path, document_type)
        
        # 2. Buscar en cache configuraciones similares
        cached_config = self._find_cached_config(doc_profile)
        if cached_config:
            self.performance_metrics['cache_hits'] += 1
            logger.info(f"Found cached config for document type: {doc_profile.document_type}")
            return cached_config
        
        # 3. Generar configuración base
        base_config = self._generate_base_config(doc_profile)
        
        # 4. Aplicar reglas de optimización
        optimized_config = self._apply_optimization_rules(base_config, doc_profile)
        
        # 5. Calcular score de optimización
        optimized_config.optimization_score = self._calculate_optimization_score(optimized_config, doc_profile)
        
        # 6. Guardar en cache
        self._cache_config(doc_profile, optimized_config)
        
        # 7. Actualizar métricas
        optimization_time = time.time() - start_time
        self._update_optimization_metrics(doc_profile, optimized_config, optimization_time)
        
        logger.info(f"Config optimized in {optimization_time:.3f}s, score: {optimized_config.optimization_score:.3f}")
        
        return optimized_config
    
    def _analyze_document_profile(self, pdf_path: str, document_type: Optional[str] = None) -> DocumentProfile:
        """Analizar características del documento para crear perfil."""
        
        try:
            import fitz
            
            # Calcular hash del archivo
            with open(pdf_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # Información básica del archivo
            file_size_mb = Path(pdf_path).stat().st_size / (1024 * 1024)
            
            # Analizar contenido con PyMuPDF
            doc = fitz.open(pdf_path)
            page_count = len(doc)
            
            total_text_length = 0
            total_image_count = 0
            table_indicators = 0
            
            # Analizar muestra de páginas (máximo 5)
            sample_pages = min(5, page_count)
            for i in range(sample_pages):
                page = doc.load_page(i)
                
                # Análisis de texto
                text = page.get_text()
                total_text_length += len(text)
                
                # Contadores de indicadores de tabla
                table_indicators += text.count('|')  # Pipes
                table_indicators += text.count('\t')  # Tabs
                table_indicators += len([line for line in text.split('\n') if len(line.split()) > 4])  # Líneas con muchas palabras
                
                # Análisis de imágenes
                image_list = page.get_images()
                total_image_count += len(image_list)
            
            doc.close()
            
            # Calcular métricas
            text_density = total_text_length / (page_count * 1000)  # Chars per 1000 per page
            image_density = total_image_count / page_count
            table_indicators_per_page = table_indicators / sample_pages
            
            # Estimar calidad de escaneo (simplificado)
            scan_quality = min(1.0, text_density / 2.0)  # Más texto = mejor calidad
            
            # Detectar tipo de documento si no se proporciona
            if not document_type:
                document_type = self._detect_document_type(pdf_path)
            
            return DocumentProfile(
                file_hash=file_hash,
                file_size_mb=file_size_mb,
                page_count=page_count,
                text_density=text_density,
                image_density=image_density,
                table_indicators=int(table_indicators_per_page),
                scan_quality=scan_quality,
                document_type=document_type
            )
            
        except Exception as e:
            logger.error(f"Error analyzing document profile: {e}")
            # Devolver perfil por defecto
            return DocumentProfile(
                file_hash="unknown",
                file_size_mb=1.0,
                page_count=10,
                text_density=1.0,
                image_density=0.1,
                table_indicators=5,
                scan_quality=0.7,
                document_type=document_type or "legal_norm"
            )
    
    def _detect_document_type(self, pdf_path: str) -> str:
        """Detectar tipo de documento automáticamente."""
        
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            
            # Analizar primera página para detectar tipo
            if len(doc) > 0:
                text = doc.load_page(0).get_text().lower()
                
                # Patrones de detección
                if "directiva" in text:
                    return "directiva"
                elif "resolución" in text or "resolucion" in text:
                    return "resolucion"
                elif "decreto" in text:
                    return "decreto"
                elif "reglamento" in text:
                    return "reglamento"
                elif "circular" in text:
                    return "circular"
                elif "manual" in text:
                    return "manual"
                elif "procedimiento" in text:
                    return "procedimiento"
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error detecting document type: {e}")
        
        return "legal_norm"  # Tipo por defecto
    
    def _find_cached_config(self, doc_profile: DocumentProfile) -> Optional[ExtractionConfig]:
        """Buscar configuración en cache para documentos similares."""
        
        # Buscar por hash exacto primero
        if doc_profile.file_hash in self.config_cache:
            return self.config_cache[doc_profile.file_hash]
        
        # Buscar documentos similares
        for cached_hash, cached_config in self.config_cache.items():
            if cached_hash in self.document_profiles:
                cached_profile = self.document_profiles[cached_hash]
                
                # Calcular similitud
                similarity = self._calculate_profile_similarity(doc_profile, cached_profile)
                
                # Si la similitud es alta, usar configuración cacheada
                if similarity > 0.8:
                    logger.debug(f"Using cached config with {similarity:.3f} similarity")
                    return cached_config
        
        return None
    
    def _calculate_profile_similarity(self, profile1: DocumentProfile, profile2: DocumentProfile) -> float:
        """Calcular similitud entre dos perfiles de documento."""
        
        # Factores de similitud con pesos
        factors = {
            'document_type': 0.4,
            'page_count': 0.15,
            'text_density': 0.15,
            'table_indicators': 0.15,
            'scan_quality': 0.15
        }
        
        similarity = 0.0
        
        # Tipo de documento (exacto o no)
        if profile1.document_type == profile2.document_type:
            similarity += factors['document_type']
        
        # Páginas (similitud basada en rango)
        page_ratio = min(profile1.page_count, profile2.page_count) / max(profile1.page_count, profile2.page_count)
        similarity += factors['page_count'] * page_ratio
        
        # Densidad de texto
        text_ratio = min(profile1.text_density, profile2.text_density) / max(profile1.text_density, profile2.text_density, 0.1)
        similarity += factors['text_density'] * text_ratio
        
        # Indicadores de tabla
        table_ratio = min(profile1.table_indicators, profile2.table_indicators) / max(profile1.table_indicators, profile2.table_indicators, 1)
        similarity += factors['table_indicators'] * table_ratio
        
        # Calidad de escaneo
        scan_diff = abs(profile1.scan_quality - profile2.scan_quality)
        scan_similarity = max(0, 1 - scan_diff)
        similarity += factors['scan_quality'] * scan_similarity
        
        return similarity
    
    def _generate_base_config(self, doc_profile: DocumentProfile) -> ExtractionConfig:
        """Generar configuración base según perfil del documento."""
        
        config = ExtractionConfig()
        
        # Configuración según tipo de documento
        if doc_profile.document_type in ["directiva", "resolucion", "decreto"]:
            config.camelot_confidence_threshold = 0.6  # Más permisivo para docs oficiales
            config.confidence_threshold = 0.75
        else:
            config.camelot_confidence_threshold = 0.7
            config.confidence_threshold = 0.8
        
        # Configuración según calidad de escaneo
        if doc_profile.scan_quality < 0.5:
            # Documentos de mala calidad
            config.opencv_enable_preprocessing = True
            config.opencv_enhance_contrast = True
            config.camelot_process_background = True
            config.camelot_line_scale = 50  # Más sensible a líneas
        elif doc_profile.scan_quality > 0.8:
            # Documentos de alta calidad
            config.opencv_enable_preprocessing = False
            config.camelot_line_scale = 30  # Menos sensible
        
        # Configuración según densidad de tablas
        if doc_profile.table_indicators > 15:
            # Muchas tablas
            config.max_tables_per_page = 15
            config.camelot_flavor = "lattice"  # Mejor para tablas con bordes
            config.pdfplumber_snap_tolerance = 5
        elif doc_profile.table_indicators < 5:
            # Pocas tablas
            config.max_tables_per_page = 5
            config.camelot_flavor = "stream"  # Mejor para tablas sin bordes
        
        # Configuración según tamaño del documento
        if doc_profile.page_count > 50:
            # Documentos grandes
            config.max_extraction_time = 60
            config.opencv_enable_preprocessing = False  # Evitar procesamiento pesado
        elif doc_profile.page_count < 5:
            # Documentos pequeños
            config.max_extraction_time = 15
        
        config.config_source = "base_generation"
        return config
    
    def _apply_optimization_rules(self, config: ExtractionConfig, doc_profile: DocumentProfile) -> ExtractionConfig:
        """Aplicar reglas de optimización a la configuración."""
        
        optimized_config = config
        rules_applied = []
        
        # Combinar reglas base y aprendidas, ordenar por prioridad
        all_rules = sorted(
            self.optimization_rules + self.learned_rules,
            key=lambda r: (r.priority, r.confidence),
            reverse=True
        )
        
        for rule in all_rules:
            try:
                # Evaluar condición de la regla
                if self._evaluate_rule_condition(rule, doc_profile, optimized_config):
                    # Aplicar cambios de la regla
                    optimized_config = self._apply_rule_action(optimized_config, rule)
                    rules_applied.append(rule.name)
                    rule.usage_count += 1
                    
                    logger.debug(f"Applied rule: {rule.name}")
                    
            except Exception as e:
                logger.warning(f"Error applying rule {rule.name}: {e}")
                continue
        
        if rules_applied:
            logger.info(f"Applied {len(rules_applied)} optimization rules: {', '.join(rules_applied)}")
        
        optimized_config.config_source = f"optimized_rules_{len(rules_applied)}"
        return optimized_config
    
    def _evaluate_rule_condition(self, rule: OptimizationRule, doc_profile: DocumentProfile, 
                                config: ExtractionConfig) -> bool:
        """Evaluar si la condición de una regla se cumple."""
        
        try:
            # Crear contexto para evaluación
            context = {
                'profile': doc_profile,
                'config': config,
                'page_count': doc_profile.page_count,
                'scan_quality': doc_profile.scan_quality,
                'document_type': doc_profile.document_type,
                'text_density': doc_profile.text_density,
                'table_indicators': doc_profile.table_indicators
            }
            
            # Evaluar condición de forma segura
            return eval(rule.condition, {"__builtins__": {}}, context)
            
        except Exception as e:
            logger.warning(f"Error evaluating rule condition '{rule.condition}': {e}")
            return False
    
    def _apply_rule_action(self, config: ExtractionConfig, rule: OptimizationRule) -> ExtractionConfig:
        """Aplicar acción de una regla a la configuración."""
        
        # Crear copia de la configuración
        config_dict = asdict(config)
        
        # Aplicar cambios especificados en la acción
        for key, value in rule.action.items():
            if key in config_dict:
                config_dict[key] = value
                logger.debug(f"Rule {rule.name}: {key} = {value}")
        
        # Recrear objeto de configuración
        return ExtractionConfig(**config_dict)
    
    def _calculate_optimization_score(self, config: ExtractionConfig, doc_profile: DocumentProfile) -> float:
        """Calcular score de calidad de la optimización."""
        
        score = 0.5  # Score base
        
        # Bonificaciones por configuraciones apropiadas
        
        # Bonus por configuración de calidad de escaneo apropiada
        if doc_profile.scan_quality < 0.5 and config.opencv_enable_preprocessing:
            score += 0.15
        elif doc_profile.scan_quality > 0.8 and not config.opencv_enable_preprocessing:
            score += 0.1
        
        # Bonus por configuración de tabla apropiada
        if doc_profile.table_indicators > 15 and config.camelot_flavor == "lattice":
            score += 0.15
        elif doc_profile.table_indicators < 5 and config.camelot_flavor == "stream":
            score += 0.1
        
        # Bonus por timeout apropiado
        expected_time = doc_profile.page_count * 2  # 2 segundos por página
        if abs(config.max_extraction_time - expected_time) < 10:
            score += 0.1
        
        # Bonus por configuración de documentos oficiales
        if doc_profile.document_type in ["directiva", "decreto"] and config.camelot_confidence_threshold <= 0.6:
            score += 0.1
        
        return min(1.0, score)
    
    def _cache_config(self, doc_profile: DocumentProfile, config: ExtractionConfig):
        """Guardar configuración en cache."""
        
        self.config_cache[doc_profile.file_hash] = config
        self.document_profiles[doc_profile.file_hash] = doc_profile
        
        # Persistir cache
        self._save_optimization_data()
    
    def _update_optimization_metrics(self, doc_profile: DocumentProfile, config: ExtractionConfig, 
                                   optimization_time: float):
        """Actualizar métricas de optimización."""
        
        self.performance_metrics['total_optimizations'] += 1
        
        if config.optimization_score > 0.7:
            self.performance_metrics['successful_optimizations'] += 1
        
        # Actualizar mejora promedio
        total_improvement = self.performance_metrics['average_improvement'] * (self.performance_metrics['total_optimizations'] - 1)
        self.performance_metrics['average_improvement'] = (total_improvement + config.optimization_score) / self.performance_metrics['total_optimizations']
        
        # Guardar en historial
        self.optimization_history.append({
            'timestamp': datetime.now().isoformat(),
            'document_type': doc_profile.document_type,
            'optimization_score': config.optimization_score,
            'optimization_time': optimization_time,
            'config_source': config.config_source
        })
    
    def _initialize_base_rules(self) -> List[OptimizationRule]:
        """Inicializar reglas de optimización base."""
        
        return [
            # Reglas para documentos escaneados de mala calidad
            OptimizationRule(
                name="Low Quality Scan Enhancement",
                condition="scan_quality < 0.5",
                action={
                    "opencv_enable_preprocessing": True,
                    "opencv_enhance_contrast": True,
                    "camelot_process_background": True,
                    "camelot_line_scale": 50
                },
                priority=5,
                confidence=0.9
            ),
            
            # Reglas para documentos con muchas tablas
            OptimizationRule(
                name="High Table Density Optimization",
                condition="table_indicators > 15",
                action={
                    "camelot_flavor": "lattice",
                    "max_tables_per_page": 15,
                    "pdfplumber_snap_tolerance": 5,
                    "camelot_line_scale": 45
                },
                priority=4,
                confidence=0.85
            ),
            
            # Reglas para documentos grandes
            OptimizationRule(
                name="Large Document Optimization",
                condition="page_count > 50",
                action={
                    "max_extraction_time": 120,
                    "opencv_enable_preprocessing": False,
                    "max_tables_per_page": 8
                },
                priority=3,
                confidence=0.8
            ),
            
            # Reglas para documentos oficiales
            OptimizationRule(
                name="Official Document Settings",
                condition="document_type in ['directiva', 'decreto', 'resolucion']",
                action={
                    "camelot_confidence_threshold": 0.6,
                    "confidence_threshold": 0.75,
                    "enable_pattern_learning": True
                },
                priority=4,
                confidence=0.9
            ),
            
            # Reglas para tablas sin bordes visibles
            OptimizationRule(
                name="Borderless Table Detection",
                condition="table_indicators < 5",
                action={
                    "camelot_flavor": "stream",
                    "pdfplumber_snap_tolerance": 1,
                    "pdfplumber_join_tolerance": 1
                },
                priority=3,
                confidence=0.8
            ),
            
            # Reglas para documentos de alta calidad
            OptimizationRule(
                name="High Quality Document Fast Track",
                condition="scan_quality > 0.8 and page_count < 20",
                action={
                    "opencv_enable_preprocessing": False,
                    "camelot_line_scale": 25,
                    "max_extraction_time": 15
                },
                priority=3,
                confidence=0.85
            )
        ]
    
    def learn_from_feedback(self, doc_profile: DocumentProfile, config: ExtractionConfig, 
                          extraction_results: Dict[str, Any]):
        """Aprender de los resultados de extracción para mejorar optimizaciones futuras."""
        
        success_metrics = extraction_results.get('metadata', {})
        extraction_confidence = success_metrics.get('confidence_score', 0.0)
        extraction_time = success_metrics.get('extraction_time', 0.0)
        tables_found = success_metrics.get('total_tables_found', 0)
        
        # Determinar si la configuración fue exitosa
        was_successful = (
            extraction_confidence > 0.7 and
            extraction_time < config.max_extraction_time and
            tables_found > 0
        )
        
        # Actualizar score de configuración basado en resultados reales
        actual_score = 0.0
        if was_successful:
            actual_score = min(1.0, extraction_confidence + 0.2)
        else:
            actual_score = max(0.0, extraction_confidence - 0.3)
        
        # Guardar feedback en historial
        feedback_entry = {
            'timestamp': datetime.now().isoformat(),
            'document_profile': asdict(doc_profile),
            'config_used': asdict(config),
            'extraction_results': success_metrics,
            'was_successful': was_successful,
            'actual_score': actual_score
        }
        
        self.optimization_history.append(feedback_entry)
        
        # Aprender nueva regla si hay patrones claros
        if was_successful and actual_score > 0.8:
            self._try_learning_new_rule(doc_profile, config, "successful_extraction")
        elif not was_successful and actual_score < 0.5:
            self._try_learning_new_rule(doc_profile, config, "failed_extraction")
        
        logger.info(f"Learned from feedback: success={was_successful}, score={actual_score:.3f}")
    
    def _try_learning_new_rule(self, doc_profile: DocumentProfile, config: ExtractionConfig, 
                             outcome: str):
        """Intentar aprender una nueva regla de optimización."""
        
        # Generar condición basada en características del documento
        conditions = []
        
        if doc_profile.scan_quality < 0.6:
            conditions.append("scan_quality < 0.6")
        if doc_profile.table_indicators > 10:
            conditions.append("table_indicators > 10")
        if doc_profile.page_count > 20:
            conditions.append("page_count > 20")
        if doc_profile.document_type:
            conditions.append(f"document_type == '{doc_profile.document_type}'")
        
        if not conditions:
            return  # No hay condiciones claras para aprender
        
        condition = " and ".join(conditions)
        
        # Generar acción basada en la configuración exitosa/fallida
        action = {}
        
        if outcome == "successful_extraction":
            # Promover configuraciones exitosas
            if config.camelot_flavor:
                action["camelot_flavor"] = config.camelot_flavor
            if config.opencv_enable_preprocessing:
                action["opencv_enable_preprocessing"] = config.opencv_enable_preprocessing
            if config.camelot_line_scale != 40:  # No es el valor por defecto
                action["camelot_line_scale"] = config.camelot_line_scale
        
        else:  # failed_extraction
            # Aplicar configuraciones contrarias a las fallidas
            if config.camelot_flavor == "lattice":
                action["camelot_flavor"] = "stream"
            elif config.camelot_flavor == "stream":
                action["camelot_flavor"] = "lattice"
            
            if not config.opencv_enable_preprocessing:
                action["opencv_enable_preprocessing"] = True
        
        if action:
            # Verificar que no existe una regla similar
            rule_signature = f"{condition}_{sorted(action.items())}"
            existing_signatures = [
                f"{rule.condition}_{sorted(rule.action.items())}"
                for rule in self.learned_rules
            ]
            
            if rule_signature not in existing_signatures:
                new_rule = OptimizationRule(
                    name=f"Learned_{outcome}_{len(self.learned_rules)}",
                    condition=condition,
                    action=action,
                    priority=2,  # Prioridad media para reglas aprendidas
                    confidence=0.7
                )
                
                self.learned_rules.append(new_rule)
                self.performance_metrics['rules_learned'] += 1
                
                logger.info(f"Learned new rule: {new_rule.name}")
                logger.debug(f"Condition: {condition}")
                logger.debug(f"Action: {action}")
    
    def _save_optimization_data(self):
        """Guardar datos de optimización de forma persistente."""
        
        try:
            # Guardar cache de configuraciones
            cache_file = self.cache_dir / "config_cache.json"
            cache_data = {
                'configs': {k: asdict(v) for k, v in self.config_cache.items()},
                'profiles': {k: asdict(v) for k, v in self.document_profiles.items()},
                'saved_at': datetime.now().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Guardar reglas aprendidas
            rules_file = self.cache_dir / "learned_rules.json"
            rules_data = {
                'learned_rules': [asdict(rule) for rule in self.learned_rules],
                'performance_metrics': self.performance_metrics,
                'saved_at': datetime.now().isoformat()
            }
            
            with open(rules_file, 'w', encoding='utf-8') as f:
                json.dump(rules_data, f, indent=2, ensure_ascii=False, default=str)
            
            # Guardar historial (solo los últimos 1000 entradas)
            history_file = self.cache_dir / "optimization_history.json"
            recent_history = self.optimization_history[-1000:]  # Mantener solo las más recientes
            
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(recent_history, f, indent=2, ensure_ascii=False, default=str)
            
        except Exception as e:
            logger.error(f"Error saving optimization data: {e}")
    
    def _load_optimization_data(self):
        """Cargar datos de optimización persistentes."""
        
        try:
            # Cargar cache de configuraciones
            cache_file = self.cache_dir / "config_cache.json"
            if cache_file.exists():
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                # Reconstruir cache
                for k, v in cache_data.get('configs', {}).items():
                    self.config_cache[k] = ExtractionConfig(**v)
                
                for k, v in cache_data.get('profiles', {}).items():
                    # Convertir datetime strings back to datetime objects
                    if 'creation_date' in v and isinstance(v['creation_date'], str):
                        v['creation_date'] = datetime.fromisoformat(v['creation_date'])
                    self.document_profiles[k] = DocumentProfile(**v)
            
            # Cargar reglas aprendidas
            rules_file = self.cache_dir / "learned_rules.json"
            if rules_file.exists():
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_data = json.load(f)
                
                self.learned_rules = [OptimizationRule(**rule) for rule in rules_data.get('learned_rules', [])]
                self.performance_metrics.update(rules_data.get('performance_metrics', {}))
            
            # Cargar historial
            history_file = self.cache_dir / "optimization_history.json"
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    self.optimization_history = json.load(f)
            
            logger.info(f"Loaded optimization data: {len(self.config_cache)} cached configs, {len(self.learned_rules)} learned rules")
            
        except Exception as e:
            logger.error(f"Error loading optimization data: {e}")
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generar reporte completo de optimización."""
        
        success_rate = 0.0
        if self.performance_metrics['total_optimizations'] > 0:
            success_rate = self.performance_metrics['successful_optimizations'] / self.performance_metrics['total_optimizations']
        
        cache_hit_rate = 0.0
        if self.performance_metrics['total_optimizations'] > 0:
            cache_hit_rate = self.performance_metrics['cache_hits'] / self.performance_metrics['total_optimizations']
        
        return {
            'performance_summary': {
                'total_optimizations': self.performance_metrics['total_optimizations'],
                'success_rate': success_rate,
                'average_improvement': self.performance_metrics['average_improvement'],
                'cache_hit_rate': cache_hit_rate
            },
            'learning_summary': {
                'base_rules': len(self.optimization_rules),
                'learned_rules': len(self.learned_rules),
                'total_rules': len(self.optimization_rules) + len(self.learned_rules),
                'rules_learned': self.performance_metrics['rules_learned']
            },
            'cache_summary': {
                'cached_configs': len(self.config_cache),
                'document_profiles': len(self.document_profiles),
                'cache_hits': self.performance_metrics['cache_hits']
            },
            'most_used_rules': sorted(
                self.optimization_rules + self.learned_rules,
                key=lambda r: r.usage_count,
                reverse=True
            )[:10],
            'document_type_distribution': self._get_document_type_distribution()
        }
    
    def _get_document_type_distribution(self) -> Dict[str, int]:
        """Obtener distribución de tipos de documentos procesados."""
        
        distribution = {}
        for profile in self.document_profiles.values():
            doc_type = profile.document_type
            distribution[doc_type] = distribution.get(doc_type, 0) + 1
        
        return distribution
    
    def clear_cache(self):
        """Limpiar cache de optimizaciones."""
        
        self.config_cache.clear()
        self.document_profiles.clear()
        self.optimization_history.clear()
        
        # Limpiar archivos persistentes
        for file in self.cache_dir.glob("*.json"):
            file.unlink()
        
        logger.info("Optimization cache cleared")