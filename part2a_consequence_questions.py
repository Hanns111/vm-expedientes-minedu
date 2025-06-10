#!/usr/bin/env python3
"""
PARTE 2A: Preguntas CONSEQUENCE (6 preguntas)
Para resolver el déficit crítico identificado en el diagnóstico
"""

import json
import os
from collections import Counter

# 6 preguntas CONSEQUENCE - Resuelve el déficit crítico
CONSEQUENCE_QUESTIONS = [
    {
        "query_id": "0021",
        "question": "¿Qué consecuencias tiene no presentar la rendición de cuentas dentro del plazo establecido?",
        "category": "procedures",
        "query_type": "consequence",
        "difficulty": "medium",
        "ground_truth_answer": "Se aplicará la recuperación de viáticos no rendidos conforme al artículo 8.7, pudiendo incluir sanciones administrativas y descuentos por planilla.",
        "supporting_chunks": ["chunk_recuperacion_viaticos_8_7"],
        "metadata": {
            "entities_required": ["plazo_rendicion", "sanciones", "descuentos"],
            "context_type": "specific"
        }
    },
    {
        "query_id": "0022",
        "question": "¿Qué sucede si se necesita reprogramar una comisión de servicios ya autorizada?",
        "category": "procedures",
        "query_type": "consequence",
        "difficulty": "medium",
        "ground_truth_answer": "Debe seguirse el procedimiento de reprogramación establecido en el artículo 8.5, con nueva autorización del jefe inmediato y disponibilidad presupuestal.",
        "supporting_chunks": ["chunk_reprogramaciones_8_5"],
        "metadata": {
            "entities_required": ["reprogramacion", "autorizacion", "presupuesto"],
            "context_type": "specific"
        }
    },
    {
        "query_id": "0023",
        "question": "¿Qué pasa si los gastos reales de viaje superan el monto de viáticos asignado?",
        "category": "amounts",
        "query_type": "consequence",
        "difficulty": "hard",
        "ground_truth_answer": "Se puede solicitar reembolso por mayor gasto según artículo 8.6, previa presentación de sustento documentario y aprobación de la autoridad competente.",
        "supporting_chunks": ["chunk_reembolso_mayor_gasto_8_6"],
        "metadata": {
            "entities_required": ["reembolso", "mayor_gasto", "sustento_documentario"],
            "context_type": "specific"
        }
    },
    {
        "query_id": "0024",
        "question": "¿Qué ocurre si surge una emergencia que requiere viaje inmediato sin autorización previa?",
        "category": "procedures",
        "query_type": "consequence",
        "difficulty": "hard",
        "ground_truth_answer": "Se aplican los procedimientos de emergencia del artículo 8.3.8, requiriendo autorización posterior inmediata y justificación detallada de la urgencia.",
        "supporting_chunks": ["chunk_procedimientos_emergencia_8_3_8"],
        "metadata": {
            "entities_required": ["emergencia", "autorizacion_posterior", "justificacion"],
            "context_type": "specific"
        }
    },
    {
        "query_id": "0025",
        "question": "¿Qué consecuencias tiene presentar documentos falsificados en la rendición de cuentas?",
        "category": "documents",
        "query_type": "consequence",
        "difficulty": "hard",
        "ground_truth_answer": "Constituye falta grave sujeta a proceso administrativo disciplinario, además de las acciones penales correspondientes conforme a las responsabilidades específicas del artículo 9.2.",
        "supporting_chunks": ["chunk_responsabilidades_9_2"],
        "metadata": {
            "entities_required": ["documentos_falsos", "proceso_disciplinario", "acciones_penales"],
            "context_type": "specific"
        }
    },
    {
        "query_id": "0026",
        "question": "¿Qué pasa si no se utiliza el formato oficial para la solicitud de viáticos?",
        "category": "documents",
        "query_type": "consequence",
        "difficulty": "easy",
        "ground_truth_answer": "La solicitud será observada y devuelta para su corrección, debiendo utilizarse obligatoriamente los anexos y modelos establecidos en las disposiciones complementarias.",
        "supporting_chunks": ["chunk_disposiciones_complementarias_10"],
        "metadata": {
            "entities_required": ["formato_oficial", "anexos", "modelos"],
            "context_type": "specific"
        }
    }
]

def save_consequence_questions():
    """Guardar preguntas consequence"""
    print("[INFO] Guardando preguntas CONSEQUENCE...")
    
    output_path = "paper_cientifico/dataset/consequence_questions.json"
    
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(CONSEQUENCE_QUESTIONS, f, indent=2, ensure_ascii=False)
        
        print(f"[OK] Preguntas consequence guardadas: {output_path}")
        print(f"[INFO] Total preguntas consequence: {len(CONSEQUENCE_QUESTIONS)}")
        
        return output_path
        
    except Exception as e:
        print(f"[ERROR] Error guardando: {e}")
        return None

def main_part2a():
    """Ejecutar Parte 2A"""
    print("[INFO] PARTE 2A: PREGUNTAS CONSEQUENCE")
    print("[INFO] Resolviendo déficit crítico de preguntas 'consequence'")
    print("=" * 50)
    
    path = save_consequence_questions()
    if path:
        print(f"[OK] Parte 2A completada exitosamente")
        print(f"[INFO] Ejecutar part2b_other_questions.py")
        return True
    else:
        print(f"[ERROR] Parte 2A falló")
        return False

if __name__ == "__main__":
    main_part2a()
