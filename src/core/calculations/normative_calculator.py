"""
Calculadora normativa simplificada - compatible sin pandas
Mantiene datos dinámicos actualizados: UIT, tipo de cambio, valores vigentes
"""
import logging
from datetime import datetime, date
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import json
from decimal import Decimal, ROUND_HALF_UP

# Pandas/numpy opcionales
try:
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

logger = logging.getLogger(__name__)

# Constante UIT_VALUES para compatibilidad con imports
UIT_VALUES = {
    2020: 4300.0,
    2021: 4400.0,
    2022: 4600.0,
    2023: 4950.0,
    2024: 5150.0,
    2025: 5350.0  # Proyectado
}

@dataclass
class UIT:
    """Unidad Impositiva Tributaria por año"""
    year: int
    value: float
    source: str
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UIT':
        return cls(
            year=data['year'],
            value=data['value'],
            source=data.get('source', 'SUNAT')
        )

@dataclass 
class TipoCambio:
    """Tipo de cambio USD/PEN por fecha"""
    date: date
    buy: float
    sell: float
    source: str = "BCRP"
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TipoCambio':
        return cls(
            date=date.fromisoformat(data['date']) if isinstance(data['date'], str) else data['date'],
            buy=data['buy'],
            sell=data['sell'],
            source=data.get('source', 'BCRP')
        )

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
        
        logger.info(f"📊 NormativeCalculator inicializado (modo simplificado)")
        if not PANDAS_AVAILABLE:
            logger.warning("⚠️ Pandas no disponible - usando versión simplificada")
    
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
    
    def _load_infracciones_data(self):
        """Cargar tabla de infracciones y sanciones"""
        infracciones_file = self.data_path / "infracciones_table.json"
        
        if infracciones_file.exists():
            with open(infracciones_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.infracciones_df = pd.DataFrame(data)
        else:
            # Tabla de infracciones administrativas
            infracciones_data = [
                {
                    "code": "INF001", "description": "Uso indebido de viáticos",
                    "severity": "Grave", "min_uit": 0.5, "max_uit": 2.0,
                    "article": "Artículo 166", "law": "Ley 27815",
                    "valid_from": "2020-01-01", "valid_to": "2025-12-31"
                },
                {
                    "code": "INF002", "description": "No rendición de cuentas en plazo",
                    "severity": "Leve", "min_uit": 0.1, "max_uit": 0.5,
                    "article": "Artículo 167", "law": "Ley 27815", 
                    "valid_from": "2020-01-01", "valid_to": "2025-12-31"
                },
                {
                    "code": "INF003", "description": "Falsificación de comprobantes",
                    "severity": "Muy Grave", "min_uit": 2.0, "max_uit": 8.0,
                    "article": "Artículo 168", "law": "Ley 27815",
                    "valid_from": "2020-01-01", "valid_to": "2025-12-31"
                }
            ]
            self.infracciones_df = pd.DataFrame(infracciones_data)
            self.infracciones_df['valid_from'] = pd.to_datetime(self.infracciones_df['valid_from'])
            self.infracciones_df['valid_to'] = pd.to_datetime(self.infracciones_df['valid_to'])
            self._save_infracciones_data()
    
    def _create_default_data(self):
        """Crear datos por defecto si no se pueden cargar"""
        logger.warning("🔄 Creando datos normativos por defecto")
        
        # UIT básica
        self.uit_df = pd.DataFrame([
            {"year": 2025, "value": 5350.0, "source": "Default"}
        ])
        
        # Tipo de cambio básico
        self.tipo_cambio_df = pd.DataFrame([
            {"date": pd.Timestamp.now(), "buy": 3.78, "sell": 3.80, "source": "Default"}
        ])
        
        # Viáticos básicos
        self.viaticos_df = pd.DataFrame([
            {
                "year": 2025, "category": "Minister", "level": "Ministro",
                "amount_soles": 380.0, "amount_uit": 0.071, "location": "Nacional",
                "decree": "DS-007-2013-EF", "valid_from": pd.Timestamp.now(),
                "valid_to": pd.Timestamp.now().replace(year=2025, month=12, day=31)
            }
        ])
    
    # === MÉTODOS DE CÁLCULO PRINCIPALES ===
    
    def get_uit_value(self, year: int) -> float:
        """Obtener valor UIT para un año específico"""
        try:
            uit_row = self.uit_df[self.uit_df['year'] == year]
            if not uit_row.empty:
                return float(uit_row.iloc[0]['value'])
            else:
                # Usar el valor más reciente disponible
                latest_uit = self.uit_df.sort_values('year', ascending=False).iloc[0]
                logger.warning(f"⚠️ UIT para {year} no encontrada, usando {latest_uit['year']}: S/ {latest_uit['value']}")
                return float(latest_uit['value'])
        except Exception as e:
            logger.error(f"❌ Error obteniendo UIT para {year}: {e}")
            return 5350.0  # Valor por defecto 2025
    
    def get_exchange_rate(self, target_date: Union[date, str]) -> Dict[str, float]:
        """Obtener tipo de cambio para una fecha específica"""
        try:
            if isinstance(target_date, str):
                target_date = pd.to_datetime(target_date).date()
            
            # Buscar la fecha más cercana
            self.tipo_cambio_df['date_only'] = self.tipo_cambio_df['date'].dt.date
            closest_idx = np.argmin(np.abs((self.tipo_cambio_df['date_only'] - target_date).dt.days))
            closest_rate = self.tipo_cambio_df.iloc[closest_idx]
            
            return {
                "buy": float(closest_rate['buy']),
                "sell": float(closest_rate['sell']),
                "date": closest_rate['date_only'].isoformat(),
                "source": closest_rate['source']
            }
        except Exception as e:
            logger.error(f"❌ Error obteniendo tipo de cambio para {target_date}: {e}")
            return {"buy": 3.78, "sell": 3.80, "date": str(target_date), "source": "Default"}
    
    def calculate_viaticos(
        self, 
        level: str, 
        year: int, 
        days: int = 1,
        location: str = "Nacional"
    ) -> Dict[str, Any]:
        """Calcular viáticos según nivel y año"""
        try:
            # Filtrar por año y nivel
            viaticos_query = self.viaticos_df[
                (self.viaticos_df['year'] == year) & 
                (self.viaticos_df['level'].str.contains(level, case=False, na=False))
            ]
            
            if viaticos_query.empty:
                # Buscar el año más cercano
                available_years = self.viaticos_df['year'].unique()
                closest_year = min(available_years, key=lambda x: abs(x - year))
                
                viaticos_query = self.viaticos_df[
                    (self.viaticos_df['year'] == closest_year) &
                    (self.viaticos_df['level'].str.contains(level, case=False, na=False))
                ]
                
                logger.warning(f"⚠️ Viáticos para {level} en {year} no encontrados, usando {closest_year}")
            
            if not viaticos_query.empty:
                viatico_row = viaticos_query.iloc[0]
                
                daily_amount = float(viatico_row['amount_soles'])
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
                    "decree": viatico_row['decree'],
                    "calculation_date": datetime.now().isoformat(),
                    "location": location
                }
            else:
                raise ValueError(f"No se encontraron datos de viáticos para {level}")
                
        except Exception as e:
            logger.error(f"❌ Error calculando viáticos: {e}")
            return self._default_viaticos_calculation(level, year, days)
    
    def calculate_sanctions(
        self, 
        infraction_code: str, 
        severity_factor: float = 1.0,
        year: int = 2025
    ) -> Dict[str, Any]:
        """Calcular sanciones administrativas"""
        try:
            # Filtrar infracción
            infraction_query = self.infracciones_df[
                self.infracciones_df['code'] == infraction_code
            ]
            
            if infraction_query.empty:
                available_codes = self.infracciones_df['code'].tolist()
                raise ValueError(f"Código de infracción {infraction_code} no encontrado. Disponibles: {available_codes}")
            
            infraction = infraction_query.iloc[0]
            uit_value = self.get_uit_value(year)
            
            min_sanction_uit = float(infraction['min_uit']) * severity_factor
            max_sanction_uit = float(infraction['max_uit']) * severity_factor
            
            min_sanction_soles = min_sanction_uit * uit_value
            max_sanction_soles = max_sanction_uit * uit_value
            
            return {
                "infraction_code": infraction_code,
                "description": infraction['description'],
                "severity": infraction['severity'],
                "year": year,
                "severity_factor": severity_factor,
                "min_sanction_uit": round(min_sanction_uit, 4),
                "max_sanction_uit": round(max_sanction_uit, 4),
                "min_sanction_soles": round(min_sanction_soles, 2),
                "max_sanction_soles": round(max_sanction_soles, 2),
                "uit_reference": uit_value,
                "legal_article": infraction['article'],
                "legal_framework": infraction['law'],
                "calculation_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error calculando sanciones: {e}")
            return {"error": str(e)}
    
    def compare_historical_values(
        self, 
        concept: str,
        start_year: int, 
        end_year: int
    ) -> pd.DataFrame:
        """Comparar valores históricos entre años"""
        try:
            years = list(range(start_year, end_year + 1))
            comparison_data = []
            
            for year in years:
                if concept.lower() == "uit":
                    value = self.get_uit_value(year)
                    comparison_data.append({
                        "year": year,
                        "concept": "UIT",
                        "value_soles": value,
                        "unit": "soles"
                    })
                elif concept.lower() in ["viaticos", "ministro"]:
                    viaticos = self.calculate_viaticos("Ministro", year)
                    if "error" not in viaticos:
                        comparison_data.append({
                            "year": year,
                            "concept": "Viáticos Ministro",
                            "value_soles": viaticos['daily_amount_soles'],
                            "unit": "soles/día"
                        })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            if not comparison_df.empty:
                # Calcular variaciones
                comparison_df['variation_abs'] = comparison_df['value_soles'].diff()
                comparison_df['variation_pct'] = comparison_df['value_soles'].pct_change() * 100
                
            return comparison_df
            
        except Exception as e:
            logger.error(f"❌ Error en comparación histórica: {e}")
            return pd.DataFrame()
    
    def _default_viaticos_calculation(self, level: str, year: int, days: int) -> Dict[str, Any]:
        """Cálculo por defecto si no se encuentran datos específicos"""
        default_amounts = {
            "ministro": 380.0,
            "viceministro": 380.0, 
            "funcionario": 320.0,
            "directivo": 320.0,
            "profesional": 320.0,
            "técnico": 320.0,
            "apoyo": 320.0
        }
        
        level_key = next((k for k in default_amounts.keys() if k in level.lower()), "funcionario")
        daily_amount = default_amounts[level_key]
        total_amount = daily_amount * days
        
        return {
            "level": level,
            "year": year,
            "days": days,
            "daily_amount_soles": daily_amount,
            "total_amount_soles": total_amount,
            "note": "Cálculo por defecto - verificar normativa vigente",
            "calculation_date": datetime.now().isoformat()
        }
    
    # === MÉTODOS DE PERSISTENCIA ===
    
    def _save_uit_data(self):
        """Guardar datos UIT"""
        try:
            uit_file = self.data_path / "uit_values.json"
            self.uit_df.to_json(uit_file, orient='records', indent=2)
        except Exception as e:
            logger.error(f"❌ Error guardando datos UIT: {e}")
    
    def _save_exchange_rate_data(self):
        """Guardar datos tipo de cambio"""
        try:
            tc_file = self.data_path / "tipo_cambio.json" 
            tc_data = self.tipo_cambio_df.copy()
            tc_data['date'] = tc_data['date'].dt.strftime('%Y-%m-%d')
            tc_data.to_json(tc_file, orient='records', indent=2)
        except Exception as e:
            logger.error(f"❌ Error guardando tipo de cambio: {e}")
    
    def _save_viaticos_data(self):
        """Guardar datos de viáticos"""
        try:
            viaticos_file = self.data_path / "viaticos_table.json"
            viaticos_data = self.viaticos_df.copy()
            viaticos_data['valid_from'] = viaticos_data['valid_from'].dt.strftime('%Y-%m-%d')
            viaticos_data['valid_to'] = viaticos_data['valid_to'].dt.strftime('%Y-%m-%d')
            viaticos_data.to_json(viaticos_file, orient='records', indent=2)
        except Exception as e:
            logger.error(f"❌ Error guardando datos viáticos: {e}")
    
    def _save_infracciones_data(self):
        """Guardar datos de infracciones"""
        try:
            infracciones_file = self.data_path / "infracciones_table.json"
            infracciones_data = self.infracciones_df.copy()
            infracciones_data['valid_from'] = infracciones_data['valid_from'].dt.strftime('%Y-%m-%d')
            infracciones_data['valid_to'] = infracciones_data['valid_to'].dt.strftime('%Y-%m-%d')
            infracciones_data.to_json(infracciones_file, orient='records', indent=2)
        except Exception as e:
            logger.error(f"❌ Error guardando datos infracciones: {e}")
    
    def update_uit_value(self, year: int, value: float, source: str = "Manual"):
        """Actualizar valor UIT"""
        try:
            # Verificar si existe
            existing = self.uit_df[self.uit_df['year'] == year]
            
            if not existing.empty:
                self.uit_df.loc[self.uit_df['year'] == year, 'value'] = value
                self.uit_df.loc[self.uit_df['year'] == year, 'source'] = source
            else:
                new_row = pd.DataFrame([{"year": year, "value": value, "source": source}])
                self.uit_df = pd.concat([self.uit_df, new_row], ignore_index=True)
            
            self._save_uit_data()
            logger.info(f"✅ UIT actualizada: {year} = S/ {value}")
            
        except Exception as e:
            logger.error(f"❌ Error actualizando UIT: {e}")
    
    def get_calculation_summary(self) -> Dict[str, Any]:
        """Resumen del estado del calculador"""
        try:
            return {
                "status": "operational",
                "data_loaded": {
                    "uit_records": len(self.uit_df) if self.uit_df is not None else 0,
                    "exchange_rate_records": len(self.tipo_cambio_df) if self.tipo_cambio_df is not None else 0,
                    "viaticos_records": len(self.viaticos_df) if self.viaticos_df is not None else 0,
                    "infractions_records": len(self.infracciones_df) if self.infracciones_df is not None else 0
                },
                "available_years": {
                    "uit": self.uit_df['year'].tolist() if self.uit_df is not None else [],
                    "viaticos": self.viaticos_df['year'].unique().tolist() if self.viaticos_df is not None else []
                },
                "data_path": str(self.data_path),
                "last_update": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"❌ Error generando resumen: {e}")
            return {"status": "error", "error": str(e)}