"""Módulo de presentación de resultados, reportes y revisión en terminal."""

from src.answer_processor import ProcessedQuestionResult
from src.form_filler import FillReport


def display_header() -> None:
    print("\n" + "=" * 50)
    print("        ASISTENTE MOODLE + GEMINI")
    print("=" * 50)


def display_final_report(
    total_detected: int,
    results: list[ProcessedQuestionResult],
    fill_reports: list[list[FillReport]],
) -> None:
    """Muestra el reporte detallado en el formato especificado."""
    completed_fields = 0
    pending_review = 0

    for q_reports in fill_reports:
        for r in q_reports:
            if r.status == "COMPLETADO":
                completed_fields += 1
            elif r.status in ("OMITIDO_POR_REVISION", "ERROR"):
                pending_review += 1

    print("\n" + "=" * 50)
    print("        ANALISIS DE MOODLE + GEMINI")
    print("=" * 50)
    print(f"Preguntas detectadas:     {total_detected}")
    print(f"Preguntas analizadas:     {len(results)}")
    print(f"Campos completados:       {completed_fields}")
    print(f"Pendientes de revisión:   {pending_review}")
    print("-" * 50)
    print("DETALLE POR PREGUNTA")
    print("-" * 50)

    for idx, (res, reports) in enumerate(zip(results, fill_reports), start=1):
        num_str = res.question_number or f"Pregunta {idx}"
        status_label = "Completada" if res.status == "LISTO_PARA_COMPLETAR" else "Pendiente de revisión"
        print(f"\n{num_str}: {status_label}")
        print(f"Confianza: {res.overall_confidence.capitalize()}")
        if res.summary:
            print(f"Resumen:   {res.summary}")
        if res.warnings:
            print("Motivos de revisión:")
            for w in res.warnings:
                print(f"  • {w}")

    print("\n" + "-" * 50)
    print("ANALISIS COMPLETADO.")
    print("")
    print("Las respuestas propuestas por Gemini fueron cargadas en Moodle.")
    print("El cuestionario NO fue enviado ni finalizado.")
    print("El navegador permanece abierto para que puedas revisar y")
    print("modificar las respuestas manualmente.")
    print("=" * 50 + "\n")

