"""
Конфигурация приложения с использованием Pydantic Settings.
Все переменные окружения валидируются и имеют значения по умолчанию.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # OpenAI API
    openai_api_key: str
    
    # Supabase (векторная БД)
    supabase_url: str
    supabase_key: str
    
    # PostgreSQL (долгосрочная память)
    postgres_db_url: str
    
    # Langfuse (Мониторинг)
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "https://cloud.langfuse.com"
    
    # Настройки приложения
    environment: str = "development"
    log_level: str = "INFO"
    
    # Настройки модели
    llm_model: str = "gpt-4o-mini"
    ollama_model: str = "llama3.1:latest"
    use_ollama: bool = True
    ollama_base_url: str = "http://localhost:11434"
    embedding_model: str = "text-embedding-3-small"
    ollama_embedding_model: str = "bge-m3"
    temperature: float = 0.7
    max_tokens: int = 2000
    
    # Настройки chunking
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # Настройки RAG
    top_k_results: int = 20  # Количество релевантных чанков для поиска
    similarity_threshold: float = 0.45  # Минимальная схожесть для включения в контекст
    
    # Настройки API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: list[str] = ["*"]
    
    # Настройки сессий
    session_token_length: int = 32


# Глобальный экземпляр настроек
settings = Settings()
