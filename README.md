# 🔒 vm-expedientes-minedu: Sistema RAG Seguro para MINEDU Perú

> **Portal de Bienvenida e Índice Central del Proyecto**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![Security](https://img.shields.io/badge/Security-100%25-green.svg)](https://github.com/Hanns111/vm-expedientes-minedu)
[![Version](https://img.shields.io/badge/Version-v1.3.0--devops--complete-orange.svg)](https://github.com/Hanns111/vm-expedientes-minedu/releases)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI/CD](https://img.shields.io/badge/CI/CD-Automated-blue.svg)](https://github.com/Hanns111/vm-expedientes-minedu/actions)

## 🎯 Descripción del Proyecto

**vm-expedientes-minedu** es un sistema de búsqueda semántica e híbrida avanzado diseñado específicamente para el Ministerio de Educación del Perú. El sistema implementa múltiples algoritmos de recuperación de información (TF-IDF, BM25, Sentence Transformers) con medidas de seguridad gubernamental completas.

### ✨ Características Principales

- **🔍 Búsqueda Híbrida**: Combinación inteligente de TF-IDF, BM25 y Sentence Transformers
- **🛡️ Seguridad Gubernamental**: Implementación completa de medidas de seguridad (100%)
- **📊 Validación Científica**: Metodología rigurosa para paper SIGIR/CLEF 2025-2026
- **🏛️ Cumplimiento Normativo**: ISO27001, NIST Cybersecurity, Estándares MINEDU
- **🚀 DevOps Profesional**: CI/CD automatizado, gestión de secretos, documentación consolidada

## 🚀 Instalación

### Prerrequisitos
```bash
# Python 3.11+
python --version

# Entorno virtual (recomendado)
conda create -n minedu-env python=3.11
conda activate minedu-env
```

### Instalación Completa
```bash
# Clonar repositorio
git clone https://github.com/Hanns111/vm-expedientes-minedu.git
cd vm-expedientes-minedu

# Instalar dependencias consolidadas
pip install -r requirements.txt

# Configurar variables de entorno (opcional)
cp config/settings_secure.example.py config/settings_secure.py
# Editar config/settings_secure.py con tus valores
```

## 🔧 Cómo Usar

### Demo Principal (Recomendado)
```bash
# Demo interactivo con todas las medidas de seguridad
python demo.py

# Demo con consulta específica
python demo.py "tu consulta aquí"

# Demo en modo seguro (validación completa)
python demo.py --secure "consulta segura"
```

### Generación de Vectorstore
```bash
# Generar vectorstore completo para búsquedas
python src/ai/generate_vectorstore_full_v2.py
```

### Auditoría de Seguridad
```bash
# Verificación completa del sistema
python verificacion_final_seguridad.py

# Auditoría de seguridad detallada
python security_audit.py
```

### Testing y Validación
```bash
# Ejecutar tests unitarios
pytest tests/

# Ejecutar tests con cobertura
pytest tests/ --cov=src --cov-report=html
```

## 📚 Índice de Documentación

### 🏗️ **Arquitectura del Sistema**
- **[Arquitectura General](docs/architecture/README.md)** - Diseño y componentes del sistema
- **[Arquitectura de Seguridad](docs/security/README.md)** - Implementación de seguridad gubernamental
- **[Flujos de Datos](docs/architecture/data-flows.md)** - Flujos de procesamiento
- **[Decisiones de Diseño](docs/architecture/design-decisions.md)** - Justificación de decisiones técnicas

### 🔬 **Investigación Científica**
- **[Paper Principal](paper_cientifico/paper_final/paper_sistema_hibrido.md)** - Documentación para SIGIR/CLEF 2025-2026
- **[Metodología](paper_cientifico/methodology.md)** - Metodología de investigación
- **[Resultados Experimentales](paper_cientifico/results/)** - Resultados y análisis
- **[Reproducibilidad](paper_cientifico/reproducibility.md)** - Cómo replicar experimentos
- **[Dataset Dorado](paper_cientifico/dataset/)** - Dataset de validación (20 preguntas)

### 🛡️ **Seguridad y Cumplimiento**
- **[Guía de Seguridad](docs/security/README.md)** - Documentación completa de seguridad
- **[Configuración Segura](docs/security/configuration.md)** - Configuración de producción
- **[Auditoría](docs/security/audit.md)** - Procedimientos de auditoría
- **[Cumplimiento Gubernamental](docs/security/compliance.md)** - Estándares y normativas

### 🚀 **Despliegue y Operaciones**
- **[Guía de Despliegue](docs/deployment/README.md)** - Instalación en producción
- **[Configuración de Producción](docs/deployment/production.md)** - Configuración para MINEDU
- **[Monitoreo](docs/deployment/monitoring.md)** - Monitoreo y alertas
- **[Troubleshooting](docs/deployment/troubleshooting.md)** - Solución de problemas

### 📋 **Guías de Usuario**
- **[Guía de Usuario](docs/user-guides/README.md)** - Cómo usar el sistema
- **[Tutoriales](docs/user-guides/tutorials.md)** - Tutoriales paso a paso
- **[FAQ](docs/user-guides/faq.md)** - Preguntas frecuentes
- **[Casos de Uso](docs/user-guides/use-cases.md)** - Ejemplos prácticos

### 📊 **Resultados y Evaluación**
- **[Métricas de Evaluación](docs/results/metrics.md)** - Métricas implementadas
- **[Comparación de Sistemas](docs/results/comparison.md)** - TF-IDF vs BM25 vs Transformers
- **[Análisis de Rendimiento](docs/results/performance.md)** - Análisis de rendimiento
- **[Validación de Calidad](docs/results/validation.md)** - Validación de resultados

### 🔧 **Desarrollo**
- **[Guía de Desarrollo](docs/development/README.md)** - Cómo contribuir al proyecto
- **[Estándares de Código](docs/development/coding-standards.md)** - Convenciones y mejores prácticas
- **[Testing](docs/development/testing.md)** - Estrategia de testing
- **[CI/CD](docs/development/ci-cd.md)** - Pipeline de integración continua

## 📁 Estructura del Proyecto

```
vm-expedientes-minedu/
├── .github/workflows/        # CI/CD Pipeline automatizado
├── config/                   # Configuraciones seguras
├── data/                     # Datos y resultados
│   ├── evaluation/           # Resultados de evaluación
│   └── processed/            # Archivos procesados
├── docs/                     # 📚 Documentación consolidada
│   ├── architecture/         # Arquitectura del sistema
│   ├── security/             # Seguridad y cumplimiento
│   ├── deployment/           # Despliegue y operaciones
│   ├── user-guides/          # Guías de usuario
│   ├── results/              # Resultados y evaluación
│   └── development/          # Guías de desarrollo
├── paper_cientifico/         # 🔬 Investigación científica
├── src/                      # Código fuente
│   ├── core/                 # Módulos centrales
│   ├── ai/                   # Scripts de IA
│   └── text_processor/       # Procesamiento de texto
├── tests/                    # Tests unitarios y de integración
├── demo.py                   # Demo principal unificado
├── requirements.txt          # Dependencias consolidadas
└── README.md                 # Este archivo
```

## 📈 Estado del Proyecto

### ✅ **Completado**
- Sistema de seguridad 100% implementado y verificado
- Validación científica completa con dataset dorado
- CI/CD pipeline automatizado
- Documentación consolidada y organizada
- Cumplimiento gubernamental verificado

### 🚧 **En Desarrollo**
- Optimizaciones de rendimiento
- API REST segura
- Interfaz web gubernamental

### 📋 **Próximos Pasos**
- Paper científico SIGIR/CLEF 2025-2026
- Despliegue en producción MINEDU
- Validación con usuarios reales

## 🤝 Contribución

Este proyecto sigue estándares científicos y gubernamentales. Para contribuir:

1. **Fork** el repositorio
2. **Crea** una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** tus cambios (`git commit -m 'feat: add some AmazingFeature'`)
4. **Push** a la rama (`git push origin feature/AmazingFeature`)
5. **Abre** un Pull Request

### Estándares de Código
- **Conventional Commits**: Para mensajes de commit
- **Type Hints**: Para documentación de tipos
- **Docstrings**: Para documentación de funciones
- **Security First**: Todas las contribuciones deben pasar auditoría de seguridad

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo `LICENSE` para más detalles.

## 📞 Contacto

- **Proyecto**: vm-expedientes-minedu
- **Autor**: Hanns (usuario)
- **Propósito**: Investigación científica y implementación gubernamental
- **Destinatario**: SIGIR/CLEF 2025-2026 + MINEDU Perú

## 🙏 Agradecimientos

- Ministerio de Educación del Perú (MINEDU)
- Comunidad científica de SIGIR/CLEF
- Contribuidores del proyecto
- Estándares de seguridad gubernamental

---

**🔒 Sistema de Seguridad: 100% Implementado y Verificado**  
**📊 Estado: Listo para Producción y Paper Científico**  
**🏛️ Cumplimiento: Normativas Gubernamentales Aprobadas**  
**🚀 DevOps: Pipeline Automatizado y Documentación Consolidada**
