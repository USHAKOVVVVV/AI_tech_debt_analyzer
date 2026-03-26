# 🛠️ Tech Debt Audit Tool

Инструмент для автоматизированного анализа технического долга репозиториев с использованием LLM (DeepSeek/Llama 3).

## 🌟 Основные возможности

- **Клонирование репозиториев:** Автоматическая загрузка кода по ссылке.
- **Анализ истории:** Учет последних коммитов и изменений для выявления "горячих точек".
- **AI-Аудит:** Оценка кода по критериям (Чистота, Безопасность, Производительность) через LLM.
- **Отчетность:** Генерация детального отчета в формате Excel.
- **История:** Сохранение всех результатов анализа в базу данных PostgreSQL (Docker).

## 🚀 Технологический стек

- **Backend:** FastAPI, SQLAlchemy, Pandas.
- **Frontend:** HTML5, JavaScript.
- **AI:** OpenAI API (openai/gpt-oss-120b).
- **Database:** PostgreSQL (в Docker-контейнере).
- **DevOps:** Docker, GitPython.

## 📦 Как запустить локально

### 1. Требования

- Docker Desktop
- Python 3.10+

### 2. Настройка окружения

Создайте файл `.env` в корне проекта:

```env
GROQ_API_KEY=your_api_key_here
DATABASE_URL=postgresql://postgres:pass@localhost:5432/tech_debt_db
```
