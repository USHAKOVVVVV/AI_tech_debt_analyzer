from fastapi import FastAPI
from pydantic import BaseModel, HttpUrl

from .utils import clone_and_extract_info

# 1. Создаем экземпляр приложения
app = FastAPI()

# 2. Описываем, как должен выглядеть запрос от пользователя.
class AnalysisRequest(BaseModel):
    repo_url: HttpUrl

# 3. Создаем endpoint, который принимает POST-запрос.
@app.post("/analyze")
async def start_analysis(data: AnalysisRequest):
    # Вызываем нашу новую функцию
    try:
        repo_data = clone_and_extract_info(str(data.repo_url))
        
        # Для проверки выведем в ответ количество найденных файлов и последний коммит
        return {
            "status": "success",
            "files_found": list(repo_data["files"].keys()),
            "last_commit": repo_data["commits"][0] if repo_data["commits"] else "No commits"
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# Добавим простой GET, чтобы проверить работоспособность в браузере
@app.get("/")
async def welcome():
    return {"message": "Сервис работает"}