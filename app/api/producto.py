from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
from openpyxl import Workbook, load_workbook
from jose import jwt
from app.database import get_db
from app.schemas.producto import ProductoCreate, ProductoUpdate, ProductoResponse
from app.crud.producto import get_productos, get_producto, get_producto_by_codigo, create_producto, update_producto, delete_producto
from app.models.producto import Producto
from app.models.categoria import Categoria
from app.models.usuario import Usuario
from app.auth import SECRET_KEY, ALGORITHM, oauth2_scheme

router = APIRouter()

@router.get("/", response_model=List[ProductoResponse])
def read_productos(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return get_productos(db, skip, limit)

@router.get("/export-xlsx")
def export_productos(db: Session = Depends(get_db)):
    productos = db.query(Producto).join(Categoria, isouter=True).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Productos"
    
    headers = ["Código", "Categoría", "Descripción", "Marca", "Peso", "Precio", "Stock Inicial", "Stock Actual", "Stock Mínimo", "Estado"]
    ws.append(headers)
    
    for p in productos:
        ws.append([
            p.codigo,
            p.categoria.nombre if p.categoria else "",
            p.descripcion,
            p.marca,
            float(p.peso),
            float(p.precio),
            p.stock_inicial,
            p.stock_actual,
            p.stock_minimo,
            "Activo" if p.activo else "Inactivo",
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="productos.xlsx"'}
    )

@router.post("/import-xlsx")
async def import_productos(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
):
    user = None
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username:
            user = db.query(Usuario).filter(Usuario.username == username).first()
    except Exception:
        pass
    
    usuario_id = user.id if user else None
    
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    content = await file.read()
    wb = load_workbook(BytesIO(content))
    ws = wb.active
    
    resultados = {"creados": 0, "actualizados": 0, "errores": []}
    
    for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        try:
            codigo, categoria_nombre, descripcion, marca, peso, precio, stock_inicial, stock_actual, stock_minimo, estado = row
            
            if not codigo or not descripcion or not marca:
                resultados["errores"].append(f"Fila {row_num}: Faltan campos obligatorios (codigo, descripcion, marca)")
                continue
            
            categoria = None
            if categoria_nombre:
                cat_nombre = str(categoria_nombre).strip()
                categoria = db.query(Categoria).filter(Categoria.nombre == cat_nombre).first()
                if not categoria:
                    categoria = Categoria(nombre=cat_nombre)
                    db.add(categoria)
                    db.flush()
            
            producto_existente = db.query(Producto).filter(Producto.codigo == str(codigo).strip()).first()
            
            if producto_existente:
                producto_existente.categoria_id = categoria.id if categoria else producto_existente.categoria_id
                producto_existente.descripcion = str(descripcion)
                producto_existente.marca = str(marca)
                producto_existente.peso = float(peso) if peso else 0
                producto_existente.precio = float(precio) if precio else 0
                producto_existente.stock_inicial = int(stock_inicial) if stock_inicial else 0
                producto_existente.stock_actual = int(stock_actual) if stock_actual else 0
                producto_existente.stock_minimo = int(stock_minimo) if stock_minimo else 0
                if estado:
                    producto_existente.activo = str(estado).strip().lower() == "activo"
                db.commit()
                resultados["actualizados"] += 1
            else:
                nuevo = Producto(
                    codigo=str(codigo).strip(),
                    categoria_id=categoria.id if categoria else None,
                    descripcion=str(descripcion),
                    marca=str(marca),
                    peso=float(peso) if peso else 0,
                    precio=float(precio) if precio else 0,
                    stock_inicial=int(stock_inicial) if stock_inicial else 0,
                    stock_actual=int(stock_actual) if stock_actual else 0,
                    stock_minimo=int(stock_minimo) if stock_minimo else 0,
                    activo=str(estado).strip().lower() == "activo" if estado else True,
                    usuario_id=usuario_id,
                )
                db.add(nuevo)
                db.commit()
                resultados["creados"] += 1
        except Exception as e:
            db.rollback()
            resultados["errores"].append(f"Fila {row_num}: {str(e)}")
    
    return resultados

@router.post("/delete-batch")
def delete_productos_batch(ids: List[int], db: Session = Depends(get_db)):
    if not ids:
        raise HTTPException(status_code=400, detail="No se proporcionaron IDs")
    count = db.query(Producto).filter(Producto.id.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return {"message": f"{count} productos eliminados", "count": count}

@router.delete("/all")
def delete_all_productos(db: Session = Depends(get_db)):
    count = db.query(Producto).delete(synchronize_session=False)
    db.commit()
    return {"message": f"Todos los productos eliminados ({count})", "count": count}

@router.get("/codigo/{codigo}", response_model=ProductoResponse)
def read_producto_by_codigo(codigo: str, db: Session = Depends(get_db)):
    db_producto = get_producto_by_codigo(db, codigo)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return db_producto

@router.get("/{producto_id}", response_model=ProductoResponse)
def read_producto(producto_id: int, db: Session = Depends(get_db)):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return db_producto

@router.post("/", response_model=ProductoResponse)
def create_producto_endpoint(producto: ProductoCreate, db: Session = Depends(get_db)):
    db_producto = get_producto_by_codigo(db, producto.codigo)
    if db_producto:
        raise HTTPException(status_code=400, detail="Codigo already registered")
    return create_producto(db, producto)

@router.put("/{producto_id}", response_model=ProductoResponse)
def update_producto_endpoint(producto_id: int, producto: ProductoUpdate, db: Session = Depends(get_db)):
    db_producto = update_producto(db, producto_id, producto)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return db_producto

@router.delete("/{producto_id}")
def delete_producto_endpoint(producto_id: int, db: Session = Depends(get_db)):
    db_producto = delete_producto(db, producto_id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return {"message": "Producto deleted"}

@router.patch("/{producto_id}/toggle-activo", response_model=ProductoResponse)
def toggle_producto_activo(producto_id: int, db: Session = Depends(get_db)):
    db_producto = get_producto(db, producto_id)
    if not db_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    db_producto.activo = not db_producto.activo
    db.commit()
    db.refresh(db_producto)
    return db_producto
