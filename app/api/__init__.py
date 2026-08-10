from fastapi import APIRouter
from app.api import usuario, rol, modulo, categoria, producto, proveedor, cliente, comprobante, estado, compra, venta, auth, reporte, configuracion, ws, empresa

api_router = APIRouter(prefix="/api")

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(usuario.router, prefix="/usuarios", tags=["Usuarios"])
api_router.include_router(rol.router, prefix="/roles", tags=["Roles"])
api_router.include_router(modulo.router, prefix="/modulos", tags=["Módulos"])
api_router.include_router(categoria.router, prefix="/categorias", tags=["Categorías"])
api_router.include_router(producto.router, prefix="/productos", tags=["Productos"])
api_router.include_router(proveedor.router, prefix="/proveedores", tags=["Proveedores"])
api_router.include_router(cliente.router, prefix="/clientes", tags=["Clientes"])
api_router.include_router(comprobante.router, prefix="/comprobantes", tags=["Comprobantes"])
api_router.include_router(estado.router, prefix="/estados", tags=["Estados"])
api_router.include_router(compra.router, prefix="/compras", tags=["Compras"])
api_router.include_router(venta.router, prefix="/ventas", tags=["Ventas"])
api_router.include_router(reporte.router, prefix="/reportes", tags=["Reportes"])
api_router.include_router(configuracion.router, prefix="/configuracion", tags=["Configuración"])
api_router.include_router(empresa.router, prefix="/empresa", tags=["Empresa"])
api_router.include_router(ws.router)
