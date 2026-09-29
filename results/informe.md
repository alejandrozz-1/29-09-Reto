# Informe de resultados - Analisis con Gemini

- **Generado:** 2026-09-29T07:49:11+00:00
- **Modelo:** `gemini-flash-latest`
- **Textos analizados:** 0 / 10
- **Imagenes analizadas:** 0 / 5

## Estado: EJECUCION INCOMPLETA

La API de Gemini no ha podido procesar el conjunto completo. Error registrado:

- `ApiError`: 403 PERMISSION_DENIED. {'error': {'code': 403, 'message': 'Your project has been denied access. Please contact support.', 'status': 'PERMISSION_DENIED'}}
- `ApiError`: 403 PERMISSION_DENIED. {'error': {'code': 403, 'message': 'Your project has been denied access. Please contact support.', 'status': 'PERMISSION_DENIED'}}

Ver `docs/API_ERROR.md` para el detalle, la reproduccion y las condiciones necesarias para obtener las metricas reales.

## 1. Analisis de texto

| Tarea | Metrica | Valor | Evaluados |
| --- | --- | --- | --- |
| Deteccion de idioma | Accuracy | n/d | 0 |
| Entidades nombradas | Precision | 0.0% | 0 |
| Entidades nombradas | Recall | 0.0% | - |
| Entidades nombradas | F1 | 0.0% | - |
| Sentimiento | Accuracy etiqueta | n/d | 0 |
| Sentimiento | MAE score (-1..1) | None | 0 |
| Resumen | ROUGE-L F1 medio | None | 0 |
| Resumen | % <= 40 palabras | n/d | 0 |

### Detalle por texto

| ID | Tipo | Idioma pred. | Idioma | Entidades | Sentim. pred. | Sentim. | ROUGE-L |
| --- | --- | --- | --- | --- | --- | --- | --- |
| t01 | noticia | - | - | 0/0 | - | - | - |

## 2. Analisis de imagenes

| Tarea | Metrica | Valor | Evaluadas |
| --- | --- | --- | --- |
| OCR | Similitud caracteres (med.) | None | 0 |
| Descripcion visual | Keyword recall medio | n/d | 0 |
| Clasificacion de escena | Accuracy | n/d | 0 |
| Deteccion de objetos | Precision | 0.0% | 0 |
| Deteccion de objetos | Recall | 0.0% | - |
| Deteccion de objetos | F1 | 0.0% | - |

### Detalle por imagen

| Imagen | Tarea | OCR sim. | Descr. recall | Escena pred. | Escena | Objetos |
| --- | --- | --- | --- | --- | --- | --- |
| 01_documento_escaneado.png | ocr | - | n/d | - | - | 0/0 |

## 3. Tabla comparativa por tipo de tarea

| Dominio | Tarea | Resultado | Metrica | Robustez metrica |
| --- | --- | --- | --- | --- |
| Texto | Clasificacion (idioma) | n/d | Exacta | Alta |
| Texto | Extraccion (entidades) | 0.0% | F1 | Alta |
| Texto | Clasificacion (sentimiento) | n/d | Exacta | Alta |
| Texto | Generacion (resumen) | None | ROUGE-L F1 | Media |
| Vision | OCR (documento) | None | Similitud caracteres | Alta |
| Vision | Descripcion visual | n/d | Keyword recall | Media |
| Vision | Clasificacion de escena | n/d | Exacta | Alta |
| Vision | Deteccion de objetos | 0.0% | F1 | Alta |

## 4. Metodologia y limitaciones

- Ground truth anotado a mano en `data/ground_truth_texto.json` y `data/ground_truth_vision.json` (imagenes sinteticas generadas con Pillow, por lo que el texto OCR de referencia es exacto).
- Las entidades anotadas **no son exhaustivas**: la precision de NER penaliza como falsos positivos entidades validas no anotadas, por lo que debe leerse como un limite superior del error.
- El recall de palabras clave de descripcion es una aproximacion: no valora el orden ni la coherencia.
- Temperatura 0 y JSON estructurado (`response_mime_type=application/json`) en todas las llamadas.
