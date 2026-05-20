from typing import Optional
from app.utils.excel import export_to_excel, import_from_excel
from app.utils.fechas import formatear_fecha, parse_fecha


def capitalizar(texto: Optional[str]) -> Optional[str]:
    if not texto:
        return texto
    return " ".join(palabra.capitalize() for palabra in texto.strip().split())
