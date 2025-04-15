## Процес встановлення залежностей та запуску сервера

#### 1. Створити віртуальне оточення:
```sh
python -m venv .venv
```

#### 2. Активувати його:
```sh
# Linux/Mac
source .venv/bin/activate

# Windows Cmd
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows Git Bash
source .venv/Scripts/activate
```

#### 3. Встановити залежності:
```sh
pip install -r requirements.txt
```

#### 4. Запустити сервер `uvicorn`:
```sh
# вказати замість `main` назву свого модуля
uvicorn main:app --reload
```
