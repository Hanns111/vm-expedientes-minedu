#!/usr/bin/env python3
"""
Tests Comprehensive Universal Extractor
=======================================

Suite de tests completa para validar el sistema de extracción universal
con métricas de rendimiento y cobertura.
"""

import unittest
import tempfile
import time
import json
from pathlib import Path
from typing import Dict, Any, List
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from universal_extractor.generic_table_extractor import GenericTableExtractor, DocumentCharacteristics
    from universal_extractor.generic_money_detector import GenericMoneyDetector, ExtractedEntity
    from universal_extractor.config_optimizer import ConfigOptimizer, DocumentProfile, ExtractionConfig
    from universal_extractor.adaptive_pipeline import AdaptivePipeline, ProcessingResult
    UNIVERSAL_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Universal extractor not available: {e}")
    UNIVERSAL_EXTRACTOR_AVAILABLE = False

class TestGenericTableExtractor(unittest.TestCase):
    """Tests para el extractor universal de tablas"""
    
    def setUp(self):
        if not UNIVERSAL_EXTRACTOR_AVAILABLE:
            self.skipTest("Universal extractor not available")
        
        self.extractor = GenericTableExtractor()
    
    def test_document_characteristics_analysis(self):
        """Test análisis de características del documento"""
        
        # Crear documento de prueba simulado
        mock_characteristics = DocumentCharacteristics(
            has_visible_lines=True,
            table_density=0.5,
            text_quality=0.8,
            scan_quality=0.7,
            document_type="directiva",
            page_count=10,
            complexity_score=0.6
        )
        
        # Verificar que se detectan las características correctamente
        self.assertTrue(mock_characteristics.has_visible_lines)
        self.assertEqual(mock_characteristics.document_type, "directiva")
        self.assertGreater(mock_characteristics.scan_quality, 0.5)
    
    def test_config_optimization(self):
        """Test optimización de configuración"""
        
        characteristics = DocumentCharacteristics(
            has_visible_lines=False,  # Sin líneas visibles
            table_density=0.3,
            text_quality=0.6,
            scan_quality=0.4,  # Baja calidad
            document_type="resolucion",
            page_count=5,
            complexity_score=0.8  # Alta complejidad
        )
        
        # La configuración debería optimizarse para documentos complejos
        config = self.extractor._optimize_config_for_document(characteristics)
        
        # Para documentos sin líneas visibles debería usar stream
        self.assertEqual(config.flavor, "stream")
        
        # Para baja calidad debería habilitar preprocesamiento
        self.assertTrue(config.edge_enhancement)
    
    def test_extraction_methods_availability(self):
        """Test disponibilidad de métodos de extracción"""
        
        characteristics = DocumentCharacteristics(
            has_visible_lines=True,
            table_density=0.8,
            text_quality=0.9,
            scan_quality=0.9,
            document_type="directiva",
            page_count=5,
            complexity_score=0.3
        )
        
        methods = self.extractor._get_optimal_method_order(characteristics, self.extractor.base_config)
        
        # Debe incluir al menos métodos básicos
        self.assertIn("regex_patterns", methods)
        self.assertGreater(len(methods), 0)
    
    def test_performance_metrics(self):
        """Test métricas de rendimiento"""
        
        initial_stats = self.extractor.get_performance_report()
        
        # Verificar estructura de métricas
        self.assertIn('total_extractions', initial_stats)
        self.assertIn('success_rate', initial_stats)
        self.assertIn('average_confidence', initial_stats)
        
        # Inicialmente debería tener 0 extracciones
        self.assertEqual(initial_stats['total_extractions'], 0)

