"""
PDF Parser v1.0
Извлечение текста из PDF с использованием PyPDF2.

Реализация PDFParserInterface.
"""

import PyPDF2
import re
from typing import Optional
from engine.schemas import ParsedDocument
from engine.interfaces import PDFParserInterface


class PDFParser(PDFParserInterface):
    """
    Парсер PDF-документов на основе PyPDF2.
    Извлекает текст и базовые метаданные.
    """
    
    def __init__(self):
        pass
    
    def parse(self, filepath: str) -> ParsedDocument:
        """
        Извлекает полный текст из PDF.
        
        Args:
            filepath: путь к PDF-файлу
            
        Returns:
            ParsedDocument: результат парсинга
            
        Raises:
            FileNotFoundError: если файл не существует
            ValueError: если файл не является валидным PDF
        """
        try:
            # Открываем PDF файл
            with open(filepath, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # Извлекаем текст со всех страниц
                text_parts = []
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                full_text = '\n\n'.join(text_parts)
                
                # Если текст пустой, возможно PDF содержит изображения
                if not full_text.strip():
                    full_text = "[PDF содержит изображения или защищён от копирования]"
                
                # Подсчитываем статистику
                word_count = len(full_text.split())
                char_count = len(full_text)
                
                # Определяем примерное время чтения (200 слов/минуту)
                reading_time_min = max(1, round(word_count / 200))
                
                # Извлекаем метаданные
                metadata = {}
                if pdf_reader.metadata:
                    metadata = {
                        "title": str(pdf_reader.metadata.get('/Title', '')),
                        "author": str(pdf_reader.metadata.get('/Author', '')),
                        "creator": str(pdf_reader.metadata.get('/Creator', '')),
                        "producer": str(pdf_reader.metadata.get('/Producer', '')),
                        "creation_date": str(pdf_reader.metadata.get('/CreationDate', '')),
                    }
                
                # Определяем язык (базовое определение по ключевым словам)
                language = self._detect_language(full_text)
                
                return ParsedDocument(
                    text=full_text,
                    pages=len(pdf_reader.pages),
                    language=language,
                    estimated_reading_time_min=reading_time_min,
                    metadata=metadata
                )
                
        except FileNotFoundError:
            raise FileNotFoundError(f"PDF file not found: {filepath}")
        except PyPDF2.errors.PdfReadError as e:
            raise ValueError(f"Invalid PDF file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {str(e)}")
    
    def _detect_language(self, text: str) -> str:
        """
        Определяет язык текста по ключевым словам.
        
        Args:
            text: текст для анализа
            
        Returns:
            str: код языка ('en', 'ru', или 'unknown')
        """
        text_lower = text.lower()
        
        # Английские ключевые слова
        english_keywords = ['the', 'and', 'of', 'to', 'in', 'that', 'for', 'is', 'on', 'with']
        english_count = sum(1 for word in english_keywords if word in text_lower)
        
        # Русские ключевые слова
        russian_keywords = ['и', 'в', 'не', 'на', 'с', 'по', 'что', 'это', 'как', 'для']
        russian_count = sum(1 for word in russian_keywords if word in text_lower)
        
        if english_count > russian_count and english_count > -1:
            return 'en'
        elif russian_count > english_count and russian_count > -1:
            return 'ru'
        else:
            return 'en'  # По умолчанию английский
    
    def split_into_sections(self, text: str) -> list:
        """
        Разбивает текст на секции по заголовкам.
        
        Args:
            text: полный текст документа
            
        Returns:
            list[dict]: список секций вида {title, content, page}
        """
        # Простая реализация: разбиваем по номерам пунктов
        sections = []
        
        # Ищем паттерны типа "1.", "1.1", "Article 1" и т.д.
        pattern = r'(\n\d+[\.\d]*\s+[A-Z].*?)(?=\n\d+[\.\d]*\s+[A-Z]|\n\s*\Z)'
        matches = re.findall(pattern, text, re.DOTALL | re.MULTILINE)
        
        for match in matches:
            # Первая строка - заголовок, остальное - содержание
            lines = match.strip().split('\n')
            if len(lines) > 1:
                title = lines[0].strip()
                content = '\n'.join(lines[1:]).strip()
                sections.append({
                    'title': title,
                    'content': content,
                    'page': 1  # TODO: определить реальную страницу
                })
        
        return sections
