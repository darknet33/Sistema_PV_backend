from sqlalchemy.orm import Session
import io
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from app.reports.common import build_header, get_empresa, empresa_colors, make_canvasmaker, get_logo_header_info

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _imagen_escalada(url, max_w, max_h):
    """Devuelve una imagen Reportlab escalada (mantiene proporción) o None."""
    if not url:
        return None
    try:
        path = BASE_DIR / url.lstrip("/")
        if not path.exists():
            return None
        from PIL import Image as PILImage
        with PILImage.open(str(path)) as img:
            w, h = img.size
        if w <= 0 or h <= 0:
            return None
        escala = min(max_w / w, max_h / h)
        return Image(str(path), width=w * escala, height=h * escala)
    except Exception:
        return None


def generar_pdf_cotizacion(db: Session, cotizacion_id: int):
    from app.models.cotizacion import Cotizacion
    from app.models.cotizacion_detalle import CotizacionDetalle
    from app.models.producto import Producto
    from app.models.categoria import Categoria
    from app.models.usuario import Usuario

    cot = db.query(Cotizacion).filter(Cotizacion.id == cotizacion_id).first()
    if not cot:
        return None

    detalles = db.query(CotizacionDetalle).filter(CotizacionDetalle.cotizacion_id == cotizacion_id).all()
    usuario = db.query(Usuario).filter(Usuario.id == cot.usuario_id).first()

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

    elements.extend(build_header(db, "COTIZACIÓN"))

    styles.add(ParagraphStyle(name='InfoCell', parent=styles['Normal'], fontSize=10, leading=13))
    styles.add(ParagraphStyle(name='CellWrap', parent=styles['Normal'], fontSize=9, leading=12, wordWrap='CJK'))
    styles.add(ParagraphStyle(name='CellCenter', parent=styles['Normal'], fontSize=9, leading=12, alignment=1))
    styles.add(ParagraphStyle(name='CellRight', parent=styles['Normal'], fontSize=9, leading=12, alignment=2))
    styles.add(ParagraphStyle(name='HeaderCell', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.white, fontName='Helvetica-Bold', alignment=1))
    styles.add(ParagraphStyle(name='TermTitle', parent=styles['Normal'], fontSize=10, leading=13, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='TermBody', parent=styles['Normal'], fontSize=9, leading=12, wordWrap='CJK'))

    estado = cot.estado or ""
    con_factura = "Sí" if cot.con_factura else "No"

    def _esc(val):
        return escape(str(val)) if val not in (None, "") else "-"

    info_data = [
        [Paragraph(f"<b>N°:</b> {_esc(cot.numero)}", styles['InfoCell']),
         Paragraph(f"<b>Fecha:</b> {_esc(cot.fecha.strftime('%d/%m/%Y %H:%M'))}", styles['InfoCell'])],
        [Paragraph(f"<b>Cliente:</b> {_esc(cot.cliente_razon_social)}", styles['InfoCell']),
         Paragraph(f"<b>Vence:</b> {_esc(cot.fecha_vencimiento.strftime('%d/%m/%Y'))}", styles['InfoCell'])],
        [Paragraph(f"<b>NIT:</b> {_esc(cot.cliente_nit)}", styles['InfoCell']),
         Paragraph(f"<b>Estado:</b> {_esc(estado)}", styles['InfoCell'])],
        [Paragraph(f"<b>Celular:</b> {_esc(cot.cliente_celular)}", styles['InfoCell']),
         Paragraph(f"<b>Con factura:</b> {_esc(con_factura)}", styles['InfoCell'])],
        [Paragraph(f"<b>Dirección:</b> {_esc(cot.cliente_direccion)}", styles['InfoCell']),
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
    elements.append(Spacer(1, 16))

    incluir_imagenes = bool(cot.incluir_imagenes)

    headers = [
        Paragraph('#', styles['HeaderCell']),
        Paragraph('Código', styles['HeaderCell']),
        Paragraph('Producto', styles['HeaderCell']),
        Paragraph('Cant.', styles['HeaderCell']),
        Paragraph('Costo (Bs.)', styles['HeaderCell']),
        Paragraph('P. Venta (Bs.)', styles['HeaderCell']),
        Paragraph('Subtotal (Bs.)', styles['HeaderCell']),
    ]

    data = [headers]

    def build_producto_cell(prod, prod_nombre):
        if not (incluir_imagenes and prod):
            return Paragraph(escape(prod_nombre), styles['CellWrap'])
        img = _imagen_escalada(prod.imagen, 0.7 * inch, 0.6 * inch)
        if not img:
            return Paragraph(escape(prod_nombre), styles['CellWrap'])
        inner = Table(
            [[img, Paragraph(escape(prod_nombre), styles['CellWrap'])]],
            colWidths=[0.75 * inch, 1.1 * inch],
        )
        inner.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 1),
            ('RIGHTPADDING', (0, 0), (-1, -1), 1),
            ('TOPPADDING', (0, 0), (-1, -1), 1),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 1),
            ('BOX', (0, 0), (-1, -1), 0.3, colors.grey),
        ]))
        return inner

    for i, d in enumerate(detalles, start=1):
        prod = db.query(Producto).filter(Producto.id == d.producto_id).first()
        cat_nombre = ''
        if prod:
            cat = db.query(Categoria).filter(Categoria.id == prod.categoria_id).first()
            cat_nombre = cat.nombre if cat else ''
        prod_nombre = f"{cat_nombre} - {prod.descripcion}" if cat_nombre and prod else (prod.descripcion if prod else '-')
        subtotal = d.cantidad * d.precio_venta

        row = [
            Paragraph(str(i), styles['CellCenter']),
            Paragraph(escape(prod.codigo) if prod else '-', styles['CellCenter']),
            build_producto_cell(prod, prod_nombre),
            Paragraph(str(d.cantidad), styles['CellCenter']),
            Paragraph(f"{d.costo:.2f}", styles['CellRight']),
            Paragraph(f"{d.precio_venta:.2f}", styles['CellRight']),
            Paragraph(f"{subtotal:.2f}", styles['CellRight']),
        ]
        data.append(row)

    data.append([
        Paragraph('', styles['CellCenter']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellCenter']),
        Paragraph('', styles['CellRight']),
        Paragraph('SUBTOTAL:', styles['CellRight']),
        Paragraph(f"Bs. {cot.subtotal:.2f}", styles['CellRight']),
    ])

    if cot.con_factura:
        data.append([
            Paragraph('', styles['CellCenter']),
            Paragraph('', styles['CellWrap']),
            Paragraph('', styles['CellWrap']),
            Paragraph('', styles['CellCenter']),
            Paragraph('', styles['CellRight']),
            Paragraph('IVA (13%):', styles['CellRight']),
            Paragraph(f"Bs. {cot.iva:.2f}", styles['CellRight']),
        ])

    data.append([
        Paragraph('', styles['CellCenter']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellWrap']),
        Paragraph('', styles['CellCenter']),
        Paragraph('', styles['CellRight']),
        Paragraph('TOTAL:', styles['CellRight']),
        Paragraph(f"Bs. {cot.total:.2f}", styles['CellRight']),
    ])

    primary, secondary = empresa_colors(db)

    col_widths = [0.35 * inch, 0.6 * inch, 2.2 * inch, 0.45 * inch, 0.7 * inch, 0.8 * inch, 0.85 * inch]

    table = Table(data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (1, 1), (1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
        ('LINEBELOW', (5, -1), (-1, -1), 1, colors.black),
        ('FONTNAME', (5, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (5, -1), (-1, -1), 11),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f0f0')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f9f9f9')]),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 16))

    if cot.modalidad_pago:
        elements.append(Paragraph(f"<b>Modalidad de pago:</b> {escape(cot.modalidad_pago)}", styles['TermBody']))
    elements.append(Paragraph(f"<b>Validez de la oferta:</b> {cot.validez_dias} día(s) - Vence el {cot.fecha_vencimiento.strftime('%d/%m/%Y')}", styles['TermBody']))
    if cot.terminos_condiciones:
        elements.append(Spacer(1, 6))
        elements.append(Paragraph("Términos y condiciones", styles['TermTitle']))
        elements.append(Spacer(1, 4))
        for linea in str(cot.terminos_condiciones).splitlines():
            linea = linea.strip()
            if linea:
                elements.append(Paragraph(escape(linea), styles['TermBody']))
                elements.append(Spacer(1, 2))

    if usuario:
        nombre_completo = f"{usuario.nombres} {usuario.apellidos}".strip()
        if not nombre_completo:
            nombre_completo = usuario.username
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Generado por: {escape(nombre_completo)}", styles['TermBody']))

    doc.build(elements, canvasmaker=make_canvasmaker(get_empresa(db), logo_path, logo_h))
    buffer.seek(0)
    return buffer