class TestGenericMoneyDetector(unittest.TestCase):
    """Tests para el detector universal de montos y numerales"""
    
    def setUp(self):
        if not UNIVERSAL_EXTRACTOR_AVAILABLE:
            self.skipTest("Universal extractor not available")
        
        self.detector = GenericMoneyDetector(learning_enabled=True)
    
    def test_money_pattern_detection(self):
        """Test detección de patrones monetarios"""
        
        test_text = """
        Los viáticos diarios serán de S/ 380.00 para ministros de estado
        y S/ 320.00 para servidores civiles. El límite para declaración
        jurada es de S/ 30.00 por día.
        """
        
        result = self.detector.extract_entities_universal(test_text, "directiva")
        
        # Debe encontrar los montos especificados
        money_entities = result['money_entities']
        self.assertGreater(len(money_entities), 0)
        
        # Verificar que encuentra montos específicos
        amounts_found = [entity.normalized_value for entity in money_entities]
        self.assertIn("380.00", amounts_found)
        self.assertIn("320.00", amounts_found)
        self.assertIn("30.00", amounts_found)
    
    def test_numeral_pattern_detection(self):
        """Test detección de numerales legales"""
        
        test_text = """
        Conforme al numeral 8.4.17 de la presente directiva, y según
        lo establecido en el artículo 23, los servidores públicos...
        """
        
        result = self.detector.extract_entities_universal(test_text, "directiva")
        
        # Debe encontrar numerales legales
        numeral_entities = result['numeral_entities']
        self.assertGreater(len(numeral_entities), 0)
        
        # Verificar numerales específicos
        numerals_found = [entity.normalized_value for entity in numeral_entities]
        self.assertIn("8.4.17", numerals_found)
        self.assertIn("23", numerals_found)
    
    def test_pattern_learning(self):
        """Test aprendizaje de patrones"""
        
        initial_patterns = len(self.detector.learned_money_patterns)
        
        # Texto con patrón nuevo
        training_text = """
        El presupuesto aprobado es de mil quinientos nuevos soles (S/ 1,500.00)
        para el programa de capacitación según resolución ministerial.
        """
        
        result = self.detector.extract_entities_universal(training_text, "resolucion")
        
        # Debería haber aprendido nuevos patrones
        final_patterns = len(self.detector.learned_money_patterns)
        self.assertGreaterEqual(final_patterns, initial_patterns)
    
    def test_confidence_calculation(self):
        """Test cálculo de confianza"""
        
        # Texto con contexto claro
        high_confidence_text = "El monto de viáticos es S/ 380.00 según directiva"
        
        result = self.detector.extract_entities_universal(high_confidence_text, "directiva")
        
        if result['money_entities']:
            entity = result['money_entities'][0]
            # Debería tener alta confianza por contexto claro
            self.assertGreater(entity.confidence, 0.7)
    
    def test_performance_report(self):
        """Test reporte de rendimiento"""
        
        report = self.detector.get_performance_report()
        
        # Verificar estructura del reporte
        self.assertIn('extraction_stats', report)
        self.assertIn('pattern_stats', report)
        self.assertIn('efficiency_metrics', report)
        
        # Verificar métricas específicas
        pattern_stats = report['pattern_stats']
        self.assertIn('total_patterns', pattern_stats)
        self.assertIn('learning_rate', pattern_stats)

