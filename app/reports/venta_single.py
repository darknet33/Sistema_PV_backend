from sqlalchemy.orm import Session, selectinload
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

    venta = db.query(Venta).filter(Venta.id == venta_id).first()
    if not venta:
        return None

    cliente = db.query(Cliente).filter(Cliente.id == venta.cliente_id).first()
    comprobante = db.query(Comprobante).filter(Comprobante.id == venta.comprobante_id).first()
    estado = db.query(Estado).filter(Estado.id == venta.estado_id).first()
    detalles = db.query(VentaDetalle).options(
        selectinload(VentaDetalle.producto).selectinload(Producto.categoria)
    ).filter(VentaDetalle.venta_id == venta_id).all()

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

    titulo = (comprobante.nombre.upper() if comprobante else 'Comprobante de Venta')
    elements.extend(build_header(db, titulo))

    primary, secondary = empresa_colors(db)

    num_comprobante = venta.num_comprobante or str(venta.id)
    styles.add(ParagraphStyle(name='NumComp', parent=styles['Normal'], fontSize=13, leading=16, textColor=secondary, fontName='Helvetica-Bold', alignment=2))
    num_para = Paragraph(f"N° de Comprobante: {num_comprobante}", styles['NumComp'])
    num_wrap = Table([[num_para]], colWidths=[6 * inch])
    num_wrap.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(num_wrap)
    elements.append(Spacer(1, 8))

    info_data = [
        [f"Venta N°: {venta.id}", f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}"],
        [f"Cliente: {cliente.nombre if cliente else '-'}", ""],
        [f"Estado: {estado.nombre if estado else '-'}", (f"Incluye IVA {venta.impuesto}%" if (venta.impuesto or 0) > 0 else "")],
    ]
    if (venta.it or 0) > 0:
        info_data[2][1] += f" + IT {venta.it}%"
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
        prod = d.producto
        cat_nombre = ""
        if prod and prod.categoria:
            cat_nombre = prod.categoria.nombre
        prod_nombre = f"{cat_nombre} - {prod.descripcion} - {prod.marca}" + (f" - {prod.procedencia}" if prod.procedencia else "") if cat_nombre and prod else (prod.descripcion if prod else '-')
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
    it_monto = subtotal_total * (venta.it or 0) / 100
    descuento_monto = subtotal_total * (venta.descuento or 0) / 100
    total = subtotal_total + impuesto_monto + it_monto - descuento_monto

    table = Table(data, colWidths=[0.4*inch, 0.8*inch, 2.6*inch, 0.6*inch, 1.0*inch, 1.0*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 16))

    styles.add(ParagraphStyle(name='TotTitle', parent=styles['Normal'], fontSize=10, leading=14, fontName='Helvetica-Bold', textColor=secondary))
    styles.add(ParagraphStyle(name='TotLabel', parent=styles['Normal'], fontSize=10, leading=14, alignment=2))
    styles.add(ParagraphStyle(name='TotValue', parent=styles['Normal'], fontSize=10, leading=14, alignment=2))
    styles.add(ParagraphStyle(name='TotTotal', parent=styles['Normal'], fontSize=12, leading=16, fontName='Helvetica-Bold', alignment=2, textColor=colors.white))

    tot_rows = [
        [Paragraph('SUBTOTAL', styles['TotLabel']), Paragraph(f"Bs. {subtotal_total:.2f}", styles['TotValue'])],
    ]
    if (venta.impuesto or 0) > 0:
        tot_rows.append([
            Paragraph(f'IVA ({venta.impuesto}%)', styles['TotLabel']),
            Paragraph(f"Bs. {impuesto_monto:.2f}", styles['TotValue']),
        ])
    if (venta.it or 0) > 0:
        tot_rows.append([
            Paragraph(f'IT ({venta.it}%)', styles['TotLabel']),
            Paragraph(f"Bs. {it_monto:.2f}", styles['TotValue']),
        ])
    if (venta.descuento or 0) > 0:
        tot_rows.append([
            Paragraph(f'DESCUENTO ({venta.descuento}%)', styles['TotLabel']),
            Paragraph(f"- Bs. {descuento_monto:.2f}", styles['TotValue']),
        ])
    tot_rows.append([
        Paragraph('TOTAL', styles['TotTotal']),
        Paragraph(f"Bs. {total:.2f}", styles['TotTotal']),
    ])

    totals_table = Table(tot_rows, colWidths=[2.2*inch, 1.6*inch])
    totals_table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, colors.grey),
        ('BACKGROUND', (0, -1), (-1, -1), secondary),
        ('ROWBACKGROUNDS', (0, 0), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
    ]))

    total_wrap = Table([[Paragraph('', styles['TotLabel']), totals_table]], colWidths=[2.2*inch, 3.8*inch])
    total_wrap.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(Paragraph('Resumen', styles['TotTitle']))
    elements.append(Spacer(1, 4))
    elements.append(total_wrap)
    doc.build(elements, canvasmaker=make_canvasmaker(get_empresa(db), logo_path, logo_h))
    buffer.seek(0)
    return buffer
