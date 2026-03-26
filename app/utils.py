import os
from git import Repo
import shutil
import stat
import pandas as pd
import io

def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)

def clone_and_extract_info(repo_url: str):
    # 1. Создаем путь для временной папки
    local_path = "./temp_repos/current_analysis"
    
    # Если папка уже есть (от старого анализа), удаляем её
    if os.path.exists(local_path):
        shutil.rmtree(local_path, onerror=remove_readonly)
    
    # 2. Клонируем репозиторий
    print(f"Клонируем {repo_url}...")
    repo = Repo.clone_from(repo_url, local_path)
    
    # 3. Собираем историю коммитов (нам нужны последние 5 для примера)
    commits_info = []
    # В utils.py внутри цикла коммитов можно добавить детализацию:
    for commit in repo.iter_commits(max_count=5):
        commits_info.append({
            "hash": commit.hexsha[:7],
            "message": commit.message.strip(),
            "stats": commit.stats.total,  # {'insertions': 10, 'deletions': 5, 'lines': 15}
            "files_changed": list(commit.stats.files.keys()) # Какие именно файлы правились
        })
        
    # 4. Собираем структуру и содержание файлов (только .py)
    files_content = {}
    for root, dirs, files in os.walk(local_path):
        # Пропускаем папку .git
        if '.git' in root:
            continue
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, local_path)
                with open(file_path, 'r', encoding='utf-8') as f:
                    files_content[relative_path] = f.read()
                    
    return {
        "commits": commits_info,
        "files": files_content
    }

# Выгрущка в excel

def generate_excel_report(data: dict):
    try:
        output = io.BytesIO()
        
        # Превращаем всё в строки, чтобы объекты типа HttpUrl не ломали Pandas
        info_cleaned = {k: str(v) for k, v in data["info"].items()}
        info_df = pd.DataFrame([info_cleaned])
        
        scores_df = pd.DataFrame(data["report"]["criteria_scores"])
        
        plan_df = pd.DataFrame({
            "Шаги рефакторинга": data["report"]["useful_info"]["refactoring_plan"]
        })

        # Записываем всё в один Excel файл
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            info_df.to_excel(writer, sheet_name='Общая информация', index=False)
            scores_df.to_excel(writer, sheet_name='Оценки', index=False)
            plan_df.to_excel(writer, sheet_name='План действий', index=False)

        output.seek(0)
        return output
    except Exception as e:
        print(f"ОШИБКА ГЕНЕРАЦИИ EXCEL: {e}") # Увидишь в консоли uvicorn
        raise e