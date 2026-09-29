# Reto del día — Análisis de texto e imágenes con Gemini

Repo completo con los dos retos del día:

1. **Análisis avanzado de texto con Gemini** — detección de idioma, extracción de
   entidades nombradas (NER), análisis de sentimiento y resumen automático sobre
   **10 textos de ejemplo** (noticias, reseñas y emails en 6 idiomas).
2. **Análisis de imágenes con Gemini** — OCR, descripción de contenido visual,
   clasificación de escenas y detección de objetos sobre **5 imágenes de test**
   (documento escaneado, recibo, foto urbana, producto y paisaje).

Ambos flujos piden al modelo **JSON estructurado** (`response_mime_type=application/json`)
y evalúan la precisión contra un *ground truth* anotado a mano.

---

## ⚠️ Estado actual del ejecutable

La ejecución real está **bloqueada por un error 403 `PERMISSION_DENIED`**
(*"Your project has been denied access"*) devuelto por la API de Gemini con todas
las API keys y todos los modelos disponibles.

- El código, las imágenes de test, el *ground truth*, las métricas y el notebook
  están **completos y verificados** (`python -m tests.test_metrics` → 8/8 OK).
- **No se han inventado métricas**: `results/informe.md` marca
  «EJECUCION INCOMPLETA» y deja los resultados como `n/d`.
- Detalle, matriz de comprobación y solución: **[docs/API_ERROR.md](docs/API_ERROR.md)**.

Con una key válida basta con ejecutar los tres comandos de abajo para obtener el
informe con métricas reales.

---

## Estructura

```
.
├── data/
│   ├── textos.json                 # 10 textos (noticias, reseñas, emails) x 6 idiomas
│   ├── ground_truth_texto.json     # idioma, entidades, sentimiento y resumen esperados
│   └── ground_truth_vision.json    # OCR exacto, escena, objetos y keywords esperados
├── images/
│   ├── 01_documento_escaneado.png  # OCR (documento con ruido de escáner)
│   ├── 02_recibo_factura.png       # OCR (ticket rotado 3°)
│   ├── 03_foto_urbana.png          # escena + objetos + OCR de cartel
│   ├── 04_producto.png             # escena + objetos
│   └── 05_paisaje_natural.png      # escena + objetos
├── scripts/
│   └── generate_test_images.py     # regenera las 5 imágenes + su ground truth
├── src/
│   ├── gemini_common.py            # cliente, .env, reintentos, parseo de JSON
│   ├── prompts.py                  # prompts estructurados de texto y visión
│   ├── text_analysis.py            # reto 1
│   ├── vision_analysis.py          # reto 2
│   └── evaluation.py               # métricas + informe comparativo
├── tests/test_metrics.py           # tests de las métricas (sin API)
├── notebooks/analisis_resultados.ipynb
├── results/                        # salidas JSON + informe.md
├── docs/API_ERROR.md               # documentación del 403
├── requirements.txt
└── .env.example
```

## Instalación

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Configuración de la API key

```powershell
copy .env.example .env
notepad .env
```

```env
GEMINI_API_KEY=AIzaSy...
GEMINI_MODEL=gemini-flash-latest
```

`.env` está en `.gitignore` y **nunca** debe subirse a git.

## Ejecución

```powershell
# 0) (opcional) regenerar las imágenes de test y su ground truth
python scripts/generate_test_images.py

# 1) reto de texto: 10 textos x 4 tareas = 40 llamadas
python -m src.text_analysis

# 2) reto de visión: 5 imágenes x 4 tareas = 20 llamadas
python -m src.vision_analysis

# 3) métricas + informe comparativo
python -m src.evaluation

# tests de las métricas (sin llamadas a la API)
python -m tests.test_metrics
```

Opciones útiles:

```powershell
python -m src.text_analysis --tareas idioma,sentimiento --limit 3
python -m src.vision_analysis --tareas ocr,escena
python -m src.evaluation -o results/informe.md
```

## Salidas

| Fichero | Contenido |
| --- | --- |
| `results/text_results.json` | predicciones crudas por texto y tarea (+ latencias) |
| `results/vision_results.json` | predicciones crudas por imagen y tarea (+ latencias) |
| `results/metricas.json` | métricas agregadas y detalle por registro |
| `results/informe.md` | **informe comparativo** con tablas de precisión |
| `notebooks/analisis_resultados.ipynb` | análisis interactivo con gráficas |

## Métricas

| Tarea | Métrica | Rango |
| --- | --- | --- |
| Detección de idioma | Accuracy exacta (ISO 639-1) | 0–1 |
| NER | Precision / Recall / F1 (normalizado sin acentos) | 0–1 |
| Sentimiento | Accuracy de etiqueta + MAE del score | 0–1 / 0–2 |
| Resumen | ROUGE-L F1 + % de resúmenes ≤ 40 palabras | 0–1 |
| OCR | Similitud de caracteres (SequenceMatcher) | 0–1 |
| Descripción visual | Recall de palabras clave | 0–1 |
| Clasificación de escena | Accuracy exacta | 0–1 |
| Detección de objetos | Precision / Recall / F1 | 0–1 |

## Notebook

```powershell
jupyter notebook notebooks/analisis_resultados.ipynb
```

El notebook carga `results/`, muestra las métricas por tarea, grafica la comparativa
texto vs. visión y explora el detalle registro a registro. Si los resultados contienen
el error de API, lo muestra explícitamente en lugar de generar gráficas vacías.
