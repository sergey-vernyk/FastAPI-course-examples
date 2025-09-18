from datetime import datetime


def log_action(action: str, data: dict):
    print(f"Logging {datetime.now()}, {action.upper()}, {data}")
