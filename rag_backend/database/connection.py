"""
Подключение к базам данных: PostgreSQL и Supabase.
Инициализация клиентов для работы с векторным хранилищем.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from supabase import create_client, Client
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_ollama import OllamaEmbeddings
from typing import Generator
import os

from config.settings import settings
from utils.logger import logger


# SQLAlchemy Engine для PostgreSQL
engine = create_engine(
    settings.postgres_db_url,
    pool_pre_ping=True,  # Проверка соединения перед использованием
    pool_size=5,
    max_overflow=10,
    echo=settings.environment == "development"  # Логирование SQL в dev режиме
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency для получения сессии БД в FastAPI.
    
    Yields:
        Session: SQLAlchemy сессия
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Supabase клиент
_supabase_client: Client | None = None


def get_supabase_client() -> Client:
    """
    Получить Supabase клиент (singleton).
    
    Returns:
        Client: Supabase клиент
    """
    global _supabase_client
    
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.supabase_url,
            settings.supabase_key
        )
    
    return _supabase_client


# Ollama Embeddings (локально, не требует VPN)
_embeddings: OllamaEmbeddings | None = None


def get_embeddings() -> OllamaEmbeddings:
    """
    Получить Ollama Embeddings модель (singleton).
    Используется для локального векторного поиска.
    """
    global _embeddings
    
    if _embeddings is None:
        # Используем модель bge-m3 для лучшего качества на русском
        model_name = getattr(settings, "ollama_embedding_model", "bge-m3")
        logger.info(f"Инициализация OllamaEmbeddings с моделью: {model_name}")
        _embeddings = OllamaEmbeddings(
            model=model_name,
            base_url=settings.ollama_base_url
        )
    
    return _embeddings


# Векторное хранилище (локальный PostgreSQL)
class LocalVectorStore:
    """Замена SupabaseVectorStore для работы напрямую с PostgreSQL."""
    def __init__(self, embeddings: OllamaEmbeddings):
        self.embeddings = embeddings

    def similarity_search(self, query: str, k: int = 5, filter: dict = None):
        """
        Поиск похожих документов через функцию match_documents.
        """
        try:
            query_embedding = self.embeddings.embed_query(query)
            
            with engine.connect() as conn:
                from sqlalchemy import text
                import json
                
                # Вызываем нашу SQL функцию
                result = conn.execute(text("""
                    SELECT content, metadata, similarity 
                    FROM match_documents(:emb, :threshold, :limit, :filter)
                """), {
                    "emb": query_embedding,
                    "threshold": settings.similarity_threshold,
                    "limit": k,
                    "filter": json.dumps(filter or {})
                })
                
                from langchain_core.documents import Document
                docs = []
                for row in result:
                    docs.append(Document(
                        page_content=row[0],
                        metadata=row[1]
                    ))
                return docs
        except Exception as e:
            logger.error(f"Error in similarity_search: {e}")
            return []

_local_vector_store: LocalVectorStore | None = None

def get_vector_store() -> LocalVectorStore:
    """
    Получить локальное векторное хранилище (singleton).
    """
    global _local_vector_store
    
    if _local_vector_store is None:
        embeddings = get_embeddings()
        _local_vector_store = LocalVectorStore(embeddings=embeddings)
    
    return _local_vector_store


def test_connections() -> dict[str, bool]:
    """
    Тестирование подключений к БД.
    
    Returns:
        dict: Статус подключений
    """
    results = {
        "postgres": False,
        "supabase": False,
        "embeddings": False
    }
    
    # Тест PostgreSQL
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        results["postgres"] = True
    except Exception as e:
        print(f"PostgreSQL connection failed: {e}")
    
    # Тест Supabase
    try:
        client = get_supabase_client()
        # Простой запрос для проверки
        client.table("users").select("id").limit(1).execute()
        results["supabase"] = True
    except Exception as e:
        print(f"Supabase connection failed: {e}")
    
    # Тест Embeddings
    try:
        embeddings = get_embeddings()
        # Создаем тестовый эмбеддинг
        embeddings.embed_query("test")
        results["embeddings"] = True
    except Exception as e:
        print(f"OpenAI Embeddings failed: {e}")
    
    return results
