"""
SQLAlchemy модели для таблиц базы данных.
Соответствуют схеме из database/init_db.sql
"""

from sqlalchemy import Column, String, Text, TIMESTAMP, UUID, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class User(Base):
    """
    Модель пользователя.
    Простая session-based авторизация.
    """
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(255), unique=True, nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_active = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"


class UserChat(Base):
    """
    Модель истории чатов пользователей.
    Хранит все сообщения (user и assistant).
    """
    __tablename__ = "user_chats"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False, index=True)
    thread_id = Column(String(255), nullable=False, index=True)  # session_id для LangGraph
    role = Column(String(50), nullable=False)  # 'user' или 'assistant'
    content = Column(Text, nullable=False)
    extra_metadata = Column("metadata", JSONB, nullable=True)  # Дополнительные данные
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    
    # Композитный индекс для быстрого поиска истории
    __table_args__ = (
        Index('idx_user_thread_created', 'user_id', 'thread_id', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UserChat(id={self.id}, user_id={self.user_id}, role={self.role})>"


class KnowledgeBase(Base):
    """
    Модель векторной базы знаний.
    Хранит чанки документов с эмбеддингами.
    """
    __tablename__ = "knowledge_base"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    content = Column(Text, nullable=False)
    # embedding - обрабатывается напрямую через SQL (тип vector(1024))
    extra_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    def __repr__(self):
        source = self.extra_metadata.get("source", "unknown") if self.extra_metadata else "unknown"
        return f"<KnowledgeBase(id={self.id}, source={source})>"


class BoardIdea(Base):
    """
    Модель идеи для доски планирования.
    """
    __tablename__ = "board_ideas"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    status = Column(String(50), default="todo") # 'todo', 'in_progress', 'done'
    cover_type = Column(String(50), nullable=True)
    extra_metadata = Column("metadata", JSONB, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<BoardIdea(id={self.id}, title={self.title})>"


class UserStrategy(Base):
    """
    Модель стратегии и позиционирования пользователя.
    """
    __tablename__ = "user_strategy"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), unique=True, nullable=False, index=True)
    
    positioning = Column(Text, nullable=True)     # "Кто я"
    target_audience = Column(Text, nullable=True) # "ЦА"
    customer_pains = Column(Text, nullable=True)  # "Боли"
    triggers = Column(Text, nullable=True)       # "Триггеры"
    
    goals = Column(Text, nullable=True)          # "Цели"
    content_architecture = Column(JSONB, nullable=True) # % виральных/экспертных и т.д.
    shorts_structure = Column(JSONB, nullable=True)     # Структура хук/боль/инсайт
    
    cases = Column(Text, nullable=True)          # "Кейсы" (E-comm, Voice AI и т.д.)
    monetization = Column(JSONB, nullable=True)  # "Монетизация" (Школа, Курс 50к)
    
    shorts_logic = Column(JSONB, nullable=True)  # Логика Shorts (Хук, Боль, Инсайт, Поляризация)
    full_context = Column(Text, nullable=True)   # Весь присланный пользователем текст для эталонного контекста
    
    content_plan_config = Column(JSONB, nullable=True) # Настройки контент-плана
    
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<UserStrategy(user_id={self.user_id})>"


# Функция для создания всех таблиц (если нужно)
def create_tables(engine):
    """
    Создать все таблицы в БД.
    
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.create_all(bind=engine)


# Функция для удаления всех таблиц (для тестов)
def drop_tables(engine):
    """
    Удалить все таблицы из БД.
    
    Args:
        engine: SQLAlchemy engine
    """
    Base.metadata.drop_all(bind=engine)
