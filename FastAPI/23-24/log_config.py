import logging
import sqlite3

from middlewares import trace_id_var

# серйозність запису логера
# може бути DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = logging.INFO

# приклад логу з таким форматом
# 17b3a363-d276-4c3e-b4da-ac6203526067 - 2025-06-30 21:13:52,226 - main - login - ERROR - User with email 'string' does not exist.
LOG_FORMAT = (
    "%(trace_id)s - %(asctime)s - %(name)s - %(funcName)s - %(levelname)s - %(message)s"
)

LOGS_DB_NAME = "logs.db"


class TraceIdFilter(logging.Filter):
    """Клас додає унікальний ID для кожного запису лога."""

    def filter(self, record):
        record.trace_id = trace_id_var.get()
        return True


class SQLiteHandler(logging.Handler):
    """Кастомний обробник логів, який зберігає записи логів в БД SQLite."""

    def __init__(self, db_path: str) -> None:
        super().__init__()
        self.conn = sqlite3.connect(db_path, check_same_thread=False)

    def emit(self, record: logging.LogRecord) -> None:
        trace_id = getattr(record, "trace_id", "no_trace")
        data = record.asctime
        module = record.name
        func = record.funcName
        level = record.levelname
        message = record.getMessage()

        try:
            self.conn.execute(
                "INSERT INTO logs (trace_id, data, module, func_name, level, message) VALUES (?, ?, ?, ?, ?, ?)",
                (trace_id, data, module, func, level, message),
            )
            self.conn.commit()
        except sqlite3.DatabaseError as e:
            print("Logging to SQLite failed:", e)


def configure_logger(name: str) -> logging.Logger:
    """Створення і конфігурація логера."""

    # створення логера
    logger = logging.getLogger(name)

    # визначення типів обробників для логера
    log_console_handler = logging.StreamHandler()
    log_file_handler = logging.FileHandler("app.log")
    log_db_handler = SQLiteHandler(LOGS_DB_NAME)

    # визначення формату записів логів
    formatter = logging.Formatter(LOG_FORMAT)

    # встановлення формату для обробників
    log_console_handler.setFormatter(formatter)
    log_file_handler.setFormatter(formatter)

    # встановлення мінімального рівня серйозності логів
    # DEBUG, INFO, WARNING, ERROR, CRITICAL
    logger.setLevel(LOG_LEVEL)

    # встановлення фільтра який додає унікальний ID для кожного запиту
    logger.addFilter(TraceIdFilter())

    # встановлення обробників для переданого логера
    logger.addHandler(log_console_handler)
    logger.addHandler(log_file_handler)
    logger.addHandler(log_db_handler)

    return logger
