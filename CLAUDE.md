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

# Full setup including vectorstore generation
make full-setup
```

### Testing and Linting
```bash
# Run tests with coverage
make test
pytest tests/ -v --cov=src --cov-report=html

# Code formatting and linting
make format  # black + isort
make lint    # flake8 + mypy

# Complete quality check
make all     # security-audit + format + lint + test
```

### Security Operations
```bash
# Comprehensive security audit
make security-audit
python security_audit.py

# Security monitoring and fixes
make security-fix
make security-monitor

# Vulnerability scanning
make security-scan  # bandit + safety + pip-audit
```

### Running the System
```bash
# Secure demo (recommended)
make run-demo-secure
python demo_secure.py "¿Cuál es el monto máximo para viáticos?"

# Basic demo
make run-demo
python demo.py

# Generate vectorstores
make generate-vectorstores
python src/data_pipeline/generate_vectorstores.py
```

## Architecture Overview

### Core Components
- **src/core/**: Base pipeline architecture and security framework
  - `base_pipeline.py`: Abstract RAG pipeline with metrics and evaluation
  - `security/`: Comprehensive security layer (input validation, rate limiting, PII protection)
  - `retrieval/`: Multi-modal search implementations (BM25, TF-IDF, Transformers)
  - `hybrid/`: Fusion strategies for combining search results

### Search System Design
The system uses a hybrid approach combining three retrieval methods:
1. **BM25Retriever**: Fast lexical search optimized for Spanish
2. **TFIDFRetriever**: Term frequency-based vectorial search  
3. **TransformerRetriever**: Semantic search using multilingual-e5-large
4. **HybridSearch**: Fusion system with configurable strategies (weighted, RRF)

### Security Architecture
Government-grade security with multiple protection layers:
- Input sanitization and validation (`InputValidator`)
- Rate limiting (30/min, 500/hour, 2000/day)
- PII protection and anonymization (`PrivacyProtector`)
- Prompt injection protection (`LLMSecurityGuard`)
- Comprehensive audit logging (`SecurityMonitor`)

### Configuration Management
- **config/settings.py**: Base project paths and environment variables
- **src/config/rag_config.py**: Pydantic-based RAG pipeline configuration
- **config/minedu_config*.yaml**: YAML configuration files for different environments

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

### Security First
- All new code must pass security audit (`make security-audit`)
- Use `SecureHybridSearch` wrapper for production code
- Never bypass input validation or rate limiting
- All file operations must use validated paths within project boundaries

### Testing Requirements  
- All new retrieval components must implement abstract base classes
- Add comprehensive tests in `tests/` directory
- Maintain test coverage above current levels
- Run full test suite before committing (`make all`)

### Configuration
- Use Pydantic models for type-safe configuration
- Support both Python and YAML configuration formats
- Environment-specific configs in `config/` directory
- Never hardcode paths - use `config/settings.py` constants

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
1. Implement retriever in `src/core/retrieval/`
2. Add configuration to `RAGConfig` 
3. Integrate into `HybridSearch` fusion strategies
4. Add tests and security validation
5. Update benchmarking in `paper_cientifico/`

### Modifying Security Rules
1. Update relevant security component in `src/core/security/`
2. Test with `make security-audit`
3. Verify compliance with government standards
4. Update documentation and audit logs

### Performance Optimization
1. Profile with existing metrics in `src/core/base_pipeline.py`
2. Optimize vectorstore generation and search algorithms  
3. Benchmark against golden dataset
4. Maintain security compliance during optimization