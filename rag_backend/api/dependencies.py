"""
FastAPI dependencies для аутентификации и получения ресурсов.
"""

from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session
from utils.llm_factory import get_llm

from database.connection import get_db
from database.repositories import UserRepository
from database.models import User
from graph.graph import get_graph
from config.settings import settings
from utils.logger import logger
from duckduckgo_search import DDGS
import json


async def get_current_user(
    authorization: str = Header(None, description="Session token"),
    db: Session = Depends(get_db)
) -> User:
    """
    Получить текущего пользователя по session token.
    В режиме разработки возвращает тестового пользователя, если токен не указан.
    """
    # Режим разработки: создаем/возвращаем тестового пользователя если токен пуст
    if not authorization and settings.environment == "development":
        user_repo = UserRepository(db)
        test_user = user_repo.get_by_username("test_user")
        if not test_user:
            test_user = user_repo.create("test_user")
        return test_user

    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use: Bearer <token>"
        )
    
    session_token = authorization.replace("Bearer ", "")
    
    user_repo = UserRepository(db)
    user = user_repo.get_by_session_token(session_token)
    
    if not user:
        logger.warning(f"Invalid session token: {session_token[:10]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid session token"
        )
    
    return user


def get_compiled_graph():
    """
    Получить скомпилированный LangGraph граф.
    
    Returns:
        CompiledGraph: Граф
    """
    return get_graph()


def search_web_tool(query: str, max_results: int = 5) -> str:
    """
    Инструмент для поиска в интернете через DuckDuckGo.
    
    Args:
        query: Поисковый запрос
        max_results: Количество результатов
        
    Returns:
        str: Текстовое описание результатов (JSON)
    """
    logger.info(f"Searching web for: {query}")
    results = []
    try:
        with DDGS() as ddgs:
            ddgs_gen = ddgs.text(query, max_results=max_results)
            for r in ddgs_gen:
                results.append(r)
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return "[]"

