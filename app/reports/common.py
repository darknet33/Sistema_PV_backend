from pathlib import Path
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph, Spacer
from reportlab.pdfgen import canvas as canvas_module

DEFAULT_PRIMARY = "#1677ff"
DEFAULT_SECONDARY = "#001529"

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def get_empresa(db: Session):
    from app.models.empresa import Empresa

    emp = db.query(Empresa).first()
    if not emp:
        return {
            "nombre": "", "razon_social": "", "nit": "", "telefono": "",
            "correo": "", "direccion": "", "ciudad": "", "logo": None,
            "imagen_encabezado": None, "imagen_pie": None,
            "color_principal": DEFAULT_PRIMARY, "color_secundario": DEFAULT_SECONDARY,
        }
    return {
        "nombre": emp.nombre or "",
        "razon_social": emp.razon_social or "",
        "nit": emp.nit or "",
        "telefono": emp.telefono or "",
        "correo": emp.correo or "",
        "direccion": emp.direccion or "",
        "ciudad": emp.ciudad or "",
        "logo": emp.logo,
        "imagen_encabezado": emp.imagen_encabezado,
        "imagen_pie": emp.imagen_pie,
        "color_principal": emp.color_principal or DEFAULT_PRIMARY,
        "color_secundario": emp.color_secundario or DEFAULT_SECONDARY,
    }


def hexcolor(value, default=DEFAULT_PRIMARY):
    try:
        return colors.HexColor(value)
    except Exception:
        return colors.HexColor(default)


def empresa_colors(db: Session):
    emp = get_empresa(db)
    return (
        hexcolor(emp["color_principal"], DEFAULT_PRIMARY),
        hexcolor(emp["color_secundario"], DEFAULT_SECONDARY),
    )


PAGE_W, PAGE_H = letter[0], letter[1]


def _get_imagen_info(url):
    """Devuelve (path, altura_a_ancho_completo) para una url de imagen, o (None, 0.0)."""
    if not url:
        return None, 0.0
    try:
        path = BASE_DIR / url.lstrip("/")
        if not path.exists():
            return None, 0.0
        from PIL import Image as PILImage
        with PILImage.open(str(path)) as img:
            w, h = img.size
        if w <= 0 or h <= 0:
            return None, 0.0
        return str(path), PAGE_W * (h / w)
    except Exception:
        return None, 0.0


def get_logo_header_info(db: Session):
    """Info de la imagen de encabezado: prioriza imagen_encabezado, respalda al logo."""
    emp = get_empresa(db)
    path, height = _get_imagen_info(emp.get("imagen_encabezado"))
    if path:
        return path, height
    return _get_imagen_info(emp.get("logo"))


def build_header(db: Session, titulo: str):
    emp = get_empresa(db)
    primary = hexcolor(emp["color_principal"], DEFAULT_PRIMARY)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name='EmpresaTitle', parent=styles['Title'],
        fontSize=14, leading=16, textColor=primary)

    return [
        Paragraph(titulo, title_style),
        Spacer(1, 12),
    ]


