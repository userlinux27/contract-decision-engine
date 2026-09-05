"""
Logging utilities.
"""

import os
from datetime import datetime


def log_event(visitor_id: str, event: str, **kwargs):
    """Запись события в CSV."""
    csv_path = "data/analytics.csv"
    timestamp = datetime.utcnow().isoformat()

    # Формируем строку
    extra = "|".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
    line = f"{timestamp},{visitor_id},{event},{extra}\n"

    # Создаём директорию если её нет
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    
    with open(csv_path, "a", encoding="utf-8") as f:
        f.write(line)
