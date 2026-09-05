"""
Document Service v1.0
Сервис работы с документами.

Отвечает за:
- Валидацию PDF файлов
- Сохранение документов
- Парсинг документов
"""

import os
from typing import Optional
from engine.schemas import ParsedDocument
from engine.pdf_parser import PDFParser


class DocumentService:
    """Сервис работы с документами."""
    
    def __init__(self):
        self.parser = PDFParser()
    
    def validate_pdf(self, filename: str, content: bytes) -> tuple[bool, Optional[str]]:
        """
        Валидирует PDF файл.
        
        Args:
            filename: имя файла
            content: содержимое файла
            
        Returns:
            tuple: (валиден ли файл, сообщение об ошибке если есть)
        """
        # Проверка расширения
        if not filename.lower().endswith('.pdf'):
            return False, "Please upload a PDF file."
        
        # Проверка размера (макс. 10 МБ)
        if len(content) > 10 * 1024 * 1024:
            return False, "File too large. Maximum 10 MB."
        
        # Проверка что файл не пустой
        if len(content) == 0:
            return False, "File is empty."
        
        return True, None
    
    def save_document(self, task_id: str, content: bytes) -> str:
        """
        Сохраняет документ на диск.
        
        Args:
            task_id: идентификатор задачи
            content: содержимое файла
            
        Returns:
            str: путь к сохранённому файлу
        """
        os.makedirs("uploads", exist_ok=True)
        filepath = f"uploads/{task_id}.pdf"
        
        with open(filepath, "wb") as f:
            f.write(content)
        
        return filepath
    
    def parse_document(self, filepath: str) -> ParsedDocument:
        """
        Парсит PDF документ.
        
        Args:
            filepath: путь к PDF файлу
            
        Returns:
            ParsedDocument: результат парсинга
        """
        return self.parser.parse(filepath)
    
    def cleanup_document(self, filepath: str):
        """
        Удаляет документ с диска.
        
        Args:
            filepath: путь к файлу
        """
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass  # Игнорируем ошибки удаления
