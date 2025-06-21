#!/usr/bin/env python3
"""
Layout Detection for Legal Documents
====================================

Advanced layout analysis using LayoutParser + Detectron2 to identify:
- Document structure (headers, paragraphs, lists, tables)
- Hierarchical elements (articles, sections, numerals)
- Visual patterns specific to legal documents
"""

import cv2
import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional
import time
from pathlib import Path

try:
    import layoutparser as lp
    from detectron2.config import get_cfg
    from detectron2.engine import DefaultPredictor
except ImportError:
    layoutparser = None
    DefaultPredictor = None

from PIL import Image
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LayoutDetector:
    """
    Advanced layout detection optimized for legal documents.
    
    Detects and classifies:
    - Text blocks (paragraphs, headers, lists)
    - Tables and structured data
    - Legal hierarchy (articles, sections, numerals)
    - Document metadata (titles, footers, page numbers)
    """
    
    def __init__(
        self,
        model_name: str = "lp://PubLayNet/mask_rcnn_X_101_32x8d_FPN_3x/config",
        confidence_threshold: float = 0.5,
        device: str = "cpu"
    ):
        """
        Initialize layout detector with legal document optimizations.
        
        Args:
            model_name: LayoutParser model for document layout detection
            confidence_threshold: Minimum confidence for layout elements
            device: Computing device ('cpu' or 'cuda')
        """
        self.model_name = model_name
        self.confidence_threshold = confidence_threshold
        self.device = device
        
        # Initialize layout detection model
        self.model = self._initialize_layout_model()
        
        # Legal document patterns
        self.legal_patterns = {
            'article': re.compile(r'artículo\s+\d+', re.IGNORECASE),
            'section': re.compile(r'\d+\.\s*[A-ZÁÉÍÓÚÑa-záéíóúñ]', re.IGNORECASE),
            'numeral': re.compile(r'\d+\.\d+\.\d*', re.IGNORECASE),
            'inciso': re.compile(r'inciso\s+[a-z]\)', re.IGNORECASE),
            'amount': re.compile(r'S/\s*\d+(?:\.\d+)?', re.IGNORECASE),
            'percentage': re.compile(r'\d+(?:\.\d+)?\s*%', re.IGNORECASE),
            'date': re.compile(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', re.IGNORECASE),
            'reference': re.compile(r'(decreto|directiva|resolución)\s+n[°º]\s*\d+', re.IGNORECASE)
        }
        
        logger.info(f"Layout detector initialized with model: {model_name}")
    
    def _initialize_layout_model(self):
        """Initialize LayoutParser model for document analysis."""
        if layoutparser is None:
            logger.warning("LayoutParser not available - using fallback detection")
            return None
        
        try:
            # Load pre-trained model for document layout analysis
            model = lp.Detectron2LayoutModel(
                self.model_name,
                extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", self.confidence_threshold],
                label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"}
            )
            return model
        except Exception as e:
            logger.error(f"Failed to initialize layout model: {e}")
            logger.info("Falling back to basic layout detection")
            return None
    
    def detect_layout(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Detect layout elements in document image.
        
        Args:
            image: Document image as numpy array
            
        Returns:
            Dictionary with detected layout elements
        """
        try:
            if self.model is not None:
                return self._advanced_layout_detection(image)
            else:
                return self._basic_layout_detection(image)
        except Exception as e:
            logger.error(f"Layout detection error: {e}")
            return self._fallback_layout_detection(image)
    
    def _advanced_layout_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Advanced layout detection using LayoutParser."""
        start_time = time.time()
        
        # Convert numpy array to PIL Image
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Detect layout elements
        layout_result = self.model.detect(pil_image)
        
        # Process detected elements
        elements = []
        for block in layout_result:
            element = {
                'type': block.type,
                'confidence': getattr(block, 'score', 1.0),
                'bbox': [
                    block.block.x_1, block.block.y_1,
                    block.block.x_2, block.block.y_2
                ],
                'area': block.block.area,
                'coordinates': {
                    'x1': block.block.x_1,
                    'y1': block.block.y_1,
                    'x2': block.block.x_2,
                    'y2': block.block.y_2,
                    'width': block.block.width,
                    'height': block.block.height
                }
            }
            elements.append(element)
        
        # Sort elements by vertical position (top to bottom)
        elements.sort(key=lambda x: x['coordinates']['y1'])
        
        processing_time = time.time() - start_time
        
        return {
            'elements': elements,
            'element_count': len(elements),
            'processing_time': processing_time,
            'detection_method': 'advanced'
        }
    
    def _basic_layout_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Basic layout detection using OpenCV."""
        start_time = time.time()
        
        # Convert to grayscale
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Find text regions using contours
        # Apply threshold
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter and process contours
        elements = []
        height, width = gray.shape
        
        for i, contour in enumerate(contours):
            # Get bounding rectangle
            x, y, w, h = cv2.boundingRect(contour)
            
            # Filter small regions
            if w < 50 or h < 20:
                continue
            
            # Classify based on dimensions
            aspect_ratio = w / h
            area = w * h
            
            if aspect_ratio > 5 and h < height * 0.1:
                element_type = 'Title'
            elif aspect_ratio > 3:
                element_type = 'Text'
            elif aspect_ratio < 0.5:
                element_type = 'List'
            else:
                element_type = 'Text'
            
            element = {
                'type': element_type,
                'confidence': 0.8,  # Default confidence
                'bbox': [x, y, x + w, y + h],
                'area': area,
                'coordinates': {
                    'x1': x, 'y1': y,
                    'x2': x + w, 'y2': y + h,
                    'width': w, 'height': h
                }
            }
            elements.append(element)
        
        # Sort by vertical position
        elements.sort(key=lambda x: x['coordinates']['y1'])
        
        processing_time = time.time() - start_time
        
        return {
            'elements': elements,
            'element_count': len(elements),
            'processing_time': processing_time,
            'detection_method': 'basic'
        }
    
    def _fallback_layout_detection(self, image: np.ndarray) -> Dict[str, Any]:
        """Fallback layout detection when other methods fail."""
        height, width = image.shape[:2]
        
        # Create a single text block covering the entire image
        element = {
            'type': 'Text',
            'confidence': 0.5,
            'bbox': [0, 0, width, height],
            'area': width * height,
            'coordinates': {
                'x1': 0, 'y1': 0,
                'x2': width, 'y2': height,
                'width': width, 'height': height
            }
        }
        
        return {
            'elements': [element],
            'element_count': 1,
            'processing_time': 0.001,
            'detection_method': 'fallback'
        }
    
    def analyze_legal_structure(self, text_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze legal document structure from text blocks.
        
        Args:
            text_blocks: List of text blocks with OCR results
            
        Returns:
            Legal structure analysis
        """
        structure_analysis = {
            'articles': [],
            'sections': [],
            'numerals': [],
            'amounts': [],
            'percentages': [],
            'references': [],
            'hierarchy_depth': 0
        }
        
        for block in text_blocks:
            text = block.get('text', '')
            if not text:
                continue
            
            # Analyze each pattern
            for pattern_name, pattern in self.legal_patterns.items():
                matches = pattern.findall(text)
                if matches:
                    for match in matches:
                        item = {
                            'text': match,
                            'block_id': block.get('id', 0),
                            'bbox': block.get('bbox', []),
                            'confidence': block.get('confidence', 0.0)
                        }
                        
                        if pattern_name == 'article':
                            structure_analysis['articles'].append(item)
                        elif pattern_name == 'section':
                            structure_analysis['sections'].append(item)
                        elif pattern_name == 'numeral':
                            structure_analysis['numerals'].append(item)
                        elif pattern_name == 'amount':
                            structure_analysis['amounts'].append(item)
                        elif pattern_name == 'percentage':
                            structure_analysis['percentages'].append(item)
                        elif pattern_name == 'reference':
                            structure_analysis['references'].append(item)
        
        # Calculate hierarchy depth
        structure_analysis['hierarchy_depth'] = self._calculate_hierarchy_depth(structure_analysis)
        
        return structure_analysis
    
    def _calculate_hierarchy_depth(self, structure: Dict[str, Any]) -> int:
        """Calculate the hierarchical depth of the document."""
        depth = 0
        
        if structure['articles']:
            depth = max(depth, 1)
        if structure['sections']:
            depth = max(depth, 2)
        if structure['numerals']:
            # Check for nested numerals (e.g., 8.4.17)
            max_dots = max(item['text'].count('.') for item in structure['numerals'])
            depth = max(depth, 2 + max_dots)
        
        return depth
    
    def combine_layout_and_text(
        self, 
        layout_result: Dict[str, Any],
        ocr_blocks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Combine layout detection with OCR text extraction.
        
        Args:
            layout_result: Result from layout detection
            ocr_blocks: OCR text blocks
            
        Returns:
            Combined layout and text information
        """
        combined_blocks = []
        
        for layout_element in layout_result['elements']:
            layout_bbox = layout_element['bbox']
            
            # Find overlapping OCR blocks
            overlapping_texts = []
            for ocr_block in ocr_blocks:
                if self._blocks_overlap(layout_bbox, ocr_block.get('bbox', [])):
                    overlapping_texts.append(ocr_block['text'])
            
            # Combine texts
            combined_text = ' '.join(overlapping_texts).strip()
            
            combined_block = {
                'id': len(combined_blocks),
                'type': layout_element['type'],
                'text': combined_text,
                'bbox': layout_bbox,
                'coordinates': layout_element['coordinates'],
                'layout_confidence': layout_element['confidence'],
                'text_confidence': np.mean([
                    block.get('confidence', 0.0) for block in ocr_blocks
                    if self._blocks_overlap(layout_bbox, block.get('bbox', []))
                ]) if ocr_blocks else 0.0,
                'word_count': len(combined_text.split()),
                'area': layout_element['area']
            }
            
            combined_blocks.append(combined_block)
        
        return combined_blocks
    
    def _blocks_overlap(self, bbox1: List[float], bbox2: List[float]) -> bool:
        """Check if two bounding boxes overlap."""
        if len(bbox1) < 4 or len(bbox2) < 4:
            return False
        
        x1_1, y1_1, x2_1, y2_1 = bbox1[:4]
        x1_2, y1_2, x2_2, y2_2 = bbox2[:4]
        
        # Check for overlap
        return not (x2_1 < x1_2 or x2_2 < x1_1 or y2_1 < y1_2 or y2_2 < y1_1)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get layout detector statistics and configuration."""
        return {
            'model': self.model_name,
            'confidence_threshold': self.confidence_threshold,
            'device': self.device,
            'patterns': list(self.legal_patterns.keys()),
            'model_available': self.model is not None,
            'status': 'initialized'
        }


if __name__ == "__main__":
    # Test the layout detector
    detector = LayoutDetector()
    
    print("Layout detector initialized successfully")
    print(f"Detector stats: {detector.get_stats()}")
    
    # Test with a sample image if available
    test_image_path = "data/raw/sample_legal_doc.png"
    if Path(test_image_path).exists():
        image = cv2.imread(test_image_path)
        if image is not None:
            print("\nTesting layout detection...")
            result = detector.detect_layout(image)
            print(f"Detected {result['element_count']} layout elements")
            print(f"Detection method: {result['detection_method']}")
            print(f"Processing time: {result['processing_time']:.3f}s")
    else:
        print("Sample image not found - layout detector ready for use")