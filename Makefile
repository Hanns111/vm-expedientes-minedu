# Makefile para el Sistema de Búsqueda Híbrido MINEDU

.PHONY: install setup test clean run-demo format

install:
	pip install -r requirements.txt
	python -m spacy download es_core_news_sm

setup:
	python setup_project.py

test:
	pytest tests/ -v

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete

run-demo:
	python demo.py "¿Cuál es el monto máximo para viáticos?"

format:
	black src/ tests/
	flake8 src/ tests/

generate-vectorstores:
	python src/data_pipeline/generate_vectorstores.py

full-setup: install setup generate-vectorstores
