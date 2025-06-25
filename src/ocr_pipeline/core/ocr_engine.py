#!/usr/bin/env python3
"""
OCR Engine optimized for Spanish Legal Documents
==============================================

PaddleOCR-based engine with Spanish optimization for legal document processing.
Handles multiple orientations, complex layouts, and poor quality scans.
"""

import logging
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import time

try:
    import cv2
except ImportError:
    cv2 = None

try:
    import numpy as np
except ImportError:
    np = None

try:
    from paddleocr import PaddleOCR
except ImportError:
    PaddleOCR = None

try:
    from PIL import Image, ImageEnhance
except ImportError:
    Image = None
    ImageEnhance = None

try:
    import pdf2image
except ImportError:
    pdf2image = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCREngine:
    """
    Advanced OCR engine optimized for Spanish legal documents.
    
    Features:
    - Multi-language support (Spanish + English)
    - Image preprocessing for enhanced accuracy
    - Confidence scoring and filtering
    - Batch processing capabilities
    - Legal document optimizations
    """
    
    def __init__(
        self,
        languages: List[str] = ['es', 'en'],
        use_gpu: bool = False,
        confidence_threshold: float = 0.5,
        enable_mkldnn: bool = True
    ):
        """
        Initialize OCR engine with Spanish legal document optimizations.
        
        Args:
            languages: Languages to recognize (default: Spanish + English)
            use_gpu: Whether to use GPU acceleration
            confidence_threshold: Minimum confidence for text recognition
            enable_mkldnn: Enable Intel MKL-DNN optimization
        """
        self.languages = languages
        self.use_gpu = use_gpu
        self.confidence_threshold = confidence_threshold
        self.enable_mkldnn = enable_mkldnn
        
        # Check dependencies
        missing_deps = []
        if cv2 is None:
            missing_deps.append("opencv-python")
        if np is None:
            missing_deps.append("numpy")
        if PaddleOCR is None:
            missing_deps.append("paddleocr")
        if Image is None:
            missing_deps.append("pillow")
        if pdf2image is None:
            missing_deps.append("pdf2image")
        
        if missing_deps:
            logger.warning(f"Missing dependencies: {missing_deps}")
            logger.warning("Install with: pip install " + " ".join(missing_deps))
            self.ocr = None
        else:
            # Initialize PaddleOCR
            self.ocr = self._initialize_paddle_ocr()
        
        # Legal document specific settings
        self.legal_keywords = [
            'artículo', 'artículo', 'inciso', 'numeral', 'párrafo',
            'directiva', 'decreto', 'resolución', 'ordenanza',
            'ministerio', 'ministro', 'servidor', 'funcionario',
            'viático', 'viáticos', 'monto', 'suma', 'cantidad'
        ]
        
        logger.info(f"OCR Engine initialized with languages: {languages}")
    
    def _initialize_paddle_ocr(self) -> PaddleOCR:
        """Initialize PaddleOCR with optimized settings for legal documents."""
        try:
            ocr = PaddleOCR(
                use_angle_cls=True,  # Detect text rotation
                lang='es',           # Primary language: Spanish
                use_gpu=self.use_gpu,
                enable_mkldnn=self.enable_mkldnn,
                show_log=False,
                # Legal document optimizations
                det_db_thresh=0.3,      # Lower threshold for faded text
                det_db_box_thresh=0.5,  # Box detection threshold
                det_db_unclip_ratio=2.0 # Text region expansion
            )
            return ocr
        except Exception as e:
            logger.error(f"Failed to initialize PaddleOCR: {e}")
            raise
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for optimal OCR performance on legal documents.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Preprocessed image
        """
        # Convert to PIL for easier manipulation
        if isinstance(image, np.ndarray):
            pil_image = Image.fromarray(image)
        else:
            pil_image = image
        
        # Enhance contrast for faded legal documents
        enhancer = ImageEnhance.Contrast(pil_image)
        pil_image = enhancer.enhance(1.2)
        
        # Enhance sharpness for scanned documents
        enhancer = ImageEnhance.Sharpness(pil_image)
        pil_image = enhancer.enhance(1.1)
        
        # Convert back to numpy
        image = np.array(pil_image)
        
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
        else:
            gray = image
        
        # Apply adaptive threshold for better text separation
        adaptive_thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Noise reduction
        denoised = cv2.medianBlur(adaptive_thresh, 3)
        
        return denoised
    
    def extract_text_from_pdf(
        self, 
        pdf_path: str, 
        dpi: int = 300,
        preprocess: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Extract text from PDF by converting to images first.
        
        Args:
            pdf_path: Path to PDF file
            dpi: Resolution for PDF to image conversion
            preprocess: Whether to preprocess images
            
        Returns:
            List of page results with text and metadata
        """
        logger.info(f"Processing PDF: {pdf_path}")
        start_time = time.time()
        
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(
                pdf_path, 
                dpi=dpi,
                fmt='RGB'
            )
            
            results = []
            for page_num, image in enumerate(images, 1):
                logger.info(f"Processing page {page_num}/{len(images)}")
                
                # Convert PIL to numpy
                image_np = np.array(image)
                
                # Preprocess if enabled
                if preprocess:
                    image_np = self.preprocess_image(image_np)
                
                # Extract text from page
                page_result = self.extract_text_from_image(image_np)
                page_result['page_number'] = page_num
                page_result['total_pages'] = len(images)
                
                results.append(page_result)
            
            processing_time = time.time() - start_time
            logger.info(f"PDF processing completed in {processing_time:.2f}s")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {e}")
            raise
    
    def extract_text_from_image(self, image: np.ndarray) -> Dict[str, Any]:
        """
        Extract text from a single image with detailed results.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Run OCR
            ocr_results = self.ocr.ocr(image, cls=True)
            
            if not ocr_results or not ocr_results[0]:
                return {
                    'text': '',
                    'blocks': [],
                    'confidence': 0.0,
                    'word_count': 0,
                    'has_legal_content': False
                }
            
            # Process OCR results
            processed_blocks = []
            full_text_parts = []
            confidence_scores = []
            
            for line in ocr_results[0]:
                if len(line) >= 2:
                    bbox, (text, confidence) = line
                    
                    # Filter by confidence threshold
                    if confidence >= self.confidence_threshold:
                        block = {
                            'text': text,
                            'confidence': confidence,
                            'bbox': bbox,
                            'coordinates': {
                                'top_left': bbox[0],
                                'top_right': bbox[1], 
                                'bottom_right': bbox[2],
                                'bottom_left': bbox[3]
                            }
                        }
                        
                        processed_blocks.append(block)
                        full_text_parts.append(text)
                        confidence_scores.append(confidence)
            
            # Combine text
            full_text = ' '.join(full_text_parts)
            avg_confidence = np.mean(confidence_scores) if confidence_scores else 0.0
            
            # Check for legal content
            has_legal_content = self._contains_legal_keywords(full_text)
            
            return {
                'text': full_text,
                'blocks': processed_blocks,
                'confidence': avg_confidence,
                'word_count': len(full_text.split()),
                'has_legal_content': has_legal_content,
                'block_count': len(processed_blocks)
            }
            
        except Exception as e:
            logger.error(f"Error in OCR extraction: {e}")
            return {
                'text': '',
                'blocks': [],
                'confidence': 0.0,
                'word_count': 0,
                'has_legal_content': False,
                'error': str(e)
            }
    
    def _contains_legal_keywords(self, text: str) -> bool:
        """Check if text contains legal keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.legal_keywords)
    
    def batch_process_images(
        self, 
        image_paths: List[str],
        output_dir: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Process multiple images in batch for better performance.
        
        Args:
            image_paths: List of image file paths
            output_dir: Optional directory to save results
            
        Returns:
            List of processing results
        """
        logger.info(f"Batch processing {len(image_paths)} images")
        
        results = []
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"Processing image {i}/{len(image_paths)}: {image_path}")
            
            try:
                # Load image
                image = cv2.imread(image_path)
                if image is None:
                    logger.warning(f"Could not load image: {image_path}")
                    continue
                
                # Extract text
                result = self.extract_text_from_image(image)
                result['source_file'] = image_path
                result['processing_order'] = i
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error processing {image_path}: {e}")
                continue
        
        return results
    
    def get_stats(self) -> Dict[str, Any]:
        """Get OCR engine statistics and configuration."""
        return {
            'engine': 'PaddleOCR',
            'languages': self.languages,
            'use_gpu': self.use_gpu,
            'confidence_threshold': self.confidence_threshold,
            'legal_keywords': len(self.legal_keywords),
            'status': 'initialized'
        }


if __name__ == "__main__":
    # Test the OCR engine
    ocr_engine = OCREngine()
    
    # Test with a sample image if available
    test_pdf = "data/raw/directiva_de_viaticos_011_2020_imagen.pdf"
    if Path(test_pdf).exists():
        print("Testing OCR engine with sample PDF...")
        results = ocr_engine.extract_text_from_pdf(test_pdf)
        
        for i, result in enumerate(results[:2]):  # Show first 2 pages
            print(f"\nPage {i+1}:")
            print(f"Text preview: {result['text'][:200]}...")
            print(f"Confidence: {result['confidence']:.3f}")
            print(f"Word count: {result['word_count']}")
            print(f"Has legal content: {result['has_legal_content']}")
    else:
        print("Sample PDF not found - OCR engine initialized successfully")
        print(f"Engine stats: {ocr_engine.get_stats()}")