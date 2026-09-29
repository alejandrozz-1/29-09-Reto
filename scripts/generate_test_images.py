#!/usr/bin/env python3
"""Genera las 5 imagenes de test para el analisis de vision con Gemini.

Las imagenes se sintetizan con Pillow para que el repo sea autocontenido y el
ground truth (texto OCR, escena, objetos) sea 100% conocido y verificable.

Uso:
    python scripts/generate_test_images.py
"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "images"

FONTS = Path("C:/Windows/Fonts")


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS / name
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


ARIAL = lambda s: font("arial.ttf", s)          # noqa: E731
ARIAL_B = lambda s: font("arialbd.ttf", s)      # noqa: E731
COURIER = lambda s: font("cour.ttf", s)         # noqa: E731
COURIER_B = lambda s: font("courbd.ttf", s)     # noqa: E731


def guardar(img: Image.Image, name: str, rotate: float = 0.0, bg=(235, 235, 235)) -> None:
    if rotate:
        img = img.rotate(rotate, expand=True, fillcolor=bg, resample=Image.BICUBIC)
    path = OUT / name
    img.save(path, "PNG")
    print(f"  -> {path.relative_to(ROOT)}  ({img.size[0]}x{img.size[1]})")


# ---------------------------------------------------------------------------
# 1. Documento escaneado
# ---------------------------------------------------------------------------
DOC_TEXT = [
    ("ACTA DE REUNION", "title"),
    ("Fecha: 14 de marzo de 2026", ""),
    ("Lugar: Sala de Juntas, Edificio Norte", ""),
    ("", ""),
    ("El Comite de Direccion se reunio el 14 de marzo de 2026 para", ""),
    ("aprobar el plan de inversion del segundo trimestre. Se aprobo", ""),
    ("un presupuesto de 1.250.000 euros para la modernizacion del", ""),
    ("centro de datos de Madrid, asi como la contratacion de doce", ""),
    ("nuevos ingenieros antes del 30 de junio de 2026.", ""),
    ("", ""),
    ("Se deja constancia de que la directora financiera, Laura", ""),
    ("Gomez, presento el informe de resultados del ejercicio 2025,", ""),
    ("con un crecimiento del 18 por ciento sobre el ano anterior.", ""),
    ("La proxima reunion quedo fijada para el 12 de abril de 2026.", ""),
]


def documento_escaneado() -> None:
    w, h = 1000, 1400
    img = Image.new("RGB", (w, h), (252, 252, 250))
    d = ImageDraw.Draw(img)
    d.rectangle([40, 40, w - 40, h - 40], outline=(200, 200, 200), width=2)

    y = 110
    for text, style in DOC_TEXT:
        if text:
            f = ARIAL_B(30) if style == "title" else ARIAL(21)
            d.text((90, y), text, font=f, fill=(25, 25, 25))
            y += 52 if style == "title" else 36
        else:
            y += 22
    d.line([90, 150, 430, 150], fill=(25, 25, 25), width=3)
    d.text((90, h - 150), "Fdo. Laura Gomez - Direccion Financiera", font=ARIAL(20), fill=(60, 60, 60))

    # ruido y ligera desenfoque para imitar un escaneo real
    img = img.filter(ImageFilter.GaussianBlur(0.4))
    px = img.load()
    for yy in range(0, h, 3):
        for xx in range(0, w, 3):
            r, g, b = px[xx, yy]
            n = (xx * 7 + yy * 13) % 11 - 5
            px[xx, yy] = (max(0, min(255, r + n)), max(0, min(255, g + n)), max(0, min(255, b + n)))
    guardar(img, "01_documento_escaneado.png", rotate=-1.5)


# ---------------------------------------------------------------------------
# 2. Recibo / factura
# ---------------------------------------------------------------------------
RECEIPT = [
    ("SUPERMERCADO EL SOL", "b"),
    ("Calle Mayor 22, Madrid", ""),
    ("NIF: B-87654321", ""),
    ("--------------------------------", ""),
    ("Fecha: 05/07/2026   18:42", ""),
    ("Caja 04   Ticket 001293", ""),
    ("--------------------------------", ""),
    ("3  LECHE ENTERA 2L      4,05", ""),
    ("1  PAN CRUJIENTE        1,85", ""),
    ("2  MANZANA GALA 1KG     3,10", ""),
    ("1  CAFE MOLIDO 250G     4,60", ""),
    ("1  DETERGENTE 3L        7,95", ""),
    ("--------------------------------", ""),
    ("SUBTOTAL                21,55", ""),
    ("IVA 10%                  2,16", ""),
    ("TOTAL                   23,71", ""),
    ("--------------------------------", ""),
    ("TARJETA **** 4471       23,71", ""),
    ("GRACIAS POR SU COMPRA", "b"),
]


def recibo() -> None:
    w, h = 640, 1080
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)
    y = 50
    for text, style in RECEIPT:
        f = COURIER_B(24) if style == "b" else COURIER(22)
        d.text((55, y), text, font=f, fill=(20, 20, 20))
        y += 40
    # codigo de barras
    x = 90
    for i in range(55):
        bw = 3 if i % 3 else 6
        d.rectangle([x, h - 130, x + bw, h - 65], fill=(10, 10, 10))
        x += bw + 4
    img = img.filter(ImageFilter.GaussianBlur(0.3))
    guardar(img, "02_recibo_factura.png", rotate=3.0, bg=(180, 180, 180))


# ---------------------------------------------------------------------------
# 3. Foto urbana (sintetica)
# ---------------------------------------------------------------------------
def foto_urbana() -> None:
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), (135, 190, 230))
    d = ImageDraw.Draw(img)

    # cielo con gradiente
    for i in range(340):
        t = i / 340
        d.line([(0, i), (w, i)], fill=(int(110 + 60 * t), int(170 + 55 * t), int(225 + 25 * t)))
    d.ellipse([1040, 60, 1140, 160], fill=(255, 240, 180))

    # edificios traseros
    buildings = [
        (40, 170, 190, 470, (196, 178, 158)),
        (200, 110, 330, 470, (170, 150, 138)),
        (340, 200, 470, 470, (210, 195, 175)),
        (760, 140, 900, 470, (150, 155, 165)),
        (910, 90, 1060, 470, (185, 170, 160)),
        (1070, 190, 1240, 470, (165, 160, 150)),
    ]
    for x0, y0, x1, y1, col in buildings:
        d.rectangle([x0, y0, x1, y1], fill=col, outline=(90, 88, 85))
        for wy in range(y0 + 22, y1 - 25, 46):
            for wx in range(x0 + 18, x1 - 25, 46):
                d.rectangle([wx, wy, wx + 22, wy + 26], fill=(120, 150, 175), outline=(80, 80, 80))

    # suelo
    d.rectangle([0, 470, w, h], fill=(95, 95, 100))          # acera lejana
    d.rectangle([0, 520, w, h], fill=(70, 70, 76))           # asfalto
    d.rectangle([0, 505, w, 522], fill=(150, 150, 148))      # bordillo
    for x in range(0, w, 130):                                # linea discontinua
        d.rectangle([x, 655, x + 70, 665], fill=(235, 235, 230))

    # arboles
    for tx in (120, 640, 1210):
        d.rectangle([tx - 9, 430, tx + 9, 520], fill=(96, 70, 42))
        for dx, dy, r in ((0, -40, 52), (-35, -10, 40), (35, -10, 40), (0, 10, 42)):
            d.ellipse([tx + dx - r, 400 + dy - r, tx + dx + r, 400 + dy + r], fill=(52, 122, 62))

    # farola
    d.line([400, 300, 400, 520], fill=(55, 55, 60), width=9)
    d.line([400, 305, 460, 305], fill=(55, 55, 60), width=8)
    d.ellipse([450, 296, 480, 326], fill=(255, 250, 210), outline=(55, 55, 60))

    # semaforo
    d.rectangle([880, 330, 920, 520], fill=(45, 45, 50))
    for i, col in enumerate(((190, 40, 40), (190, 160, 30), (40, 150, 60))):
        d.ellipse([890, 350 + i * 55, 910, 370 + i * 55], fill=col)

    # coche rojo
    d.rounded_rectangle([470, 545, 760, 640], radius=18, fill=(200, 45, 45))
    d.polygon([(520, 545), (560, 495), (690, 495), (730, 545)], fill=(178, 38, 38))
    d.polygon([(545, 540), (575, 505), (625, 505), (625, 540)], fill=(160, 195, 215))
    d.polygon([(640, 505), (685, 505), (710, 540), (640, 540)], fill=(160, 195, 215))
    for cx in (545, 715):
        d.ellipse([cx - 34, 612, cx + 34, 672], fill=(35, 35, 38))
        d.ellipse([cx - 14, 632, cx + 14, 654], fill=(185, 185, 190))

    # coche azul
    d.rounded_rectangle([60, 570, 320, 655], radius=16, fill=(40, 80, 175))
    d.polygon([(105, 570), (145, 525), (260, 525), (300, 570)], fill=(35, 70, 155))
    d.polygon([(130, 565), (160, 535), (200, 535), (200, 565)], fill=(165, 200, 220))
    for cx in (120, 270):
        d.ellipse([cx - 30, 630, cx + 30, 685], fill=(35, 35, 38))

    # cartel de calle
    d.line([1010, 380, 1010, 520], fill=(70, 70, 75), width=8)
    d.rounded_rectangle([930, 325, 1245, 390], radius=6, fill=(25, 110, 60), outline=(240, 240, 240), width=3)
    d.text((952, 341), "AVENIDA DEL SOL", font=ARIAL_B(26), fill=(255, 255, 255))

    guardar(img, "03_foto_urbana.png")


# ---------------------------------------------------------------------------
# 4. Producto sobre fondo blanco
# ---------------------------------------------------------------------------
def producto() -> None:
    w = h = 1000
    img = Image.new("RGB", (w, h), (255, 255, 255))
    d = ImageDraw.Draw(img)

    # sombra
    d.ellipse([300, 745, 760, 815], fill=(228, 228, 228))

    # asa
    d.ellipse([640, 380, 830, 610], outline=(178, 35, 40), width=34)
    d.ellipse([686, 424, 784, 566], fill=(255, 255, 255))

    # cuerpo de la taza
    d.rounded_rectangle([300, 350, 700, 760], radius=40, fill=(200, 45, 52))
    d.ellipse([300, 700, 700, 790], fill=(168, 32, 40))
    d.ellipse([300, 310, 700, 400], fill=(226, 78, 84))
    d.ellipse([322, 332, 678, 378], fill=(58, 34, 26))
    d.ellipse([340, 345, 660, 368], fill=(94, 58, 40))

    # etiqueta
    d.rectangle([330, 500, 670, 615], fill=(252, 252, 250), outline=(170, 170, 170), width=2)
    d.text((372, 520), "CAFFE NERO", font=ARIAL_B(38), fill=(40, 40, 40))
    d.text((378, 570), "MUG 350ml", font=ARIAL(24), fill=(110, 110, 110))

    guardar(img, "04_producto.png")


# ---------------------------------------------------------------------------
# 5. Paisaje natural
# ---------------------------------------------------------------------------
def paisaje() -> None:
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), (170, 210, 235))
    d = ImageDraw.Draw(img)

    for i in range(430):
        t = i / 430
        d.line([(0, i), (w, i)], fill=(int(95 + 80 * t), int(150 + 75 * t), int(215 + 35 * t)))

    # sol y nubes
    d.ellipse([150, 70, 250, 170], fill=(255, 245, 200))
    for cx, cy, r in ((980, 130, 55), (1050, 145, 42), (930, 150, 40), (520, 100, 38), (575, 112, 30)):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(248, 250, 252))

    # montanas
    d.polygon([(0, 470), (250, 210), (470, 470)], fill=(105, 118, 138))
    d.polygon([(300, 470), (620, 160), (940, 470)], fill=(88, 100, 122))
    d.polygon([(760, 470), (1060, 240), (1280, 470)], fill=(118, 128, 146))
    d.polygon([(560, 245), (620, 160), (682, 248), (640, 232), (615, 255), (592, 230)], fill=(245, 248, 252))
    d.polygon([(205, 258), (250, 210), (296, 260), (262, 248), (246, 268), (228, 246)], fill=(245, 248, 252))

    # lago
    d.rectangle([0, 470, w, 640], fill=(70, 130, 165))
    for i in range(470, 640, 16):
        d.line([(0, i), (w, i)], fill=(95, 152, 182), width=3)
    d.polygon([(560, 470), (620, 470), (600, 640), (575, 640)], fill=(120, 168, 195))

    # pradera y arboles
    d.rectangle([0, 620, w, h], fill=(74, 128, 66))
    d.rectangle([0, 640, w, 668], fill=(94, 148, 78))
    for tx, ty, sc in ((120, 720, 1.0), (240, 745, 0.8), (1060, 735, 1.1), (1180, 760, 0.9), (640, 770, 0.7)):
        d.rectangle([tx - 10 * sc, ty - 70 * sc, tx + 10 * sc, ty], fill=(92, 66, 40))
        for j, r in enumerate((58, 48, 36)):
            rr = r * sc
            cy = ty - (80 + j * 42) * sc
            d.ellipse([tx - rr, cy - rr, tx + rr, cy + rr], fill=(40 + j * 12, 110 + j * 10, 55))

    guardar(img, "05_paisaje_natural.png")


def ground_truth() -> None:
    """Escribe data/ground_truth_vision.json con el texto OCR exacto renderizado."""
    import json

    doc_lines = [t for t, _ in DOC_TEXT if t]
    doc_lines.append("Fdo. Laura Gomez - Direccion Financiera")
    rec_lines = [t for t, _ in RECEIPT]

    gt = {
        "meta": {
            "descripcion": "Ground truth de las 5 imagenes generadas por scripts/generate_test_images.py",
            "criterios": {
                "ocr": "similitud de caracteres normalizada (SequenceMatcher) sobre el texto esperado",
                "escena": "match exacto de la etiqueta de escena",
                "objetos": "precision/recall/F1 sobre el conjunto de objetos esperados",
                "descripcion": "recall de palabras clave esperadas en la descripcion",
            },
        },
        "imagenes": {
            "01_documento_escaneado.png": {
                "tipo_tarea": "ocr",
                "escena_esperada": "documento_escaneado",
                "ocr_esperado": "\n".join(doc_lines),
                "objetos_esperados": ["documento", "texto", "titulo", "firma", "pagina blanca", "borde"],
                "descripcion_keywords": ["documento", "acta", "reunion", "texto", "firma", "blanco"],
            },
            "02_recibo_factura.png": {
                "tipo_tarea": "ocr",
                "escena_esperada": "recibo_factura",
                "ocr_esperado": "\n".join(rec_lines),
                "objetos_esperados": ["recibo", "ticket", "texto", "codigo de barras", "total", "productos"],
                "descripcion_keywords": ["recibo", "ticket", "compra", "total", "barras", "supermercado"],
            },
            "03_foto_urbana.png": {
                "tipo_tarea": "escena_objetos",
                "escena_esperada": "escena_urbana",
                "ocr_esperado": "AVENIDA DEL SOL",
                "objetos_esperados": [
                    "edificio", "coche", "árbol", "semáforo",
                    "farola", "carretera", "cielo", "cartel",
                ],
                "descripcion_keywords": [
                    "calle", "ciudad", "edificio", "coche", "árbol", "semáforo",
                    "carretera", "cielo", "cartel",
                ],
            },
            "04_producto.png": {
                "tipo_tarea": "escena_objetos",
                "escena_esperada": "producto_fondo_blanco",
                "ocr_esperado": "CAFFE NERO\nMUG 350ml",
                "objetos_esperados": ["taza", "asa", "etiqueta", "café", "fondo blanco", "sombra"],
                "descripcion_keywords": ["taza", "roja", "rojo", "asa", "etiqueta", "blanco", "café", "cafe"],
            },
            "05_paisaje_natural.png": {
                "tipo_tarea": "escena_objetos",
                "escena_esperada": "paisaje_natural",
                "ocr_esperado": "",
                "objetos_esperados": ["montaña", "lago", "árbol", "cielo", "nube", "sol", "pradera"],
                "descripcion_keywords": [
                    "montaña", "montañas", "lago", "agua", "árbol", "árboles",
                    "cielo", "nube", "nubes", "sol", "paisaje",
                ],
            },
        },
    }
    path = ROOT / "data" / "ground_truth_vision.json"
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(gt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  -> {path.relative_to(ROOT)}")


def main() -> None:
    OUT.mkdir(exist_ok=True)
    print(f"Generando imagenes de test en {OUT.relative_to(ROOT)}")
    documento_escaneado()
    recibo()
    foto_urbana()
    producto()
    paisaje()
    ground_truth()
    print("Listo.")


if __name__ == "__main__":
    main()
