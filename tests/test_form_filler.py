"""Pruebas del completador seguro de formularios."""

from unittest.mock import MagicMock
from src.form_filler import FormFiller, ValidatedAction, ProcessedQuestionResult
from src.safety import SecurityViolationError
import pytest


def test_fill_skips_invalid_actions():
    page_mock = MagicMock()
    filler = FormFiller(page_mock)

    proc_q = ProcessedQuestionResult(
        question_id="q1",
        question_number="Pregunta 1",
        status="PENDIENTE_REVISION",
        overall_confidence="MEDIA",
        summary="Revisión necesaria",
        actions=[
            ValidatedAction(
                control_id="btn_dangerous",
                control_type="select",
                action_type="select",
                target_value="val",
                is_valid=False,
                confidence="BAJA",
                explanation="Inválido",
                error_message="Opción no disponible",
            )
        ],
    )

    reports = filler.fill_question_safely(proc_q)
    assert len(reports) == 1
    assert reports[0].status == "OMITIDO_POR_REVISION"
    page_mock.locator.assert_not_called()


def test_fill_blocks_forbidden_control_id():
    page_mock = MagicMock()
    filler = FormFiller(page_mock)

    proc_q = ProcessedQuestionResult(
        question_id="q1",
        question_number="Pregunta 1",
        status="LISTO_PARA_COMPLETAR",
        overall_confidence="ALTA",
        summary="Prueba de intento de submit",
        actions=[
            ValidatedAction(
                control_id="finishattempt_btn",
                control_type="button",
                action_type="check",
                target_value="submit",
                is_valid=True,
                confidence="ALTA",
                explanation="Intento malicioso",
            )
        ],
    )

    with pytest.raises(SecurityViolationError):
        filler.fill_question_safely(proc_q)

