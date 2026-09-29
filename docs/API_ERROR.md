# Error de API: 403 PERMISSION_DENIED

**Estado:** bloqueo del lado de Google. El desarrollo está completo y verificado, pero
no se han podido obtener métricas reales porque el proyecto asociado a las API keys
recibidas está suspendido/denegado.

Fecha de la última comprobación: **2026-09-29**.

---

## 1. Síntoma

Toda llamada a `generateContent` devuelve HTTP 403:

```json
{
  "error": {
    "code": 403,
    "message": "Your project has been denied access. Please contact support.",
    "status": "PERMISSION_DENIED"
  }
}
```

La key **sí autentica** (no devuelve 400/401 `API_KEY_INVALID`), y `models.list`
responde con normalidad y devuelve el catálogo completo. El rechazo es
**a nivel de proyecto**, no de credencial.

## 2. Reproducción

Con `GEMINI_API_KEY` definida (fichero `.env`, no versionado):

```powershell
python -m src.text_analysis
#   ABORTADO por error de API en 'idioma': 403 PERMISSION_DENIED ...

python -m src.vision_analysis
#   ABORTADO por error de API en 'ocr': 403 PERMISSION_DENIED ...
```

Ambos scripts abortan en la primera llamada y dejan constancia del error en
`results/text_results.json` y `results/vision_results.json` (campo `error`).

Petición REST en crudo (misma respuesta):

```powershell
Invoke-WebRequest `
  -Uri "https://generativelanguage.googleapis.com/v1beta/models/gemini-flash-latest:generateContent" `
  -Method Post `
  -Headers @{ "x-goog-api-key" = $env:GEMINI_API_KEY } `
  -ContentType "application/json" `
  -Body '{"contents":[{"parts":[{"text":"hola"}]}]}'
```

## 3. Matriz de comprobación

Dos API keys distintas (ambas con formato `AQ.Ab8...`, no el formato habitual
`AIzaSy...` de AI Studio) y los modelos disponibles en `models.list`:

| Key | Modelo probado | Resultado |
| --- | --- | --- |
| key-1 | `gemini-2.5-flash` | 404 `no longer available to new users` |
| key-1 | `gemini-2.5-pro` | 404 `no longer available to new users` |
| key-1 | `gemini-flash-latest` | **403 PERMISSION_DENIED** |
| key-1 | `gemini-3.1-flash-lite` | **403 PERMISSION_DENIED** |
| key-1 | `gemini-3.5-flash` | **403 PERMISSION_DENIED** |
| key-1 | `gemini-3.6-flash` | **403 PERMISSION_DENIED** |
| key-1 | `gemini-3.8-flash` | **403 PERMISSION_DENIED** |
| key-1 | `gemini-pro-latest` | **403 PERMISSION_DENIED** |
| key-1 | `gemma-4-26b-a4b-it` | **403 PERMISSION_DENIED** |
| key-2 | `gemini-flash-latest` | **403 PERMISSION_DENIED** |
| key-2 | `gemini-3.5-flash` | **403 PERMISSION_DENIED** |
| key-2 | `gemini-3.1-flash-lite` | **403 PERMISSION_DENIED** |

Conclusión: el bloqueo es **del proyecto** y persiste entre credenciales.
Los dos únicos 404 no son errores de acceso: indican que esos modelos concretos
ya no se ofrecen a usuarios nuevos y remiten a versiones más recientes
(que a su vez devuelven 403).

## 4. Qué se ha hecho para descartar otros fallos

- Verificación a nivel REST (sin SDK) → mismo 403.
- Dos API keys distintas → mismo 403.
- 11 modelos distintos del catálogo → 403 en todos los disponibles.
- SDK `google-genai` 2.25.0 instalado y funcional (el error llega desde la API, no del cliente).
- SDK, Python 3.14 y red: operativos (el catálogo de modelos se descarga correctamente).

## 5. Resultados: no se han fabricado métricas

Para que el entregable no contenga números inventados:

- `results/text_results.json` y `results/vision_results.json` contienen el **error real**,
  sin predicciones.
- `results/informe.md` marca explícitamente **«EJECUCION INCOMPLETA»** y deja las
  métricas como `n/d`.
- Las pruebas unitarias (`tests/test_metrics.py`) validan las métricas sobre datos
  sintéticos marcados como `mock`; **no** se han volcado al informe.

## 6. Cómo desbloquear

1. Generar una API key nueva en <https://aistudio.google.com/apikey> con una cuenta
   cuyo proyecto **no** esté suspendido (o crear un proyecto nuevo en
   <https://console.cloud.google.com/> y habilitar *Generative Language API*). **Se necesita de facturacion**
2. Pegarla en `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...
   GEMINI_MODEL=gemini-flash-latest
   ```
3. Ejecutar:
   ```powershell
   python -m src.text_analysis
   python -m src.vision_analysis
   python -m src.evaluation
   ```
4. `results/informe.md` se regenera con las métricas reales y la sección
   «EJECUCION INCOMPLETA» desaparece automáticamente.

> **Nota de seguridad:** las API keys facilitadas por cualquier medio quedan expuestas en
> el historial. Deben revocarse y regenerarse. Este repositorio no las contiene:
> `.env` está en `.gitignore`.
