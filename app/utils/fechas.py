from datetime import datetime
from typing import Optional

def formatear_fecha(fecha: datetime, formato: str = "%Y-%m-%d") -> str:
    if not fecha:
        return ""
    return fecha.strftime(formato)

def parse_fecha(fecha_str: str, formato: str = "%Y-%m-%d") -> Optional[datetime]:
    if not fecha_str:
        return None
    return datetime.strptime(fecha_str, formato)

def obtener_inicio_dia(fecha: datetime) -> datetime:
    return fecha.replace(hour=0, minute=0, second=0, microsecond=0)

def obtener_fin_dia(fecha: datetime) -> datetime:
    return fecha.replace(hour=23, minute=59, second=59, microsecond=999999)
