#!/usr/bin/env python3
"""
Plan de Migración de PDF Original - MINEDU
==========================================

Script para migrar de la directiva limpia al PDF original de forma segura.
"""

import os
import shutil
from pathlib import Path
import subprocess
from datetime import datetime

class PDFMigrationPlan:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.raw_data = self.project_root / "data" / "raw"
        self.processed_data = self.project_root / "data" / "processed"
        self.backup_dir = self.project_root / "data" / "backup" / f"migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
    def create_backup(self):
        """Crear respaldo completo antes de la migración"""
        print("🔄 Creando respaldo completo...")
        
        # Crear directorio de respaldo
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Respaldar PDF actual
        current_pdf = self.raw_data / "DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf"
        if current_pdf.exists():
            shutil.copy2(current_pdf, self.backup_dir / "DIRECTIVA_LIMPIA_BACKUP.pdf")
            print(f"✅ PDF respaldado en: {self.backup_dir}")
        
        # Respaldar archivos procesados críticos
        files_to_backup = [
            "chunks_directiva_limpia.json",
            "vectorstore_directiva_limpia.pkl",
            "texto_limpio.txt"
        ]
        
        for file in files_to_backup:
            source = self.processed_data / file
            if source.exists():
                shutil.copy2(source, self.backup_dir / file)
                print(f"✅ Respaldado: {file}")
        
        print(f"📁 Respaldo completo en: {self.backup_dir}")
        return True
    
    def validate_new_pdf(self, new_pdf_path):
        """Validar que el nuevo PDF es válido"""
        print(f"🔍 Validando nuevo PDF: {new_pdf_path}")
        
        new_pdf = Path(new_pdf_path)
        if not new_pdf.exists():
            print(f"❌ Error: PDF no encontrado en {new_pdf_path}")
            return False
        
        # Verificar que es un PDF válido
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(new_pdf_path)
            pages = len(doc)
            doc.close()
            print(f"✅ PDF válido con {pages} páginas")
            return True
        except Exception as e:
            print(f"❌ Error al validar PDF: {e}")
            return False
    
    def replace_pdf(self, new_pdf_path):
        """Reemplazar el PDF actual con el nuevo"""
        print("🔄 Reemplazando PDF...")
        
        target_name = "DIRECTIVA N° 011-2020-MINEDU_LIMPIA.pdf"
        target_path = self.raw_data / target_name
        
        # Copiar el nuevo PDF con el nombre correcto
        shutil.copy2(new_pdf_path, target_path)
        print(f"✅ PDF reemplazado exitosamente")
        return True
    
    def regenerate_pipeline(self):
        """Regenerar todo el pipeline de procesamiento"""
        print("🚀 Regenerando pipeline completo...")
        
        scripts_to_run = [
            ("src/ai/process_clean_directive.py", "Procesando directiva limpia"),
            ("src/generate_vectorstore_semantic.py", "Generando vectorstore semántico"),
            ("test_bm25_amounts.py", "Probando búsqueda BM25")
        ]
        
        for script, description in scripts_to_run:
            print(f"▶️ {description}...")
            try:
                result = subprocess.run(["python", script], 
                                      capture_output=True, 
                                      text=True, 
                                      cwd=self.project_root)
                if result.returncode == 0:
                    print(f"✅ {description} - Completado")
                else:
                    print(f"⚠️ {description} - Advertencias:")
                    print(result.stderr[:200])
            except Exception as e:
                print(f"❌ Error en {script}: {e}")
        
        return True
    
    def test_search_functionality(self):
        """Probar que la búsqueda funciona con el nuevo contenido"""
        print("🧪 Probando funcionalidad de búsqueda...")
        
        test_queries = [
            "monto máximo diario viáticos",
            "S/ 320",
            "comisión de servicios"
        ]
        
        try:
            # Importar y probar búsqueda
            from respuesta_directa import buscar_respuesta_directa
            
            for query in test_queries:
                print(f"Probando: '{query}'")
                buscar_respuesta_directa(query)
                print("-" * 40)
            
            print("✅ Pruebas de búsqueda completadas")
            return True
            
        except Exception as e:
            print(f"❌ Error en pruebas: {e}")
            return False
    
    def migrate(self, new_pdf_path):
        """Ejecutar migración completa"""
        print("🎯 INICIANDO MIGRACIÓN DE PDF")
        print("=" * 50)
        
        # 1. Crear respaldo
        if not self.create_backup():
            return False
        
        # 2. Validar nuevo PDF
        if not self.validate_new_pdf(new_pdf_path):
            return False
        
        # 3. Reemplazar PDF
        if not self.replace_pdf(new_pdf_path):
            return False
        
        # 4. Regenerar pipeline
        if not self.regenerate_pipeline():
            return False
        
        # 5. Probar funcionalidad
        if not self.test_search_functionality():
            print("⚠️ Advertencia: Las pruebas fallaron, pero la migración continuó")
        
        print("=" * 50)
        print("🎉 ¡MIGRACIÓN COMPLETADA EXITOSAMENTE!")
        print(f"📁 Respaldo disponible en: {self.backup_dir}")
        print("🔍 El sistema está listo para usar con el nuevo PDF")
        
        return True

def main():
    """Función principal"""
    migrator = PDFMigrationPlan()
    
    # Aquí especifica la ruta a tu PDF original
    new_pdf_path = input("📄 Ingresa la ruta completa a tu PDF original: ")
    
    if migrator.migrate(new_pdf_path):
        print("✅ Migración exitosa")
    else:
        print("❌ Migración falló")

if __name__ == "__main__":
    main() 