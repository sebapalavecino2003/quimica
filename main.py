"""Punto de entrada principal del asistente inteligente para Moodle con Gemini y Playwright."""

import sys
import time
from src.config import Config
from src.moodle_url import parse_moodle_url
from src.browser import BrowserManager, ChromeNotFoundError, ProfileLockedError
from src.moodle_parser import extract_questions_from_page
from src.gemini_client import GeminiQuizClient
from src.answer_processor import process_question_analysis
from src.form_filler import FormFiller
from src.review import display_header, display_final_report


def prompt_moodle_url() -> str:
    """Solicita interactivamente la URL de Moodle al usuario."""
    print("\nIntroducí la URL del cuestionario de Moodle:")
    try:
        url = input("URL: ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\nOperación cancelada por el usuario.")
        sys.exit(0)
    return url


def main() -> None:
    display_header()

    # 1. Validación de clave de API de Gemini
    if not Config.validate_api_key():
        print("\n[ERROR] No se encontró la variable GEMINI_API_KEY en el entorno.")
        print("Instrucciones:")
        print("  1. Creá el archivo .env copiando .env.example: cp .env.example .env")
        print("  2. Obtené una clave de API gratuita en: https://aistudio.google.com/")
        print("  3. Colocá tu clave en el archivo .env: GEMINI_API_KEY=tu_clave_aqui")
        sys.exit(1)

    print(f"[OK] Configuración cargada. Modelo Gemini: {Config.GEMINI_MODEL}")

    # 2. Solicitud y validación de URL
    raw_url = prompt_moodle_url()
    url_info = parse_moodle_url(raw_url)

    if not url_info.is_valid:
        print("\n[ERROR] La URL introducida no es válida:")
        for w in url_info.warnings:
            print(f"  • {w}")
        sys.exit(1)

    # 3. Advertencia si es una página previa de cuestionario (sin intento iniciado)
    if url_info.kind == "view":
        print("\n[ATENCIÓN] La URL corresponde a la portada del cuestionario, no a un intento en curso.")
        print("El programa nunca iniciará un intento de forma automática.")
        print("Por favor, inicia el intento manualmente desde Moodle e introduce la URL de 'attempt.php'.")
        confirm = input("¿Deseas abrir el navegador en esta URL para iniciar sesión y acceder? (s/N): ").strip().lower()
        if confirm not in ("s", "si", "y", "yes"):
            print("Operación cancelada.")
            sys.exit(0)

    # 4. Iniciar Playwright y Google Chrome oficial
    print("\n[1/5] Iniciando Google Chrome en modo visible con perfil persistente...")
    browser_mgr = BrowserManager()
    try:
        page = browser_mgr.start()
    except ChromeNotFoundError as c_err:
        print(f"\n[ERROR DE NAVEGADOR]\n{c_err}")
        sys.exit(1)
    except ProfileLockedError as p_err:
        print(f"\n[PERFIL BLOQUEADO]\n{p_err}")
        sys.exit(1)
    except Exception as exc:
        print(f"\n[ERROR AL INICIAR CHROME] {exc}")
        sys.exit(1)

    try:
        print(f"[2/5] Accediendo a: {url_info.raw_url}")
        browser_mgr.navigate_to(url_info.raw_url)

        # Detectar si se requiere autenticación manual
        time.sleep(2)
        if "login" in page.url.lower() or page.locator('input[type="password"]').count() > 0:
            print("\n" + "!" * 50)
            print("[ACCIÓN REQUERIDA] Se detectó pantalla de inicio de sesión.")
            print("Inicia sesión manualmente en la ventana de Google Chrome abierta.")
            print("Una vez dentro del cuestionario, presiona [ENTER] en esta terminal para continuar...")
            print("!" * 50)
            input()

        # 5. Extracción de preguntas
        print("\n[3/5] Analizando estructura del cuestionario en pantalla...")
        questions = extract_questions_from_page(page)

        if not questions:
            print("[AVISO] No se detectaron preguntas en la página actual.")
            print("Verifica que te encuentres en una página activa del cuestionario.")
            browser_mgr.keep_open_until_user_closes()
            return

        print(f"[OK] Se detectaron {len(questions)} pregunta(s).")

        # 6. Inicialización de cliente Gemini
        gemini_client = GeminiQuizClient()
        filler = FormFiller(page)

        processed_results = []
        all_fill_reports = []

        # 7. Procesamiento y completado seguro
        print("\n[4/5] Analizando preguntas con Gemini y completando campos...")
        for idx, q in enumerate(questions, start=1):
            num_display = q.question_number or f"Pregunta {idx}"
            print(f"  -> Procesando {num_display} ({q.question_type})...")

            analysis = gemini_client.analyze_question(q)
            processed_q = process_question_analysis(q, analysis)
            processed_results.append(processed_q)

            reports = filler.fill_question_safely(processed_q)
            all_fill_reports.append(reports)

        # 8. Reporte y revisión final
        print("\n[5/5] Presentando informe final...")
        display_final_report(len(questions), processed_results, all_fill_reports)

        # 9. Mantener el navegador abierto
        browser_mgr.keep_open_until_user_closes()

    except Exception as exc:
        print(f"\n[ERROR INESPERADO] {exc}")
        browser_mgr.keep_open_until_user_closes()


if __name__ == "__main__":
    main()

