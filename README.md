# Asistente para Cuestionarios Moodle con Gemini y Playwright

Aplicación en Python que analiza cuestionarios de Moodle con inteligencia artificial (Google Gemini) y completa automáticamente los campos usando Playwright con **Google Chrome oficial**.

> **REGLA FUNDAMENTAL:**
> **El programa NUNCA envía, entrega ni finaliza cuestionarios.**
> Solo asiste en el análisis y completado. El usuario revisa todas las respuestas y envía manualmente.

---

## Plataformas compatibles

| Sistema | Scripts | Estado |
|---|---|---|
| Windows 10 / 11 | `install.bat` / `run.bat` | ✅ Soportado (uso principal) |
| Ubuntu / Linux | `install.sh` / `run.sh` | ✅ Soportado |
| macOS | `install.sh` / `run.sh` | ✅ Compatible |

---

## Requisitos previos

### En Windows (obligatorio)

1. **Python 3.11 o superior**
   - Descargar desde: https://www.python.org/downloads/
   - Durante la instalación, marcar la casilla **"Add python.exe to PATH"**
   - Verificar en CMD: `python --version`

2. **Google Chrome oficial**
   - Descargar desde: https://www.google.com/chrome/
   - El programa detecta Chrome automáticamente en las rutas estándar de Windows
   - No usar Chromium, Edge ni otro navegador

3. **Git** (para clonar el repositorio)
   - Descargar desde: https://git-scm.com/download/win

4. **Clave de API de Google Gemini** (gratuita)
   - Obtener en: https://aistudio.google.com/

---

## Instalación en Windows

Abrir **CMD** o **PowerShell** y ejecutar:

```bat
git clone https://github.com/sebapalavecino2003/quimica.git
cd quimica
scripts\install.bat
```

El instalador realizará automáticamente:
- Verificación de Python 3.11+
- Creación del entorno virtual `.venv`
- Instalación de todas las dependencias
- Detección de Google Chrome en el sistema
- Creación del archivo `.env` inicial

---

## Configuración de Gemini API

Abrir el archivo `.env` con el Bloc de notas:

```bat
notepad .env
```

Completar la clave de API:

```env
GEMINI_API_KEY=AIzaSy...tu_clave_real_aqui...
GEMINI_MODEL=gemini-2.5-flash
BROWSER_PROFILE_DIR=./browser_data
HEADLESS=False
```

Guardar el archivo y cerrar el Bloc de notas.

---

## Ejecución en Windows

Hacer doble clic en `scripts\run.bat` o ejecutar desde CMD:

```bat
scripts\run.bat
```

El programa mostrará en pantalla:

```
==================================================
        ASISTENTE MOODLE + GEMINI
==================================================
```

Luego pedirá la URL del cuestionario.

---

## Flujo de uso

1. El programa solicita la URL del cuestionario de Moodle
2. Se abre **Google Chrome** con un perfil independiente de automatización
3. Si la sesión no está guardada, el programa detecta la pantalla de login
4. **Iniciar sesión manualmente** en la ventana de Chrome que aparece
5. Una vez dentro del cuestionario, presionar **[ENTER]** en la terminal
6. Gemini analiza automáticamente cada pregunta visible
7. Playwright completa los campos con las respuestas propuestas
8. Se muestra un resumen en la terminal con el estado de cada pregunta
9. **Chrome permanece abierto** para revisar, corregir y enviar manualmente

---

## Inicio de sesión y persistencia de sesión

El programa utiliza un **perfil independiente de Chrome** guardado en la carpeta `browser_data/`.

- La primera vez: iniciar sesión manualmente en Moodle cuando Chrome lo solicite
- Las siguientes ejecuciones: Chrome recordará la sesión automáticamente
- El perfil **no se sincroniza con GitHub** (está en `.gitignore`)
- En otra computadora: iniciar sesión nuevamente desde cero

> Si aparece el error **"perfil bloqueado"**, cerrar todas las ventanas de Chrome del asistente antes de reiniciar.

---

## Tipos de preguntas soportadas

