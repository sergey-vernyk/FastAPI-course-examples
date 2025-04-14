## Процесс втсновлення залежностей та запуску сервера

#### 1. Створити вірутальне оточення:
```sh
python -m venv .venv
```

#### 2. Активувати його:
```sh
# Linux/Mac
source .venv/bin/activate

# windows
# Cmd
.venv\Scripts\activate.bat

# PowerShell
.venv\Scripts\Activate.ps1

# Git Bash
source .venv/bin/activate
```

#### 3. Встановити залежності:
```sh
pip install -r requirements.txt
```

#### 4. Запуск сервера uvicorn:
```sh
# вказати замість `main` назву свого модуля
uvicorn main:app --reload
```
