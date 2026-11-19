"""Cliente oficial de Google Gen AI SDK para análisis de preguntas de Moodle."""

import json
from typing import Any
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

from src.config import Config
from src.moodle_parser import QuestionData


class FieldProposal(BaseModel):
    control_id: str = Field(description="ID o nombre del control HTML")
    control_type: str = Field(description="Tipo de control: radio, checkbox, select, text, textarea")
    selected_value: str | None = Field(default=None, description="Valor del value attribute o texto de la opción para select/radio/checkbox")
    text_content: str | None = Field(default=None, description="Texto propuesto para campos de texto o textarea")
    confidence: str = Field(description="Nivel de confianza: ALTA, MEDIA, BAJA")
    explanation: str = Field(description="Breve justificación técnica o de cálculo")


class QuestionAnalysis(BaseModel):
    question_id: str
    question_number: str
    status: str = Field(description="Estado: RESUELTO, AMBIGUO, REQUIERE_REVISION")
    overall_confidence: str = Field(description="Confianza general: ALTA, MEDIA, BAJA")
    summary: str = Field(description="Resumen de la solución o deducción")
    proposals: list[FieldProposal] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


SYSTEM_PROMPT = """Eres un asistente académico experto en resolver cuestionarios de química, física y ciencias.
Tu objetivo es analizar preguntas extraídas directamente del campus Moodle y proponer las respuestas más precisas y rigurosas.
REGLAS OBLIGATORIAS:
1. Analiza el enunciado, opciones, tablas y contexto de cada pregunta.
2. Identifica con exactitud el control HTML (radio, checkbox, select, input text) y su valor o texto correspondiente.
3. Para menús desplegables (select) y botones de opción (radio), el valor propuesto debe coincidir con una de las opciones disponibles.
4. Si una pregunta o campo es ambiguo o falta información, clasifícalo como AMBIGUO o REQUIERE_REVISION y añade una advertencia.
5. No inventes respuestas. Si no dispones de suficiente certeza, indica confianza BAJA.
6. Tu salida debe cumplir estrictamente el esquema JSON indicado.
"""


class GeminiQuizClient:
    def __init__(self, api_key: str | None = None, model: str | None = None):
        self.api_key = api_key or Config.GEMINI_API_KEY
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY no configurada. Configure su clave en el archivo .env")

        self.model = model or Config.GEMINI_MODEL
        self.client = genai.Client(api_key=self.api_key)

    def analyze_question(self, q: QuestionData) -> QuestionAnalysis:
        """Envía una pregunta estructurada a Gemini y obtiene una propuesta analítica."""
        controls_desc = []
        for c in q.controls:
            c_info = {
                "control_id": c.control_id,
                "control_type": c.control_type,
                "name": c.name,
                "label": c.label_text,
                "options": [{"value": o.value, "text": o.text} for o in c.options],
            }
            controls_desc.append(c_info)

        prompt_payload = {
            "question_id": q.question_id,
            "question_number": q.question_number,
            "grade_info": q.grade_info,
            "question_type": q.question_type,
            "prompt_text": q.prompt_text,
            "controls": controls_desc,
        }

        user_content = f"Analiza la siguiente pregunta y devuelve las propuestas correspondientes:\n{json.dumps(prompt_payload, ensure_ascii=False, indent=2)}"

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=QuestionAnalysis,
                    temperature=0.1,
                ),
            )

            result_text = response.text
            data = json.loads(result_text)
            return QuestionAnalysis(**data)

        except Exception as exc:
            return QuestionAnalysis(
                question_id=q.question_id,
                question_number=q.question_number,
                status="REQUIERE_REVISION",
                overall_confidence="BAJA",
                summary=f"Error en comunicación con Gemini API: {exc}",
                proposals=[],
                warnings=[str(exc)],
            )