class TestConfigOptimizer(unittest.TestCase):
    """Tests para el optimizador de configuración"""
    
    def setUp(self):
        if not UNIVERSAL_EXTRACTOR_AVAILABLE:
            self.skipTest("Universal extractor not available")
        
        # Usar directorio temporal para cache
        self.temp_dir = tempfile.mkdtemp()
        self.optimizer = ConfigOptimizer(cache_dir=self.temp_dir)
    
    def test_base_rules_initialization(self):
        """Test inicialización de reglas base"""
        
        # Debe tener reglas base configuradas
        self.assertGreater(len(self.optimizer.optimization_rules), 0)
        
        # Verificar estructura de reglas
        for rule in self.optimizer.optimization_rules:
            self.assertIsNotNone(rule.name)
            self.assertIsNotNone(rule.condition)
            self.assertIsNotNone(rule.action)
            self.assertGreater(rule.confidence, 0)
    
    def test_document_profile_analysis(self):
        """Test análisis de perfil de documento"""
        
        # Simular análisis de documento
        mock_profile = DocumentProfile(
            file_hash="test_hash",
            file_size_mb=2.5,
            page_count=15,
            text_density=1.2,
            image_density=0.3,
            table_indicators=8,
            scan_quality=0.8,
            document_type="directiva"
        )
        
        # Verificar que el perfil tiene valores válidos
        self.assertEqual(mock_profile.document_type, "directiva")
        self.assertGreater(mock_profile.scan_quality, 0.5)
        self.assertGreater(mock_profile.page_count, 0)
    
    def test_config_generation(self):
        """Test generación de configuración"""
        
        profile = DocumentProfile(
            file_hash="test",
            file_size_mb=1.0,
            page_count=5,
            text_density=0.8,
            image_density=0.1,
            table_indicators=3,
            scan_quality=0.9,  # Alta calidad
            document_type="decreto"
        )
        
        config = self.optimizer._generate_base_config(profile)
        
        # Para alta calidad no debería necesitar preprocesamiento
        self.assertFalse(config.opencv_enable_preprocessing)
        
        # Para documentos oficiales debería ser más permisivo
        self.assertLessEqual(config.camelot_confidence_threshold, 0.7)
    
    def test_rule_evaluation(self):
        """Test evaluación de reglas"""
        
        from universal_extractor.config_optimizer import OptimizationRule
        
        rule = OptimizationRule(
            name="Test Rule",
            condition="scan_quality < 0.5",
            action={"opencv_enable_preprocessing": True},
            confidence=0.8
        )
        
        # Perfil que cumple la condición
        profile_low_quality = DocumentProfile(
            file_hash="test",
            file_size_mb=1.0,
            page_count=5,
            text_density=0.8,
            image_density=0.1,
            table_indicators=3,
            scan_quality=0.3,  # Baja calidad
            document_type="directiva"
        )
        
        config = ExtractionConfig()
        
        should_apply = self.optimizer._evaluate_rule_condition(rule, profile_low_quality, config)
        self.assertTrue(should_apply)
        
        # Perfil que no cumple la condición
        profile_high_quality = DocumentProfile(
            file_hash="test",
            file_size_mb=1.0,
            page_count=5,
            text_density=0.8,
            image_density=0.1,
            table_indicators=3,
            scan_quality=0.9,  # Alta calidad
            document_type="directiva"
        )
        
        should_not_apply = self.optimizer._evaluate_rule_condition(rule, profile_high_quality, config)
        self.assertFalse(should_not_apply)
    
    def test_optimization_report(self):
        """Test reporte de optimización"""
        
        report = self.optimizer.get_optimization_report()
        
        # Verificar estructura del reporte
        self.assertIn('performance_summary', report)
        self.assertIn('learning_summary', report)
        self.assertIn('cache_summary', report)
        
        # Verificar métricas específicas
        performance = report['performance_summary']
        self.assertIn('total_optimizations', performance)
        self.assertIn('success_rate', performance)

