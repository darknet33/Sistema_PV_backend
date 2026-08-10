from sqlalchemy.orm import Session
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from app.reports.common import build_header, get_empresa, empresa_colors, make_canvasmaker, get_logo_header_info

def generar_comprobante_venta(db: Session, venta_id: int):
    from app.models.venta import Venta
    from app.models.venta_detalle import VentaDetalle
    from app.models.cliente import Cliente
    from app.models.comprobante import Comprobante
    from app.models.estado import Estado
    from app.models.producto import Producto
    from app.models.categoria import Categoria

    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        return None

    cliente = db.query(Cliente).filter(Cliente.id == venta.cliente_id).first()
    comprobante = db.query(Comprobante).filter(Comprobante.id == venta.comprobante_id).first()
    estado = db.query(Estado).filter(Estado.id == venta.estado_id).first()
    detalles = db.query(VentaDetalle).filter(VentaDetalle.venta_id == venta_id).all()

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

    styles.add(ParagraphStyle(name='RightAlign', parent=styles['Normal'], alignment=2))

    elements.extend(build_header(db, "Comprobante de Venta"))

    info_data = [
        [f"Venta N°: {venta.id}", f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}"],
        [f"Cliente: {cliente.nombre if cliente else '-'}", ""],
        [f"Comprobante: {comprobante.nombre if comprobante else '-'} {venta.num_comprobante or ''}", ""],
        [f"Estado: {estado.nombre if estado else '-'}", f"Impuesto: {venta.impuesto or 0}%  Descuento: {venta.descuento or 0}%"],
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
            Paragraph('#', styles['HeaderCell']),
            Paragraph('Código', styles['HeaderCell']),
            Paragraph('Producto', styles['HeaderCell']),
            Paragraph('Cant.', styles['HeaderCell']),
            Paragraph('Precio (Bs.)', styles['HeaderCell']),
            Paragraph('Subtotal (Bs.)', styles['HeaderCell']),
        ]
    ]
    subtotal_total = 0
    for i, d in enumerate(detalles, start=1):
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        cat_nombre = ''
        if prod:
            cat = db.query(Categoria).filter(Categoria.id == prod.categoria_id).first()
            cat_nombre = cat.nombre if cat else ''
        prod_nombre = f"{cat_nombre} - {prod.descripcion}" if cat_nombre and prod else (prod.descripcion if prod else '-')
        subtotal = d.cantidad * d.precio
        subtotal_total += subtotal
        data.append([
            Paragraph(str(i), styles['CellCenter']),
            Paragraph(prod.codigo if prod else '-', styles['CellCenter']),
            Paragraph(prod_nombre, styles['CellWrap']),
            Paragraph(str(d.cantidad), styles['CellCenter']),
            Paragraph(f"{d.precio:.2f}", styles['CellRight']),
            Paragraph(f"{subtotal:.2f}", styles['CellRight']),
        ])

    impuesto_monto = subtotal_total * (venta.impuesto or 0) / 100
    descuento_monto = subtotal_total * (venta.descuento or 0) / 100
    total = subtotal_total + impuesto_monto - descuento_monto

    data.append([
        Paragraph('', styles['CellCenter']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellCenter']),
        Paragraph('SUBTOTAL:', styles['CellRight']),
        Paragraph(f"Bs. {subtotal_total:.2f}", styles['CellRight']),
    ])

    if (venta.impuesto or 0) > 0:
        data.append([
            Paragraph('', styles['CellCenter']),
            Paragraph('', styles['CellWrap']),
            Paragraph('', styles['CellWrap']),
            Paragraph('', styles['CellCenter']),
            Paragraph(f'IMP. ({venta.impuesto}%):', styles['CellRight']),
            Paragraph(f"Bs. {impuesto_monto:.2f}", styles['CellRight']),
        ])

    if (venta.descuento or 0) > 0:
        data.append([
            Paragraph('', styles['CellCenter']),
            Paragraph('', styles['CellWrap']),
            Paragraph('', styles['CellWrap']),
            Paragraph('', styles['CellCenter']),
            Paragraph(f'DESC. ({venta.descuento}%):', styles['CellRight']),
            Paragraph(f"- Bs. {descuento_monto:.2f}", styles['CellRight']),
        ])

    data.append([
        Paragraph('', styles['CellCenter']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellCenter']),
        Paragraph('TOTAL:', styles['CellRight']),
        Paragraph(f"Bs. {total:.2f}", styles['CellRight']),
    ])

    primary, secondary = empresa_colors(db)

    table = Table(data, colWidths=[0.4*inch, 0.8*inch, 2.6*inch, 0.6*inch, 1.0*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary),
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
    doc.build(elements, canvasmaker=make_canvasmaker(get_empresa(db), logo_path, logo_h))
    buffer.seek(0)
    return buffer
