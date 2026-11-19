"""Módulo de seguridad estricta para prevenir envíos o finalizaciones accidentales."""

import re
from typing import Any, Iterable


class SecurityViolationError(Exception):
    """Excepción lanzada cuando una acción viola la regla de no-envío."""
    pass


FORBIDDEN_KEYWORDS: list[str] = [
    "terminar intento",
    "finalizar intento",
    "enviar todo",
    "enviar y terminar",
    "entregar intento",
    "entregar",
    "finishattempt",
    "submit",
    "finish",
]

FORBIDDEN_ATTRIBUTES: list[str] = [
    "finishattempt",
    "submit",
    "finalizar",
    "terminar",
]


def normalize_text(text: str) -> str:
    """Normaliza texto para comparación eliminando espacios y signos."""
    if not text:
        return ""
    cleaned = re.sub(r"[^\w\s]", " ", text.lower())
    return " ".join(cleaned.split())


def is_forbidden_text(text: str) -> bool:
    """Verifica si un texto contiene palabras clave asociadas a finalización."""
    norm = normalize_text(text)
    for kw in FORBIDDEN_KEYWORDS:
        if kw in norm:
            return True
    return False


def is_forbidden_element(attributes: dict[str, Any]) -> bool:
    """Inspecciona los atributos de un elemento HTML para detectar si es de envío."""
    for key, val in attributes.items():
        if not val or not isinstance(val, str):
            continue
        val_norm = val.lower().strip()
        for kw in FORBIDDEN_KEYWORDS + FORBIDDEN_ATTRIBUTES:
            if kw in val_norm:
                return True
    return False


def validate_safe_action(action_description: str, element_data: dict[str, Any] | None = None) -> None:
    """Valida que una acción sea segura. Si detecta riesgo, lanza SecurityViolationError."""
    if is_forbidden_text(action_description):
        raise SecurityViolationError(
            f"ACCIÓN BLOQUEADA POR SEGURIDAD: '{action_description}' coincide con palabras de finalización."
        )

    if element_data and is_forbidden_element(element_data):
        raise SecurityViolationError(
            f"ACCIÓN BLOQUEADA POR SEGURIDAD: Atributos peligrosos detectados: {element_data}"
        )

