"""Módulo de inspección y extracción DOM de preguntas en Moodle (Solo Lectura)."""

from dataclasses import dataclass, field
from typing import Any
from playwright.sync_api import Page, Locator


@dataclass
class OptionItem:
    value: str
    text: str
    is_selected: bool = False


@dataclass
class ControlItem:
    control_id: str
    control_type: str  # 'radio', 'checkbox', 'select', 'text', 'textarea'
    name: str
    label_text: str = ""
    current_value: str = ""
    options: list[OptionItem] = field(default_factory=list)
    cell_context: str = ""  # Por ejemplo, fila/columna de tabla


@dataclass
class QuestionData:
    question_id: str
    question_number: str
    state: str
    grade_info: str
    question_type: str
    prompt_text: str
    raw_html: str
    controls: list[ControlItem] = field(default_factory=list)
    images_base64: list[str] = field(default_factory=list)


def extract_questions_from_page(page: Page) -> list[QuestionData]:
    """Extrae de forma segura y en modo solo lectura todas las preguntas del DOM de Moodle."""
    questions: list[QuestionData] = []
    question_nodes = page.locator(".que")
    count = question_nodes.count()

    for idx in range(count):
        q_loc = question_nodes.nth(idx)
        q_data = _parse_single_question(q_loc)
        if q_data:
            questions.append(q_data)

    return questions


def _parse_single_question(q_loc: Locator) -> QuestionData | None:
    """Parsea una pregunta individual a partir de su contenedor .que."""
    try:
        q_id = q_loc.get_attribute("id") or f"q_unknown_{id(q_loc)}"
        classes = (q_loc.get_attribute("class") or "").split()

        q_type = "unknown"
        for cls in classes:
            if cls.startswith("que_") or cls in (
                "multichoice", "multianswer", "shortanswer", "match", "truefalse", "essay"
            ):
                q_type = cls.replace("que_", "")
                break

        # Metadatos del bloque .info
        info_loc = q_loc.locator(".info")
        q_num = ""
        q_state = ""
        q_grade = ""
        if info_loc.count() > 0:
            no_loc = info_loc.locator(".no")
            if no_loc.count() > 0:
                q_num = no_loc.first.inner_text().strip()

            state_loc = info_loc.locator(".state")
            if state_loc.count() > 0:
                q_state = state_loc.first.inner_text().strip()

            grade_loc = info_loc.locator(".grade")
            if grade_loc.count() > 0:
                q_grade = grade_loc.first.inner_text().strip()

        # Enunciado y contenido
        formulation = q_loc.locator(".content .formulation")
        if formulation.count() == 0:
            return None

        prompt_text = formulation.inner_text().strip()
        raw_html = formulation.inner_html()

        controls: list[ControlItem] = []

        # 1. Menús desplegables (select)
        select_locs = formulation.locator("select")
        select_count = select_locs.count()
        for s_idx in range(select_count):
            s = select_locs.nth(s_idx)
            s_id = s.get_attribute("id") or s.get_attribute("name") or f"sel_{s_idx}"
            s_name = s.get_attribute("name") or s_id
            options: list[OptionItem] = []

            opt_locs = s.locator("option")
            for o_idx in range(opt_locs.count()):
                opt = opt_locs.nth(o_idx)
                opt_val = opt.get_attribute("value") or ""
                opt_txt = opt.inner_text().strip()
                is_sel = opt.get_attribute("selected") is not None
                options.append(OptionItem(value=opt_val, text=opt_txt, is_selected=is_sel))

            controls.append(
                ControlItem(
                    control_id=s_id,
                    control_type="select",
                    name=s_name,
                    options=options,
                )
            )

        # 2. Radio buttons (opción múltiple simple)
        radio_locs = formulation.locator('input[type="radio"]')
        radio_count = radio_locs.count()
        for r_idx in range(radio_count):
            r = radio_locs.nth(r_idx)
            r_id = r.get_attribute("id") or f"radio_{r_idx}"
            r_name = r.get_attribute("name") or ""
            r_val = r.get_attribute("value") or ""
            is_checked = r.is_checked()

            # Buscar etiqueta asociada
            label_text = ""
            label_loc = formulation.locator(f'label[for="{r_id}"]')
            if label_loc.count() > 0:
                label_text = label_loc.first.inner_text().strip()

            controls.append(
                ControlItem(
                    control_id=r_id,
                    control_type="radio",
                    name=r_name,
                    label_text=label_text,
                    current_value=r_val,
                    options=[OptionItem(value=r_val, text=label_text, is_selected=is_checked)],
                )
            )

        # 3. Checkboxes (opción múltiple múltiple)
        check_locs = formulation.locator('input[type="checkbox"]')
        check_count = check_locs.count()
        for c_idx in range(check_count):
            c = check_locs.nth(c_idx)
            c_id = c.get_attribute("id") or f"check_{c_idx}"
            c_name = c.get_attribute("name") or ""
            c_val = c.get_attribute("value") or ""
            is_checked = c.is_checked()

            label_text = ""
            label_loc = formulation.locator(f'label[for="{c_id}"]')
            if label_loc.count() > 0:
                label_text = label_loc.first.inner_text().strip()

            controls.append(
                ControlItem(
                    control_id=c_id,
                    control_type="checkbox",
                    name=c_name,
                    label_text=label_text,
                    current_value=c_val,
                    options=[OptionItem(value=c_val, text=label_text, is_selected=is_checked)],
                )
            )

        # 4. Inputs de texto (short answer / celdas de tablas)
        text_locs = formulation.locator('input[type="text"]')
        text_count = text_locs.count()
        for t_idx in range(text_count):
            t = text_locs.nth(t_idx)
            t_id = t.get_attribute("id") or f"text_{t_idx}"
            t_name = t.get_attribute("name") or t_id
            curr_val = t.input_value()

            controls.append(
                ControlItem(
                    control_id=t_id,
                    control_type="text",
                    name=t_name,
                    current_value=curr_val,
                )
            )

        # 5. Textareas (respuestas abiertas)
        area_locs = formulation.locator("textarea")
        area_count = area_locs.count()
        for a_idx in range(area_count):
            a = area_locs.nth(a_idx)
            a_id = a.get_attribute("id") or f"area_{a_idx}"
            a_name = a.get_attribute("name") or a_id
            curr_val = a.input_value()

            controls.append(
                ControlItem(
                    control_id=a_id,
                    control_type="textarea",
                    name=a_name,
                    current_value=curr_val,
                )
            )

        return QuestionData(
            question_id=q_id,
            question_number=q_num,
            state=q_state,
            grade_info=q_grade,
            question_type=q_type,
            prompt_text=prompt_text,
            raw_html=raw_html,
            controls=controls,
        )
    except Exception:
        return None

