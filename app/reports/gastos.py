from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from app.reports.common import build_header, get_empresa, empresa_colors, make_canvasmaker, get_logo_header_info

def generar_reporte_gastos(db: Session, fecha_inicio: datetime, fecha_fin: datetime,
                           categoria_id: Optional[int] = None, estado_id: Optional[int] = None):
    from app.models.gasto import Gasto
    from app.models.categoria_gasto import CategoriaGasto
    from app.models.estado import Estado

    query = db.query(Gasto, CategoriaGasto, Estado)\
        .join(CategoriaGasto, Gasto.categoria_gasto_id == CategoriaGasto.id)\
        .outerjoin(Estado, Gasto.estado_id == Estado.id)\
        .filter(Gasto.fecha.between(fecha_inicio, fecha_fin))

    if categoria_id:
        query = query.filter(Gasto.categoria_gasto_id == categoria_id)
    if estado_id:
        query = query.filter(Gasto.estado_id == estado_id)

    gastos = query.order_by(Gasto.fecha.desc()).all()

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

    elements.extend(build_header(db, "Reporte de Gastos"))
    elements.append(Paragraph(f"Período: {fecha_inicio.date()} al {fecha_fin.date()}", styles['Normal']))
    elements.append(Spacer(1, 20))

    data = [['ID', 'Fecha', 'Categoría', 'Descripción', 'Estado', 'Monto (Bs.)']]

    total_general = 0
    for g, cat, e in gastos:
        monto = g.monto if g.monto else 0
        anulados = e.nombre.upper() == 'ANULADO' if e and e.nombre else False
        if not anulados:
            total_general += monto
        data.append([str(g.id), str(g.fecha.date()), cat.nombre,
                    (g.descripcion or '')[:40], e.nombre if e else '', f"{monto:.2f}"])

    primary, secondary = empresa_colors(db)

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 1), (3, -1), 'LEFT'),
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
    elements.append(Paragraph(f"Total General: Bs. {total_general:.2f}", styles['Heading2']))

    doc.build(elements, canvasmaker=make_canvasmaker(get_empresa(db), logo_path, logo_h))
    buffer.seek(0)
    return buffer
