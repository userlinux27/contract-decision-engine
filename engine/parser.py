"""
Legacy Parser Module v0.1
Совместимость со старым кодом.

Этот модуль оставлен для обратной совместимости.
Новый код должен использовать engine.pdf_parser.PDFParser
"""

from engine.pdf_parser import PDFParser as NewPDFParser


class DocumentParser:
    """
    Legacy parser для обратной совместимости.
    """
    
    def __init__(self):
        self._parser = NewPDFParser()
    
    def parse(self, filepath: str) -> str:
        """
        Извлекает полный текст из PDF.
        Args:
            filepath: путь к PDF-файлу
        Returns:
            str: полный текст документа
        """
        parsed_doc = self._parser.parse(filepath)
        return parsed_doc.text
    
    def split_into_sections(self, text: str) -> list:
        """
        Разбивает текст на секции по заголовкам.
        Args:
            text: полный текст документа
        Returns:
            list[dict]: список секций вида {title, content, page}
        """
        return self._parser.split_into_sections(text)
