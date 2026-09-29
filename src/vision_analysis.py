#!/usr/bin/env python3
"""Reto del dia - Analisis de imagenes con Gemini (OCR, descripcion, escena, objetos).

Procesa las 5 imagenes de images/ y guarda la salida en results/vision_results.json.

Uso:
    python -m src.vision_analysis
    python -m src.vision_analysis --tareas ocr,escena
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
from .prompts import VISION_SYSTEM, VISION_TASKS

IMAGES_DIR = Path(__file__).resolve().parent.parent / "images"
IMAGE_GLOB = "*.png"


def run(tasks: list[str], limit: int | None = None) -> dict[str, Any]:
    client = get_client()
    model = get_model_name()
    imagenes = sorted(IMAGES_DIR.glob(IMAGE_GLOB))[:limit]

    resultados: dict[str, Any] = {
        "meta": {
            "fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "modelo": model,
            "tareas": tasks,
            "n_imagenes": len(imagenes),
            "directorio": "images/",
        },
        "imagenes": [],
        "error": None,
    }

    print(f"Modelo: {model} | imagenes: {len(imagenes)} | tareas: {', '.join(tasks)}")

    for i, path in enumerate(imagenes, 1):
        blob = path.read_bytes()
        registro: dict[str, Any] = {
            "archivo": path.name,
            "predicciones": {},
        }
        print(f"  [{i}/{len(imagenes)}] {path.name}", end="", flush=True)
        for tarea in tasks:
            t0 = time.time()
            try:
                salida = generate_json(
                    client,
                    model,
                    VISION_TASKS[tarea],
                    system=VISION_SYSTEM,
                    image=blob,
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
                    "imagen": path.name,
                }
                print(f"\n  ABORTADO por error de API en '{tarea}': {exc}")
                resultados["imagenes"].append(registro)
                return resultados
            except Exception as exc:  # noqa: BLE001
                registro["predicciones"][tarea] = {"ok": False, "error": str(exc)}
                print(f" {tarea}:FAIL", end="", flush=True)
        print()
        resultados["imagenes"].append(registro)

    return resultados


def main() -> int:
    parser = argparse.ArgumentParser(description="Analisis de vision con Gemini")
    parser.add_argument(
        "--tareas",
        default="ocr,descripcion,escena,objetos",
        help="Lista separada por comas: ocr,descripcion,escena,objetos",
    )
    parser.add_argument("--limit", type=int, default=None, help="Limitar numero de imagenes")
    parser.add_argument("-o", "--output", default=None, help="Ruta de salida JSON")
    args = parser.parse_args()

    tasks = [t.strip() for t in args.tareas.split(",") if t.strip()]
    desconocidas = [t for t in tasks if t not in VISION_TASKS]
    if desconocidas:
        parser.error(f"tareas desconocidas: {desconocidas}. Validas: {list(VISION_TASKS)}")

    try:
        resultados = run(tasks, args.limit)
    except (ApiError, RuntimeError) as exc:
        resultados = {
            "meta": {"fecha": datetime.now(timezone.utc).isoformat(timespec="seconds")},
            "imagenes": [],
            "error": {"tipo": type(exc).__name__, "mensaje": str(exc)},
        }
        print(f"\nERROR: {exc}", file=sys.stderr)

    RESULTS_DIR.mkdir(exist_ok=True)
    salida = Path(args.output) if args.output else RESULTS_DIR / "vision_results.json"
    salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nResultados escritos en {salida}")
    return 1 if resultados.get("error") else 0


if __name__ == "__main__":
    raise SystemExit(main())
