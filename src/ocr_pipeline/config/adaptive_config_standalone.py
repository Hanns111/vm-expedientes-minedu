#!/usr/bin/env python3
"""
Configuración Adaptativa Standalone
==================================

Sistema de configuración standalone sin dependencias problemáticas.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ExtractionConfigStandalone:
    """Configuración standalone para extracción"""
    
    def __init__(self, **kwargs):
        # Configuración de Camelot
        self.camelot_stream_edge_tol = kwargs.get('camelot_stream_edge_tol', 50)
        self.camelot_lattice_line_scale = kwargs.get('camelot_lattice_line_scale', 15)
        self.camelot_process_background = kwargs.get('camelot_process_background', False)
        
        # Configuración de PDFplumber
        self.pdfplumber_snap_tolerance = kwargs.get('pdfplumber_snap_tolerance', 3)
        self.pdfplumber_join_tolerance = kwargs.get('pdfplumber_join_tolerance', 3)
        self.pdfplumber_edge_min_length = kwargs.get('pdfplumber_edge_min_length', 3)
        
        # Configuración de OpenCV
        self.opencv_threshold_type = kwargs.get('opencv_threshold_type', "THRESH_BINARY")
        self.opencv_kernel_size = kwargs.get('opencv_kernel_size', (3, 3))
        self.opencv_enhance_contrast = kwargs.get('opencv_enhance_contrast', True)
        
        # Configuración del detector de montos
        self.money_context_window = kwargs.get('money_context_window', 100)
        self.money_confidence_threshold = kwargs.get('money_confidence_threshold', 0.5)
        self.money_learning_enabled = kwargs.get('money_learning_enabled', True)
        
        # Configuración de chunks
        self.chunk_min_length = kwargs.get('chunk_min_length', 30)
        self.chunk_max_length = kwargs.get('chunk_max_length', 2000)
        self.chunk_overlap = kwargs.get('chunk_overlap', 50)
        
        # Timeouts y límites
        self.extraction_timeout = kwargs.get('extraction_timeout', 30)
        self.max_pages_to_analyze = kwargs.get('max_pages_to_analyze', 3)
        self.max_tables_per_page = kwargs.get('max_tables_per_page', 10)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte la configuración a diccionario"""
        return {
            'camelot_stream_edge_tol': self.camelot_stream_edge_tol,
            'camelot_lattice_line_scale': self.camelot_lattice_line_scale,
            'camelot_process_background': self.camelot_process_background,
            'pdfplumber_snap_tolerance': self.pdfplumber_snap_tolerance,
            'pdfplumber_join_tolerance': self.pdfplumber_join_tolerance,
            'pdfplumber_edge_min_length': self.pdfplumber_edge_min_length,
            'opencv_threshold_type': self.opencv_threshold_type,
            'opencv_kernel_size': self.opencv_kernel_size,
            'opencv_enhance_contrast': self.opencv_enhance_contrast,
            'money_context_window': self.money_context_window,
            'money_confidence_threshold': self.money_confidence_threshold,
            'money_learning_enabled': self.money_learning_enabled,
            'chunk_min_length': self.chunk_min_length,
            'chunk_max_length': self.chunk_max_length,
            'chunk_overlap': self.chunk_overlap,
            'extraction_timeout': self.extraction_timeout,
            'max_pages_to_analyze': self.max_pages_to_analyze,
            'max_tables_per_page': self.max_tables_per_page
        }

