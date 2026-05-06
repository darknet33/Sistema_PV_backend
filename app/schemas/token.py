from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class ModuloItem(BaseModel):
    id: int
    nombre: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: dict
    modulos: List[ModuloItem]
