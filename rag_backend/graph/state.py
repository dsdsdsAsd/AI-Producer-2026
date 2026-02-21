"""
Определение состояния LangGraph графа.
State хранит сообщения и метаданные на протяжении всего выполнения.
"""

from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage
import operator


class GraphState(TypedDict):
    """
    Состояние графа для Agentic RAG системы.
    
    Поля:
        messages: История сообщений (user и assistant)
        user_id: ID пользователя
        thread_id: ID треда (сессии)
        intent: Определенное намерение (knowledge_base_search, creative_writing, direct_response)
        context: Контекст из RAG (если был поиск)
        sources: Метаданные источников (если был RAG)
        current_stage: Текущий этап продюсерского пайплайна (1-10)
        blueprint: Данные стратегии, накопленные по этапам
        metadata: Дополнительные метаданные
    """
    
    # История сообщений (добавляются через operator.add)
    messages: Annotated[List[BaseMessage], operator.add]
    
    # Идентификаторы пользователя и сессии
    user_id: str
    thread_id: str
    
    # Результаты маршрутизации
    intent: str | None
    persona: str | None # Текущая роль (например, 'velizhanin', 'esther')
    
    # Контекст из RAG
    summary: str | None
    context: str | None
    sources: List[Dict[str, Any]] | None
    
    # Данные для продюсерского пайплайна
    current_stage: int | None
    blueprint: Dict[str, Any]
    
    # Дополнительные метаданные
    metadata: Dict[str, Any]


# Вспомогательная функция для создания начального состояния
def create_initial_state(
    user_id: str,
    thread_id: str,
    messages: List[BaseMessage] | None = None
) -> GraphState:
    """
    Создать начальное состояние графа.
    
    Args:
        user_id: ID пользователя
        thread_id: ID треда
        messages: Начальные сообщения (опционально)
        
    Returns:
        GraphState: Начальное состояние
    """
    return {
        "messages": messages or [],
        "user_id": user_id,
        "thread_id": thread_id,
        "intent": None,
        "summary": None,
        "context": None,
        "sources": None,
        "current_stage": 1,
        "blueprint": {},
        "metadata": {}
    }
