from pydantic import BaseModel

class RolModuloAssign(BaseModel):
    modulo_ids: list[int]

class RolModuloResponse(BaseModel):
    id: int
    rol_id: int
    modulo_id: int

    class Config:
        from_attributes = True
