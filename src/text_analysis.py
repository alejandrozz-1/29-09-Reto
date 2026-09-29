#!/usr/bin/env python3
"""Reto del dia - Analisis avanzado de texto con Gemini.

Ejecuta 4 tareas (idioma, entidades, sentimiento, resumen) sobre los 10 textos
de data/textos.json y guarda la salida en results/text_results.json.

Uso:
    python -m src.text_analysis            # analisis completo
    python -m src.text_analysis --tareas idioma,sentimiento
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .gemini_common import RESULTS_DIR, ApiError, generate_json, get_client, get_model_name
from .prompts import TEXT_SYSTEM, TEXT_TASKS

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "textos.json"


def load_texts() -> list[dict[str, Any]]:
    return json.loads(DATA_FILE.read_text(encoding="utf-8"))["textos"]


def run(tasks: list[str], limit: int | None = None) -> dict[str, Any]:
    client = get_client()
    model = get_model_name()
    textos = load_texts()[:limit]

    resultados: dict[str, Any] = {
        "meta": {
            "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "modelo": model,
            "tareas": tasks,
            "n_textos": len(textos),
            "fuente": str(DATA_FILE.relative_to(DATA_FILE.parents[1])),
        },
        "textos": [],
        "error": None,
    }

    print(f"Modelo: {model} | textos: {len(textos)} | tareas: {', '.join(tasks)}")

    for i, texto in enumerate(textos, 1):
        registro: dict[str, Any] = {
            "id": texto["id"],
            "tipo": texto["tipo"],
            "idioma_esperado": texto["idioma_esperado"],
            "texto": texto["texto"],
            "predicciones": {},
        }
        print(f"  [{i}/{len(textos)}] {texto['id']} ({texto['tipo']})", end="", flush=True)
        for tarea in tasks:
            t0 = time.time()
            try:
                salida = generate_json(
                    client,
                    model,
                    TEXT_TASKS[tarea].format(text=texto["texto"]),
                    system=TEXT_SYSTEM,
                )
                registro["predicciones"][tarea] = {
                    "ok": True,
                    "latencia_s": round(time.time() - t0, 2),
                    "data": salida,
                }
                print(f" {tarea}:ok", end="", flush=True)
            except ApiError as exc:
                registro["predicciones"][tarea] = {"ok": False, "error": str(exc)}
                resultados["error"] = {
                    "tipo": "ApiError",
                    "mensaje": str(exc),
                    "tarea": tarea,
                    "texto_id": texto["id"],
                }
                print(f"\n  ABORTADO por error de API en '{tarea}': {exc}")
                resultados["textos"].append(registro)
                return resultados
            except Exception as exc:  # noqa: BLE001
                registro["predicciones"][tarea] = {"ok": False, "error": str(exc)}
                print(f" {tarea}:FAIL", end="", flush=True)
        print()
        resultados["textos"].append(registro)

    return resultados


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisis de texto con Gemini")
    parser.add_argument(
        "--tareas",
        default="idioma,entidades,sentimiento,resumen",
        help="Lista separada por comas: idioma,entidades,sentimiento,resumen",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limitar numero de textos")
    parser.add_argument("-o", "--output", default=None, help="Ruta de salida JSON")
    args = parser.parse_args()

    tasks = [t.strip() for t in args.tareas.split(",") if t.strip()]
    desconocidas = [t for t in tasks if t not in TEXT_TASKS]
    if desconocidas:
        parser.error(f"tareas desconocidas: {desconocidas}. Validas: {list(TEXT_TASKS)}")

    try:
        resultados = run(tasks, args.limit)
    except (ApiError, RuntimeError) as exc:
        resultados = {
            "meta": {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds")},
            "textos": [],
            "error": {"tipo": type(exc).__name__, "mensaje": str(exc)},
        }
        print(f"\nERROR: {exc}", file=sys.stderr)

    RESULTS_DIR.mkdir(exist_ok=True)
    salida = Path(args.output) if args.output else RESULTS_DIR / "text_results.json"
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados escritos en {salida}")
    return 1 if resultados.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
