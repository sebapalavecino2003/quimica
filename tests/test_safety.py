"""Pruebas estrictas de seguridad: verificación de bloqueo de envíos y finalización."""

import pytest
from src.safety import (
    is_forbidden_text,
    is_forbidden_element,
    validate_safe_action,
    SecurityViolationError,
)


def test_forbidden_keywords_detection():
    forbidden_samples = [
        "Terminar intento...",
        "terminar intento",
        "Finalizar intento...",
        "FINALIZAR INTENTO",
        "Enviar todo y terminar",
        "enviar y terminar",
        "Entregar intento",
        "submit exam",
        "finishattempt",
    ]
    for text in forbidden_samples:
        assert is_forbidden_text(text), f"Fallo al detectar texto prohibido: {text}"


def test_allowed_navigation_keywords():
    allowed_samples = [
        "Siguiente página",
        "Página anterior",
        "Atrás",
        "Regresar a Curso",
        "Marcar pregunta",
    ]
    for text in allowed_samples:
        assert not is_forbidden_text(text), f"Texto válido falsamente bloqueado: {text}"


def test_forbidden_element_attributes():
    dangerous_elements = [
        {"name": "finishattempt", "value": "Terminar intento..."},
        {"type": "submit", "name": "submitbutton", "value": "Enviar todo y terminar"},
        {"class": "btn finish", "aria-label": "finalizar intento"},
    ]
    for attrs in dangerous_elements:
        assert is_forbidden_element(attrs), f"Atributos peligrosos no detectados: {attrs}"


def test_validate_safe_action_raises_security_exception():
    with pytest.raises(SecurityViolationError):
        validate_safe_action("Hacer click en Terminar intento...")

    with pytest.raises(SecurityViolationError):
        validate_safe_action("Click botón", element_data={"name": "finishattempt"})


def test_validate_safe_action_permits_safe_inputs():
    # Acciones que deben permitirse normalmente
    validate_safe_action("Rellenar campo de texto q1_a")
    validate_safe_action("Seleccionar opción select", element_data={"id": "menuq1", "name": "q1"})

