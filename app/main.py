from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from fastapi import Depends
import os
import json

from .database import engine, get_db
from . import models
from .utils import clone_and_extract_info, generate_excel_report

# 1. Создаем экземпляр приложения
app = FastAPI()

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1"
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Создает таблицы, если их еще нет
models.Base.metadata.create_all(bind=engine)

# 2. Описываем, как должен выглядеть запрос от пользователя.
class AnalysisRequest(BaseModel):
    repo_url: HttpUrl

# 3. Создаем endpoint, который принимает POST-запрос.

def prepare_prompt_context(repo_data: dict):
    # Собираем историю коммитов в читаемый текст
    history_text = "ИСТОРИЯ ПОСЛЕДНИХ ИЗМЕНЕНИЙ:\n"
    for c in repo_data["commits"]:
        history_text += f"- {c['hash']}: {c['message']} (Изменено строк: {c['stats']['lines']})\n"
    
    # Собираем содержимое файлов
    code_text = "\nСОДЕРЖИМОЕ ФАЙЛОВ:\n"
    for path, content in repo_data["files"].items():
        code_text += f"\n--- ФАЙЛ: {path} ---\n{content}\n"
        
    return history_text + code_text

system_prompt = """
Ты — эксперт по аудиту кода и управлению техническим долгом. 
Проанализируй историю коммитов и содержимое файлов репозитория.

Верни ответ СТРОГО в формате JSON со следующей структурой:
{
  "criteria_scores": [
    {"name": "Чистота кода", "score": 1-10, "comment": "почему такая оценка"},
    {"name": "Безопасность", "score": 1-10, "comment": "наличие уязвимостей"},
    {"name": "Производительность", "score": 1-10, "comment": "эффективность алгоритмов"}
  ],
  "analysis_summary": "Краткий итог: общее состояние проекта и критичность долга",
  "useful_info": {
    "maintenance_risk": "Насколько сложно будет поддерживать проект через полгода",
    "hotspots": "Список файлов, которые чаще всего меняются и содержат плохой код",
    "refactoring_plan": ["Шаг 1...", "Шаг 2..."]
  }
}
"""

async def get_llm_report(full_context: str):
    # Используем твой рабочий конфиг Groq/OpenAI
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b", # или твоя рабочая модель
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": full_context}
        ],
        response_format={ "type": "json_object" } # Важно: заставляем модель выдать JSON
    )
    return json.loads(response.choices[0].message.content)

@app.post("/analyze")
async def start_analysis(data: AnalysisRequest, db: Session = Depends(get_db)):
    try:
        # ... твой текущий код (клонирование, вызов ЛЛМ) ...
        repo_data = clone_and_extract_info(str(data.repo_url))
        full_context = prepare_prompt_context(repo_data)
        report_json = await get_llm_report(full_context)
        
        # Подготавливаем объект для БД
        new_result = models.AnalysisResult(
            repo_url=str(data.repo_url),
            model_name="openai/gpt-oss-120b",
            full_report=report_json
        )
        
        # Сохраняем в PostgreSQL
        db.add(new_result)
        db.commit()
        db.refresh(new_result)

        return {
            "status": "success",
            "id": new_result.id, # Теперь у каждого анализа есть свой ID!
            "info": {
                "repo_url": str(data.repo_url),
                "analysis_date": new_result.analysis_date.isoformat(),
                "model_used": "gpt-oss-120b"
            },
            "report": report_json
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.post("/download/excel")
async def download_report(data: dict): # Временно принимаем JSON отчета обратно
    excel_file = generate_excel_report(data)
    
    headers = {
        'Content-Disposition': 'attachment; filename="tech_debt_report.xlsx"'
    }
    return StreamingResponse(excel_file, headers=headers, media_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

# Добавим простой GET, чтобы проверить работоспособность в браузере
@app.get("/", response_class=HTMLResponse)
async def read_index():

    template_path = os.path.join(BASE_DIR, "templates", "index.html")

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()