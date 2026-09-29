"""Tests de las metricas de evaluacion (sin llamadas a la API).

Ejecutar:  python -m tests.test_metrics
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.evaluation import (  # noqa: E402
    build_report,
    char_similarity,
    evaluate_text,
    evaluate_vision,
    keyword_recall,
    normalize,
    prf,
    rouge_l,
)


def test_normalize() -> None:
    assert normalize("  Ávila,   CAFÉ! ") == "avila cafe"
    assert normalize("MÜLLER") == "muller"


def test_prf() -> None:
    m = prf(tp=8, fp=2, fn=2)
    assert m["precision"] == 0.8 and m["recall"] == 0.8 and m["f1"] == 0.8
    assert prf(0, 0, 0)["f1"] == 0.0


def test_rouge_l() -> None:
    assert rouge_l("el gato negro salto", "el gato negro salto")["f1"] == 1.0
    assert rouge_l("", "algo")["f1"] == 0.0
    assert 0.0 < rouge_l("el gato salto", "el gato negro salto")["f1"] < 1.0


def test_char_similarity() -> None:
    assert char_similarity("Hola Mundo", "hola mundo") == 1.0
    assert char_similarity("abc", "xyz") == 0.0


def test_keyword_recall() -> None:
    assert keyword_recall("Una taza roja sobre fondo blanco", ["taza", "roja", "blanco"]) == 1.0
    assert keyword_recall("nada que ver", ["taza", "roja"]) == 0.0
    assert keyword_recall("x", []) == 1.0


def _mock_text_results() -> dict:
    return {
        "meta": {"modelo": "mock", "fecha": "2026-01-01T00:00:00+00:00"},
        "textos": [
            {
                "id": "t01",
                "tipo": "noticia",
                "idioma_esperado": "es",
                "texto": "x",
                "predicciones": {
                    "idioma": {"ok": True, "data": {"idioma": "es"}},
                    "entidades": {
                        "ok": True,
                        "data": {"entidades": [{"texto": "Real Madrid", "tipo": "ORG"}]},
                    },
                    "sentimiento": {
                        "ok": True,
                        "data": {"etiqueta": "positivo", "score": 0.7},
                    },
                    "resumen": {"ok": True, "data": {"resumen": "Resumen de prueba"}},
                },
            }
        ],
        "error": None,
    }


def _mock_vision_results() -> dict:
    return {
        "meta": {"modelo": "mock", "fecha": "2026-01-01T00:00:00+00:00"},
        "imagenes": [
            {
                "archivo": "01_documento_escaneado.png",
                "predicciones": {
                    "ocr": {"ok": True, "data": {"texto": "ACTA DE REUNION\nFecha: 14 de marzo de 2026"}},
                    "descripcion": {"ok": True, "data": {"descripcion": "Documento de acta con texto y firma"}},
                    "escena": {"ok": True, "data": {"escena": "documento_escaneado"}},
                    "objetos": {"ok": True, "data": {"objetos": [{"nombre": "documento"}, {"nombre": "texto"}]}},
                },
            }
        ],
        "error": None,
    }


def test_evaluate_text() -> None:
    ev = evaluate_text(_mock_text_results())
    r = ev["resumen"]
    assert r["idioma"]["accuracy"] == 1.0
    assert r["sentimiento"]["accuracy"] == 1.0
    assert r["sentimiento"]["mae_score"] == 0.0
    assert r["entidades"]["recall"] == 1 / 8
    assert r["entidades"]["precision"] == 1.0
    assert r["resumen"]["rougeL_f1_medio"] is not None


def test_evaluate_vision() -> None:
    ev = evaluate_vision(_mock_vision_results())
    r = ev["resumen"]
    assert r["escena"]["accuracy"] == 1.0
    assert r["ocr"]["similitud_media"] is not None
    assert r["objetos"]["recall"] > 0


def test_build_report() -> None:
    te = evaluate_text(_mock_text_results())
    ve = evaluate_vision(_mock_vision_results())
    informe = build_report(te, ve, _mock_text_results(), _mock_vision_results())
    assert "## 1. Analisis de texto" in informe
    assert "## 3. Tabla comparativa" in informe


def main() -> int:
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS {t.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"  FAIL {t.__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} tests OK")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
