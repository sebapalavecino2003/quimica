"""Pruebas del módulo de análisis de URLs de Moodle."""

from src.moodle_url import parse_moodle_url


def test_parse_attempt_url():
    url = "https://campus.ejemplo.edu/mod/quiz/attempt.php?attempt=206895&cmid=339200&page=17"
    info = parse_moodle_url(url)
    assert info.is_valid
    assert info.is_quiz
    assert info.kind == "attempt"
    assert info.attempt_id == "206895"
    assert info.cmid == "339200"
    assert info.page == 17
    assert info.host == "campus.ejemplo.edu"


def test_parse_view_url():
    url = "https://campus.ejemplo.edu.ar/mod/quiz/view.php?id=123"
    info = parse_moodle_url(url)
    assert info.is_valid
    assert info.is_quiz
    assert info.kind == "view"
    assert info.cmid == "123"
    assert len(info.warnings) > 0


def test_parse_review_url():
    url = "https://campus.ejemplo.edu.ar/mod/quiz/review.php?attempt=456"
    info = parse_moodle_url(url)
    assert info.is_valid
    assert info.is_quiz
    assert info.kind == "review"
    assert info.attempt_id == "456"


def test_parse_course_url():
    url = "https://campus.ejemplo.edu.ar/course/view.php?id=10"
    info = parse_moodle_url(url)
    assert info.is_valid
    assert not info.is_quiz
    assert info.kind == "course"
    assert info.course_id == "10"


def test_parse_invalid_or_empty_url():
    empty_info = parse_moodle_url("")
    assert not empty_info.is_valid

    invalid_info = parse_moodle_url("no_es_una_url_valida")
    assert not invalid_info.is_quiz
