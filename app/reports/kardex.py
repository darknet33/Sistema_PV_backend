from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from app.reports.common import build_header, get_empresa, empresa_colors, make_canvasmaker, get_logo_header_info, BASE_DIR

def _sin_anuladas():
    from app.models.estado import Estado
    return func.upper(Estado.nombre) != 'ANULADO'

def _get_imagen_producto(url):
    """Devuelve (path, ancho_pts, alto_pts) para una miniatura, o (None, 0, 0)."""
    if not url:
        return None, 0, 0
    try:
        path = BASE_DIR / url.lstrip("/")
        if not path.exists():
            return None, 0, 0
        from PIL import Image as PILImage
        with PILImage.open(str(path)) as img:
            w, h = img.size
        if w <= 0 or h <= 0:
            return None, 0, 0
        width = 1.6 * inch
        return str(path), width, width * (h / w)
    except Exception:
        return None, 0, 0

def generar_kardex(db: Session, producto_id: int, fecha_inicio: datetime, fecha_fin: datetime):
    from app.models.producto import Producto
    from app.models.compra import Compra
    from app.models.compra_detalle import CompraDetalle
    from app.models.venta import Venta
    from app.models.venta_detalle import VentaDetalle
    from app.models.comprobante import Comprobante
    from app.models.estado import Estado

    producto = db.query(Producto).filter(Producto.id == producto_id).first()
    if not producto:
        return None

    entradas_q = db.query(
        Compra.fecha,
        CompraDetalle.cantidad,
        CompraDetalle.costo,
        Comprobante.nombre.label('comprobante'),
        Compra.num_comprobante
    ).join(CompraDetalle, Compra.id == CompraDetalle.compra_id)\
     .join(Comprobante, Compra.comprobante_id == Comprobante.id)\
     .join(Estado, Compra.estado_id == Estado.id)\
     .filter(CompraDetalle.producto_id == producto_id,
             _sin_anuladas())

    salidas_q = db.query(
        Venta.fecha,
        VentaDetalle.cantidad,
        VentaDetalle.precio,
        Comprobante.nombre.label('comprobante'),
        Venta.num_comprobante
    ).join(VentaDetalle, Venta.id == VentaDetalle.venta_id)\
     .join(Comprobante, Venta.comprobante_id == Comprobante.id)\
     .join(Estado, Venta.estado_id == Estado.id)\
     .filter(VentaDetalle.producto_id == producto_id,
             _sin_anuladas())

    entradas_previas = sum(e.cantidad for e in entradas_q.filter(Compra.fecha < fecha_inicio).all())
    salidas_previas = sum(s.cantidad for s in salidas_q.filter(Venta.fecha < fecha_inicio).all())
    saldo_inicial = producto.stock_inicial + entradas_previas - salidas_previas

    entradas = entradas_q.filter(Compra.fecha.between(fecha_inicio, fecha_fin)).all()
    salidas = salidas_q.filter(Venta.fecha.between(fecha_inicio, fecha_fin)).all()

    buffer = io.BytesIO()
    logo_path, logo_h = get_logo_header_info(db)
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        bottomMargin=1.1 * inch,
        topMargin=(logo_h + 0.4 * inch) if logo_h else 0.8 * inch,
        leftMargin=0.6 * inch,
        rightMargin=0.6 * inch,
    )
    styles = getSampleStyleSheet()
    primary, secondary = empresa_colors(db)

    styles.add(ParagraphStyle(name='InfoLabel', parent=styles['Normal'], fontSize=9, leading=13, fontName='Helvetica-Bold', textColor=secondary))
    styles.add(ParagraphStyle(name='InfoValue', parent=styles['Normal'], fontSize=9, leading=13))
    styles.add(ParagraphStyle(name='CellWrap', parent=styles['Normal'], fontSize=9, leading=12, wordWrap='CJK'))
    styles.add(ParagraphStyle(name='CellCenter', parent=styles['Normal'], fontSize=9, leading=12, alignment=1))
    styles.add(ParagraphStyle(name='CellRight', parent=styles['Normal'], fontSize=9, leading=12, alignment=2))
    styles.add(ParagraphStyle(name='HeaderCell', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.white, fontName='Helvetica-Bold', alignment=1))
    styles.add(ParagraphStyle(name='GreenCell', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#389e0d'), alignment=1, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='RedCell', parent=styles['Normal'], fontSize=9, leading=12, textColor=colors.HexColor('#cf1322'), alignment=1, fontName='Helvetica-Bold'))

    elements = []
    elements.extend(build_header(db, f"Kardex - {producto.descripcion}"))

    img_path, img_w, img_h = _get_imagen_producto(producto.imagen)
    if img_path:
        prod_img = Image(img_path, width=img_w, height=img_h)
    else:
        prod_img = Paragraph('-', styles['InfoValue'])

    cat = producto.categoria.nombre if producto.categoria else '-'
    estado = 'INACTIVO' if producto.activo is False else 'ACTIVO'

    def cell(label, value):
        return [
            [Paragraph(label, styles['InfoLabel'])],
            [Paragraph(str(value), styles['InfoValue'])],
        ]

    campos = [
        ('Código', producto.codigo),
        ('Categoría', cat),
        ('Marca', producto.marca),
        ('Procedencia', producto.procedencia or '-'),
        ('Costo Bs.', f"{float(producto.precio):.2f}"),
        ('Utilidad Bs.', f"{float(producto.utilidad):.2f}"),
        ('Stock Inicial', producto.stock_inicial),
        ('Stock Actual', producto.stock_actual),
        ('Stock Mín. / Máx.', f"{producto.stock_minimo} / {producto.stock_maximo}"),
        ('Estado', estado),
    ]

    info_cols = 5
    grid_rows = [campos[i:i + info_cols] for i in range(0, len(campos), info_cols)]
    info_data = [[cell(l, v) for (l, v) in fila] for fila in grid_rows]

    info_tbl = Table(info_data, colWidths=[5.2 * inch / info_cols] * info_cols)
    info_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#f7f7f7')),
        ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor('#d9d9d9')),
        ('INNERGRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e8e8e8')),
    ]))

    header_tbl = Table([[prod_img, info_tbl]], colWidths=[1.9 * inch, 5.2 * inch])
    header_tbl.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 0),
        ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    elements.append(header_tbl)
    elements.append(Spacer(1, 10))
    elements.append(Paragraph(
        f"Período: {fecha_inicio.strftime('%d/%m/%Y')} al {fecha_fin.strftime('%d/%m/%Y')}",
        styles['InfoValue']
    ))
    elements.append(Spacer(1, 12))

    def bs(v):
        return f"Bs. {float(v):.2f}"

    def celda_tipo(tipo):
        if tipo == 'ENTRADA':
            return Paragraph('ENTRADA', styles['GreenCell'])
        if tipo == 'SALIDA':
            return Paragraph('SALIDA', styles['RedCell'])
        return Paragraph('SALDO INICIAL', styles['CellCenter'])

    data = [
        [
            Paragraph('Fecha', styles['HeaderCell']),
            Paragraph('Tipo', styles['HeaderCell']),
            Paragraph('Comprobante', styles['HeaderCell']),
            Paragraph('Cantidad', styles['HeaderCell']),
            Paragraph('Precio (Bs.)', styles['HeaderCell']),
            Paragraph('Total (Bs.)', styles['HeaderCell']),
            Paragraph('Saldo', styles['HeaderCell']),
        ]
    ]

    data.append([
        fecha_inicio.strftime('%d/%m/%Y'),
        celda_tipo('SALDO INICIAL'),
        '-', '-', '-', '-',
        str(saldo_inicial),
    ])

    saldo = saldo_inicial
    movimientos = []
    for e in entradas:
        movimientos.append({
            'fecha': e.fecha,
            'tipo': 'ENTRADA',
            'detalle': f"{e.comprobante} {e.num_comprobante}",
            'cantidad': e.cantidad,
            'precio': float(e.costo),
            'total': float(e.cantidad * e.costo),
        })
    for s in salidas:
        movimientos.append({
            'fecha': s.fecha,
            'tipo': 'SALIDA',
            'detalle': f"{s.comprobante} {s.num_comprobante}",
            'cantidad': s.cantidad,
            'precio': float(s.precio),
            'total': float(s.cantidad * s.precio),
        })
    movimientos.sort(key=lambda x: x['fecha'])

    for m in movimientos:
        saldo += m['cantidad'] if m['tipo'] == 'ENTRADA' else -m['cantidad']
        data.append([
            m['fecha'].strftime('%d/%m/%Y %H:%M'),
            celda_tipo(m['tipo']),
            m['detalle'],
            str(m['cantidad']),
            bs(m['precio']),
            bs(m['total']),
            str(saldo),
        ])

    table = Table(data, repeatRows=1, colWidths=[1.0*inch, 1.1*inch, 2.1*inch, 0.8*inch, 0.9*inch, 0.9*inch, 0.7*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (3, 0), (-1, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica'),
        ('FONTNAME', (2, 1), (2, -1), 'Helvetica'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#d9d9d9')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#fff7e6')),
        ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))

    elements.append(table)
    doc.build(elements, canvasmaker=make_canvasmaker(get_empresa(db), logo_path, logo_h))

    buffer.seek(0)
    return buffer
