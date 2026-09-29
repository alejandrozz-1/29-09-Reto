"""Infraestructura compartida: cliente Gemini, carga de .env y parseo robusto de JSON."""

from __future__ import annotations

import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any

# silencia el aviso interno del SDK sobre automatic function calling
logging.getLogger("google_genai").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)

ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = ROOT / "results"

try:
    from google import genai
    from google.genai import types as genai_types
except ImportError:  # pragma: no cover - dependencia declarada en requirements.txt
    genai = None
    genai_types = None

DEFAULT_MODEL = "gemini-flash-latest"


def load_env(path: Path | None = None) -> None:
    """Carga un fichero .env sencillo (KEY=VALUE) sin sobreescribir el entorno."""
    path = path or (ROOT / ".env")
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_model_name() -> str:
    load_env()
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


def get_api_key() -> str:
    load_env()
    for var in ("GEMINI_API_KEY", "GOOGLE_API_KEY", "GOOGLE_GENAI_API_KEY"):
        if os.environ.get(var):
            return os.environ[var]
    raise RuntimeError(
        "Falta la API key. Copia .env.example a .env y define GEMINI_API_KEY."
    )


def get_client() -> "genai.Client":
    if genai is None:
        raise RuntimeError("google-genai no esta instalado: pip install -r requirements.txt")
    return genai.Client(api_key=get_api_key())


class ApiError(RuntimeError):
    """Error irrecuperable de la API (403/401/429 bloqueantes)."""


def _extract_json(raw: str) -> Any:
    """Extrae el primer objeto/array JSON de una respuesta de modelo."""
    text = raw.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", text, re.DOTALL)
    if fence:
        text = fence.group(1).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for opener, closer in (("{", "}"), ("[", "]")):
        start = text.find(opener)
        if start == -1:
            continue
        depth = 0
        in_str = False
        esc = False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
                continue
            if ch == '"':
                in_str = True
            elif ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except json.JSONDecodeError:
                        break
    raise ValueError(f"Respuesta sin JSON valido: {raw[:400]}")


def generate_json(
    client: Any,
    model: str,
    prompt: str,
    *,
    system: str | None = None,
    image: Any = None,
    retries: int = 3,
    temperature: float = 0.0,
) -> Any:
    """Llama al modelo pidiendo JSON y devuelve el objeto ya parseado.

    Lanza ApiError ante 401/403 (clave/proyecto bloqueado) porque reintentar
    no tiene sentido en esos casos.
    """
    config_kwargs: dict[str, Any] = {
        "temperature": temperature,
        "response_mime_type": "application/json",
    }
    if system:
        config_kwargs["system_instruction"] = system

    contents: Any
    if image is not None:
        contents = [
            genai_types.Part.from_bytes(data=image, mime_type="image/png"),
            genai_types.Part.from_text(text=prompt),
        ]
    else:
        contents = prompt

    last_exc: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            response = client.models.generate_content(
                model=model, contents=contents, config=genai_types.GenerateContentConfig(**config_kwargs)
            )
            if not response.text:
                raise ValueError("Respuesta vacia del modelo")
            return _extract_json(response.text)
        except Exception as exc:  # noqa: BLE001 - normalizado abajo
            msg = str(exc)
            if "403" in msg or "PERMISSION_DENIED" in msg or "401" in msg or "UNAUTHENTICATED" in msg:
                raise ApiError(msg) from exc
            last_exc = exc
            if attempt < retries:
                time.sleep(2 * attempt)
    raise RuntimeError(f"Fallo tras {retries} intentos: {last_exc}")
