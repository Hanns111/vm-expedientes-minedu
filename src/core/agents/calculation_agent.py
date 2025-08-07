"""
Agente Especializado en Cálculos
Maneja consultas sobre montos, viáticos, cálculos normativos y valores monetarios
"""
import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP

# Integración con sistema existente (versión simplificada)
from ..calculations.normative_calculator_simple import NormativeCalculator, UIT_VALUES
# TemporalLegalProcessor comentado temporalmente (requiere pandas)
# from ..calculations.temporal_legal import TemporalLegalProcessor

logger = logging.getLogger(__name__)

@dataclass
class CalculationResult:
    """Resultado de cálculo especializado"""
    calculation_type: str
    result_value: Decimal
    result_formatted: str
    legal_basis: str
    calculation_steps: List[str]
    confidence: float
    applicable_year: int
    metadata: Dict[str, Any]

class CalculationAgent:
    """
    Agente especializado en cálculos normativos
    Integra el sistema de cálculos existente con reasoning avanzado
    """
    
    def __init__(self):
        # Integrar calculadoras existentes
        self.normative_calculator = NormativeCalculator()
        # TemporalLegalProcessor comentado temporalmente
        # self.temporal_processor = TemporalLegalProcessor()
        
        # Patrones de detección de cálculos
        self.calculation_patterns = self._setup_calculation_patterns()
        
        # Base de conocimiento de cálculos
        self.calculation_knowledge = self._setup_calculation_knowledge()
        
        logger.info("🧮 CalculationAgent inicializado")
    
    def _setup_calculation_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Configurar patrones para detectar tipos de cálculo"""
        return {
            "viaticos": {
                "patterns": [
                    r"viático.*(?:monto|cantidad|valor)",
                    r"(?:monto|valor).*viático",
                    r"cuánto.*viático",
                    r"viático.*(?:máximo|mínimo)"
                ],
                "keywords": ["viático", "viáticos", "comisión", "servicio"],
                "calculation_type": "travel_allowance"
            },
            
            "uit_calculations": {
                "patterns": [
                    r"uit.*(?:valor|monto)",
                    r"unidad.*impositiva.*tributaria",
                    r"uit.*(?:año|\d{4})",
                    r"valor.*uit"
                ],
                "keywords": ["uit", "unidad impositiva", "tributaria"],
                "calculation_type": "uit_value"
            },
            
            "percentage_calculations": {
                "patterns": [
                    r"(\d+(?:\.\d+)?)\s*%",
                    r"porcentaje.*de",
                    r"(?:calcular|aplicar).*porcentaje",
                    r"(\d+)\s*por\s*ciento"
                ],
                "keywords": ["porcentaje", "por ciento", "%"],
                "calculation_type": "percentage"
            },
            
            "daily_rates": {
                "patterns": [
                    r"(?:monto|tarifa).*(?:diario|día)",
                    r"por\s+día",
                    r"diario.*(?:monto|valor)",
                    r"tarifa.*diaria"
                ],
                "keywords": ["diario", "día", "tarifa", "por día"],
                "calculation_type": "daily_rate"
            },
            
            "total_calculations": {
                "patterns": [
                    r"total.*(?:días|período)",
                    r"(?:calcular|total).*(?:\d+)\s*días",
                    r"por.*(\d+)\s*días",
                    r"durante.*(\d+)\s*días"
                ],
                "keywords": ["total", "días", "período", "durante"],
                "calculation_type": "total_amount"
            }
        }
    
    def _setup_calculation_knowledge(self) -> Dict[str, Any]:
        """Base de conocimiento para cálculos especializados"""
        return {
            "viaticos_hierarchy": {
                "ministro": {
                    "nacional": 380.00,
                    "internacional": 650.00,
                    "legal_basis": "DS-007-2013-EF Art. 15"
                },
                "viceministro": {
                    "nacional": 340.00,
                    "internacional": 580.00,
                    "legal_basis": "DS-007-2013-EF Art. 16"
                },
                "funcionario": {
                    "nacional": 320.00,
                    "internacional": 520.00,
                    "legal_basis": "DS-007-2013-EF Art. 17"
                },
                "servidor": {
                    "nacional": 280.00,
                    "internacional": 450.00,
                    "legal_basis": "DS-007-2013-EF Art. 18"
                }
            },
            
            "calculation_rules": {
                "minimum_days": 1,
                "maximum_continuous_days": 30,
                "fractional_day_rule": "complete_day_only",
                "weekend_inclusion": True,
                "holiday_inclusion": True
            },
            
            "adjustment_factors": {
                "remote_location": 1.2,
                "emergency_mission": 1.1,
                "international_training": 1.15,
                "academic_conference": 0.9
            }
        }
    
    def process_calculation_query(self, 
                                query: str, 
                                context: Dict[str, Any] = None) -> CalculationResult:
        """
        Procesar consulta de cálculo y generar resultado especializado
        
        Args:
            query: Consulta sobre cálculos
            context: Contexto adicional (usuario, fecha, etc.)
            
        Returns:
            Resultado de cálculo con detalles y razonamiento
        """
        try:
            # 1. Detectar tipo de cálculo
            calculation_type = self._detect_calculation_type(query)
            
            # 2. Extraer parámetros de la consulta
            parameters = self._extract_calculation_parameters(query)
            
            # 3. Determinar año aplicable
            applicable_year = self._determine_applicable_year(query, context)
            
            # 4. Ejecutar cálculo según tipo
            result = self._execute_calculation(calculation_type, parameters, applicable_year)
            
            # 5. Generar explicación de pasos
            steps = self._generate_calculation_steps(calculation_type, parameters, result)
            
            # 6. Determinar base legal
            legal_basis = self._determine_legal_basis(calculation_type, applicable_year)
            
            # 7. Calcular confianza
            confidence = self._calculate_confidence(calculation_type, parameters, result)
            
            calculation_result = CalculationResult(
                calculation_type=calculation_type,
                result_value=result["value"],
                result_formatted=result["formatted"],
                legal_basis=legal_basis,
                calculation_steps=steps,
                confidence=confidence,
                applicable_year=applicable_year,
                metadata={
                    "parameters": parameters,
                    "query": query,
                    "context": context or {},
                    "calculation_date": datetime.now().isoformat()
                }
            )
            
            logger.info(f"🧮 Cálculo completado: {calculation_type} = {result['formatted']}")
            return calculation_result
            
        except Exception as e:
            logger.error(f"❌ Error en cálculo: {e}")
            return self._create_fallback_result(query)
    
    def _detect_calculation_type(self, query: str) -> str:
        """Detectar tipo de cálculo basado en patrones"""
        query_lower = query.lower()
        
        for calc_type, pattern_data in self.calculation_patterns.items():
            # Verificar patrones regex
            for pattern in pattern_data["patterns"]:
                if re.search(pattern, query_lower):
                    return pattern_data["calculation_type"]
            
            # Verificar keywords
            keyword_matches = sum(1 for keyword in pattern_data["keywords"] 
                                if keyword in query_lower)
            
            if keyword_matches >= 2:  # Al menos 2 keywords coinciden
                return pattern_data["calculation_type"]
        
        return "general_calculation"
    
    def _extract_calculation_parameters(self, query: str) -> Dict[str, Any]:
        """Extraer parámetros de cálculo de la consulta"""
        parameters = {}
        
        # Extraer números/montos
        amounts = re.findall(r's/\s*(\d+(?:\.\d+)?)', query, re.IGNORECASE)
        if amounts:
            parameters["amounts"] = [float(amount) for amount in amounts]
        
        # Extraer días
        days_patterns = [
            r'(\d+)\s*días?',
            r'durante\s+(\d+)',
            r'por\s+(\d+)\s*días?'
        ]
        for pattern in days_patterns:
            days_match = re.search(pattern, query, re.IGNORECASE)
            if days_match:
                parameters["days"] = int(days_match.group(1))
                break
        
        # Extraer porcentajes
        percentage_match = re.search(r'(\d+(?:\.\d+)?)\s*%', query)
        if percentage_match:
            parameters["percentage"] = float(percentage_match.group(1))
        
        # Extraer destino/ubicación
        location_patterns = [
            r'(?:en|a|para)\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+?)(?:\s|$)',
            r'destino\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)',
            r'viaje\s+a\s+([A-Za-záéíóúñÁÉÍÓÚÑ\s]+)'
        ]
        for pattern in location_patterns:
            location_match = re.search(pattern, query, re.IGNORECASE)
            if location_match:
                location = location_match.group(1).strip()
                if len(location) > 2 and location.lower() not in ['el', 'la', 'los', 'las', 'un', 'una']:
                    parameters["location"] = location
                break
        
        # Extraer nivel jerárquico
        hierarchy_keywords = {
            "ministro": ["ministro", "ministros"],
            "viceministro": ["viceministro", "viceministros"],
            "funcionario": ["funcionario", "funcionarios", "directivo"],
            "servidor": ["servidor", "servidores", "empleado"]
        }
        
        query_lower = query.lower()
        for level, keywords in hierarchy_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                parameters["hierarchy_level"] = level
                break
        
        # Detectar tipo de viaje
        if any(word in query_lower for word in ["internacional", "extranjero", "exterior"]):
            parameters["travel_type"] = "internacional"
        elif any(word in query_lower for word in ["nacional", "interior", "país"]):
            parameters["travel_type"] = "nacional"
        
        return parameters
    
    def _determine_applicable_year(self, query: str, context: Dict[str, Any] = None) -> int:
        """Determinar año aplicable para el cálculo"""
        # 1. Buscar año explícito en la consulta
        year_match = re.search(r'(?:año\s+)?(\d{4})', query)
        if year_match:
            year = int(year_match.group(1))
            if 2010 <= year <= datetime.now().year + 1:
                return year
        
        # 2. Verificar contexto
        if context and "year" in context:
            return context["year"]
        
        # 3. Usar año actual por defecto
        return datetime.now().year
    
    def _execute_calculation(self, 
                           calculation_type: str, 
                           parameters: Dict[str, Any], 
                           year: int) -> Dict[str, Any]:
        """Ejecutar cálculo según tipo y parámetros"""
        
        if calculation_type == "travel_allowance":
            return self._calculate_travel_allowance(parameters, year)
        
        elif calculation_type == "uit_value":
            return self._calculate_uit_value(parameters, year)
        
        elif calculation_type == "percentage":
            return self._calculate_percentage(parameters)
        
        elif calculation_type == "daily_rate":
            return self._calculate_daily_rate(parameters, year)
        
        elif calculation_type == "total_amount":
            return self._calculate_total_amount(parameters, year)
        
        else:
            return self._calculate_general(parameters, year)
    
    def _calculate_travel_allowance(self, parameters: Dict[str, Any], year: int) -> Dict[str, Any]:
        """Calcular viáticos usando el sistema existente"""
        
        # Usar calculadora existente
        level = parameters.get("hierarchy_level", "funcionario")
        days = parameters.get("days", 1)
        location = parameters.get("location", "Nacional")
        
        # Determinar si es nacional o internacional
        travel_type = parameters.get("travel_type")
        if not travel_type:
            travel_type = "Nacional" if "nacional" in location.lower() else "Internacional"
        
        # Usar sistema de cálculos existente
        calculation_result = self.normative_calculator.calculate_viaticos(
            level=level,
            year=year,
            days=days,
            location=travel_type
        )
        
        value = Decimal(str(calculation_result["total_amount_soles"]))
        
        return {
            "value": value,
            "formatted": f"S/ {value:,.2f}",
            "details": calculation_result,
            "breakdown": {
                "daily_rate": calculation_result.get("daily_amount_soles", 320.0),
                "days": days,
                "level": level,
                "location": travel_type
            }
        }
    
    def _calculate_uit_value(self, parameters: Dict[str, Any], year: int) -> Dict[str, Any]:
        """Calcular valor UIT"""
        uit_value = UIT_VALUES.get(year, UIT_VALUES[max(UIT_VALUES.keys())])
        
        # Si hay cantidad específica
        quantity = parameters.get("quantity", 1)
        total_value = Decimal(str(uit_value)) * Decimal(str(quantity))
        
        return {
            "value": total_value,
            "formatted": f"S/ {total_value:,.2f}",
            "details": {
                "uit_unit_value": uit_value,
                "quantity": quantity,
                "year": year
            }
        }
    
    def _calculate_percentage(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Calcular porcentajes"""
        percentage = parameters.get("percentage", 0)
        base_amount = parameters.get("amounts", [100])[0] if parameters.get("amounts") else 100
        
        result_value = Decimal(str(base_amount)) * Decimal(str(percentage)) / Decimal("100")
        
        return {
            "value": result_value,
            "formatted": f"S/ {result_value:,.2f}",
            "details": {
                "percentage": percentage,
                "base_amount": base_amount,
                "calculation": f"{base_amount} × {percentage}% = {result_value}"
            }
        }
    
    def _calculate_daily_rate(self, parameters: Dict[str, Any], year: int) -> Dict[str, Any]:
        """Calcular tarifa diaria"""
        level = parameters.get("hierarchy_level", "funcionario")
        travel_type = parameters.get("travel_type", "nacional")
        
        # Obtener tarifa base del conocimiento
        viaticos_data = self.calculation_knowledge["viaticos_hierarchy"]
        daily_rate = viaticos_data.get(level, viaticos_data["funcionario"])[travel_type]
        
        value = Decimal(str(daily_rate))
        
        return {
            "value": value,
            "formatted": f"S/ {value:,.2f}",
            "details": {
                "level": level,
                "travel_type": travel_type,
                "year": year
            }
        }
    
    def _calculate_total_amount(self, parameters: Dict[str, Any], year: int) -> Dict[str, Any]:
        """Calcular monto total para período"""
        days = parameters.get("days", 1)
        
        # Calcular tarifa diaria primero
        daily_result = self._calculate_daily_rate(parameters, year)
        daily_rate = daily_result["value"]
        
        total_value = daily_rate * Decimal(str(days))
        
        return {
            "value": total_value,
            "formatted": f"S/ {total_value:,.2f}",
            "details": {
                "daily_rate": float(daily_rate),
                "days": days,
                "calculation": f"{daily_rate} × {days} días = {total_value}"
            }
        }
    
    def _calculate_general(self, parameters: Dict[str, Any], year: int) -> Dict[str, Any]:
        """Cálculo general/fallback"""
        amounts = parameters.get("amounts", [0])
        value = Decimal(str(amounts[0])) if amounts else Decimal("0")
        
        return {
            "value": value,
            "formatted": f"S/ {value:,.2f}",
            "details": parameters
        }
    
    def _generate_calculation_steps(self, 
                                  calculation_type: str, 
                                  parameters: Dict[str, Any], 
                                  result: Dict[str, Any]) -> List[str]:
        """Generar pasos explicativos del cálculo"""
        steps = []
        
        if calculation_type == "travel_allowance":
            level = parameters.get("hierarchy_level", "funcionario")
            days = parameters.get("days", 1)
            daily_rate = result["details"].get("daily_amount_soles", 320.0)
            
            steps.extend([
                f"1. Identificar nivel jerárquico: {level}",
                f"2. Tarifa diaria aplicable: S/ {daily_rate:,.2f}",
                f"3. Número de días: {days}",
                f"4. Cálculo: S/ {daily_rate:,.2f} × {days} días = {result['formatted']}"
            ])
        
        elif calculation_type == "uit_value":
            year = result["details"]["year"]
            uit_value = result["details"]["uit_unit_value"]
            quantity = result["details"]["quantity"]
            
            steps.extend([
                f"1. Valor UIT año {year}: S/ {uit_value:,.2f}",
                f"2. Cantidad solicitada: {quantity} UIT",
                f"3. Cálculo: S/ {uit_value:,.2f} × {quantity} = {result['formatted']}"
            ])
        
        else:
            steps.append(f"Cálculo {calculation_type}: {result['formatted']}")
        
        return steps
    
    def _determine_legal_basis(self, calculation_type: str, year: int) -> str:
        """Determinar base legal del cálculo"""
        
        if calculation_type == "travel_allowance":
            return "Decreto Supremo N° 007-2013-EF - Viáticos para el sector público"
        
        elif calculation_type == "uit_value":
            return f"Decreto Supremo sobre UIT año {year} - MEF"
        
        else:
            return "Normativa vigente aplicable según consulta"
    
    def _calculate_confidence(self, 
                            calculation_type: str, 
                            parameters: Dict[str, Any], 
                            result: Dict[str, Any]) -> float:
        """Calcular nivel de confianza del cálculo"""
        confidence_factors = []
        
        # Factor 1: Tipo de cálculo reconocido
        if calculation_type in ["travel_allowance", "uit_value"]:
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.6)
        
        # Factor 2: Parámetros completos
        required_params = {"travel_allowance": ["hierarchy_level"], "uit_value": []}
        required = required_params.get(calculation_type, [])
        
        if all(param in parameters for param in required):
            confidence_factors.append(0.9)
        else:
            confidence_factors.append(0.7)
        
        # Factor 3: Resultado válido
        if result["value"] > 0:
            confidence_factors.append(0.8)
        else:
            confidence_factors.append(0.4)
        
        return sum(confidence_factors) / len(confidence_factors)
    
    def _create_fallback_result(self, query: str) -> CalculationResult:
        """Crear resultado de fallback en caso de error"""
        return CalculationResult(
            calculation_type="error",
            result_value=Decimal("0"),
            result_formatted="Error en cálculo",
            legal_basis="No determinada",
            calculation_steps=["Error procesando consulta"],
            confidence=0.0,
            applicable_year=datetime.now().year,
            metadata={"query": query, "error": True}
        )
    
    def get_agent_capabilities(self) -> Dict[str, Any]:
        """Obtener capacidades del agente de cálculos"""
        return {
            "calculation_types": list(self.calculation_patterns.keys()),
            "supported_hierarchies": list(self.calculation_knowledge["viaticos_hierarchy"].keys()),
            "supported_years": list(UIT_VALUES.keys()),
            "features": [
                "Cálculo de viáticos por nivel jerárquico",
                "Valores UIT históricos",
                "Cálculos porcentuales",
                "Tarifas diarias",
                "Montos totales por período",
                "Base legal automática",
                "Explicación paso a paso"
            ]
        }

# Instancia global
global_calculation_agent = CalculationAgent()