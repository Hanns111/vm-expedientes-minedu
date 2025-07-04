#!/usr/bin/env python3
"""
Test de validación automática del snapshot del sistema
Verifica integridad y coherencia de los componentes críticos
"""
import json
import os
import hashlib
import subprocess
import requests
from pathlib import Path

class SnapshotValidator:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.context_dir = self.project_root / "context"
        self.errors = []
        self.warnings = []
        
    def test_snapshot_integrity(self):
        """Validar integridad del snapshot.json"""
        snapshot_file = self.context_dir / "snapshot.json"
        
        if not snapshot_file.exists():
            self.errors.append("CRITICAL: snapshot.json missing")
            return False
            
        try:
            with open(snapshot_file) as f:
                snapshot = json.load(f)
            
            required_sections = ["snapshot_metadata", "verification_results", "file_checksums"]
            for section in required_sections:
                if section not in snapshot:
                    self.errors.append(f"CRITICAL: Missing section {section} in snapshot.json")
                    
            return len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"CRITICAL: Failed to parse snapshot.json: {e}")
            return False
    
    def test_legal_reasoner_exists(self):
        """Verificar que motor legal existe y tiene contenido"""
        legal_file = self.project_root / "backend/src/domain/legal_reasoning.py"
        
        if not legal_file.exists():
            self.errors.append("CRITICAL: legal_reasoning.py missing")
            return False
            
        try:
            with open(legal_file) as f:
                content = f.read()
                
            if "class LegalReasoner" not in content:
                self.errors.append("CRITICAL: LegalReasoner class not found")
                return False
                
            lines = len(content.splitlines())
            if lines < 100:
                self.warnings.append(f"WARNING: Legal reasoner only {lines} lines (expected >100)")
                
            return True
        except Exception as e:
            self.errors.append(f"CRITICAL: Failed to read legal_reasoning.py: {e}")
            return False
    
    def test_backend_health(self):
        """Verificar que backend responde"""
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    return True
                else:
                    self.errors.append(f"CRITICAL: Backend unhealthy: {data}")
                    return False
            else:
                self.errors.append(f"CRITICAL: Backend HTTP {response.status_code}")
                return False
        except Exception as e:
            self.errors.append(f"CRITICAL: Backend unreachable: {e}")
            return False
    
    def test_chunks_data_exists(self):
        """Verificar que chunks.json existe y tiene contenido"""
        chunks_file = self.project_root / "data/processed/chunks.json"
        
        if not chunks_file.exists():
            self.errors.append("CRITICAL: chunks.json missing")
            return False
            
        try:
            with open(chunks_file) as f:
                chunks = json.load(f)
                
            if not isinstance(chunks, list):
                self.errors.append("CRITICAL: chunks.json is not a list")
                return False
                
            if len(chunks) < 5:
                self.warnings.append(f"WARNING: Only {len(chunks)} chunks (expected >5)")
                
            return True
        except Exception as e:
            self.errors.append(f"CRITICAL: Failed to parse chunks.json: {e}")
            return False
    
    def test_vectorstore_files(self):
        """Verificar que vectorstores existen"""
        vectorstore_dir = self.project_root / "data/vectorstores"
        
        if not vectorstore_dir.exists():
            self.errors.append("CRITICAL: vectorstores directory missing")
            return False
            
        pkl_files = list(vectorstore_dir.glob("*.pkl"))
        if len(pkl_files) < 2:
            self.errors.append(f"CRITICAL: Only {len(pkl_files)} vectorstore files (expected >=2)")
            return False
            
        return True
    
    def calculate_confidence(self):
        """Calcular confianza basada en TODOs"""
        critical_count = len([e for e in self.errors if "CRITICAL" in e])
        minor_count = len([w for w in self.warnings if "WARNING" in w])
        
        confidence = 100 - (critical_count * 20) - (minor_count * 5)
        return max(0, confidence)
    
    def run_all_tests(self):
        """Ejecutar todas las validaciones"""
        tests = [
            self.test_snapshot_integrity,
            self.test_legal_reasoner_exists, 
            self.test_backend_health,
            self.test_chunks_data_exists,
            self.test_vectorstore_files
        ]
        
        results = {}
        for test in tests:
            test_name = test.__name__
            try:
                results[test_name] = test()
            except Exception as e:
                self.errors.append(f"CRITICAL: Test {test_name} crashed: {e}")
                results[test_name] = False
                
        return results
    
    def generate_report(self):
        """Generar reporte de validación"""
        results = self.run_all_tests()
        confidence = self.calculate_confidence()
        
        report = {
            "timestamp": "2025-07-04T20:50Z",
            "confidence": confidence,
            "test_results": results,
            "critical_errors": len([e for e in self.errors if "CRITICAL" in e]),
            "warnings": len(self.warnings),
            "errors": self.errors,
            "warnings_list": self.warnings,
            "verdict": "PASS" if confidence >= 75 else "FAIL"
        }
        
        return report

if __name__ == "__main__":
    validator = SnapshotValidator()
    report = validator.generate_report()
    
    print("🧪 SNAPSHOT VALIDATION REPORT")
    print("=" * 50)
    print(f"Confidence: {report['confidence']}%")
    print(f"Critical Errors: {report['critical_errors']}")
    print(f"Warnings: {report['warnings']}")
    print(f"Verdict: {report['verdict']}")
    
    if report['critical_errors'] > 0:
        print("\n❌ CRITICAL ERRORS:")
        for error in report['errors']:
            if "CRITICAL" in error:
                print(f"  - {error}")
    
    if report['warnings'] > 0:
        print("\n⚠️ WARNINGS:")
        for warning in report['warnings_list']:
            print(f"  - {warning}")
    
    print("\n📊 TEST RESULTS:")
    for test_name, result in report['test_results'].items():
        status = "✅" if result else "❌"
        print(f"  {status} {test_name}")
    
    # Exit code based on verdict
    exit(0 if report['verdict'] == "PASS" else 1)