class ConfigOptimizerStandalone:
    """Optimizador standalone de configuración"""
    
    def __init__(self):
        self.base_configs = self._create_base_configs()
        self.performance_data = []
        self.optimization_rules = self._create_optimization_rules()
        
        # Cargar datos históricos
        self._load_performance_data()
    
    def _create_base_configs(self) -> Dict[str, ExtractionConfigStandalone]:
        """Crea configuraciones base"""
        
        return {
            'digital_simple': ExtractionConfigStandalone(
                camelot_stream_edge_tol=50,
                camelot_lattice_line_scale=15,
                pdfplumber_snap_tolerance=3,
                extraction_timeout=15,
                max_pages_to_analyze=5
            ),
            
            'digital_complex': ExtractionConfigStandalone(
                camelot_stream_edge_tol=30,
                camelot_lattice_line_scale=25,
                pdfplumber_snap_tolerance=5,
                pdfplumber_join_tolerance=5,
                extraction_timeout=45,
                max_tables_per_page=15
            ),
            
            'scanned_good_quality': ExtractionConfigStandalone(
                camelot_lattice_line_scale=40,
                camelot_process_background=True,
                pdfplumber_snap_tolerance=2,
                opencv_enhance_contrast=True,
                extraction_timeout=60,
                money_confidence_threshold=0.4
            ),
            
            'scanned_poor_quality': ExtractionConfigStandalone(
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
            
            'large_document': ExtractionConfigStandalone(
                extraction_timeout=120,
                max_pages_to_analyze=2,
                max_tables_per_page=8,
                chunk_max_length=1500,
                money_context_window=150
            ),
            
            'financial_document': ExtractionConfigStandalone(
                money_context_window=200,
                money_confidence_threshold=0.6,
                money_learning_enabled=True,
                chunk_min_length=50,
                camelot_lattice_line_scale=20
            )
        }
    
    def _create_optimization_rules(self) -> List[Dict[str, Any]]:
        """Crea reglas de optimización"""
        
        return [
            {
                'condition': lambda chars: chars.get('file_size_mb', 0) > 20,
                'adjustments': {
                    'extraction_timeout': lambda config: int(config.extraction_timeout * 1.5),
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
                    'extraction_timeout': lambda config: int(config.extraction_timeout * 1.2)
                },
                'description': 'Tablas complejas'
            },
            
            {
                'condition': lambda chars: not chars.get('has_borders', False),
                'adjustments': {
                    'pdfplumber_snap_tolerance': lambda config: max(1, config.pdfplumber_snap_tolerance // 2),
                    'pdfplumber_join_tolerance': lambda config: max(1, config.pdfplumber_join_tolerance // 2)
                },
                'description': 'Sin bordes visibles'
            }
        ]
    
    def get_optimal_config(self, document_characteristics: Dict[str, Any], 
                          performance_history: Optional[List[Dict[str, Any]]] = None) -> ExtractionConfigStandalone:
        """
        Obtiene configuración óptima para un documento
        
        Args:
            document_characteristics: Características del documento
            performance_history: Historial de rendimiento opcional
            
        Returns:
            Configuración optimizada
        """
        
        # Seleccionar configuración base
        base_config_name = self._select_base_config(document_characteristics)
        base_config = self.base_configs[base_config_name]
        
        # Crear copia para modificar
        config_dict = base_config.to_dict()
        config = ExtractionConfigStandalone(**config_dict)
        
        logger.info(f"🔧 Configuración base seleccionada: {base_config_name}")
        
        # Aplicar reglas de optimización
        applied_rules = []
        
        for rule in self.optimization_rules:
            if rule['condition'](document_characteristics):
                applied_rules.append(rule['description'])
                
                for attr_name, adjustment_func in rule['adjustments'].items():
                    if hasattr(config, attr_name):
                        old_value = getattr(config, attr_name)
                        new_value = adjustment_func(config)
                        setattr(config, attr_name, new_value)
                        
                        logger.info(f"   📝 {attr_name}: {old_value} → {new_value}")
        
        if applied_rules:
            logger.info(f"✅ Reglas aplicadas: {', '.join(applied_rules)}")
        
        # Optimizar desde historial si disponible
        if performance_history:
            config = self._optimize_from_history(config, document_characteristics, performance_history)
        
        # Validar configuración
        config = self._validate_config(config)
        
        return config
    
    def _select_base_config(self, characteristics: Dict[str, Any]) -> str:
        """Selecciona configuración base apropiada"""
        
        # Documento financiero
        if self._is_financial_document(characteristics):
            return 'financial_document'
        
        # Documento grande
        if characteristics.get('file_size_mb', 0) > 15 or characteristics.get('page_count', 0) > 30:
            return 'large_document'
        
        # Documento escaneado
        if characteristics.get('is_scanned', False):
            if characteristics.get('text_quality', 'good') == 'poor':
                return 'scanned_poor_quality'
            else:
                return 'scanned_good_quality'
        
        # Documento digital
        if characteristics.get('has_complex_tables', False) or characteristics.get('layout_complexity') == 'complex':
            return 'digital_complex'
        else:
            return 'digital_simple'
    
    def _is_financial_document(self, characteristics: Dict[str, Any]) -> bool:
        """Determina si es documento financiero"""
        financial_keywords = ['viáticos', 'gastos', 'presupuesto', 'financiero', 'monto', 'pago']
        
        summary = characteristics.get('summary', '').lower()
        return any(keyword in summary for keyword in financial_keywords)
    
    def _optimize_from_history(self, config: ExtractionConfigStandalone, 
                              characteristics: Dict[str, Any],
                              history: List[Dict[str, Any]]) -> ExtractionConfigStandalone:
        """Optimiza basado en historial de rendimiento"""
        
        # Buscar documentos similares en el historial
        similar_records = []
        
        for record in history:
            if self._calculate_similarity(characteristics, record.get('characteristics', {})) > 0.7:
                similar_records.append(record)
        
        if similar_records:
            # Usar configuración promedio de registros exitosos
            successful_records = [r for r in similar_records if r.get('success_rate', 0) > 0.8]
            
            if successful_records:
                config = self._average_successful_configs(config, successful_records)
                logger.info(f"📊 Optimizado con {len(successful_records)} registros similares exitosos")
        
        return config
    
    def _calculate_similarity(self, chars1: Dict[str, Any], chars2: Dict[str, Any]) -> float:
        """Calcula similitud entre características de documentos"""
        
        # Características numéricas
        numeric_attrs = ['file_size_mb', 'page_count']
        numeric_similarity = 0.0
        
        for attr in numeric_attrs:
            val1 = chars1.get(attr, 0)
            val2 = chars2.get(attr, 0)
            
            if val1 > 0 and val2 > 0:
                similarity = 1.0 - abs(val1 - val2) / max(val1, val2)
                numeric_similarity += max(0, similarity)
        
        numeric_similarity /= len(numeric_attrs)
        
        # Características booleanas
        boolean_attrs = ['is_scanned', 'has_complex_tables', 'has_borders']
        boolean_similarity = 0.0
        
        for attr in boolean_attrs:
            if chars1.get(attr) == chars2.get(attr):
                boolean_similarity += 1.0
        
        boolean_similarity /= len(boolean_attrs)
        
        # Características categóricas
        categorical_similarity = 0.0
        if chars1.get('text_quality') == chars2.get('text_quality'):
            categorical_similarity += 0.5
        if chars1.get('layout_complexity') == chars2.get('layout_complexity'):
            categorical_similarity += 0.5
        
        # Promedio ponderado
        total_similarity = (numeric_similarity * 0.4 + 
                          boolean_similarity * 0.4 + 
                          categorical_similarity * 0.2)
        
        return total_similarity
    
    def _average_successful_configs(self, base_config: ExtractionConfigStandalone, 
                                  successful_records: List[Dict[str, Any]]) -> ExtractionConfigStandalone:
        """Promedia configuraciones exitosas"""
        
        # Atributos numéricos a promediar
        numeric_attrs = [
            'camelot_stream_edge_tol', 'camelot_lattice_line_scale',
            'pdfplumber_snap_tolerance', 'pdfplumber_join_tolerance',
            'money_context_window', 'money_confidence_threshold',
            'extraction_timeout', 'max_pages_to_analyze'
        ]
        
        config_dict = base_config.to_dict()
        
        for attr in numeric_attrs:
            values = []
            for record in successful_records:
                config_used = record.get('config_used', {})
                if attr in config_used:
                    values.append(config_used[attr])
            
            if values:
                avg_value = sum(values) / len(values)
                if isinstance(config_dict[attr], int):
                    config_dict[attr] = int(avg_value)
                else:
                    config_dict[attr] = avg_value
        
        return ExtractionConfigStandalone(**config_dict)
    
    def _validate_config(self, config: ExtractionConfigStandalone) -> ExtractionConfigStandalone:
        """Valida y corrige configuración"""
        
        # Límites mínimos y máximos
        config.camelot_stream_edge_tol = max(10, min(100, config.camelot_stream_edge_tol))
        config.camelot_lattice_line_scale = max(5, min(100, config.camelot_lattice_line_scale))
        config.pdfplumber_snap_tolerance = max(1, min(10, config.pdfplumber_snap_tolerance))
        config.money_confidence_threshold = max(0.1, min(1.0, config.money_confidence_threshold))
        config.extraction_timeout = max(10, min(300, config.extraction_timeout))
        config.max_pages_to_analyze = max(1, min(10, config.max_pages_to_analyze))
        
        return config
    
    def record_performance(self, document_characteristics: Dict[str, Any],
                          config_used: Dict[str, Any],
                          results: Dict[str, Any]):
        """Registra rendimiento para aprendizaje futuro"""
        
        performance_record = {
            'timestamp': datetime.now().isoformat(),
            'characteristics': document_characteristics,
            'config_used': config_used,
            'results': results,
            'success_rate': results.get('success_rate', 0.0),
            'processing_time': results.get('processing_time', 0.0),
            'amounts_found': results.get('amounts_found', 0)
        }
        
        self.performance_data.append(performance_record)
        
        # Mantener solo últimos 100 registros
        if len(self.performance_data) > 100:
            self.performance_data = self.performance_data[-100:]
        
        # Guardar datos
        self._save_performance_data()
        
        logger.info(f"📊 Rendimiento registrado: {results.get('success_rate', 0):.1%} éxito")
    
    def _load_performance_data(self):
        """Carga datos de rendimiento histórico"""
        try:
            performance_file = Path('data/performance_history.json')
            if performance_file.exists():
                with open(performance_file, 'r', encoding='utf-8') as f:
                    self.performance_data = json.load(f)
                    logger.info(f"📊 Cargados {len(self.performance_data)} registros de rendimiento")
        except Exception as e:
            logger.warning(f"No se pudieron cargar datos de rendimiento: {e}")
    
    def _save_performance_data(self):
        """Guarda datos de rendimiento"""
        try:
            data_dir = Path('data')
            data_dir.mkdir(exist_ok=True)
            
            performance_file = data_dir / 'performance_history.json'
            
            with open(performance_file, 'w', encoding='utf-8') as f:
                json.dump(self.performance_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.warning(f"No se pudieron guardar datos de rendimiento: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de rendimiento"""
        
        if not self.performance_data:
            return {'total_records': 0}
        
        success_rates = [r.get('success_rate', 0) for r in self.performance_data]
        processing_times = [r.get('processing_time', 0) for r in self.performance_data]
        
        return {
            'total_records': len(self.performance_data),
            'avg_success_rate': sum(success_rates) / len(success_rates),
            'avg_processing_time': sum(processing_times) / len(processing_times),
            'best_success_rate': max(success_rates),
            'fastest_processing_time': min([t for t in processing_times if t > 0], default=0)
        }

def get_optimal_config_standalone(document_characteristics: Dict[str, Any],
                                performance_history: Optional[List[Dict[str, Any]]] = None) -> ExtractionConfigStandalone:
    """Función de conveniencia para obtener configuración óptima"""
    optimizer = ConfigOptimizerStandalone()
    return optimizer.get_optimal_config(document_characteristics, performance_history) 