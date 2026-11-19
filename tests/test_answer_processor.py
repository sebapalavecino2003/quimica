"""Pruebas del procesador de respuestas y validación de propuestas."""

from src.moodle_parser import QuestionData, ControlItem, OptionItem
from src.gemini_client import QuestionAnalysis, FieldProposal
from src.answer_processor import process_question_analysis


def test_process_valid_select_proposal():
    q_data = QuestionData(
        question_id="q1",
        question_number="Pregunta 1",
        state="Sin responder aún",
        grade_info="10,00",
        question_type="multianswer",
        prompt_text="Seleccione la opción correcta",
        raw_html="<select id='sel1'><option value='A'>Opción A</option><option value='B'>Opción B</option></select>",
        controls=[
            ControlItem(
                control_id="sel1",
                control_type="select",
                name="resp_sel1",
                options=[
                    OptionItem(value="A", text="Opción A"),
                    OptionItem(value="B", text="Opción B"),
                ],
            )
        ],
    )

    analysis = QuestionAnalysis(
        question_id="q1",
        question_number="Pregunta 1",
        status="RESUELTO",
        overall_confidence="ALTA",
        summary="Deducción teórica",
        proposals=[
            FieldProposal(
                control_id="sel1",
                control_type="select",
                selected_value="B",
                confidence="ALTA",
                explanation="B es la respuesta correcta.",
            )
        ],
    )

    result = process_question_analysis(q_data, analysis)
    assert result.status == "LISTO_PARA_COMPLETAR"
    assert len(result.actions) == 1
    assert result.actions[0].is_valid
    assert result.actions[0].target_value == "B"


def test_process_invalid_select_proposal_flags_review():
    q_data = QuestionData(
        question_id="q1",
        question_number="Pregunta 1",
        state="Sin responder aún",
        grade_info="10,00",
        question_type="multianswer",
        prompt_text="Seleccione la opción correcta",
        raw_html="",
        controls=[
            ControlItem(
                control_id="sel1",
                control_type="select",
                name="resp_sel1",
                options=[
                    OptionItem(value="X", text="Opción X"),
                ],
            )
        ],
    )

    analysis = QuestionAnalysis(
        question_id="q1",
        question_number="Pregunta 1",
        status="RESUELTO",
        overall_confidence="ALTA",
        summary="Deducción",
        proposals=[
            FieldProposal(
                control_id="sel1",
                control_type="select",
                selected_value="VALOR_INEXISTENTE",
                confidence="ALTA",
                explanation="Intento de valor que no existe.",
            )
        ],
    )

    result = process_question_analysis(q_data, analysis)
    assert result.status == "PENDIENTE_REVISION"
    assert not result.actions[0].is_valid
    assert len(result.warnings) > 0


def test_process_low_confidence_marks_review():
    q_data = QuestionData(
        question_id="q2",
        question_number="Pregunta 2",
        state="Sin responder aún",
        grade_info="5,00",
        question_type="shortanswer",
        prompt_text="Ingrese el valor",
        raw_html="",
        controls=[
            ControlItem(
                control_id="txt1",
                control_type="text",
                name="resp_txt1",
            )
        ],
    )

    analysis = QuestionAnalysis(
        question_id="q2",
        question_number="Pregunta 2",
        status="AMBIGUO",
        overall_confidence="BAJA",
        summary="Pregunta ambigua",
        proposals=[
            FieldProposal(
                control_id="txt1",
                control_type="text",
                text_content="posible",
                confidence="BAJA",
                explanation="No hay suficiente certeza.",
            )
        ],
    )

    result = process_question_analysis(q_data, analysis)
    assert result.status == "PENDIENTE_REVISION"

