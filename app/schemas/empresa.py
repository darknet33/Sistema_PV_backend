from pydantic import BaseModel, field_validator
from typing import Optional


def _normalize_color(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return v
    low = v.lower()
    if low.startswith("rgb"):
        try:
            inner = low[low.index("(") + 1 : low.index(")")]
            parts = [p.strip() for p in inner.split(",")]
            r, g, b = (int(parts[i]) for i in range(3))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            pass
    if v.startswith("#") and len(v) == 9:
        return v[:7]
    if v.startswith("#") and len(v) == 4:
        return f"#{v[1]}{v[1]}{v[2]}{v[2]}{v[3]}{v[3]}"
    return v[:9]

class EmpresaBase(BaseModel):
    nombre: str = ""
    razon_social: str = ""
    nit: str = ""
    telefono: str = ""
    correo: str = ""
    direccion: str = ""
    ciudad: str = ""
    color_principal: str = "#1677ff"
    color_secundario: str = "#001529"

    @field_validator("color_principal", "color_secundario")
    @classmethod
    def _validate_color(cls, value: str) -> str:
        return _normalize_color(value)

class EmpresaUpdate(EmpresaBase):
    pass

class EmpresaResponse(EmpresaBase):
    id: int
    logo: Optional[str] = None
    imagen_encabezado: Optional[str] = None
    imagen_pie: Optional[str] = None

    class Config:
        from_attributes = True
