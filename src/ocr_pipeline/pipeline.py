#!/usr/bin/env python3
"""
Document Processing Pipeline - Main Integration Module
====================================================

Main pipeline that orchestrates OCR, layout analysis, structure detection,
NER, and intelligent chunking. Integrates seamlessly with existing hybrid
search system while replacing manual chunking.
"""

import os
import json
import logging
import time
from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import traceback

from .core.ocr_engine import OCREngine
from .core.layout_detector import LayoutDetector
from .core.structure_analyzer import StructureAnalyzer
from .processors.legal_ner import LegalNER
from .processors.intelligent_chunker import IntelligentChunker
from .processors.hybrid_chunker import HybridChunker
from .validation.entity_validator import EntityValidator
from .validation import DirectivaEntities, ValidationResults, VALIDATION_AVAILABLE
from .extractors import CamelotTableExtractor, CAMELOT_EXTRACTOR_AVAILABLE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Complete document processing pipeline for legal documents.
    
    Workflow:
    1. PDF → Images (if needed)
    2. OCR → Text extraction
    3. Layout → Structure detection
    4. Hierarchy → Legal structure analysis
    5. NER → Entity extraction
    6. Chunking → Intelligent chunk creation
    7. Output → Compatible with existing hybrid system
    """
    
    def __init__(
        self,
        output_dir: str = "data/processed",
        backup_dir: str = "data/backup/ocr_pipeline",
        enable_fallbacks: bool = True,
        chunk_strategy: str = "hybrid",
        use_camelot_tables: bool = True
    ):
        """
        Initialize document processing pipeline.
        
        Args:
            output_dir: Directory for processed outputs
            backup_dir: Directory for backups
            enable_fallbacks: Enable fallback methods if primary fails
            chunk_strategy: Chunking strategy ('hierarchy_based', 'semantic_based', 'hybrid')
            use_camelot_tables: Whether to use Camelot for table extraction
        """
        self.output_dir = Path(output_dir)
        self.backup_dir = Path(backup_dir)
        self.enable_fallbacks = enable_fallbacks
        self.chunk_strategy = chunk_strategy
        self.use_camelot_tables = use_camelot_tables
        
        # Create directories
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize pipeline components
        self.ocr_engine = None
        self.layout_detector = None
        self.structure_analyzer = None
        self.ner_system = None
        self.chunker = None
        self.hybrid_chunker = None
        self.entity_validator = None
        
        self._initialize_components()
        
        # Processing statistics
        self.stats = {
            'documents_processed': 0,
            'total_chunks_created': 0,
            'total_entities_extracted': 0,
            'processing_time_total': 0.0,
            'errors': []
        }
        
        logger.info(f"Document processor initialized - output: {output_dir}")
    
    def _initialize_components(self):
        """Initialize all pipeline components with error handling."""
        try:
            logger.info("Initializing OCR engine...")
            self.ocr_engine = OCREngine(confidence_threshold=0.6)
            logger.info("✓ OCR engine ready")
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            if not self.enable_fallbacks:
                raise
        
        try:
            logger.info("Initializing layout detector...")
            self.layout_detector = LayoutDetector(confidence_threshold=0.5)
            logger.info("✓ Layout detector ready")
        except Exception as e:
            logger.error(f"Failed to initialize layout detector: {e}")
            if not self.enable_fallbacks:
                raise
        
        try:
            logger.info("Initializing structure analyzer...")
            self.structure_analyzer = StructureAnalyzer()
            logger.info("✓ Structure analyzer ready")
        except Exception as e:
            logger.error(f"Failed to initialize structure analyzer: {e}")
            if not self.enable_fallbacks:
                raise
        
        try:
            logger.info("Initializing NER system...")
            self.ner_system = LegalNER()
            logger.info("✓ NER system ready")
        except Exception as e:
            logger.error(f"Failed to initialize NER system: {e}")
            if not self.enable_fallbacks:
                raise
        
        try:
            logger.info("Initializing intelligent chunker...")
            self.chunker = IntelligentChunker()
            logger.info("✓ Intelligent chunker ready")
        except Exception as e:
            logger.error(f"Failed to initialize chunker: {e}")
            if not self.enable_fallbacks:
                raise
        
        try:
            logger.info("Initializing hybrid chunker with Camelot integration...")
            self.hybrid_chunker = HybridChunker(
                chunk_size=500,
                overlap=50,
                preserve_numerals=True,
                integrate_tables=self.use_camelot_tables
            )
            if CAMELOT_EXTRACTOR_AVAILABLE and self.use_camelot_tables:
                logger.info("✓ Hybrid chunker with Camelot integration ready")
            else:
                logger.info("✓ Hybrid chunker ready (no Camelot)")
        except Exception as e:
            logger.error(f"Failed to initialize hybrid chunker: {e}")
            if not self.enable_fallbacks:
                raise
        
        try:
            logger.info("Initializing entity validator...")
            self.entity_validator = EntityValidator(strict_validation=False)
            if VALIDATION_AVAILABLE:
                logger.info("✓ Pydantic entity validator ready")
            else:
                logger.info("✓ Fallback entity validator ready")
        except Exception as e:
            logger.error(f"Failed to initialize entity validator: {e}")
            if not self.enable_fallbacks:
                raise
    
    def process_pdf(
        self,
        pdf_path: str,
        document_id: Optional[str] = None,
        save_intermediates: bool = True
    ) -> Dict[str, Any]:
        """
        Process a PDF document through the complete pipeline.
        
        Args:
            pdf_path: Path to PDF file
            document_id: Optional document identifier
            save_intermediates: Save intermediate processing results
            
        Returns:
            Complete processing results including chunks
        """
        start_time = time.time()
        
        if document_id is None:
            document_id = Path(pdf_path).stem
        
        logger.info(f"Processing document: {pdf_path} (ID: {document_id})")
        
        try:
            # Step 1: OCR - Extract text from PDF
            logger.info("Step 1: OCR text extraction...")
            ocr_results = self._run_ocr(pdf_path)
            
            if save_intermediates:
                self._save_intermediate('ocr_results', document_id, ocr_results)
            
            # Step 2: Layout Detection
            logger.info("Step 2: Layout detection...")
            layout_results = self._run_layout_detection(pdf_path, ocr_results)
            
            if save_intermediates:
                self._save_intermediate('layout_results', document_id, layout_results)
            
            # Step 3: Structure Analysis
            logger.info("Step 3: Structure analysis...")
            structure_results = self._run_structure_analysis(ocr_results, layout_results)
            
            if save_intermediates:
                self._save_intermediate('structure_results', document_id, structure_results)
            
            # Step 4: NER - Entity Extraction
            logger.info("Step 4: Entity extraction...")
            entity_results = self._run_entity_extraction(structure_results)
            
            if save_intermediates:
                self._save_intermediate('entity_results', document_id, entity_results)
            
            # Step 4.5: Entity Validation (NEW)
            logger.info("Step 4.5: Entity validation...")
            validation_results = self._run_entity_validation(entity_results, document_id)
            
            if save_intermediates:
                self._save_intermediate('validation_results', document_id, validation_results)
            
            # Step 5: Hybrid Chunking with Camelot Integration
            logger.info("Step 5: Hybrid chunking with numeral preservation...")
            chunks = self._run_hybrid_chunking(structure_results, pdf_path)
            
            # Step 6: Create final output compatible with existing system
            final_output = self._create_final_output(
                document_id, chunks, ocr_results, layout_results, 
                structure_results, entity_results, validation_results
            )
            
            # Save final chunks in compatible format
            self._save_final_chunks(document_id, chunks)
            
            processing_time = time.time() - start_time
            self._update_stats(chunks, entity_results, processing_time)
            
            logger.info(f"✓ Document processed successfully in {processing_time:.2f}s")
            logger.info(f"  Created {len(chunks)} chunks with {sum(len(e.get('entities', {})) for e in entity_results)} entities")
            
            return final_output
            
        except Exception as e:
            logger.error(f"Error processing document {pdf_path}: {e}")
            logger.error(traceback.format_exc())
            self.stats['errors'].append({
                'document_id': document_id,
                'error': str(e),
                'timestamp': time.time()
            })
            raise
    
    def _run_ocr(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Run OCR extraction on PDF."""
        if self.ocr_engine is None:
            raise ValueError("OCR engine not initialized")
        
        return self.ocr_engine.extract_text_from_pdf(pdf_path)
    
    def _run_layout_detection(
        self, 
        pdf_path: str, 
        ocr_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Run layout detection on document pages."""
        if self.layout_detector is None:
            logger.warning("Layout detector not available - skipping layout analysis")
            return []
        
        layout_results = []
        
        # Convert PDF to images for layout detection
        try:
            from pdf2image import convert_from_path
            images = convert_from_path(pdf_path, dpi=200)
            
            for i, image in enumerate(images):
                import numpy as np
                image_np = np.array(image)
                
                layout_result = self.layout_detector.detect_layout(image_np)
                layout_result['page_number'] = i + 1
                layout_results.append(layout_result)
        
        except Exception as e:
            logger.warning(f"Layout detection failed: {e}")
            if not self.enable_fallbacks:
                raise
        
        return layout_results
    
    def _run_structure_analysis(
        self,
        ocr_results: List[Dict[str, Any]],
        layout_results: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run structure analysis on OCR and layout results."""
        if self.structure_analyzer is None:
            raise ValueError("Structure analyzer not initialized")
        
        # Combine OCR text blocks from all pages
        all_text_blocks = []
        for page_result in ocr_results:
            for block in page_result.get('blocks', []):
                all_text_blocks.append({
                    'text': block.get('text', ''),
                    'bbox': block.get('bbox', []),
                    'confidence': block.get('confidence', 0.0),
                    'page': page_result.get('page_number', 1)
                })
        
        return self.structure_analyzer.analyze_document_structure(all_text_blocks)
    
    def _run_entity_extraction(self, structure_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run NER entity extraction on structured content."""
        if self.ner_system is None:
            logger.warning("NER system not available - skipping entity extraction")
            return []
        
        entity_results = []
        
        # Extract entities from each section
        for section in structure_results.get('sections', []):
            section_text = section.get('text_content', '')
            if section_text:
                entities = self.ner_system.extract_entities(section_text)
                entity_summary = self.ner_system.get_entity_summary(entities)
                
                entity_results.append({
                    'section_id': section.get('id'),
                    'section_number': section.get('number'),
                    'entities': [
                        {
                            'text': e.text,
                            'label': e.label,
                            'normalized_value': e.normalized_value,
                            'confidence': e.confidence
                        } for e in entities
                    ],
                    'summary': entity_summary
                })
        
        return entity_results
    
    def _run_intelligent_chunking(self, structure_results: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Run intelligent chunking on structured content."""
        if self.chunker is None:
            raise ValueError("Chunker not initialized")
        
        return self.chunker.create_intelligent_chunks(structure_results, self.chunk_strategy)
    
    def _run_hybrid_chunking(self, 
                           structure_results: Dict[str, Any], 
                           pdf_path: str) -> List[Dict[str, Any]]:
        """Run hybrid chunking with Camelot table extraction and numeral preservation."""
        if self.hybrid_chunker is None:
            logger.warning("Hybrid chunker not available - using fallback")
            return self._run_intelligent_chunking(structure_results)
        
        try:
            # Use hybrid chunker with table integration
            chunks = self.hybrid_chunker.create_hybrid_chunks(
                content=structure_results,
                pdf_path=pdf_path if self.use_camelot_tables else None
            )
            
            logger.info(f"Hybrid chunking created {len(chunks)} chunks")
            
            # Log chunking statistics
            stats = self.hybrid_chunker.get_chunking_stats()
            logger.info(f"Chunking stats: {stats}")
            
            return chunks
            
        except Exception as e:
            logger.error(f"Hybrid chunking failed: {e}")
            logger.info("Falling back to intelligent chunking")
            return self._run_intelligent_chunking(structure_results)
    
    def _run_entity_validation(
        self, 
        entity_results: List[Dict[str, Any]], 
        document_id: str
    ) -> Dict[str, Any]:
        """Run Pydantic validation on extracted entities."""
        if self.entity_validator is None:
            logger.warning("Entity validator not available - skipping validation")
            return {"validation_skipped": True}
        
        # Combine all entities from all sections
        combined_entities = {}
        overall_confidence = 0.0
        entity_count = 0
        
        for section_result in entity_results:
            entities = section_result.get('entities', [])
            for entity in entities:
                label = entity.get('label', 'unknown')
                if label not in combined_entities:
                    combined_entities[label] = []
                
                combined_entities[label].append({
                    'text': entity.get('text', ''),
                    'normalized': entity.get('normalized_value', ''),
                    'confidence': entity.get('confidence', 0.8)
                })
                
                overall_confidence += entity.get('confidence', 0.8)
                entity_count += 1
        
        # Calculate average confidence
        if entity_count > 0:
            overall_confidence = overall_confidence / entity_count
        else:
            overall_confidence = 0.8
        
        logger.info(f"Validating {entity_count} entities with avg confidence {overall_confidence:.3f}")
        
        # Run validation
        try:
            validation_results = self.entity_validator.validate_entities(
                combined_entities, 
                overall_confidence, 
                document_id
            )
            
            if VALIDATION_AVAILABLE and hasattr(validation_results, 'get_summary'):
                summary = validation_results.get_summary()
                logger.info(f"Validation complete: {summary}")
                
                # Log validation issues
                if hasattr(validation_results, 'validation_errors'):
                    for error in validation_results.validation_errors:
                        logger.warning(f"Validation {error.severity}: {error.error_message}")
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Entity validation failed: {e}")
            # Return fallback validation
            return {
                'document_id': document_id,
                'validation_error': str(e),
                'validation_skipped': True,
                'is_valid': True,  # Assume valid to not block pipeline
                'ready_for_vectorstore': True
            }
    
    def _create_final_output(
        self,
        document_id: str,
        chunks: List[Dict[str, Any]],
        ocr_results: List[Dict[str, Any]],
        layout_results: List[Dict[str, Any]],
        structure_results: Dict[str, Any],
        entity_results: List[Dict[str, Any]],
        validation_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create final output with all processing results."""
        # Extract validation summary
        validation_summary = {}
        if isinstance(validation_results, dict):
            if validation_results.get('validation_skipped'):
                validation_summary = {
                    'validation_status': 'skipped',
                    'reason': validation_results.get('validation_error', 'validator not available')
                }
            else:
                validation_summary = {
                    'validation_status': 'completed',
                    'is_valid': validation_results.get('is_valid', True),
                    'ready_for_vectorstore': validation_results.get('ready_for_vectorstore', True),
                    'overall_confidence': validation_results.get('overall_confidence', 0.8),
                    'confidence_level': validation_results.get('confidence_level', 'medium'),
                    'validation_errors': len(validation_results.get('validation_errors', [])),
                    'critical_errors': validation_results.get('critical_errors', 0)
                }
        elif hasattr(validation_results, 'get_summary'):
            validation_summary = validation_results.get_summary()
            validation_summary['validation_status'] = 'completed'
        else:
            validation_summary = {'validation_status': 'unknown'}
        
        return {
            'document_id': document_id,
            'processing_timestamp': time.time(),
            'pipeline_version': '1.0.0',
            'chunks': chunks,
            'chunk_count': len(chunks),
            'total_entities': sum(len(e.get('entities', [])) for e in entity_results),
            'validation_summary': validation_summary,
            'processing_summary': {
                'ocr_pages': len(ocr_results),
                'layout_elements': sum(len(l.get('elements', [])) for l in layout_results),
                'structure_sections': len(structure_results.get('sections', [])),
                'hierarchy_depth': structure_results.get('max_depth', 0),
                'document_type': structure_results.get('document_type', 'unknown')
            },
            'pipeline_components': {
                'ocr_engine': self.ocr_engine.get_stats() if self.ocr_engine else None,
                'layout_detector': self.layout_detector.get_stats() if self.layout_detector else None,
                'structure_analyzer': self.structure_analyzer.get_stats() if self.structure_analyzer else None,
                'ner_system': self.ner_system.get_stats() if self.ner_system else None,
                'chunker': self.chunker.get_stats() if self.chunker else None,
                'entity_validator': {'validation_available': VALIDATION_AVAILABLE}
            }
        }
    
    def _save_intermediate(self, stage: str, document_id: str, data: Any):
        """Save intermediate processing results."""
        filename = f"{document_id}_{stage}.json"
        filepath = self.backup_dir / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.debug(f"Saved intermediate: {filepath}")
        except Exception as e:
            logger.warning(f"Failed to save intermediate {stage}: {e}")
    
    def _save_final_chunks(self, document_id: str, chunks: List[Dict[str, Any]]):
        """Save final chunks in format compatible with existing system."""
        # Save in the same format as current chunks.json
        output_file = self.output_dir / f"chunks_ocr_{document_id}.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Saved {len(chunks)} chunks to {output_file}")
            
            # Also update the main chunks.json for compatibility
            main_chunks_file = self.output_dir / "chunks.json"
            if main_chunks_file.exists():
                # Backup existing chunks
                backup_file = self.backup_dir / f"chunks_backup_{int(time.time())}.json"
                import shutil
                shutil.copy2(main_chunks_file, backup_file)
                logger.info(f"Backed up existing chunks to {backup_file}")
            
            # Write new chunks
            with open(main_chunks_file, 'w', encoding='utf-8') as f:
                json.dump(chunks, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Updated main chunks file: {main_chunks_file}")
            
        except Exception as e:
            logger.error(f"Failed to save chunks: {e}")
            raise
    
    def _update_stats(
        self, 
        chunks: List[Dict[str, Any]], 
        entity_results: List[Dict[str, Any]], 
        processing_time: float
    ):
        """Update processing statistics."""
        self.stats['documents_processed'] += 1
        self.stats['total_chunks_created'] += len(chunks)
        self.stats['total_entities_extracted'] += sum(len(e.get('entities', [])) for e in entity_results)
        self.stats['processing_time_total'] += processing_time
    
    def process_batch(
        self,
        pdf_files: List[str],
        max_workers: int = 1  # Sequential for now, can be parallelized later
    ) -> List[Dict[str, Any]]:
        """Process multiple PDF files in batch."""
        logger.info(f"Processing batch of {len(pdf_files)} documents")
        
        results = []
        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"Processing document {i}/{len(pdf_files)}: {pdf_file}")
            
            try:
                result = self.process_pdf(pdf_file)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                results.append({
                    'document_id': Path(pdf_file).stem,
                    'error': str(e),
                    'success': False
                })
        
        logger.info(f"Batch processing completed: {len(results)} results")
        return results
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics."""
        avg_processing_time = (
            self.stats['processing_time_total'] / max(self.stats['documents_processed'], 1)
        )
        
        return {
            **self.stats,
            'avg_processing_time': avg_processing_time,
            'avg_chunks_per_document': (
                self.stats['total_chunks_created'] / max(self.stats['documents_processed'], 1)
            ),
            'avg_entities_per_document': (
                self.stats['total_entities_extracted'] / max(self.stats['documents_processed'], 1)
            ),
            'component_status': {
                'ocr_engine': self.ocr_engine is not None,
                'layout_detector': self.layout_detector is not None,
                'structure_analyzer': self.structure_analyzer is not None,
                'ner_system': self.ner_system is not None,
                'chunker': self.chunker is not None
            }
        }


if __name__ == "__main__":
    # Test the complete pipeline
    processor = DocumentProcessor()
    
    print("Document processor initialized successfully")
    print(f"Processing stats: {processor.get_processing_stats()}")
    
    # Test with sample PDF if available
    test_pdf = "data/raw/directiva_de_viaticos_011_2020_imagen.pdf"
    if Path(test_pdf).exists():
        print(f"\nTesting complete pipeline with: {test_pdf}")
        
        try:
            result = processor.process_pdf(test_pdf, document_id="test_directiva")
            
            print(f"✓ Processing completed successfully!")
            print(f"  Document ID: {result['document_id']}")
            print(f"  Chunks created: {result['chunk_count']}")
            print(f"  Total entities: {result['total_entities']}")
            print(f"  Document type: {result['processing_summary']['document_type']}")
            
            # Show sample chunks
            chunks = result['chunks']
            if chunks:
                print(f"\nSample chunks:")
                for i, chunk in enumerate(chunks[:2]):
                    print(f"  Chunk {i+1}: {chunk['titulo']}")
                    print(f"    Text: {chunk['texto'][:100]}...")
                    entities = chunk.get('metadatos', {}).get('entities', {})
                    if entities:
                        print(f"    Entities: {entities}")
            
        except Exception as e:
            print(f"✗ Pipeline test failed: {e}")
    else:
        print(f"Sample PDF not found at {test_pdf}")
        print("Pipeline ready for use with: processor.process_pdf('path/to/document.pdf')")