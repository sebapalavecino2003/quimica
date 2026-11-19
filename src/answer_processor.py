"""Módulo de validación y procesamiento de respuestas propuestas por Gemini."""

from dataclasses import dataclass, field
from src.gemini_client import QuestionAnalysis, FieldProposal
from src.moodle_parser import QuestionData, ControlItem


@dataclass
class ValidatedAction:
    control_id: str
    control_type: str
    action_type: str  # 'check', 'select', 'fill'
    target_value: str
    is_valid: bool
    confidence: str
    explanation: str
    error_message: str | None = None


@dataclass
class ProcessedQuestionResult:
    question_id: str
    question_number: str
    status: str  # 'LISTO_PARA_COMPLETAR', 'PENDIENTE_REVISION', 'ERROR'
    overall_confidence: str
    summary: str
    actions: list[ValidatedAction] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def process_question_analysis(
    question_data: QuestionData,
    analysis: QuestionAnalysis,
) -> ProcessedQuestionResult:
    """Valida cada propuesta de Gemini contra los controles reales del DOM."""
    control_map: dict[str, ControlItem] = {c.control_id: c for c in question_data.controls}
    # Mapa secundario por nombre de control para robustez
    name_map: dict[str, ControlItem] = {c.name: c for c in question_data.controls if c.name}

    actions: list[ValidatedAction] = []
    warnings: list[str] = list(analysis.warnings)
    has_errors = False
    has_low_confidence = analysis.overall_confidence == "BAJA"

    for prop in analysis.proposals:
        ctrl = control_map.get(prop.control_id) or name_map.get(prop.control_id)

        if not ctrl:
            warnings.append(f"Control no encontrado en el DOM: {prop.control_id}")
            actions.append(
                ValidatedAction(
                    control_id=prop.control_id,
                    control_type=prop.control_type,
                    action_type="unknown",
                    target_value=prop.selected_value or prop.text_content or "",
                    is_valid=False,
                    confidence=prop.confidence,
                    explanation=prop.explanation,
                    error_message=f"Elemento {prop.control_id} no existe en la página actual.",
                )
            )
            has_errors = True
            continue

        # Validación por tipo
        if ctrl.control_type == "select":
            selected_val = prop.selected_value or ""
            # Buscar coincidencia exacta por value o por texto de la opción
            matching_opt = None
            for opt in ctrl.options:
                if opt.value == selected_val or opt.text.strip().lower() == selected_val.strip().lower():
                    matching_opt = opt
                    break

            if matching_opt:
                actions.append(
                    ValidatedAction(
                        control_id=ctrl.control_id,
                        control_type="select",
                        action_type="select",
                        target_value=matching_opt.value,
                        is_valid=True,
                        confidence=prop.confidence,
                        explanation=prop.explanation,
                    )
                )
            else:
                warnings.append(
                    f"Opción propuesta '{selected_val}' no coincide con las opciones del desplegable {ctrl.control_id}."
                )
                actions.append(
                    ValidatedAction(
                        control_id=ctrl.control_id,
                        control_type="select",
                        action_type="select",
                        target_value=selected_val,
                        is_valid=False,
                        confidence=prop.confidence,
                        explanation=prop.explanation,
                        error_message="Opción no válida para el menú desplegable.",
                    )
                )
                has_errors = True

        elif ctrl.control_type in ("radio", "checkbox"):
            val_to_check = prop.selected_value or ctrl.current_value
            actions.append(
                ValidatedAction(
                    control_id=ctrl.control_id,
                    control_type=ctrl.control_type,
                    action_type="check",
                    target_value=val_to_check,
                    is_valid=True,
                    confidence=prop.confidence,
                    explanation=prop.explanation,
                )
            )

        elif ctrl.control_type in ("text", "textarea"):
            text_val = prop.text_content or prop.selected_value or ""
            actions.append(
                ValidatedAction(
                    control_id=ctrl.control_id,
                    control_type=ctrl.control_type,
                    action_type="fill",
                    target_value=text_val,
                    is_valid=True,
                    confidence=prop.confidence,
                    explanation=prop.explanation,
                )
            )

    # Determinar estado
    if has_errors or has_low_confidence or analysis.status in ("AMBIGUO", "REQUIERE_REVISION"):
        status = "PENDIENTE_REVISION"
    else:
        status = "LISTO_PARA_COMPLETAR"

    return ProcessedQuestionResult(
        question_id=question_data.question_id,
        question_number=question_data.question_number,
        status=status,
        overall_confidence=analysis.overall_confidence,
        summary=analysis.summary,
        actions=actions,
        warnings=warnings,
    )

