from sqlalchemy.orm import Session
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generar_comprobante_compra(db: Session, compra_id: int):
    from app.models.compra import Compra
    from app.models.compra_detalle import CompraDetalle
    from app.models.proveedor import Proveedor
    from app.models.comprobante import Comprobante
    from app.models.estado import Estado
    from app.models.producto import Producto
    from app.models.categoria import Categoria

    compra = db.query(Compra).filter(Compra.id == compra_id).first()
    if not compra:
        return None

    proveedor = db.query(Proveedor).filter(Proveedor.id == compra.proveedor_id).first()
    comprobante = db.query(Comprobante).filter(Comprobante.id == compra.comprobante_id).first()
    estado = db.query(Estado).filter(Estado.id == compra.estado_id).first()
    detalles = db.query(CompraDetalle).filter(CompraDetalle.compra_id == compra_id).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    styles.add(ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2))

    elements.append(Paragraph("Comprobante de Compra", styles['Title']))
    elements.append(Spacer(1, 12))

    info_data = [
        [f"Compra N°: {compra.id}", f"Fecha: {compra.fecha.strftime('%d/%m/%Y %H:%M')}"],
        [f"Proveedor: {proveedor.nombre if proveedor else '-'}", ""],
        [f"Comprobante: {comprobante.nombre if comprobante else '-'} {compra.num_comprobante or ''}", ""],
        [f"Estado: {estado.nombre if estado else '-'}", ""],
    ]
    info_table = Table(info_data, colWidths=[3*inch, 3*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 20))

    styles.add(ParagraphStyle(name='CellWrap', parent=styles['Normal'], fontSize=9, leading=12, wordWrap='CJK'))
    styles.add(ParagraphStyle(name='CellCenter', parent=styles['Normal'], fontSize=9, leading=12, alignment=1))
    styles.add(ParagraphStyle(name='CellRight', parent=styles['Normal'], fontSize=9, leading=12, alignment=2))
    styles.add(ParagraphStyle(name='HeaderCell', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.white, fontName='Helvetica-Bold', alignment=1))

    data = [
        [
            Paragraph('Código', styles['HeaderCell']),
            Paragraph('Producto', styles['HeaderCell']),
            Paragraph('Cant.', styles['HeaderCell']),
            Paragraph('Costo (Bs.)', styles['HeaderCell']),
            Paragraph('Subtotal (Bs.)', styles['HeaderCell']),
        ]
    ]
    total = 0
    for d in detalles:
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        cat_nombre = ''
        if prod:
            cat = db.query(Categoria).filter(Categoria.id == prod.categoria_id).first()
            cat_nombre = cat.nombre if cat else ''
        prod_nombre = f"{cat_nombre} - {prod.descripcion}" if cat_nombre and prod else (prod.descripcion if prod else '-')
        subtotal = d.cantidad * d.costo
        total += subtotal
        data.append([
            Paragraph(prod.codigo if prod else '-', styles['CellCenter']),
            Paragraph(prod_nombre, styles['CellWrap']),
            Paragraph(prod.marca if prod else '-', styles['CellWrap']),
            Paragraph(str(d.cantidad), styles['CellCenter']),
            Paragraph(f"{d.costo:.2f}", styles['CellRight']),
            Paragraph(f"{subtotal:.2f}", styles['CellRight']),
        ])

    data.append([
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellCenter']),
        Paragraph('TOTAL:', styles['CellRight']),
        Paragraph(f"{total:.2f}", styles['CellRight']),
    ])

    table = Table(data, colWidths=[0.9*inch, 2.8*inch, 0.7*inch, 1.0*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('LINEBELOW', (3, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (3, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (3, -1), (-1, -1), 11),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))

    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer
