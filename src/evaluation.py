#!/usr/bin/env python3
"""Evaluacion de precision y generacion del informe comparativo.

Compara results/text_results.json y results/vision_results.json contra los
ground truths de data/ y escribe results/informe.md.

Uso:
    python -m src.evaluation
"""

from __future__ import annotations

import json
import re
import sys
import unicodedata
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
DATA = ROOT / "data"

PUNCT_RE = re.compile(r"[^\w\s%€$]", re.UNICODE)


# ---------------------------------------------------------------------------
# Normalizacion y metricas basicas
# ---------------------------------------------------------------------------
def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.casefold()
    text = PUNCT_RE.sub(" ", text)
    return " ".join(text.split())


def tokens(text: str) -> list[str]:
    return normalize(text).split()


def prf(tp: int, fp: int, fn: int) -> dict[str, float]:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f, 4)}


def rouge_l(pred: str, ref: str) -> dict[str, float]:
    a, b = tokens(pred), tokens(ref)
    if not a or not b:
        return {"p": 0.0, "r": 0.0, "f1": 0.0}
    m = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            m[i][j] = m[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1] else max(m[i - 1][j], m[i][j - 1])
    lcs = m[-1][-1]
    p, r = lcs / len(a), lcs / len(b)
    return {
        "p": round(p, 4),
        "r": round(r, 4),
        "f1": round(2 * p * r / (p + r), 4) if p + r else 0.0,
    }


def char_similarity(pred: str, ref: str) -> float:
    return round(SequenceMatcher(None, normalize(pred), normalize(ref)).ratio(), 4)


def keyword_recall(text: str, keywords: list[str]) -> float:
    if not keywords:
        return 1.0
    norm = normalize(text)
    hits = sum(1 for k in keywords if normalize(k) and normalize(k) in norm)
    return round(hits / len(keywords), 4)


# ---------------------------------------------------------------------------
# Evaluacion de texto
# ---------------------------------------------------------------------------
def evaluate_text(results: dict[str, Any]) -> dict[str, Any]:
    gt = json.loads((DATA / "ground_truth_texto.json").read_text(encoding="utf-8"))["esperado"]

    idioma_ok = 0
    idioma_n = 0
    sent_ok = 0
    sent_n = 0
    score_abs_err = 0.0
    ent_tp = ent_fp = ent_fn = 0
    ent_n = 0
    rouge_f1s: list[float] = []
    within40 = 0
    summary_n = 0
    detalle: list[dict[str, Any]] = []

    for reg in results.get("textos", []):
        tid = reg["id"]
        esperado = gt.get(tid)
        if not esperado:
            continue
        pred = reg.get("predicciones", {})
        fila: dict[str, Any] = {"id": tid, "tipo": reg.get("tipo"), "idioma_real": esperado["idioma"]}

        p_idioma = pred.get("idioma", {})
        if p_idioma.get("ok"):
            idioma_n += 1
            got = normalize(p_idioma["data"].get("idioma") or "")
            fila["idioma_pred"] = got
            if got == esperado["idioma"]:
                idioma_ok += 1
                fila["idioma_ok"] = True
            else:
                fila["idioma_ok"] = False

        p_ent = pred.get("entidades", {})
        pred_set = set()
        if p_ent.get("ok"):
            for e in p_ent["data"].get("entidades", []):
                if isinstance(e, dict):
                    val = e.get("texto")
                else:
                    val = e
                if val:
                    pred_set.add(normalize(val))
            gt_set = {normalize(e) for e in esperado["entidades"]}
            tp = len(pred_set & gt_set)
            fp = len(pred_set - gt_set)
            fn = len(gt_set - pred_set)
            ent_tp += tp
            ent_fp += fp
            ent_fn += fn
            ent_n += 1
            fila["entidades_pred"] = sorted(pred_set)
            fila["entidades_gt"] = sorted(gt_set)
            fila["entidades_aciertos"] = tp
            fila["entidades_faltan"] = fn
            fila["entidades_inventadas"] = fp

        p_sent = pred.get("sentimiento", {})
        if p_sent.get("ok"):
            sent_n += 1
            etiqueta = normalize(p_sent["data"].get("etiqueta") or "")
            score = float(p_sent["data"].get("score") or 0.0)
            fila["sentimiento_pred"] = etiqueta
            fila["sentimiento_score_pred"] = score
            fila["sentimiento_gt"] = esperado["sentimiento"]["etiqueta"]
            fila["sentimiento_ok"] = etiqueta == normalize(esperado["sentimiento"]["etiqueta"])
            if fila["sentimiento_ok"]:
                sent_ok += 1
            score_abs_err += abs(score - esperado["sentimiento"]["score"])

        p_res = pred.get("resumen", {})
        if p_res.get("ok"):
            summary_n += 1
            resumen = p_res["data"].get("resumen") or ""
            rl = rouge_l(resumen, esperado["resumen"])
            rouge_f1s.append(rl["f1"])
            fila["resumen_pred"] = resumen
            fila["resumen_rougeL_f1"] = rl["f1"]
            fila["resumen_palabras"] = len(tokens(resumen))
            if len(tokens(resumen)) <= 40:
                within40 += 1

        fila["latencias_s"] = {
            k: v.get("latencia_s") for k, v in pred.items() if isinstance(v, dict) and v.get("latencia_s")
        }
        detalle.append(fila)

    resumen = {
        "n_textos": len(results.get("textos", [])),
        "idioma": {"accuracy": round(idioma_ok / idioma_n, 4) if idioma_n else None, "evaluados": idioma_n},
        "entidades": {
            **prf(ent_tp, ent_fp, ent_fn),
            "tp": ent_tp, "fp": ent_fp, "fn": ent_fn, "evaluados": ent_n,
        },
        "sentimiento": {
            "accuracy": round(sent_ok / sent_n, 4) if sent_n else None,
            "mae_score": round(score_abs_err / sent_n, 4) if sent_n else None,
            "evaluados": sent_n,
        },
        "resumen": {
            "rougeL_f1_medio": round(sum(rouge_f1s) / len(rouge_f1s), 4) if rouge_f1s else None,
            "dentro_40_palabras": round(within40 / summary_n, 4) if summary_n else None,
            "evaluados": summary_n,
        },
    }
    return {"resumen": resumen, "detalle": detalle}


# ---------------------------------------------------------------------------
# Evaluacion de vision
# ---------------------------------------------------------------------------
def evaluate_vision(results: dict[str, Any]) -> dict[str, Any]:
    gt = json.loads((DATA / "ground_truth_vision.json").read_text(encoding="utf-8"))["imagenes"]

    ocr_sims: list[float] = []
    desc_recalls: list[float] = []
    escena_ok = escena_n = 0
    obj_tp = obj_fp = obj_fn = 0
    obj_n = 0
    detalle: list[dict[str, Any]] = []

    for reg in results.get("imagenes", []):
        name = reg["archivo"]
        esperado = gt.get(name)
        if not esperado:
            continue
        pred = reg.get("predicciones", {})
        fila: dict[str, Any] = {"archivo": name, "tipo_tarea": esperado["tipo_tarea"]}

        p_ocr = pred.get("ocr", {})
        if p_ocr.get("ok"):
            texto = p_ocr["data"].get("texto") or ""
            sim = char_similarity(texto, esperado["ocr_esperado"]) if esperado["ocr_esperado"] else 1.0
            ocr_sims.append(sim)
            fila["ocr_similitud"] = sim
            fila["ocr_pred"] = texto
            fila["ocr_gt"] = esperado["ocr_esperado"]

        p_desc = pred.get("descripcion", {})
        if p_desc.get("ok"):
            desc = p_desc["data"].get("descripcion") or ""
            rec = keyword_recall(desc, esperado["descripcion_keywords"])
            desc_recalls.append(rec)
            fila["descripcion"] = desc
            fila["descripcion_keyword_recall"] = rec

        p_esc = pred.get("escena", {})
        if p_esc.get("ok"):
            escena_n += 1
            got = normalize(p_esc["data"].get("escena") or "")
            want = normalize(esperado["escena_esperada"])
            fila["escena_pred"] = got
            fila["escena_gt"] = want
            fila["escena_ok"] = got == want
            if fila["escena_ok"]:
                escena_ok += 1

        p_obj = pred.get("objetos", {})
        if p_obj.get("ok"):
            pred_set: set[str] = set()
            for o in p_obj["data"].get("objetos", []):
                val = o.get("nombre") if isinstance(o, dict) else o
                if val:
                    pred_set.add(normalize(val))
            gt_set = {normalize(o) for o in esperado["objetos_esperados"]}
            tp = len(pred_set & gt_set)
            fp = len(pred_set - gt_set)
            fn = len(gt_set - pred_set)
            obj_tp += tp
            obj_fp += fp
            obj_fn += fn
            obj_n += 1
            fila["objetos_pred"] = sorted(pred_set)
            fila["objetos_gt"] = sorted(gt_set)
            fila["objetos_aciertos"] = tp
            fila["objetos_faltan"] = fn
            fila["objetos_inventados"] = fp

        detalle.append(fila)

    resumen = {
        "n_imagenes": len(results.get("imagenes", [])),
        "ocr": {
            "similitud_media": round(sum(ocr_sims) / len(ocr_sims), 4) if ocr_sims else None,
            "evaluadas": len(ocr_sims),
        },
        "descripcion": {
            "keyword_recall_medio": round(sum(desc_recalls) / len(desc_recalls), 4) if desc_recalls else None,
            "evaluadas": len(desc_recalls),
        },
        "escena": {"accuracy": round(escena_ok / escena_n, 4) if escena_n else None, "evaluadas": escena_n},
        "objetos": {
            **prf(obj_tp, obj_fp, obj_fn),
            "tp": obj_tp, "fp": obj_fp, "fn": obj_fn, "evaluados": obj_n,
        },
    }
    return {"resumen": resumen, "detalle": detalle}


# ---------------------------------------------------------------------------
# Informe
# ---------------------------------------------------------------------------
def _pct(v: Any) -> str:
    return f"{v * 100:.1f}%" if isinstance(v, (int, float)) else "n/d"


def _tabla(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def build_report(
    text_eval: dict[str, Any] | None,
    vision_eval: dict[str, Any] | None,
    text_results: dict[str, Any] | None,
    vision_results: dict[str, Any] | None,
) -> str:
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    modelo = (
        (text_results or {}).get("meta", {}).get("modelo")
        or (vision_results or {}).get("meta", {}).get("modelo")
        or "desconocido"
    )
    errores = [
        r.get("error")
        for r in (text_results, vision_results)
        if isinstance(r, dict) and r.get("error")
    ]

    lines: list[str] = []
    lines.append("# Informe de resultados - Analisis con Gemini\n")
    lines.append(f"- **Generado:** {now}")
    lines.append(f"- **Modelo:** `{modelo}`")
    def _completados(registros: list) -> int:
        return sum(
            1
            for reg in registros
            if any(
                isinstance(p, dict) and p.get("ok")
                for p in (reg.get("predicciones") or {}).values()
            )
        )

    lines.append(
        f"- **Textos analizados:** {_completados((text_results or {}).get('textos', []))} / 10"
    )
    lines.append(
        f"- **Imagenes analizadas:** {_completados((vision_results or {}).get('imagenes', []))} / 5"
    )
    lines.append("")

    if errores:
        lines.append("## Estado: EJECUCION INCOMPLETA\n")
        lines.append("La API de Gemini no ha podido procesar el conjunto completo. Error registrado:\n")
        for e in errores:
            if e:
                lines.append(f"- `{e.get('tipo')}`: {e.get('mensaje')}")
        lines.append("")
        lines.append(
            "Ver `docs/API_ERROR.md` para el detalle, la reproduccion y las condiciones "
            "necesarias para obtener las metricas reales.\n"
        )

    # ---- Texto ----
    lines.append("## 1. Analisis de texto\n")
    if text_eval:
        r = text_eval["resumen"]
        lines.append(_tabla(
            ["Tarea", "Metrica", "Valor", "Evaluados"],
            [
                ["Deteccion de idioma", "Accuracy", _pct(r["idioma"]["accuracy"]), r["idioma"]["evaluados"]],
                ["Entidades nombradas", "Precision", _pct(r["entidades"]["precision"]), r["entidades"]["evaluados"]],
                ["Entidades nombradas", "Recall", _pct(r["entidades"]["recall"]), "-"],
                ["Entidades nombradas", "F1", _pct(r["entidades"]["f1"]), "-"],
                ["Sentimiento", "Accuracy etiqueta", _pct(r["sentimiento"]["accuracy"]), r["sentimiento"]["evaluados"]],
                ["Sentimiento", "MAE score (-1..1)", str(r["sentimiento"]["mae_score"]), r["sentimiento"]["evaluados"]],
                ["Resumen", "ROUGE-L F1 medio", str(r["resumen"]["rougeL_f1_medio"]), r["resumen"]["evaluados"]],
                ["Resumen", "% <= 40 palabras", _pct(r["resumen"]["dentro_40_palabras"]), r["resumen"]["evaluados"]],
            ],
        ))
        lines.append("")
        lines.append("### Detalle por texto\n")
        rows = []
        for f in text_eval["detalle"]:
            rows.append([
                f["id"],
                f["tipo"],
                f.get("idioma_pred", "-"),
                "-" if "idioma_ok" not in f else ("OK" if f["idioma_ok"] else "FAIL"),
                f"{f.get('entidades_aciertos', 0)}/{len(f.get('entidades_gt', []))}",
                f.get("sentimiento_pred", "-"),
                "OK" if f.get("sentimiento_ok") else ("-" if "sentimiento_ok" not in f else "FAIL"),
                str(f.get("resumen_rougeL_f1", "-")),
            ])
        lines.append(_tabla(
            ["ID", "Tipo", "Idioma pred.", "Idioma", "Entidades", "Sentim. pred.", "Sentim.", "ROUGE-L"],
            rows,
        ))
        lines.append("")
    else:
        lines.append("_No hay resultados de texto disponibles._\n")

    # ---- Vision ----
    lines.append("## 2. Analisis de imagenes\n")
    if vision_eval:
        r = vision_eval["resumen"]
        lines.append(_tabla(
            ["Tarea", "Metrica", "Valor", "Evaluadas"],
            [
                ["OCR", "Similitud caracteres (med.)", str(r["ocr"]["similitud_media"]), r["ocr"]["evaluadas"]],
                ["Descripcion visual", "Keyword recall medio", _pct(r["descripcion"]["keyword_recall_medio"]), r["descripcion"]["evaluadas"]],
                ["Clasificacion de escena", "Accuracy", _pct(r["escena"]["accuracy"]), r["escena"]["evaluadas"]],
                ["Deteccion de objetos", "Precision", _pct(r["objetos"]["precision"]), r["objetos"]["evaluados"]],
                ["Deteccion de objetos", "Recall", _pct(r["objetos"]["recall"]), "-"],
                ["Deteccion de objetos", "F1", _pct(r["objetos"]["f1"]), "-"],
            ],
        ))
        lines.append("")
        lines.append("### Detalle por imagen\n")
        rows = []
        for f in vision_eval["detalle"]:
            rows.append([
                f["archivo"],
                f["tipo_tarea"],
                str(f.get("ocr_similitud", "-")),
                _pct(f.get("descripcion_keyword_recall")),
                f.get("escena_pred", "-"),
                "OK" if f.get("escena_ok") else ("-" if "escena_ok" not in f else "FAIL"),
                f"{f.get('objetos_aciertos', 0)}/{len(f.get('objetos_gt', []))}",
            ])
        lines.append(_tabla(
            ["Imagen", "Tarea", "OCR sim.", "Descr. recall", "Escena pred.", "Escena", "Objetos"],
            rows,
        ))
        lines.append("")
    else:
        lines.append("_No hay resultados de vision disponibles._\n")

    # ---- Comparativa ----
    lines.append("## 3. Tabla comparativa por tipo de tarea\n")
    rows = []
    if text_eval:
        r = text_eval["resumen"]
        rows += [
            ["Texto", "Clasificacion (idioma)", _pct(r["idioma"]["accuracy"]), "Exacta", "Alta"],
            ["Texto", "Extraccion (entidades)", _pct(r["entidades"]["f1"]), "F1", "Alta"],
            ["Texto", "Clasificacion (sentimiento)", _pct(r["sentimiento"]["accuracy"]), "Exacta", "Alta"],
            ["Texto", "Generacion (resumen)", str(r["resumen"]["rougeL_f1_medio"]), "ROUGE-L F1", "Media"],
        ]
    if vision_eval:
        r = vision_eval["resumen"]
        rows += [
            ["Vision", "OCR (documento)", str(r["ocr"]["similitud_media"]), "Similitud caracteres", "Alta"],
            ["Vision", "Descripcion visual", _pct(r["descripcion"]["keyword_recall_medio"]), "Keyword recall", "Media"],
            ["Vision", "Clasificacion de escena", _pct(r["escena"]["accuracy"]), "Exacta", "Alta"],
            ["Vision", "Deteccion de objetos", _pct(r["objetos"]["f1"]), "F1", "Alta"],
        ]
    if rows:
        lines.append(_tabla(["Dominio", "Tarea", "Resultado", "Metrica", "Robustez metrica"], rows))
        lines.append("")

    lines.append("## 4. Metodologia y limitaciones\n")
    lines.append(
        "- Ground truth anotado a mano en `data/ground_truth_texto.json` y "
        "`data/ground_truth_vision.json` (imagenes sinteticas generadas con Pillow, "
        "por lo que el texto OCR de referencia es exacto).\n"
        "- Las entidades anotadas **no son exhaustivas**: la precision de NER penaliza "
        "como falsos positivos entidades validas no anotadas, por lo que debe leerse "
        "como un limite superior del error.\n"
        "- El recall de palabras clave de descripcion es una aproximacion: no valora el orden ni la coherencia.\n"
        "- Temperatura 0 y JSON estructurado (`response_mime_type=application/json`) en todas las llamadas."
    )
    return "\n".join(lines) + "\n"


def main() -> int:
    text_results = vision_results = None
    text_path = RESULTS / "text_results.json"
    vision_path = RESULTS / "vision_results.json"

    if text_path.exists():
        text_results = json.loads(text_path.read_text(encoding="utf-8"))
    if vision_path.exists():
        vision_results = json.loads(vision_path.read_text(encoding="utf-8"))

    if not text_results and not vision_results:
        print("No hay results/*.json. Ejecuta antes:\n  python -m src.text_analysis\n  python -m src.vision_analysis")
        return 1

    text_eval = evaluate_text(text_results) if text_results and text_results.get("textos") else None
    vision_eval = evaluate_vision(vision_results) if vision_results and vision_results.get("imagenes") else None

    metricas = {"texto": text_eval, "vision": vision_eval}
    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "metricas.json").write_text(
        json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    informe = build_report(text_eval, vision_eval, text_results, vision_results)
    (RESULTS / "informe.md").write_text(informe, encoding="utf-8")
    print(f"Informe escrito en {RESULTS / 'informe.md'}")
    print(f"Metricas  escritas en {RESULTS / 'metricas.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
