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


def get_logo_header_info(db: Session):
    emp = get_empresa(db)
    url = emp.get("logo")
    if not url:
        return None, 0.0
    try:
        path = BASE_DIR / url.lstrip("/")
        if not path.exists():
            return None, 0.0
        from PIL import Image as PILImage
        with PILImage.open(path) as img:
            w, h = img.size
        if w <= 0 or h <= 0:
            return None, 0.0
        return str(path), PAGE_W * (h / w)
    except Exception:
        return None, 0.0


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

    def _draw_footer(self, num_pages):
        emp = self._empresa or {}
        primary = hexcolor(emp.get("color_principal", DEFAULT_PRIMARY), DEFAULT_PRIMARY)
        secondary = hexcolor(emp.get("color_secundario", DEFAULT_SECONDARY), DEFAULT_SECONDARY)
        self.saveState()

        # Datos de la empresa
        nombre = (emp.get("nombre") or "").strip()
        nit = (emp.get("nit") or "").strip()
        telefono = (emp.get("telefono") or "").strip()
        correo = (emp.get("correo") or "").strip()
        direccion = (emp.get("direccion") or "").strip()
        ciudad = (emp.get("ciudad") or "").strip()

        # ---- ESTILO TARJETA: fondo beige con borde ----
        # Definir dimensiones de la tarjeta en el footer
        card_width = 6.5 * inch   # ancho de la tarjeta
        card_height = 1.8 * inch  # altura de la tarjeta
        card_x = (letter[0] - card_width) / 2  # centrado horizontal
        card_y = 0.20 * inch      # posición desde abajo

        # Fondo de la tarjeta (beige)
        background = hexcolor(emp.get("color_fondo", "#eae3d7"))
        self.setFillColor(background)
        self.setStrokeColor(colors.Color(0.75, 0.71, 0.64))  # #bfb5a2
        self.setLineWidth(0.8)
        self.roundRect(card_x, card_y, card_width, card_height, 8, fill=1, stroke=1)

        # Sombra sutil
        self.setFillColor(colors.Color(0, 0, 0, alpha=0.08))
        self.roundRect(card_x + 2, card_y - 2, card_width, card_height, 8, fill=1, stroke=0)

        # ---- MARGENES INTERNOS ----
        margin_left = 0.25 * inch
        margin_top = 0.15 * inch
        text_x = card_x + margin_left
        text_y = card_y + card_height - margin_top

        # ---- FUNCIÓN PARA DIBUJAR CAMPO ----
        def draw_field(label_text, content_text, y_pos, is_nit=False, is_address=False):
            """Dibuja un campo estilo tarjeta"""
            # Etiqueta en negrita
            self.setFillColor(primary)
            self.setFont('Helvetica-Bold', 7)
            self.drawString(text_x, y_pos, label_text)

            # Línea debajo de la etiqueta
            label_width = self.stringWidth(label_text, 'Helvetica-Bold', 7)
            line_y = y_pos - 2.5
            self.setStrokeColor(primary)
            self.setLineWidth(1.2)
            self.line(text_x, line_y, text_x + label_width + 4, line_y)

            # Contenido
            self.setFillColor(secondary)
            if is_nit:
                self.setFont('Helvetica-Bold', 8.5)
            else:
                self.setFont('Helvetica', 8.5)

            content_y = y_pos - 10

            if is_address:
                lines = content_text.split('\n')
                for i, line in enumerate(lines):
                    self.drawString(text_x, content_y - (i * 12), line.strip())
                return content_y - (len(lines) * 12) - 4
            else:
                self.drawString(text_x, content_y, content_text)
                return content_y - 12

        # ---- DIBUJAR CAMPOS EN EL FOOTER ----
        current_y = text_y

        # 1. NOMBRE / RAZÓN SOCIAL (si existe)
        if nombre:
            current_y = draw_field("EMPRESA:", nombre, current_y)
            current_y -= 4

        # 2. DIRECCIÓN
        address_text = f"{direccion}\n{ciudad}" if direccion and ciudad else direccion or ciudad
        if address_text:
            current_y = draw_field("DIRECCIÓN:", address_text, current_y, is_address=True)
            current_y -= 4

        # 3. TELÉFONO
        if telefono:
            current_y = draw_field("TELÉFONO:", telefono, current_y)
            current_y -= 4

        # 4. CORREO
        if correo:
            current_y = draw_field("CORREO:", correo, current_y)
            current_y -= 4

        # 5. NIT (con estilo más grueso)
        if nit:
            # Etiqueta NIT
            self.setFillColor(primary)
            self.setFont('Helvetica-Bold', 7)
            self.drawString(text_x, current_y, "NIT:")

            label_width = self.stringWidth("NIT:", 'Helvetica-Bold', 7)
            line_y = current_y - 2.5
            self.setStrokeColor(primary)
            self.setLineWidth(1.2)
            self.line(text_x, line_y, text_x + label_width + 4, line_y)

            # Contenido NIT (más grueso)
            self.setFillColor(secondary)
            self.setFont('Helvetica-Bold', 8.5)
            self.drawString(text_x, current_y - 10, nit)

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