class _NumberedCanvas(canvas_module.Canvas):
    def __init__(self, *args, **kwargs):
        self._empresa = kwargs.pop('empresa', None)
        self._logo_path = kwargs.pop('logo_path', None)
        self._logo_height = kwargs.pop('logo_height', 0.0)
        self._saved_page_states = []
        super().__init__(*args, **kwargs)

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_header_logo()
            self._draw_footer_image()
            self._draw_footer(num_pages)
            canvas_module.Canvas.showPage(self)
        canvas_module.Canvas.save(self)

    def _draw_header_logo(self):
        if not self._logo_path or self._logo_height <= 0:
            return
        self.saveState()
        self.drawImage(
            self._logo_path,
            0,
            PAGE_H - self._logo_height,
            PAGE_W,
            self._logo_height,
            preserveAspectRatio=True,
            mask='auto',
        )
        self.restoreState()

    def _draw_footer_image(self):
        """Dibuja la imagen de pie de página a ancho completo respetando su escala si existe."""
        url = (self._empresa or {}).get("imagen_pie")
        if not url:
            return
        try:
            path = BASE_DIR / url.lstrip("/")
            if not path.exists():
                return
            from PIL import Image as PILImage
            with PILImage.open(str(path)) as img:
                w, h = img.size
            if w <= 0 or h <= 0:
                return
            band_h = PAGE_W * (h / w)
            self.saveState()
            self.drawImage(
                str(path),
                0,
                0,
                PAGE_W,
                band_h,
                preserveAspectRatio=True,
                mask='auto',
            )
            self.restoreState()
        except Exception:
            return

    def _draw_footer(self, num_pages):
        emp = self._empresa or {}
        primary = hexcolor(emp.get("color_principal", DEFAULT_PRIMARY), DEFAULT_PRIMARY)
        secondary = hexcolor(emp.get("color_secundario", DEFAULT_SECONDARY), DEFAULT_SECONDARY)
        self.saveState()

        url_pie = (emp.get("imagen_pie") or "").strip()
        tiene_pie_imagen = bool(url_pie) and (BASE_DIR / url_pie.lstrip("/")).exists()

        # Datos de la empresa
        nombre = (emp.get("nombre") or "").strip()
        nit = (emp.get("nit") or "").strip()
        telefono = (emp.get("telefono") or "").strip()
        correo = (emp.get("correo") or "").strip()
        direccion = (emp.get("direccion") or "").strip()
        ciudad = (emp.get("ciudad") or "").strip()

        # ---- ICONOS (glifos ZapfDingbats) ----
        ICON_STAR = '\x4b'    # estrella rellena
        ICON_PHONE = '\x26'   # teléfono
        ICON_MAIL = '\x40'    # sobre (correo)
        ICON_PIN = '\x41'     # índice apuntando (dirección)

        items = []
        if nombre:
            items.append((ICON_STAR, nombre))
        if telefono:
            items.append((ICON_PHONE, telefono))
        if correo:
            items.append((ICON_MAIL, correo))
        address = ", ".join(x for x in (direccion, ciudad) if x)
        if address:
            items.append((ICON_PIN, address))
        if nit:
            items.append((ICON_STAR, f"NIT: {nit}"))

        if not tiene_pie_imagen and not items:
            self.restoreState()
            return

        # Con imagen de pie: solo se muestra el número de página sobre la imagen
        if tiene_pie_imagen:
            page_text = f"Página {self._pageNumber} de {num_pages}"
            self.setFont('Helvetica', 7)
            self.setFillColor(secondary)
            self.drawCentredString(letter[0] / 2, 0.08 * inch, page_text)
            self.restoreState()
            return

        # ---- ESTILO TARJETA: fondo beige con borde ----
        card_width = 6.9 * inch   # ancho de la tarjeta
        card_x = (letter[0] - card_width) / 2  # centrado horizontal
        card_y = 0.20 * inch      # posición desde abajo

        # Parámetros de layout (puntos)
        icon_size = 9
        icon_radius = 6.5
        gap_icon_text = 5
        gap_items = 22
        margin_x = 0.35 * inch
        line_step = 0.24 * inch
        pad_y = 0.08 * inch

        def item_width(icon, text):
            return 2 * icon_radius + gap_icon_text + self.stringWidth(text, 'Helvetica', 8.5)

        def line_width(line):
            return sum(item_width(i, t) for i, t in line) + gap_items * (len(line) - 1)

        # Distribuir ítems en líneas centradas (envuelve si no caben)
        available = card_width - 2 * margin_x
        lines = []
        current = []
        current_w = 0.0
        for it in items:
            w = item_width(*it)
            add = w if not current else w + gap_items
            if current and current_w + add > available:
                lines.append(current)
                current = [it]
                current_w = w
            else:
                current.append(it)
                current_w += add
        if current:
            lines.append(current)

        # Altura de la tarjeta según número de líneas
        card_height = pad_y * 2 + line_step * len(lines)
        background = hexcolor(emp.get("color_fondo", "#eae3d7"))

        # Sombra sutil (detrás de la tarjeta)
        self.setFillColor(colors.Color(0, 0, 0, alpha=0.08))
        self.roundRect(card_x + 2, card_y - 2, card_width, card_height, 8, fill=1, stroke=0)

        # Fondo de la tarjeta (beige)
        self.setFillColor(background)
        self.setStrokeColor(colors.Color(0.75, 0.71, 0.64))  # #bfb5a2
        self.setLineWidth(0.8)
        self.roundRect(card_x, card_y, card_width, card_height, 8, fill=1, stroke=1)

        # Fondo suave de los iconos
        icon_bg = colors.Color(primary.red, primary.green, primary.blue, alpha=0.15)

        # ---- DIBUJAR LÍNEAS CENTRADAS ----
        for li, line in enumerate(lines):
            lw = line_width(line)
            start_x = card_x + (card_width - lw) / 2
            cy = card_y + card_height - pad_y - line_step * li - line_step / 2
            x = start_x
            for i, (icon, text) in enumerate(line):
                if i > 0:
                    x += gap_items
                cx = x + icon_radius
                # Círculo de icono
                self.setFillColor(icon_bg)
                self.setStrokeColor(primary)
                self.setLineWidth(0.8)
                self.circle(cx, cy, icon_radius, fill=1, stroke=1)
                # Glifo del icono centrado en el círculo
                self.setFillColor(primary)
                self.setFont('ZapfDingbats', icon_size)
                self.drawCentredString(cx, cy - icon_size * 0.35, icon)
                # Texto junto al icono
                self.setFillColor(secondary)
                self.setFont('Helvetica', 8.5)
                self.drawString(x + 2 * icon_radius + gap_icon_text, cy - 3, text)
                x += item_width(icon, text)

        # ---- NÚMERO DE PÁGINA (fuera de la tarjeta, abajo) ----
        page_text = f"Página {self._pageNumber} de {num_pages}"
        self.setFont('Helvetica', 7)
        self.setFillColor(secondary)
        self.drawCentredString(letter[0] / 2, card_y - 0.12 * inch, page_text)

        self.restoreState()


def make_canvasmaker(empresa: dict, logo_path=None, logo_height=0.0):
    def factory(filename, *args, **kwargs):
        kwargs['empresa'] = empresa
        kwargs['logo_path'] = logo_path
        kwargs['logo_height'] = logo_height
        return _NumberedCanvas(filename, *args, **kwargs)
    return factory
