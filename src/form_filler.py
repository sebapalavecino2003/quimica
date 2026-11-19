"""Módulo para el completado seguro de campos en el navegador (Sin envíos)."""

from dataclasses import dataclass
from playwright.sync_api import Page, Locator
from src.safety import validate_safe_action, SecurityViolationError
from src.answer_processor import ValidatedAction, ProcessedQuestionResult


@dataclass
class FillReport:
    control_id: str
    control_type: str
    status: str  # 'COMPLETADO', 'OMITIDO_POR_REVISION', 'ERROR'
    verified: bool = False
    details: str = ""


class FormFiller:
    def __init__(self, page: Page):
        self.page = page

    def fill_question_safely(self, processed_q: ProcessedQuestionResult) -> list[FillReport]:
        """Aplica únicamente las acciones validadas y seguras sobre la página."""
        reports: list[FillReport] = []

        if processed_q.status == "PENDIENTE_REVISION" and not processed_q.actions:
            return [
                FillReport(
                    control_id=processed_q.question_id,
                    control_type="question",
                    status="OMITIDO_POR_REVISION",
                    verified=False,
                    details="Pregunta marcada para revisión humana.",
                )
            ]

        for act in processed_q.actions:
            if not act.is_valid:
                reports.append(
                    FillReport(
                        control_id=act.control_id,
                        control_type=act.control_type,
                        status="OMITIDO_POR_REVISION",
                        verified=False,
                        details=act.error_message or "Acción inválida.",
                    )
                )
                continue

            report = self._apply_single_action(act)
            reports.append(report)

        return reports

    def _apply_single_action(self, act: ValidatedAction) -> FillReport:
        """Aplica una acción individual en el control correspondiente."""
        # Validación de seguridad estricta
        validate_safe_action(f"Interactuar con control {act.control_id}")

        try:
            # Selector flexible: busca por ID exacto o por atributo name
            selector = f"#{act.control_id}" if not act.control_id.startswith("#") else act.control_id
            loc = self.page.locator(selector)
            if loc.count() == 0:
                # Intentar por name
                loc = self.page.locator(f'[name="{act.control_id}"]')

            if loc.count() == 0:
                return FillReport(
                    control_id=act.control_id,
                    control_type=act.control_type,
                    status="ERROR",
                    verified=False,
                    details=f"No se encontró el elemento con id/name '{act.control_id}' en el DOM.",
                )

            target = loc.first

            if act.action_type == "select":
                # Seleccionar opción por valor o texto
                target.select_option(value=act.target_value)
                # Verificación
                curr_val = target.input_value()
                is_ok = (curr_val == act.target_value)
                return FillReport(
                    control_id=act.control_id,
                    control_type="select",
                    status="COMPLETADO" if is_ok else "ERROR",
                    verified=is_ok,
                    details=f"Valor seleccionado: {act.target_value}",
                )

            elif act.action_type == "check":
                target.check()
                is_ok = target.is_checked()
                return FillReport(
                    control_id=act.control_id,
                    control_type=act.control_type,
                    status="COMPLETADO" if is_ok else "ERROR",
                    verified=is_ok,
                    details="Opción marcada.",
                )

            elif act.action_type == "fill":
                target.fill(act.target_value)
                curr_val = target.input_value()
                is_ok = (curr_val == act.target_value)
                return FillReport(
                    control_id=act.control_id,
                    control_type=act.control_type,
                    status="COMPLETADO" if is_ok else "ERROR",
                    verified=is_ok,
                    details=f"Texto completado: {act.target_value[:30]}...",
                )

            else:
                return FillReport(
                    control_id=act.control_id,
                    control_type=act.control_type,
                    status="ERROR",
                    verified=False,
                    details=f"Tipo de acción desconocido: {act.action_type}",
                )

        except SecurityViolationError as sec_err:
            raise sec_err
        except Exception as exc:
            return FillReport(
                control_id=act.control_id,
                control_type=act.control_type,
                status="ERROR",
                verified=False,
                details=f"Excepción al completar: {exc}",
            )

