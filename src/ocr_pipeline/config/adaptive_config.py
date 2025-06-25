#!/usr/bin/env python3
"""
Configuración Adaptativa del Sistema
===================================

Sistema de configuración que se auto-ajusta basado en características del documento
y rendimiento histórico para optimizar la extracción.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ExtractionConfig:
    """Configuración para un tipo específico de extracción"""
    
    # Configuración de Camelot
    camelot_stream_edge_tol: int = 50
    camelot_lattice_line_scale: int = 15
    camelot_process_background: bool = False
    
    # Configuración de PDFplumber
    pdfplumber_snap_tolerance: int = 3
    pdfplumber_join_tolerance: int = 3
    pdfplumber_edge_min_length: int = 3
    
    # Configuración de OpenCV
    opencv_threshold_type: str = "THRESH_BINARY"
    opencv_kernel_size: tuple = (3, 3)
    opencv_enhance_contrast: bool = True
    
    # Configuración del detector de montos
    money_context_window: int = 100
    money_confidence_threshold: float = 0.5
    money_learning_enabled: bool = True
    
    # Configuración de chunks
    chunk_min_length: int = 30
    chunk_max_length: int = 2000
    chunk_overlap: int = 50
    
    # Timeouts y límites
    extraction_timeout: int = 30
    max_pages_to_analyze: int = 3
    max_tables_per_page: int = 10

class ConfigOptimizer:
    """Optimizador que ajusta configuración basado en características del documento"""
    
    def __init__(self):
        self.base_configs = self._create_base_configs()
        self.performance_data = []
        self.optimization_rules = self._create_optimization_rules()
        
        # Cargar datos históricos
        self._load_performance_data()
    
    def _create_base_configs(self) -> Dict[str, ExtractionConfig]:
        """Crea configuraciones base para diferentes tipos de documentos"""
        
        return {
            'digital_simple': ExtractionConfig(
                camelot_stream_edge_tol=50,
                camelot_lattice_line_scale=15,
                pdfplumber_snap_tolerance=3,
                extraction_timeout=15,
                max_pages_to_analyze=5
            ),
            
            'digital_complex': ExtractionConfig(
                camelot_stream_edge_tol=30,
                camelot_lattice_line_scale=25,
                pdfplumber_snap_tolerance=5,
                pdfplumber_join_tolerance=5,
                extraction_timeout=45,
                max_tables_per_page=15
            ),
            
            'scanned_good_quality': ExtractionConfig(
                camelot_lattice_line_scale=40,
                camelot_process_background=True,
                pdfplumber_snap_tolerance=2,
                opencv_enhance_contrast=True,
                extraction_timeout=60,
                money_confidence_threshold=0.4
            ),
            
            'scanned_poor_quality': ExtractionConfig(
                camelot_lattice_line_scale=60,
                camelot_process_background=True,
                opencv_threshold_type="ADAPTIVE_THRESH_GAUSSIAN_C",
                opencv_kernel_size=(5, 5),
                opencv_enhance_contrast=True,
                pdfplumber_snap_tolerance=1,
                extraction_timeout=90,
                money_confidence_threshold=0.3,
                chunk_min_length=20
            ),
            
            'large_document': ExtractionConfig(
                extraction_timeout=120,
                max_pages_to_analyze=2,
                max_tables_per_page=8,
                chunk_max_length=1500,
                money_context_window=150
            ),
            
            'financial_document': ExtractionConfig(
                money_context_window=200,
                money_confidence_threshold=0.6,
                money_learning_enabled=True,
                chunk_min_length=50,
                camelot_lattice_line_scale=20
            )
        }
    
    def _create_optimization_rules(self) -> List[Dict[str, Any]]:
        """Crea reglas de optimización basadas en características"""
        
        return [
            {
                'condition': lambda chars: chars.get('file_size_mb', 0) > 20,
                'adjustments': {
                    'extraction_timeout': lambda config: config.extraction_timeout * 1.5,
                    'max_pages_to_analyze': lambda config: max(1, config.max_pages_to_analyze // 2)
                },
                'description': 'Documento muy grande'
            },
            
            {
                'condition': lambda chars: chars.get('page_count', 0) > 50,
                'adjustments': {
                    'max_pages_to_analyze': lambda config: min(2, config.max_pages_to_analyze),
                    'chunk_max_length': lambda config: config.chunk_max_length // 2
                },
                'description': 'Muchas páginas'
            },
            
            {
                'condition': lambda chars: chars.get('text_quality') == 'poor',
                'adjustments': {
                    'money_confidence_threshold': lambda config: config.money_confidence_threshold * 0.8,
                    'opencv_enhance_contrast': lambda config: True,
                    'camelot_process_background': lambda config: True
                },
                'description': 'Calidad de texto pobre'
            },
            
            {
                'condition': lambda chars: chars.get('has_complex_tables', False),
                'adjustments': {
                    'camelot_lattice_line_scale': lambda config: config.camelot_lattice_line_scale + 10,
                    'max_tables_per_page': lambda config: config.max_tables_per_page + 5,
                    'extraction_timeout': lambda config: config.extraction_timeout * 1.2
                },
                'description': 'Tablas complejas'
            },
            
            {
                'condition': lambda chars: not chars.get('has_borders', False),
                'adjustments': {
                    'pdfplumber_snap_tolerance': lambda config: config.pdfplumber_snap_tolerance // 2,
                    'pdfplumber_join_tolerance': lambda config: config.pdfplumber_join_tolerance // 2
                },
                'description': 'Sin bordes visibles'
            }
        ]
    
    def get_optimal_config(self, document_characteristics: Dict[str, Any], 
                          performance_history: Optional[List[Dict[str, Any]]] = None) -> ExtractionConfig:
        """
        Obtiene configuración óptima para un documento específico
        
        Args:
            document_characteristics: Características del documento
            performance_history: Historial de rendimiento opcional
            
        Returns:
            Configuración optimizada
        """
        
        # Seleccionar configuración base
        base_config_name = self._select_base_config(document_characteristics)
        config = ExtractionConfig(**asdict(self.base_configs[base_config_name]))
        
        logger.info(f"🔧 Configuración base seleccionada: {base_config_name}")
        
        # Aplicar reglas de optimización
        applied_rules = []
        
        for rule in self.optimization_rules:
            if rule['condition'](document_characteristics):
                applied_rules.append(rule['description'])
                
                for param, adjustment_func in rule['adjustments'].items():
                    if hasattr(config, param):
                        old_value = getattr(config, param)
                        new_value = adjustment_func(config)
                        setattr(config, param, new_value)
                        
                        logger.debug(f"   {param}: {old_value} → {new_value}")
        
        if applied_rules:
            logger.info(f"🎯 Reglas aplicadas: {', '.join(applied_rules)}")
        
        # Optimización basada en historial
        if performance_history:
            config = self._optimize_from_history(config, document_characteristics, performance_history)
        
        # Validar configuración
        config = self._validate_config(config)
        
        return config
    
    def _select_base_config(self, characteristics: Dict[str, Any]) -> str:
        """Selecciona la configuración base más apropiada"""
        
        # Lógica de selección basada en características
        if characteristics.get('is_scanned', False):
            if characteristics.get('text_quality') == 'poor':
                return 'scanned_poor_quality'
            else:
                return 'scanned_good_quality'
        
        elif characteristics.get('file_size_mb', 0) > 15 or characteristics.get('page_count', 0) > 30:
            return 'large_document'
        
        elif characteristics.get('has_complex_tables', False):
            return 'digital_complex'
        
        # Detectar documentos financieros por contexto
        elif self._is_financial_document(characteristics):
            return 'financial_document'
        
        else:
            return 'digital_simple'
    
    def _is_financial_document(self, characteristics: Dict[str, Any]) -> bool:
        """Detecta si es un documento financiero/legal"""
        
        financial_indicators = [
            'viático', 'monto', 'valor', 'importe', 'suma', 'cantidad',
            'precio', 'costo', 'tarifa', 'pago', 'remuneración',
            'directiva', 'norma', 'decreto', 'resolución'
        ]
        
        # Buscar en el resumen de características
        summary = characteristics.get('summary', '').lower()
        
        return any(indicator in summary for indicator in financial_indicators)
    
    def _optimize_from_history(self, config: ExtractionConfig, 
                              characteristics: Dict[str, Any],
                              history: List[Dict[str, Any]]) -> ExtractionConfig:
        """Optimiza configuración basada en historial de rendimiento"""
        
        # Buscar documentos similares en el historial
        similar_docs = []
        
        for record in history:
            similarity = self._calculate_similarity(
                characteristics, 
                record.get('document_characteristics', {})
            )
            
            if similarity > 0.7:  # Umbral de similitud
                similar_docs.append(record)
        
        if not similar_docs:
            return config
        
        # Analizar configuraciones exitosas
        successful_configs = [
            record for record in similar_docs 
            if record.get('confidence', 0) > 0.8
        ]
        
        if successful_configs:
            # Promediuar parámetros de configuraciones exitosas
            config = self._average_successful_configs(config, successful_configs)
            logger.info(f"📈 Configuración optimizada basada en {len(successful_configs)} casos exitosos")
        
        return config
    
    def _calculate_similarity(self, chars1: Dict[str, Any], chars2: Dict[str, Any]) -> float:
        """Calcula similitud entre características de documentos"""
        
        if not chars1 or not chars2:
            return 0.0
        
        similarity_factors = []
        
        # Comparar propiedades booleanas
        bool_props = ['is_scanned', 'has_complex_tables', 'has_borders']
        for prop in bool_props:
            if chars1.get(prop) == chars2.get(prop):
                similarity_factors.append(0.2)
        
        # Comparar propiedades categóricas
        cat_props = ['text_quality', 'layout_complexity']
        for prop in cat_props:
            if chars1.get(prop) == chars2.get(prop):
                similarity_factors.append(0.15)
        
        # Comparar tamaños (similar rango)
        size1 = chars1.get('file_size_mb', 0)
        size2 = chars2.get('file_size_mb', 0)
        
        if size1 > 0 and size2 > 0:
            size_ratio = min(size1, size2) / max(size1, size2)
            if size_ratio > 0.5:
                similarity_factors.append(0.1)
        
        return sum(similarity_factors)
    
    def _average_successful_configs(self, base_config: ExtractionConfig, 
                                  successful_records: List[Dict[str, Any]]) -> ExtractionConfig:
        """Promedia parámetros de configuraciones exitosas"""
        
        # Extraer configuraciones usadas
        configs = []
        for record in successful_records:
            if 'config_used' in record:
                configs.append(record['config_used'])
        
        if not configs:
            return base_config
        
        # Promediuar parámetros numéricos
        numeric_params = [
            'camelot_stream_edge_tol', 'camelot_lattice_line_scale',
            'pdfplumber_snap_tolerance', 'pdfplumber_join_tolerance',
            'money_context_window', 'extraction_timeout'
        ]
        
        for param in numeric_params:
            if hasattr(base_config, param):
                values = [
                    config.get(param, getattr(base_config, param)) 
                    for config in configs
                ]
                
                if values:
                    avg_value = sum(values) / len(values)
                    setattr(base_config, param, int(avg_value))
        
        return base_config
    
    def _validate_config(self, config: ExtractionConfig) -> ExtractionConfig:
        """Valida y corrige configuración para evitar valores inválidos"""
        
        # Límites mínimos y máximos
        limits = {
            'camelot_stream_edge_tol': (10, 100),
            'camelot_lattice_line_scale': (5, 100),
            'pdfplumber_snap_tolerance': (1, 10),
            'pdfplumber_join_tolerance': (1, 10),
            'money_context_window': (50, 500),
            'money_confidence_threshold': (0.1, 1.0),
            'extraction_timeout': (10, 300),
            'chunk_min_length': (10, 100),
            'chunk_max_length': (500, 5000)
        }
        
        for param, (min_val, max_val) in limits.items():
            if hasattr(config, param):
                current_val = getattr(config, param)
                
                if isinstance(current_val, (int, float)):
                    clamped_val = max(min_val, min(max_val, current_val))
                    
                    if clamped_val != current_val:
                        logger.debug(f"🔧 Corrigiendo {param}: {current_val} → {clamped_val}")
                        setattr(config, param, clamped_val)
        
        return config
    
    def record_performance(self, document_characteristics: Dict[str, Any],
                          config_used: Dict[str, Any],
                          results: Dict[str, Any]):
        """Registra rendimiento para optimización futura"""
        
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'document_characteristics': document_characteristics,
            'config_used': config_used,
            'confidence': results.get('confidence', 0.0),
            'extraction_time': results.get('extraction_time', 0.0),
            'amounts_found': len(results.get('amounts', [])),
            'chunks_found': len(results.get('chunks', [])),
            'success': results.get('confidence', 0.0) > 0.7
        }
        
        self.performance_data.append(performance_record)
        
        # Mantener solo los últimos 200 registros
        if len(self.performance_data) > 200:
            self.performance_data = self.performance_data[-200:]
        
        # Guardar datos
        self._save_performance_data()
        
        logger.debug(f"📊 Rendimiento registrado: confianza {results.get('confidence', 0.0):.2f}")
    
    def _load_performance_data(self):
        """Carga datos de rendimiento histórico"""
        
        data_file = Path("data/config_performance.json")
        
        if data_file.exists():
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.performance_data = data.get('performance_records', [])
                    logger.info(f"📚 Cargados {len(self.performance_data)} registros de configuración")
            except Exception as e:
                logger.warning(f"Error cargando datos de configuración: {e}")
    
    def _save_performance_data(self):
        """Guarda datos de rendimiento"""
        
        data_file = Path("data/config_performance.json")
        data_file.parent.mkdir(exist_ok=True)
        
        try:
            data = {
                'performance_records': self.performance_data,
                'last_updated': datetime.now().isoformat(),
                'total_records': len(self.performance_data)
            }
            
            with open(data_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"Error guardando datos de configuración: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento de configuraciones"""
        
        if not self.performance_data:
            return {'message': 'No hay datos de rendimiento disponibles'}
        
        # Calcular estadísticas
        total_records = len(self.performance_data)
        successful_records = [r for r in self.performance_data if r.get('success', False)]
        success_rate = len(successful_records) / total_records if total_records > 0 else 0
        
        avg_confidence = sum(r.get('confidence', 0) for r in self.performance_data) / total_records
        avg_time = sum(r.get('extraction_time', 0) for r in self.performance_data) / total_records
        
        # Configuraciones más exitosas
        config_performance = defaultdict(list)
        
        for record in self.performance_data:
            config_key = self._get_config_key(record.get('config_used', {}))
            config_performance[config_key].append(record.get('confidence', 0))
        
        best_config = max(
            config_performance.items(),
            key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0,
            default=('none', [])
        )[0]
        
        return {
            'total_records': total_records,
            'success_rate': success_rate,
            'average_confidence': avg_confidence,
            'average_extraction_time': avg_time,
            'best_configuration': best_config,
            'configuration_count': len(config_performance)
        }
    
    def _get_config_key(self, config: Dict[str, Any]) -> str:
        """Genera clave única para una configuración"""
        
        key_params = [
            'camelot_lattice_line_scale',
            'pdfplumber_snap_tolerance',
            'money_confidence_threshold'
        ]
        
        key_parts = []
        for param in key_params:
            if param in config:
                key_parts.append(f"{param}_{config[param]}")
        
        return "_".join(key_parts) if key_parts else "default"
    
    def suggest_improvements(self) -> List[str]:
        """Sugiere mejoras basadas en análisis de rendimiento"""
        
        suggestions = []
        
        if not self.performance_data:
            suggestions.append("Ejecutar más extracciones para generar datos de optimización")
            return suggestions
        
        stats = self.get_performance_stats()
        
        # Analizar tasa de éxito
        if stats['success_rate'] < 0.7:
            suggestions.append("Tasa de éxito baja - considerar ajustar umbrales de confianza")
        
        # Analizar tiempo de extracción
        if stats['average_extraction_time'] > 60:
            suggestions.append("Tiempo de extracción alto - optimizar timeouts y límites")
        
        # Analizar confianza promedio
        if stats['average_confidence'] < 0.6:
            suggestions.append("Confianza promedio baja - revisar configuración de detectores")
        
        # Analizar diversidad de configuraciones
        if stats['configuration_count'] < 3:
            suggestions.append("Poca diversidad en configuraciones - probar con más tipos de documentos")
        
        return suggestions


# Instancia global del optimizador
config_optimizer = ConfigOptimizer()

def get_optimal_config(document_characteristics: Dict[str, Any],
                      performance_history: Optional[List[Dict[str, Any]]] = None) -> ExtractionConfig:
    """
    Función de conveniencia para obtener configuración óptima
    
    Args:
        document_characteristics: Características del documento
        performance_history: Historial de rendimiento opcional
        
    Returns:
        Configuración optimizada
    """
    return config_optimizer.get_optimal_config(document_characteristics, performance_history)

def record_performance(document_characteristics: Dict[str, Any],
                      config_used: Dict[str, Any],
                      results: Dict[str, Any]):
    """
    Función de conveniencia para registrar rendimiento
    
    Args:
        document_characteristics: Características del documento
        config_used: Configuración utilizada
        results: Resultados obtenidos
    """
    config_optimizer.record_performance(document_characteristics, config_used, results)