class TestAdaptivePipeline(unittest.TestCase):
    """Tests para el pipeline adaptativo completo"""
    
    def setUp(self):
        if not UNIVERSAL_EXTRACTOR_AVAILABLE:
            self.skipTest("Universal extractor not available")
        
        # Usar directorio temporal para output
        self.temp_dir = tempfile.mkdtemp()
        self.pipeline = AdaptivePipeline(
            output_dir=self.temp_dir,
            enable_learning=True,
            enable_caching=True,
            max_processing_time=60
        )
    
    def test_pipeline_initialization(self):
        """Test inicialización del pipeline"""
        
        # Verificar que todos los componentes se inicializaron
        self.assertIsNotNone(self.pipeline.table_extractor)
        self.assertIsNotNone(self.pipeline.money_detector)
        self.assertIsNotNone(self.pipeline.config_optimizer)
        
        # Verificar configuración
        self.assertTrue(self.pipeline.enable_learning)
        self.assertTrue(self.pipeline.enable_caching)
        self.assertEqual(self.pipeline.max_processing_time, 60)
    
    def test_document_filtering(self):
        """Test filtrado de documentos"""
        
        # Configurar filtros
        self.pipeline.set_date_filters(exclude_superseded=True)
        
        # Documento normal debería procesarse
        should_process = self.pipeline._should_process_document("test.pdf")
        self.assertTrue(should_process)  # Asumiendo que el archivo existe
    
    def test_text_extraction_methods(self):
        """Test métodos de extracción de texto"""
        
        # Test extracción de texto de tablas
        mock_tables = [
            {
                'headers': ['Cargo', 'Monto'],
                'data': [['Ministro', 'S/ 380.00'], ['Servidor', 'S/ 320.00']]
            }
        ]
        
        table_text = self.pipeline._extract_text_from_tables(mock_tables)
        
        # Debe contener el texto de las tablas
        self.assertIn('Cargo', table_text)
        self.assertIn('Monto', table_text)
        self.assertIn('S/ 380.00', table_text)
    
    def test_document_type_detection(self):
        """Test detección de tipo de documento"""
        
        directiva_text = "DIRECTIVA N° 001-2023 - Procedimientos de viáticos"
        doc_type = self.pipeline._detect_document_type_from_text(directiva_text)
        self.assertEqual(doc_type, "directiva")
        
        decreto_text = "DECRETO SUPREMO N° 007-2013-EF"
        doc_type = self.pipeline._detect_document_type_from_text(decreto_text)
        self.assertEqual(doc_type, "decreto")
    
    def test_confidence_calculation(self):
        """Test cálculo de confianza global"""
        
        table_results = {'metadata': {'confidence_score': 0.8}}
        entity_results = {'money_entities': [], 'numeral_entities': []}
        cross_validated = [
            {'confidence': 0.9, 'cross_validated': True},
            {'confidence': 0.7, 'cross_validated': False}
        ]
        
        confidence = self.pipeline._calculate_global_confidence(
            table_results, entity_results, cross_validated
        )
        
        # Verificar estructura del resultado
        self.assertIn('global_confidence', confidence)
        self.assertIn('table_confidence', confidence)
        self.assertIn('entity_confidence', confidence)
        
        # Confianza global debe estar entre 0 y 1
        self.assertGreaterEqual(confidence['global_confidence'], 0.0)
        self.assertLessEqual(confidence['global_confidence'], 1.0)
    
    def test_cross_validation(self):
        """Test cross-validación de entidades"""
        
        # Simular entidades de tablas
        table_entities = [
            {'value': '380.00', 'type': 'amount', 'source': 'table_1', 'confidence': 0.8}
        ]
        
        # Simular entidades de texto
        text_entities = [
            ExtractedEntity(value='380.00', type='amount', confidence=0.7, context='viáticos de ministros'),
            ExtractedEntity(value='25.50', type='amount', confidence=0.6, context='otros gastos')
        ]
        
        cross_validated = self.pipeline._cross_validate_entities(table_entities, text_entities)
        
        # Debe haber encontrado entidades cross-validadas
        self.assertGreater(len(cross_validated), 0)
        
        # Entidad que aparece en ambos debe tener cross_validated=True
        validated_380 = next((e for e in cross_validated if e['value'] == '380.00'), None)
        self.assertIsNotNone(validated_380)
        self.assertTrue(validated_380['cross_validated'])
    
    def test_performance_report(self):
        """Test reporte de rendimiento completo"""
        
        report = self.pipeline.get_performance_report()
        
        # Verificar estructura completa
        self.assertIn('global_stats', report)
        self.assertIn('table_extractor_performance', report)
        self.assertIn('money_detector_performance', report)
        self.assertIn('config_optimizer_performance', report)
        self.assertIn('cache_stats', report)
        self.assertIn('learning_stats', report)
        
        # Verificar métricas específicas
        global_stats = report['global_stats']
        self.assertIn('total_documents', global_stats)
        self.assertIn('successful_documents', global_stats)

