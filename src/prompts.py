"""Prompts estructurados. Cada uno pide al modelo devolver exclusivamente JSON."""

from __future__ import annotations

# ---------------------------------------------------------------------------
# TEXTO
# ---------------------------------------------------------------------------

TEXT_SYSTEM = (
    "Eres un sistema de analisis de texto de produccion. Respondes SIEMPRE con un "
    "unico objeto JSON valido, sin markdown, sin comentarios y sin texto adicional. "
    "Si un campo no puede determinarse, usa null en lugar de inventar."
)

LANGUAGE_PROMPT = """Analiza el siguiente texto.

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "idioma": "<codigo ISO 639-1 en minusculas: es, en, fr, de, it, pt, ...>",
  "idioma_nombre": "<nombre del idioma>",
  "confianza": <numero entre 0 y 1>,
  "es_mixto": <true|false>
}}

TEXTO:
{text}"""

NER_PROMPT = """Extrae las entidades nombradas del siguiente texto.

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "entidades": [
    {{
      "texto": "<mencion literal en el texto>",
      "tipo": "PERSON|ORG|LOC|DATE|MONEY|PRODUCT|EVENT|CONTACT|OTHER"
    }}
  ]
}}

Reglas:
- Solo entidades que aparezcan literalmente en el texto.
- No dupliques menciones.
- No inventes entidades.
- Cada entidad es un objeto con las claves "texto" y "tipo".

TEXTO:
{text}"""

SENTIMENT_PROMPT = """Analiza el sentimiento del siguiente texto.

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "etiqueta": "positivo|neutral|negativo",
  "score": <numero entre -1 (muy negativo) y 1 (muy positivo)>,
  "subjetividad": <numero entre 0 (objetivo) y 1 (subjetivo)>,
  "justificacion": "<una frase breve en espanol>"
}}

TEXTO:
{text}"""

SUMMARY_PROMPT = """Resume el siguiente texto en UNA sola frase de maximo 40 palabras,
conservando la informacion mas importante (quien, que, donde, cuando).

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "resumen": "<una frase>",
  "palabras": <entero con el numero de palabras del resumen>,
  "mantiene_datos_clave": <true|false>
}}

TEXTO:
{text}"""

TEXT_TASKS = {
    "idioma": LANGUAGE_PROMPT,
    "entidades": NER_PROMPT,
    "sentimiento": SENTIMENT_PROMPT,
    "resumen": SUMMARY_PROMPT,
}

# ---------------------------------------------------------------------------
# VISION
# ---------------------------------------------------------------------------

VISION_SYSTEM = (
    "Eres un sistema de vision por computadora de produccion. Respondes SIEMPRE con "
    "un unico objeto JSON valido, sin markdown y sin texto adicional. No inventes "
    "elementos que no sean visibles en la imagen."
)

OCR_PROMPT = """Transcribe TODO el texto visible en esta imagen, respetando lineas con \\n.

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "texto": "<transcripcion completa>",
  "lineas": [<numero de lineas de texto detectadas>],
  "idioma": "<codigo ISO 639-1>",
  "confianza_ocr": <numero entre 0 y 1>
}}"""

DESCRIPTION_PROMPT = """Describe el contenido visual de esta imagen en 2-3 frases,
mencionando los elementos principales, colores y contexto.

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "descripcion": "<2-3 frases en espanol>",
  "elementos_visibles": ["<objeto 1>", "<objeto 2>"]
}}"""

SCENE_PROMPT = """Clasifica la escena de esta imagen en UNA sola etiqueta exacta de esta lista:
"documento_escaneado", "recibo_factura", "escena_urbana", "producto_fondo_blanco", "paisaje_natural", "otro"

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "escena": "<etiqueta exacta de la lista>",
  "confianza": <numero entre 0 y 1>
}}"""

OBJECT_PROMPT = """Detecta los objetos principales visibles en esta imagen.

DEVUELVE EXCLUSIVAMENTE este objeto JSON:
{{
  "objetos": [
    {{"nombre": "<objeto>", "confianza": <0-1>}}
  ]
}}

Reglas: maximo 10 objetos, solo cosas realmente visibles, sin inventar.

IMAGEN adjunta."""

VISION_TASKS = {
    "ocr": OCR_PROMPT,
    "descripcion": DESCRIPTION_PROMPT,
    "escena": SCENE_PROMPT,
    "objetos": OBJECT_PROMPT,
}
