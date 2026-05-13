from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generar_reporte_compras(db: Session, fecha_inicio: datetime, fecha_fin: datetime):
    from app.models.compra import Compra
    from app.models.proveedor import Proveedor
    from app.models.comprobante import Comprobante
    from app.models.estado import Estado
    
    fecha_fin = fecha_fin.replace(hour=23, minute=59, second=59)
    
    compras = db.query(Compra, Proveedor, Comprobante, Estado)\
        .join(Proveedor, Compra.proveedor_id == Proveedor.id)\
        .join(Comprobante, Compra.comprobante_id == Comprobante.id)\
        .join(Estado, Compra.estado_id == Estado.id)\
        .filter(Compra.fecha.between(fecha_inicio, fecha_fin))\
        .order_by(Compra.fecha.desc()).all()
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []
    
    elements.append(Paragraph("Reporte de Compras", styles['Title']))
    elements.append(Paragraph(f"Período: {fecha_inicio.date()} al {fecha_fin.date()}", styles['Normal']))
    elements.append(Spacer(1, 20))
    
    data = [['ID', 'Fecha', 'Proveedor', 'Comprobante', 'Estado', 'Total']]
    
    total_general = 0
    for c, p, comp, e in compras:
        total = c.total if c.total else 0
        data.append([str(c.id), str(c.fecha.date()), p.nombre, 
                    f"{comp.nombre} {c.num_comprobante}", e.nombre, f"{total:.2f}"])
        total_general += total
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
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
    elements.append(Spacer(1, 20))
    elements.append(Paragraph(f"Total General: {total_general:.2f}", styles['Heading2']))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer
