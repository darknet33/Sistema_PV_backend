from sqlalchemy.orm import Session
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from app.reports.common import build_header, get_empresa, empresa_colors, make_canvasmaker, get_logo_header_info

def generar_kardex(db: Session, producto_id: int, fecha_inicio: datetime, fecha_fin: datetime):
    from app.models.producto import Producto
    from app.models.compra import Compra
    from app.models.compra_detalle import CompraDetalle
    from app.models.venta import Venta
    from app.models.venta_detalle import VentaDetalle
    from app.models.comprobante import Comprobante
    
    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    
    entradas = db.query(
        Compra.fecha,
        CompraDetalle.cantidad,
        CompraDetalle.costo,
        Comprobante.nombre.label('comprobante'),
        Compra.num_comprobante
    ).join(CompraDetalle, Compra.id == CompraDetalle.compra_id)\
     .join(Comprobante, Compra.comprobante_id == Comprobante.id)\
     .filter(CompraDetalle.producto_id == producto_id,
             Compra.fecha.between(fecha_inicio, fecha_fin)).all()
    
    salidas = db.query(
        Venta.fecha,
        VentaDetalle.cantidad,
        VentaDetalle.precio,
        Comprobante.nombre.label('comprobante'),
        Venta.num_comprobante
    ).join(VentaDetalle, Venta.id == VentaDetalle.venta_id)\
     .join(Comprobante, Venta.comprobante_id == Comprobante.id)\
     .filter(VentaDetalle.producto_id == producto_id,
             Venta.fecha.between(fecha_inicio, fecha_fin)).all()
    
    buffer = io.BytesIO()
    logo_path, logo_h = get_logo_header_info(db)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        bottomMargin=1.1 * inch,
        topMargin=(logo_h + 0.4 * inch) if logo_h else 0.8 * inch,
    )
    styles = getSampleStyleSheet()
    elements = []
    
    elements.extend(build_header(db, f"Kardex - {producto.descripcion if producto else 'N/A'}"))
    elements.append(Paragraph(f"Código: {producto.codigo if producto else 'N/A'}", styles['Normal']))
    elements.append(Paragraph(f"Stock Actual: {producto.stock_actual if producto else 0}", styles['Normal']))
    elements.append(Paragraph(f"Período: {fecha_inicio.date()} al {fecha_fin.date()}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    data = [['Fecha', 'Tipo', 'Comprobante', 'Cantidad', 'Precio', 'Total']]
    
    saldo = producto.stock_inicial if producto else 0
    
    for e in entradas:
        total = e.cantidad * e.costo
        data.append([str(e.fecha), 'ENTRADA', f"{e.comprobante} {e.num_comprobante}", 
                    str(e.cantidad), str(e.costo), str(total)])
    
    for s in salidas:
        total = s.cantidad * s.precio
        data.append([str(s.fecha), 'SALIDA', f"{s.comprobante} {s.num_comprobante}", 
                    str(s.cantidad), str(s.precio), str(total)])
    
    primary, secondary = empresa_colors(db)

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))
    
    elements.append(table)
    doc.build(elements, canvasmaker=make_canvasmaker(get_empresa(db), logo_path, logo_h))

    buffer.seek(0)
    return buffer