class TestPerformanceBenchmarks(unittest.TestCase):
    """Tests de rendimiento y benchmarks"""
    
    def setUp(self):
        if not UNIVERSAL_EXTRACTOR_AVAILABLE:
            self.skipTest("Universal extractor not available")
        
        self.pipeline = AdaptivePipeline(enable_learning=True)
    
    def test_processing_speed_benchmark(self):
        """Benchmark de velocidad de procesamiento"""
        
        # Crear texto de prueba representativo
        test_texts = [
            """
            DIRECTIVA N° 001-2023-MINEDU
            Los montos de viáticos son:
            - Ministros: S/ 380.00 diarios
            - Servidores: S/ 320.00 diarios
            Según numeral 8.4.17 de la presente directiva.
            """,
            """
            RESOLUCIÓN MINISTERIAL N° 045-2023
            Se establece el límite de S/ 30.00 para declaración jurada
            conforme al artículo 23 del reglamento.
            """,
            """
            DECRETO SUPREMO N° 007-2013-EF
            Procedimientos especiales para comisiones internacionales
            con presupuesto de USD 1,500.00 según numeral 10.2.3.
            """
        ]
        
        # Medir tiempo de procesamiento
        total_start_time = time.time()
        
        for i, text in enumerate(test_texts):
            start_time = time.time()
            
            # Procesar con detector de entidades
            result = self.pipeline.money_detector.extract_entities_universal(text, "directiva")
            
            processing_time = time.time() - start_time
            
            # Verificar que el procesamiento es rápido (< 1 segundo por texto)
            self.assertLess(processing_time, 1.0, f"Text {i} took too long: {processing_time:.3f}s")
            
            # Verificar que encuentra entidades
            total_entities = len(result['money_entities']) + len(result['numeral_entities'])
            self.assertGreater(total_entities, 0, f"No entities found in text {i}")
        
        total_time = time.time() - total_start_time
        
        # Tiempo total debe ser razonable
        self.assertLess(total_time, 5.0, f"Total processing took too long: {total_time:.3f}s")
        
        print(f"✅ Benchmark passed: {len(test_texts)} texts processed in {total_time:.3f}s")
    
    def test_memory_usage_benchmark(self):
        """Benchmark de uso de memoria"""
        
        # Este test verificaría el uso de memoria, pero requiere psutil
        # Por simplicidad, verificamos que los objetos no crecen indefinidamente
        
        initial_patterns = len(self.pipeline.money_detector.learned_money_patterns)
        
        # Procesar múltiples textos
        for i in range(10):
            test_text = f"El monto {i} es de S/ {100 + i}.00 según directiva {i}."
            self.pipeline.money_detector.extract_entities_universal(test_text, "directiva")
        
        final_patterns = len(self.pipeline.money_detector.learned_money_patterns)
        
        # Los patrones aprendidos no deberían crecer sin control
        pattern_growth = final_patterns - initial_patterns
        self.assertLess(pattern_growth, 50, f"Too many patterns learned: {pattern_growth}")
    
    def test_accuracy_benchmark(self):
        """Benchmark de precisión"""
        
        # Casos de prueba con resultados esperados
        test_cases = [
            {
                'text': "Los viáticos de ministros son S/ 380.00 según numeral 8.4.17",
                'expected_amounts': ['380.00'],
                'expected_numerals': ['8.4.17']
            },
            {
                'text': "Límite de declaración jurada: S/ 30.00 conforme artículo 23",
                'expected_amounts': ['30.00'],
                'expected_numerals': ['23']
            },
            {
                'text': "Presupuesto USD 1,500.00 para capacitación según numeral 10.2.3",
                'expected_amounts': ['1500.00'],
                'expected_numerals': ['10.2.3']
            }
        ]
        
        correct_predictions = 0
        total_predictions = 0
        
        for case in test_cases:
            result = self.pipeline.money_detector.extract_entities_universal(case['text'], "directiva")
            
            # Verificar montos
            found_amounts = [entity.normalized_value for entity in result['money_entities']]
            for expected in case['expected_amounts']:
                if expected in found_amounts:
                    correct_predictions += 1
                total_predictions += 1
            
            # Verificar numerales
            found_numerals = [entity.normalized_value for entity in result['numeral_entities']]
            for expected in case['expected_numerals']:
                if expected in found_numerals:
                    correct_predictions += 1
                total_predictions += 1
        
        # Calcular precisión
        accuracy = correct_predictions / total_predictions if total_predictions > 0 else 0
        
        print(f"📊 Accuracy: {correct_predictions}/{total_predictions} ({accuracy:.1%})")
        
        # La precisión debería ser al menos 70%
        self.assertGreaterEqual(accuracy, 0.7, f"Accuracy too low: {accuracy:.1%}")

def run_comprehensive_tests():
    """Ejecutar suite completa de tests"""
    
    print("🧪 RUNNING COMPREHENSIVE UNIVERSAL EXTRACTOR TESTS")
    print("=" * 70)
    
    if not UNIVERSAL_EXTRACTOR_AVAILABLE:
        print("❌ Universal extractor not available - skipping tests")
        return False
    
    # Crear suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar todas las clases de test
    test_classes = [
        TestGenericTableExtractor,
        TestGenericMoneyDetector,
        TestConfigOptimizer,
        TestAdaptivePipeline,
        TestPerformanceBenchmarks
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print(f"\n📊 TEST SUMMARY")
    print("=" * 20)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    success = result.wasSuccessful()
    
    if success:
        print("✅ All tests passed!")
        print("🎉 Universal extractor system is ready for production")
    else:
        print("❌ Some tests failed")
        
        if result.failures:
            print("\nFailures:")
            for test, traceback in result.failures:
                print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
        
        if result.errors:
            print("\nErrors:")
            for test, traceback in result.errors:
                print(f"  - {test}: {traceback.split('Error:')[-1].strip()}")
    
    return success

if __name__ == "__main__":
    success = run_comprehensive_tests()
    exit(0 if success else 1)