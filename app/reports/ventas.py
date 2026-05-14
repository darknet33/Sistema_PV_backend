from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def generar_reporte_ventas(db: Session, fecha_inicio: datetime, fecha_fin: datetime,
                           cliente_text: Optional[str] = None, estado_id: Optional[int] = None):
    from app.models.venta import Venta
    from app.models.cliente import Cliente
    from app.models.comprobante import Comprobante
    from app.models.estado import Estado

    query = db.query(Venta, Cliente, Comprobante, Estado)\
        .join(Cliente, Venta.cliente_id == Cliente.id)\
        .join(Comprobante, Venta.comprobante_id == Comprobante.id)\
        .join(Estado, Venta.estado_id == Estado.id)\
        .filter(Venta.fecha.between(fecha_inicio, fecha_fin))

    if cliente_text:
        query = query.filter(Cliente.nombre.ilike(f'%{cliente_text}%'))
    if estado_id:
        query = query.filter(Venta.estado_id == estado_id)

    ventas = query.order_by(Venta.fecha.desc()).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Reporte de Ventas", styles['Title']))
    elements.append(Paragraph(f"Período: {fecha_inicio.date()} al {fecha_fin.date()}", styles['Normal']))
    elements.append(Spacer(1, 20))

    data = [['ID', 'Fecha', 'Cliente', 'Comprobante', 'Estado', 'Total']]

    total_general = 0
    for v, c, comp, e in ventas:
        total = v.total if v.total else 0
        data.append([str(v.id), str(v.fecha.date()), c.nombre,
                    f"{comp.nombre} {v.num_comprobante}", e.nombre, f"{total:.2f}"])
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
