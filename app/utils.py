import os
from git import Repo
import shutil
import stat

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
    for commit in repo.iter_commits(max_count=5):
        commits_info.append({
            "hash": commit.hexsha[:7],
            "author": commit.author.name,
            "date": commit.authored_datetime.isoformat(),
            "message": commit.message.strip(),
            "stats": commit.stats.total # Показывает вставки и удаления строк
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