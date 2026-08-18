from sqlalchemy.orm import Session
import io
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from app.reports.common import build_header, get_empresa, empresa_colors, make_canvasmaker, get_logo_header_info

def generar_pdf_nota_entrega(db: Session, nota_id: int):
    from app.models.nota_entrega import NotaEntrega, NotaEntregaDetalle
    from app.models.venta import Venta
    from app.models.cliente import Cliente
    from app.models.comprobante import Comprobante
    from app.models.producto import Producto
    from app.models.categoria import Categoria

    nota = db.query(NotaEntrega).filter(NotaEntrega.id == nota_id).first()
    if not nota:
        return None

    venta = db.query(Venta).filter(Venta.id == nota.venta_id).first()
    cliente = db.query(Cliente).filter(Cliente.id == venta.cliente_id).first() if venta else None
    comprobante = db.query(Comprobante).filter(Comprobante.id == venta.comprobante_id).first() if venta else None
    detalles = db.query(NotaEntregaDetalle).filter(NotaEntregaDetalle.nota_entrega_id == nota_id).all()

    buffer = io.BytesIO()
    logo_path, logo_h = get_logo_header_info(db)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
        bottomMargin=1.1 * inch,
        topMargin=(logo_h + 0.4 * inch) if logo_h else 0.8 * inch,
    )
    styles = getSampleStyleSheet()
    elements = []

    elements.extend(build_header(db, "NOTA DE ENTREGA"))

    primary, secondary = empresa_colors(db)

    styles.add(ParagraphStyle(name='InfoCell', parent=styles['Normal'], fontSize=10, leading=13))
    styles.add(ParagraphStyle(name='NumComp', parent=styles['Normal'], fontSize=13, leading=16, textColor=secondary, fontName='Helvetica-Bold', alignment=2))
    styles.add(ParagraphStyle(name='CellWrap', parent=styles['Normal'], fontSize=9, leading=12, wordWrap='CJK'))
    styles.add(ParagraphStyle(name='CellCenter', parent=styles['Normal'], fontSize=9, leading=12, alignment=1))
    styles.add(ParagraphStyle(name='CellRight', parent=styles['Normal'], fontSize=9, leading=12, alignment=2))
    styles.add(ParagraphStyle(name='HeaderCell', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.white, fontName='Helvetica-Bold', alignment=1))
    styles.add(ParagraphStyle(name='FirmaTitle', parent=styles['Normal'], fontSize=11, leading=14, fontName='Helvetica-Bold', alignment=1, textColor=secondary))
    styles.add(ParagraphStyle(name='FirmaBody', parent=styles['Normal'], fontSize=10, leading=15))

    def _esc(val):
        return escape(str(val)) if val not in (None, "") else "-"

    num_para = Paragraph(f"N°: {_esc(nota.numero)}", styles['NumComp'])
    num_wrap = Table([[num_para]], colWidths=[6.3 * inch])
    num_wrap.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
    ]))
    elements.append(num_wrap)
    elements.append(Spacer(1, 8))

    num_venta = f"{comprobante.nombre} {venta.num_comprobante}" if comprobante and venta and venta.num_comprobante else (str(venta.id) if venta else '-')

    info_data = [
        [Paragraph(f"<b>Cliente:</b> {_esc(cliente.nombre if cliente else '-')}", styles['InfoCell']),
         Paragraph(f"<b>Fecha:</b> {_esc(nota.fecha.strftime('%d/%m/%Y %H:%M'))}", styles['InfoCell'])],
        [Paragraph(f"<b>NIT:</b> {_esc(cliente.nit if cliente else '-')}", styles['InfoCell']),
         Paragraph(f"<b>Venta N°:</b> {_esc(num_venta)}", styles['InfoCell'])],
        [Paragraph(f"<b>Dirección:</b> {_esc(cliente.direccion if cliente else '-')}", styles['InfoCell']),
         Paragraph('', styles['InfoCell'])],
    ]
    info_table = Table(info_data, colWidths=[3.5 * inch, 3.5 * inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 18))

    data = [
        [
            Paragraph('#', styles['HeaderCell']),
            Paragraph('Código', styles['HeaderCell']),
            Paragraph('Producto', styles['HeaderCell']),
            Paragraph('Cant.', styles['HeaderCell']),
        ]
    ]
    total_cantidad = 0
    for i, d in enumerate(detalles, start=1):
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        cat_nombre = ''
        if prod:
            cat = db.query(Categoria).filter(Categoria.id == prod.categoria_id).first()
            cat_nombre = cat.nombre if cat else ''
        prod_nombre = f"{cat_nombre} - {prod.descripcion}" if cat_nombre and prod else (prod.descripcion if prod else '-')
        total_cantidad += d.cantidad
        data.append([
            Paragraph(str(i), styles['CellCenter']),
            Paragraph(escape(prod.codigo) if prod else '-', styles['CellCenter']),
            Paragraph(escape(prod_nombre), styles['CellWrap']),
            Paragraph(str(d.cantidad), styles['CellCenter']),
        ])

    data.append([
        Paragraph('', styles['CellCenter']),
        Paragraph('', styles['CellWrap']),
        Paragraph('TOTAL DE CANTIDADES A ENTREGAR', styles['CellRight']),
        Paragraph(str(total_cantidad), styles['CellRight']),
    ])

    table = Table(data, colWidths=[0.4 * inch, 0.9 * inch, 4.6 * inch, 0.7 * inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('LINEBELOW', (2, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (2, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (2, -1), (-1, -1), 10),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 22))

    def firma_block(titulo, nombre, carnet):
        inner = Table([
            [Paragraph(titulo, styles['FirmaTitle'])],
            [Spacer(1, 6)],
            [Paragraph(f"Nombre: {_esc(nombre)}", styles['FirmaBody'])],
            [Paragraph(f"Carnet de identidad: {_esc(carnet)}", styles['FirmaBody'])],
            [Spacer(1, 22)],
            [Paragraph('_' * 46, styles['FirmaBody'])],
            [Paragraph('Firma', styles['FirmaBody'])],
        ], colWidths=[3.15 * inch])
        inner.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('LEFTPADDING', (0, 0), (-1, -1), 8),
            ('RIGHTPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('BOX', (0, 0), (-1, -1), 0.6, colors.HexColor('#cccccc')),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
        ]))
        return inner

    firma_table = Table(
        [[firma_block("ENTREGUE CONFORME", nota.entregue_nombre, nota.entregue_carnet),
          firma_block("RECIBÍ CONFORME", nota.recibi_nombre, nota.recibi_carnet)]],
        colWidths=[3.5 * inch, 3.5 * inch],
    )
    firma_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(firma_table)

    doc.build(elements, canvasmaker=make_canvasmaker(get_empresa(db), logo_path, logo_h))
    buffer.seek(0)
    return buffer
