"""
Утилиты для разбивки документов на чанки.
Используется RecursiveCharacterTextSplitter из LangChain.
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
import tiktoken
import re

from config.settings import settings
from utils.logger import logger


def get_token_count(text: str, model: str = "gpt-4o-mini") -> int:
    """
    Подсчитать количество токенов в тексте.
    
    Args:
        text: Текст для подсчета
        model: Модель для токенизации
        
    Returns:
        int: Количество токенов
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback на cl100k_base (используется в GPT-4)
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))


def chunk_text(
    text: str,
    chunk_size: int | None = None,
    chunk_overlap: int | None = None,
    add_metadata: bool = True
) -> List[dict]:
    """
    Разбить текст на чанки с использованием RecursiveCharacterTextSplitter.
    
    Args:
        text: Исходный текст
        chunk_size: Размер чанка в символах (по умолчанию из settings)
        chunk_overlap: Перекрытие между чанками (по умолчанию из settings)
        add_metadata: Добавлять ли метаданные (номер чанка, токены)
        
    Returns:
        List[dict]: Список чанков с метаданными
    """
    chunk_size = chunk_size or settings.chunk_size
    chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    logger.info(f"Chunking text: {len(text)} chars, chunk_size={chunk_size}, overlap={chunk_overlap}")
    
    # Создаем text splitter
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        is_separator_regex=True,
        separators=[
            r"\n\s*[Гг]лава\s+\d+",       # Глава / глава
            r"\n\s*ГЛАВА\s+\d+",          # ГЛАВА
            r"\n\s*[Чч]асть\s+\d+",       # Часть / часть
            r"\n\s*ЧАСТЬ\s+\d+",          # ЧАСТЬ
            r"\n\s*[Cc]hapter\s+\d+",     # Chapter / chapter
            r"\n\s*CHAPTER\s+\d+",        # CHAPTER
            r"\n\n",                      # Параграфы
            r"\n",                        # Строки
            r"\. ",                       # Предложения
            r" ",                         # Слова
            r""                           # Символы
        ]
    )
    
    # Разбиваем текст
    chunks = text_splitter.split_text(text)
    
    logger.info(f"Created {len(chunks)} chunks")
    
    # Если не нужны метаданные, возвращаем просто список строк
    if not add_metadata:
        return [{"content": chunk} for chunk in chunks]
    
    # Добавляем метаданные к каждому чанку
    result = []
    current_chapter = None
    
    for i, chunk in enumerate(chunks):
        # Пытаемся найти главу в начале чанка (увеличиваем окно поиска до 200 символов)
        # Ищем паттерны типа "Глава 1", "ГЛАВА 1", "Часть 1", "ЧАСТЬ 1" и т.д.
        chapter_match = re.search(r"(?i)(?:Глава|ГЛАВА|Chapter|CHAPTER|Часть|ЧАСТЬ)\s*(\d+)", chunk[:200])
        if chapter_match:
            current_chapter = chapter_match.group(1)
            
        chunk_data = {
            "content": chunk,
            "chunk_index": i,
            "total_chunks": len(chunks),
            "char_count": len(chunk),
            "token_count": get_token_count(chunk),
            "chapter": str(current_chapter) if current_chapter is not None else None
        }
        result.append(chunk_data)
    
    return result


def chunk_document(
    text: str,
    source: str,
    additional_metadata: dict | None = None
) -> List[dict]:
    """
    Разбить документ на чанки с полными метаданными для сохранения в БД.
    
    Args:
        text: Текст документа
        source: Название источника (например, "book.pdf")
        additional_metadata: Дополнительные метаданные (page, author и т.д.)
        
    Returns:
        List[dict]: Список чанков с метаданными для БД
    """
    chunks = chunk_text(text, add_metadata=True)
    
    # Добавляем метаданные источника
    for chunk in chunks:
        chunk["metadata"] = {
            "source": source,
            "chunk_index": chunk["chunk_index"],
            "total_chunks": chunk["total_chunks"],
            "char_count": chunk["char_count"],
            "token_count": chunk["token_count"],
            "chapter": chunk.get("chapter"),
            **(additional_metadata or {})
        }
        
        # Оставляем только content и metadata для БД
        chunk_content = chunk["content"]
        chunk_metadata = chunk["metadata"]
        
        chunk.clear()
        chunk["content"] = chunk_content
        chunk["metadata"] = chunk_metadata
    
    logger.info(f"Document '{source}' chunked into {len(chunks)} pieces")
    
    return chunks


def estimate_chunks_count(text: str, chunk_size: int | None = None) -> int:
    """
    Оценить количество чанков без фактического разбиения.
    
    Args:
        text: Текст
        chunk_size: Размер чанка
        
    Returns:
        int: Примерное количество чанков
    """
    chunk_size = chunk_size or settings.chunk_size
    return max(1, len(text) // chunk_size)
