#!/usr/bin/env python3
"""
Model Manager for MINEDU Backend
Handles preloading, caching, and optimization of ML models
"""

import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading
from concurrent.futures import ThreadPoolExecutor
import pickle
import gc
import psutil
import os

# ML/AI imports
try:
    import sentence_transformers
    from sentence_transformers import SentenceTransformer
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

logger = logging.getLogger('minedu.models')

class ModelManager:
    """Centralized model management with preloading and optimization"""
    
    def __init__(self, 
                 models_cache_dir: str = "models/cache",
                 max_memory_usage: float = 0.7,  # 70% of available RAM
                 enable_model_sharing: bool = True):
        
        self.models_cache_dir = Path(models_cache_dir)
        self.models_cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.max_memory_usage = max_memory_usage
        self.enable_model_sharing = enable_model_sharing
        
        # Model storage
        self._models: Dict[str, Any] = {}
        self._model_metadata: Dict[str, Dict] = {}
        self._loading_locks: Dict[str, threading.Lock] = {}
        
        # Performance tracking
        self._load_times: Dict[str, float] = {}
        self._usage_counts: Dict[str, int] = {}
        
        # Thread pool for async loading
        self._executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="model_loader")
        
        logger.info(f"Model manager initialized - Cache: {self.models_cache_dir}")
    
    def _get_memory_usage(self) -> Dict[str, float]:
        """Get current memory usage statistics"""
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': memory_percent,
            'available_mb': psutil.virtual_memory().available / 1024 / 1024
        }
    
    def _check_memory_limit(self) -> bool:
        """Check if we can load more models without exceeding memory limit"""
        memory_stats = self._get_memory_usage()
        return memory_stats['percent'] < (self.max_memory_usage * 100)
    
    async def preload_sentence_transformer(self, 
                                         model_name: str = "paraphrase-multilingual-MiniLM-L12-v2",
                                         device: str = "auto") -> bool:
        """Preload sentence transformer model"""
        if not TRANSFORMERS_AVAILABLE:
            logger.warning("Sentence transformers not available")
            return False
        
        model_key = f"sentence_transformer_{model_name}"
        
        if model_key in self._models:
            logger.info(f"Model {model_name} already loaded")
            return True
        
        if not self._check_memory_limit():
            logger.warning(f"Memory limit reached, cannot load {model_name}")
            return False
        
        try:
            start_time = time.time()
            logger.info(f"🔄 Preloading sentence transformer: {model_name}")
            
            # Determine device
            if device == "auto":
                if TORCH_AVAILABLE and torch.cuda.is_available():
                    device = "cuda"
                else:
                    device = "cpu"
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                self._executor,
                self._load_sentence_transformer,
                model_name,
                device
            )
            
            if model:
                self._models[model_key] = model
                load_time = time.time() - start_time
                self._load_times[model_key] = load_time
                self._usage_counts[model_key] = 0
                
                # Store metadata
                self._model_metadata[model_key] = {
                    'type': 'sentence_transformer',
                    'name': model_name,
                    'device': device,
                    'load_time': load_time,
                    'memory_footprint': self._estimate_model_memory(model)
                }
                
                logger.info(f"✅ Loaded {model_name} in {load_time:.2f}s on {device}")
                return True
            
        except Exception as e:
            logger.error(f"❌ Failed to load sentence transformer {model_name}: {e}")
            return False
        
        return False
    
    def _load_sentence_transformer(self, model_name: str, device: str) -> Optional[SentenceTransformer]:
        """Synchronous model loading (runs in thread pool)"""
        try:
            # Check for cached model
            cache_path = self.models_cache_dir / f"{model_name.replace('/', '_')}"
            
            if cache_path.exists():
                logger.info(f"Loading cached model from {cache_path}")
                model = SentenceTransformer(str(cache_path))
            else:
                logger.info(f"Downloading model {model_name}")
                model = SentenceTransformer(model_name)
                # Cache for future use
                model.save(str(cache_path))
                logger.info(f"Model cached to {cache_path}")
            
            # Move to appropriate device
            if device == "cuda" and TORCH_AVAILABLE:
                model = model.to(torch.device("cuda"))
            
            # Warmup with dummy input
            dummy_text = ["This is a warmup sentence for the model."]
            _ = model.encode(dummy_text, show_progress_bar=False)
            
            return model
            
        except Exception as e:
            logger.error(f"Failed to load sentence transformer: {e}")
            return None
    
    def _estimate_model_memory(self, model) -> float:
        """Estimate model memory usage in MB"""
        try:
            if hasattr(model, 'get_memory_footprint'):
                return model.get_memory_footprint() / 1024 / 1024
            
            # Fallback estimation
            if TORCH_AVAILABLE and hasattr(model, 'modules'):
                total_params = sum(p.numel() for p in model.parameters() if p.requires_grad)
                # Rough estimate: 4 bytes per parameter
                return (total_params * 4) / 1024 / 1024
            
            return 0.0
        except:
            return 0.0
    
    async def preload_vectorstores(self, vectorstore_paths: Dict[str, str]) -> Dict[str, bool]:
        """Preload vectorstore files into memory"""
        results = {}
        
        for store_type, path in vectorstore_paths.items():
            try:
                start_time = time.time()
                logger.info(f"🔄 Preloading vectorstore: {store_type}")
                
                path_obj = Path(path)
                if not path_obj.exists():
                    logger.warning(f"Vectorstore not found: {path}")
                    results[store_type] = False
                    continue
                
                # Load vectorstore in thread pool
                loop = asyncio.get_event_loop()
                vectorstore = await loop.run_in_executor(
                    self._executor,
                    self._load_vectorstore,
                    path
                )
                
                if vectorstore:
                    store_key = f"vectorstore_{store_type}"
                    self._models[store_key] = vectorstore
                    load_time = time.time() - start_time
                    self._load_times[store_key] = load_time
                    
                    logger.info(f"✅ Loaded {store_type} vectorstore in {load_time:.2f}s")
                    results[store_type] = True
                else:
                    results[store_type] = False
                    
            except Exception as e:
                logger.error(f"❌ Failed to load vectorstore {store_type}: {e}")
                results[store_type] = False
        
        return results
    
    def _load_vectorstore(self, path: str):
        """Load vectorstore from pickle file"""
        try:
            with open(path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load vectorstore from {path}: {e}")
            return None
    
    def get_model(self, model_key: str) -> Optional[Any]:
        """Get a preloaded model"""
        if model_key in self._models:
            self._usage_counts[model_key] = self._usage_counts.get(model_key, 0) + 1
            return self._models[model_key]
        
        logger.warning(f"Model not found: {model_key}")
        return None
    
    def get_sentence_transformer(self, model_name: str = "paraphrase-multilingual-MiniLM-L12-v2") -> Optional[SentenceTransformer]:
        """Get preloaded sentence transformer"""
        model_key = f"sentence_transformer_{model_name}"
        return self.get_model(model_key)
    
    def get_vectorstore(self, store_type: str) -> Optional[Any]:
        """Get preloaded vectorstore"""
        store_key = f"vectorstore_{store_type}"
        return self.get_model(store_key)
    
    async def warmup_models(self) -> Dict[str, Any]:
        """Warmup all loaded models with dummy data"""
        warmup_results = {}
        
        for model_key, model in self._models.items():
            try:
                start_time = time.time()
                
                if model_key.startswith("sentence_transformer"):
                    # Warmup sentence transformer
                    dummy_texts = [
                        "Esta es una oración de prueba para calentar el modelo.",
                        "¿Cuál es el monto máximo para viáticos?",
                        "Directiva ministerial de educación"
                    ]
                    _ = model.encode(dummy_texts, show_progress_bar=False)
                
                warmup_time = time.time() - start_time
                warmup_results[model_key] = {
                    'success': True,
                    'warmup_time': warmup_time
                }
                
                logger.info(f"🔥 Warmed up {model_key} in {warmup_time:.3f}s")
                
            except Exception as e:
                logger.error(f"Failed to warmup {model_key}: {e}")
                warmup_results[model_key] = {
                    'success': False,
                    'error': str(e)
                }
        
        return warmup_results
    
    def get_model_stats(self) -> Dict[str, Any]:
        """Get comprehensive model statistics"""
        memory_stats = self._get_memory_usage()
        
        model_info = {}
        for model_key, model in self._models.items():
            metadata = self._model_metadata.get(model_key, {})
            model_info[model_key] = {
                'loaded': True,
                'load_time': self._load_times.get(model_key, 0),
                'usage_count': self._usage_counts.get(model_key, 0),
                'memory_footprint_mb': metadata.get('memory_footprint', 0),
                'type': metadata.get('type', 'unknown'),
                'device': metadata.get('device', 'unknown')
            }
        
        return {
            'total_models': len(self._models),
            'memory_stats': memory_stats,
            'model_details': model_info,
            'cache_directory': str(self.models_cache_dir),
            'memory_limit_percent': self.max_memory_usage * 100
        }
    
    def cleanup_unused_models(self, min_usage_count: int = 0) -> List[str]:
        """Clean up models with low usage"""
        cleaned_models = []
        
        for model_key in list(self._models.keys()):
            usage_count = self._usage_counts.get(model_key, 0)
            if usage_count <= min_usage_count:
                del self._models[model_key]
                if model_key in self._model_metadata:
                    del self._model_metadata[model_key]
                if model_key in self._load_times:
                    del self._load_times[model_key]
                if model_key in self._usage_counts:
                    del self._usage_counts[model_key]
                
                cleaned_models.append(model_key)
                logger.info(f"🗑️ Cleaned up unused model: {model_key}")
        
        # Force garbage collection
        gc.collect()
        
        return cleaned_models
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of model manager"""
        try:
            memory_stats = self._get_memory_usage()
            
            # Test model access
            model_health = {}
            for model_key in self._models.keys():
                try:
                    model = self.get_model(model_key)
                    model_health[model_key] = model is not None
                except Exception as e:
                    model_health[model_key] = False
                    logger.error(f"Model health check failed for {model_key}: {e}")
            
            return {
                'status': 'healthy',
                'models_loaded': len(self._models),
                'memory_usage_mb': memory_stats['rss_mb'],
                'memory_usage_percent': memory_stats['percent'],
                'within_memory_limit': memory_stats['percent'] < (self.max_memory_usage * 100),
                'model_health': model_health,
                'cache_directory_exists': self.models_cache_dir.exists(),
                'total_load_time': sum(self._load_times.values())
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def close(self):
        """Clean up resources"""
        logger.info("🔄 Shutting down model manager...")
        self._executor.shutdown(wait=True)
        
        # Clear models from memory
        self._models.clear()
        self._model_metadata.clear()
        gc.collect()
        
        logger.info("✅ Model manager shutdown complete")

# Global model manager instance
_model_manager = None

def get_model_manager() -> ModelManager:
    """Get global model manager instance"""
    global _model_manager
    if _model_manager is None:
        _model_manager = ModelManager()
    return _model_manager

async def preload_all_models() -> Dict[str, Any]:
    """Preload all required models for MINEDU"""
    manager = get_model_manager()
    results = {}
    
    # 1. Preload sentence transformer
    st_result = await manager.preload_sentence_transformer(
        "paraphrase-multilingual-MiniLM-L12-v2"
    )
    results['sentence_transformer'] = st_result
    
    # 2. Preload vectorstores
    vectorstore_paths = {
        'bm25': 'data/vectorstores/bm25.pkl',
        'tfidf': 'data/vectorstores/tfidf.pkl',
        'transformers': 'data/vectorstores/transformers.pkl'
    }
    
    vs_results = await manager.preload_vectorstores(vectorstore_paths)
    results['vectorstores'] = vs_results
    
    # 3. Warmup models
    warmup_results = await manager.warmup_models()
    results['warmup'] = warmup_results
    
    return results