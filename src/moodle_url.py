"""Módulo para análisis, validación y clasificación de enlaces Moodle."""

from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import parse_qs, urlparse


UrlKind = Literal["attempt", "view", "review", "course", "unknown"]


@dataclass
class MoodleUrlInfo:
    raw_url: str
    kind: UrlKind
    host: str
    is_valid: bool
    is_quiz: bool
    attempt_id: str | None = None
    cmid: str | None = None
    page: int | None = None
    course_id: str | None = None
    warnings: list[str] = field(default_factory=list)


def parse_moodle_url(url_str: str) -> MoodleUrlInfo:
    """Analiza una URL de Moodle e identifica sus componentes y tipo de recurso."""
    url_str = url_str.strip()
    if not url_str:
        return MoodleUrlInfo(
            raw_url="",
            kind="unknown",
            host="",
            is_valid=False,
            is_quiz=False,
            warnings=["URL vacía."],
        )

    if not url_str.startswith(("http://", "https://")):
        url_str = "https://" + url_str

    try:
        parsed = urlparse(url_str)
    except Exception as exc:
        return MoodleUrlInfo(
            raw_url=url_str,
            kind="unknown",
            host="",
            is_valid=False,
            is_quiz=False,
            warnings=[f"Error al analizar sintaxis de URL: {exc}"],
        )

    host = parsed.netloc
    path = parsed.path.lower()
    query_params = parse_qs(parsed.query)

    warnings: list[str] = []
    kind: UrlKind = "unknown"
    is_quiz = False
    attempt_id: str | None = query_params.get("attempt", [None])[0]
    cmid: str | None = query_params.get("cmid", [None])[0] or query_params.get("id", [None])[0]
    page_param = query_params.get("page", [None])[0]
    course_id: str | None = None

    page: int | None = None
    if page_param is not None and page_param.isdigit():
        page = int(page_param)

    if "/mod/quiz/attempt.php" in path:
        kind = "attempt"
        is_quiz = True
        if not attempt_id:
            warnings.append("URL de intento sin parámetro 'attempt'.")
    elif "/mod/quiz/view.php" in path:
        kind = "view"
        is_quiz = True
        warnings.append("URL de portada de cuestionario. No se ha iniciado un intento activo.")
    elif "/mod/quiz/review.php" in path:
        kind = "review"
        is_quiz = True
        warnings.append("URL de revisión. Este intento ya fue entregado o finalizado.")
    elif "/course/view.php" in path:
        kind = "course"
        course_id = query_params.get("id", [None])[0]
        warnings.append("La URL corresponde a la página principal de un curso, no a un cuestionario.")
    else:
        warnings.append("No se reconoció una ruta estándar de Moodle Quiz (/mod/quiz/).")

    is_valid = bool(host and (kind != "unknown" or is_quiz))

    return MoodleUrlInfo(
        raw_url=url_str,
        kind=kind,
        host=host,
        is_valid=is_valid,
        is_quiz=is_quiz,
        attempt_id=attempt_id,
        cmid=cmid,
        page=page,
        course_id=course_id,
        warnings=warnings,
    )

