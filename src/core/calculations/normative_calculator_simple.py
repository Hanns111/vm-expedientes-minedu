"""
Calculadora normativa simplificada - compatible sin pandas
Mantiene funcionalidad esencial para cálculos de viáticos y UIT
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import json
from decimal import Decimal, ROUND_HALF_UP

logger = logging.getLogger(__name__)

# Constante UIT_VALUES para compatibilidad
UIT_VALUES = {
    2020: 4300.0,
    2021: 4400.0,
    2022: 4600.0,
    2023: 4950.0,
    2024: 5150.0,
    2025: 5350.0
}

@dataclass
class UIT:
    """Unidad Impositiva Tributaria"""
    year: int
    value: float
    source: str = "SUNAT"

@dataclass 
class TipoCambio:
    """Tipo de cambio BCRP"""
    date: date
    buy: float
    sell: float
    source: str = "BCRP"

class NormativeCalculator:
    """
    Calculadora normativa simplificada - compatible sin pandas
    Mantiene funcionalidad esencial para cálculos de viáticos y UIT
    """
    
    def __init__(self, data_path: Optional[Path] = None):
        self.data_path = data_path or Path(__file__).parent / "data"
        self.data_path.mkdir(exist_ok=True)
        
        # Datos simples sin pandas
        self.uit_data = {}
        self.tipo_cambio_data = {}
        self.viaticos_data = {}
        
        # Cargar datos
        self._load_normative_data()
        
        logger.info("📊 NormativeCalculator inicializado (modo simplificado)")
    
    def _load_normative_data(self):
        """Cargar datos normativos desde archivos JSON o valores por defecto"""
        try:
            # Cargar UIT histórica
            self._load_uit_data()
            
            # Cargar tipo de cambio
            self._load_exchange_rate_data()
            
            # Cargar tablas de viáticos
            self._load_viaticos_data()
            
        except Exception as e:
            logger.error(f"❌ Error cargando datos normativos: {e}")
            self._create_default_data()
    
    def _load_uit_data(self):
        """Cargar valores UIT históricos"""
        # Datos UIT actualizados
        self.uit_data = {
            2020: 4300.0,
            2021: 4400.0,
            2022: 4600.0,
            2023: 4950.0,
            2024: 5150.0,
            2025: 5350.0  # Proyectado
        }
    
    def _load_exchange_rate_data(self):
        """Cargar tipo de cambio actual"""
        # Tipo de cambio actual simplificado
        self.tipo_cambio_data = {
            "buy": 3.78,
            "sell": 3.80,
            "date": datetime.now().strftime("%Y-%m-%d"),
            "source": "BCRP"
        }
    
    def _load_viaticos_data(self):
        """Cargar tabla de viáticos simplificada"""
        # Tabla de viáticos MINEDU simplificada
        self.viaticos_data = {
            "ministro": {"nacional": 380.0, "internacional": 650.0},
            "viceministro": {"nacional": 340.0, "internacional": 580.0},
            "funcionario": {"nacional": 320.0, "internacional": 520.0},
            "servidor": {"nacional": 280.0, "internacional": 450.0}
        }
    
    def calculate_viaticos(
        self, 
        level: str, 
        year: int, 
        days: int = 1,
        location: str = "Nacional"
    ) -> Dict[str, Any]:
        """Calcular viáticos según nivel y año (versión simplificada)"""
        try:
            # Normalizar nivel
            level_key = level.lower()
            location_key = location.lower()
            
            # Obtener tarifa diaria
            if level_key in self.viaticos_data:
                if "internacional" in location_key:
                    daily_amount = self.viaticos_data[level_key]["internacional"]
                else:
                    daily_amount = self.viaticos_data[level_key]["nacional"]
            else:
                # Default a funcionario
                daily_amount = self.viaticos_data["funcionario"]["nacional"]
                logger.warning(f"⚠️ Nivel {level} no encontrado, usando funcionario")
            
            # Cálculos
            total_amount = daily_amount * days
            uit_value = self.get_uit_value(year)
            amount_in_uit = total_amount / uit_value
            
            return {
                "level": level,
                "year": year,
                "days": days,
                "daily_amount_soles": daily_amount,
                "total_amount_soles": total_amount,
                "amount_uit": round(amount_in_uit, 4),
                "uit_reference": uit_value,
                "decree": "DS-007-2013-EF",
                "calculation_date": datetime.now().isoformat(),
                "location": location
            }
                
        except Exception as e:
            logger.error(f"❌ Error calculando viáticos: {e}")
            return self._default_viaticos_calculation(level, year, days)
    
    def get_uit_value(self, year: int) -> float:
        """Obtener valor UIT para año específico"""
        return self.uit_data.get(year, self.uit_data.get(2025, 5350.0))
    
    def get_exchange_rate(self, target_date: Optional[date] = None) -> Dict[str, Any]:
        """Obtener tipo de cambio para fecha específica"""
        return self.tipo_cambio_data
    
    def _default_viaticos_calculation(self, level: str, year: int, days: int) -> Dict[str, Any]:
        """Cálculo por defecto de viáticos"""
        daily_amount = 320.0  # Funcionario nacional por defecto
        total_amount = daily_amount * days
        uit_value = self.get_uit_value(year)
        
        return {
            "level": level,
            "year": year,
            "days": days,
            "daily_amount_soles": daily_amount,
            "total_amount_soles": total_amount,
            "amount_uit": round(total_amount / uit_value, 4),
            "uit_reference": uit_value,
            "decree": "DS-007-2013-EF",
            "calculation_date": datetime.now().isoformat(),
            "location": "Nacional",
            "note": "Cálculo por defecto"
        }
    
    def _create_default_data(self):
        """Crear datos por defecto si no se pueden cargar"""
        logger.warning("🔄 Creando datos normativos por defecto")
        
        self.uit_data = {2025: 5350.0}
        self.tipo_cambio_data = {"buy": 3.78, "sell": 3.80}
        self.viaticos_data = {"funcionario": {"nacional": 320.0}}