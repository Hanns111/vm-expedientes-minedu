# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a secure hybrid RAG (Retrieval-Augmented Generation) system for Peru's Ministry of Education (MINEDU) that searches regulatory documents. It implements multiple search methods (TF-IDF, BM25, Sentence Transformers) with government-grade security features for handling administrative documents.

## Development Commands

### Setup and Installation
```bash
# Install dependencies and setup project
make install
make setup

# Development setup with pre-commit hooks
make dev-setup

# Full setup including vectorstore generation
make full-setup
```

### Code Quality (Ruff + MyPy)
```bash
# Format and fix code automatically
make format

# Check format without changes
make format-check

# Run linting
make lint

# Fix linting issues automatically
make lint-fix

# Type checking
make type-check

# Security analysis
make security

# All quality checks together
make all
```

### Testing
```bash
# Run tests with coverage
make test

# Fast tests without coverage
make test-fast

# Integration tests only
make test-integration

# Unit tests only
make test-unit

# Single test file
pytest tests/test_specific.py -v
```

### Running the System
```bash
# Secure demo (recommended for production)
make run-demo-secure
python demo_secure.py "¿Cuál es el monto máximo para viáticos?"

# Basic demo for development
make run-demo

# Performance demo with Streamlit UI
make run-performance

# Generate vectorstores
make generate-vectorstores
```

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up --build

# Production deployment with nginx and redis
docker-compose --profile production up -d

# Development deployment
docker-compose up backend
```

## Architecture Overview

### Core Pipeline Architecture
The system follows an abstract base pipeline pattern defined in `src/core/base_pipeline.py`:
- **BasePipeline**: Abstract class defining common RAG pipeline interface
- All pipelines implement: `search()`, `generate()`, `evaluate()` methods
- Built-in metrics collection (latency, tokens, memory usage)
- Configurable through Pydantic models in `src/config/rag_config.py`

### Hybrid Search System (`src/core/hybrid/hybrid_search.py`)
Multi-retrieval fusion system combining:
1. **BM25Retriever**: Fast lexical search with Spanish optimization
2. **TFIDFRetriever**: Term frequency-based vectorial search  
3. **TransformerRetriever**: Semantic search using multilingual-e5-large
4. **HybridSearch**: Configurable fusion strategies (weighted, RRF)
   - Amount-aware boosting for financial queries
   - Query pattern recognition for domain-specific optimization

### Security Architecture (`src/core/security/`)
Government-grade security with layered protection:
- **InputValidator**: Query sanitization and validation
- **RateLimiter**: Multi-level rate limiting (30/min, 500/hour, 2000/day)
- **PrivacyProtector**: PII detection and anonymization
- **LLMSecurityGuard**: Prompt injection protection
- **SecurityMonitor**: Comprehensive audit logging
- **FileValidator**: Safe file operations with path validation
- **SafePickle**: Secure serialization/deserialization

### Configuration System
Type-safe configuration using Pydantic models:
- **RAGConfig**: Main pipeline configuration
- **BM25Config, DenseRetrievalConfig, HybridFusionConfig**: Component-specific configs
- **SecurityConfig**: Centralized security settings
- Supports both Python objects and YAML files

## Key File Patterns

### Vectorstore Generation
- `src/ai/generate_vectorstore_*.py`: Scripts to create search indexes
- `data/processed/`: Generated vectorstores (bm25, tfidf, transformers)
- `src/data_pipeline/generate_vectorstores.py`: Unified vectorstore generation

### Text Processing Pipeline
- `src/text_processor/`: PDF extraction, text cleaning, chunking
- `src/chunker.py`: Text segmentation for RAG processing
- `data/raw/`: Source documents (PDFs)
- `data/processed/`: Cleaned text and chunks

### Demo and Testing
- `demo_secure.py`: Production-ready demo with full security
- `demo.py`: Basic demo for development
- `tests/`: Unit tests for all components
- `paper_cientifico/`: Scientific evaluation and benchmarking

## Development Guidelines

### Code Quality Standards
- **Formatting**: Use Ruff for formatting and linting (`make format`)
- **Type Safety**: All functions must have type hints, checked with MyPy
- **Testing**: Maintain >80% test coverage, use pytest with proper markers
- **Security**: All code must pass security audit (`make security`)
- **Pre-commit**: Install hooks with `make dev-setup` for automatic quality checks

### Architecture Patterns
- **Pipeline Pattern**: Extend `BasePipeline` for new RAG implementations
- **Retriever Pattern**: Implement common interface for search components
- **Configuration**: Use Pydantic models, avoid hardcoded values
- **Security Wrapper**: Always use security-validated wrappers in production
- **Dependency Injection**: Pass configurations rather than accessing globals

### Adding New Components
1. **New Retriever**: Extend base retriever, add to `src/core/retrieval/`
2. **New Pipeline**: Extend `BasePipeline`, implement required methods
3. **Configuration**: Add Pydantic model to `src/config/rag_config.py`
4. **Security**: Integrate with security framework components
5. **Testing**: Add comprehensive tests with proper coverage

## Scientific Research Context

This system is designed for SIGIR/CLEF 2025-2026 research paper submission. Key research components:
- **paper_cientifico/**: Complete experimental framework
- **data/evaluation/**: Benchmarking datasets and ground truth
- **Golden dataset**: 20 validated queries for reproducible evaluation
- **Metrics**: token_overlap, exact_match, length_ratio, query_time

## Domain-Specific Features

### MINEDU Document Processing
- Specialized for Peruvian educational administrative documents
- Spanish language processing with `es_core_news_sm` spaCy model  
- Entity extraction for amounts, dates, procedures
- Amount-aware query boosting for financial regulations

### Government Compliance
- ISO27001 and NIST Cybersecurity Framework compliance
- PII protection with automatic anonymization
- Comprehensive audit logging for government accountability
- Secure file handling for classified documents

## Common Workflows

### Adding New Search Method
1. Create retriever class in `src/core/retrieval/` extending base interface
2. Add Pydantic configuration model to `src/config/rag_config.py`
3. Integrate into `HybridSearch.search()` method with fusion strategy
4. Add comprehensive tests in `tests/test_retrieval.py`
5. Run security audit and update benchmarking data

### Debugging Search Issues
1. Use `demo_secure.py` with debug logging enabled
2. Check vectorstore integrity in `data/processed/`
3. Analyze metrics from `BasePipeline` built-in profiling
4. Compare results across different retrievers individually
5. Validate input preprocessing and query normalization

### Performance Optimization
1. Profile with `src/core/performance/` utilities
2. Check cache hit rates and async pipeline performance
3. Optimize vectorstore loading and search algorithms
4. Benchmark against golden dataset in `paper_cientifico/dataset/`
5. Monitor memory usage and token consumption metrics

### Security Updates
1. Modify security components in `src/core/security/`
2. Run comprehensive audit: `make security`
3. Test with edge cases and malicious inputs
4. Update rate limiting and PII protection rules
5. Verify compliance with government security standards

### Deployment Troubleshooting
1. Check Docker health endpoints and container logs
2. Verify vectorstore availability and permissions
3. Test API endpoints with realistic government data
4. Monitor rate limiting and security audit logs
5. Validate production vs development configuration differences