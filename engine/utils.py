"""
Utilities v0.1
Вспомогательные функции.

Пока заглушка — будет пополняться по мере необходимости.
"""

import uuid


def generate_id() -> str:
    """Генерирует уникальный идентификатор."""
    return str(uuid.uuid4())


def validate_pdf_extension(filename: str) -> bool:
    """Проверяет, что файл имеет расширение .pdf."""
    return filename.lower().endswith(".pdf")


def format_confidence(confidence: float) -> int:
    """
    Форматирует confidence в проценты.
    Args:
        confidence: float от 0.0 до 1.0
    Returns:
        int: процент (0-100)
    """
    return round(confidence * 100)