| Tipo | Control HTML | Estado |
|---|---|---|
| Opción múltiple simple | `input[type="radio"]` | ✅ |
| Respuesta embebida / Cloze | `select` en texto | ✅ |
| Tablas con celdas interactivas | `input[text]` + `select` | ✅ |
| Respuesta corta | `input[type="text"]` | ✅ |
| Respuesta abierta | `textarea` | ✅ |
| Opción múltiple múltiple | `input[type="checkbox"]` | ✅ |

---

## Protecciones de seguridad activas

El módulo `safety.py` bloquea activamente cualquier acción relacionada con:

- `Terminar intento...`
- `Finalizar intento...`
- `Enviar todo y terminar`
- Atributo `finishattempt`
- Eventos `form.submit()` o `requestSubmit()`

Si se detecta alguno de estos elementos, el programa se detiene y solicita intervención manual.

---

## Instalación en Ubuntu / Linux

```bash
git clone https://github.com/sebapalavecino2003/quimica.git
cd quimica
chmod +x scripts/install.sh scripts/run.sh
./scripts/install.sh
```

Instalar Google Chrome en Ubuntu si no está disponible:

```bash
wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install /tmp/chrome.deb
```

Ejecutar:

```bash
./scripts/run.sh
```

---

## Pruebas automatizadas

```bat
rem Windows
.venv\Scripts\activate
pytest tests\ -v
```

```bash
# Linux
source .venv/bin/activate
pytest tests/ -v
```

Resultado esperado: **20 pruebas aprobadas**.

---

## Resolución de problemas

| Error | Causa probable | Solución |
|---|---|---|
| `GEMINI_API_KEY no configurada` | Falta la clave en `.env` | Editar `.env` y agregar la clave |
| `Google Chrome no encontrado` | Chrome no instalado | Instalar desde google.com/chrome |
| `Perfil bloqueado` | Otra instancia de Chrome con el mismo perfil | Cerrar otras ventanas del asistente |
| `No se detectaron preguntas` | Página incorrecta o no cargada | Verificar que la URL sea `attempt.php` |
| `python` no reconocido (Windows) | Python no agregado al PATH | Reinstalar Python marcando "Add to PATH" |

---

## Arquitectura del proyecto

```
quimica/
├── main.py                     # Orquestador principal
├── requirements.txt            # Dependencias
├── .env.example                # Plantilla de configuración
├── LICENSE
├── README.md
│
├── src/
│   ├── config.py               # Variables de entorno
│   ├── safety.py               # Protección contra envíos
│   ├── moodle_url.py           # Validador de URL
│   ├── browser.py              # Google Chrome con Playwright
│   ├── moodle_parser.py        # Extracción DOM (solo lectura)
│   ├── gemini_client.py        # Cliente Gemini API
│   ├── answer_processor.py     # Validador de respuestas
│   ├── form_filler.py          # Completado seguro de campos
│   └── review.py               # Reporte en consola
│
├── scripts/
│   ├── install.bat             # Instalador para Windows
│   ├── run.bat                 # Ejecutor para Windows
│   ├── install.sh              # Instalador para Linux/macOS
│   └── run.sh                  # Ejecutor para Linux/macOS
│
└── tests/
    ├── test_safety.py
    ├── test_moodle_url.py
    ├── test_answer_processor.py
    ├── test_form_filler.py
    └── test_browser.py
```

---

## Tecnologías utilizadas

- **Python 3.11+**
- **Playwright** — automatización de Google Chrome
- **Google Gen AI SDK** (`google-genai`) — integración con Gemini API
- **Pydantic** — validación de esquemas JSON estructurados
- **python-dotenv** — gestión de variables de entorno
- **pytest** — pruebas automatizadas

---

## Limitaciones conocidas

- El análisis se realiza sobre la página actualmente visible. Si el cuestionario tiene múltiples páginas, debe ejecutarse por página o navegarse manualmente entre ellas.
- Preguntas con imágenes complejas pueden requerir revisión manual (confianza baja).
- El perfil persistente de Chrome no puede compartirse entre computadoras.
- Las pruebas de integración con Chrome real requieren una computadora con Chrome instalado; las pruebas unitarias funcionan en cualquier entorno.

---

**El programa nunca envía ni finaliza cuestionarios. La decisión final siempre es del usuario.**
