"""
Репозитории для работы с базой данных.
Инкапсулируют логику доступа к данным.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from typing import List, Optional
import secrets
import uuid

from database.models import User, UserChat, KnowledgeBase


class UserRepository:
    """Репозиторий для работы с пользователями"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_username(self, username: str) -> Optional[User]:
        """
        Получить пользователя по username.
        
        Args:
            username: Имя пользователя
            
        Returns:
            User или None
        """
        return self.db.query(User).filter(User.username == username).first()
    
    def get_by_session_token(self, session_token: str) -> Optional[User]:
        """
        Получить пользователя по session token.
        
        Args:
            session_token: Токен сессии
            
        Returns:
            User или None
        """
        return self.db.query(User).filter(User.session_token == session_token).first()
    
    def create(self, username: str) -> User:
        """
        Создать нового пользователя.
        
        Args:
            username: Имя пользователя
            
        Returns:
            User: Созданный пользователь
        """
        # Генерируем session token
        session_token = secrets.token_urlsafe(32)
        
        user = User(
            username=username,
            session_token=session_token
        )
        
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def update_session_token(self, user: User) -> User:
        """
        Обновить session token пользователя.
        
        Args:
            user: Пользователь
            
        Returns:
            User: Обновленный пользователь
        """
        user.session_token = secrets.token_urlsafe(32)
        self.db.commit()
        self.db.refresh(user)
        
        return user


class ChatRepository:
    """Репозиторий для работы с историей чатов"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def add_message(
        self,
        user_id: str,
        thread_id: str,
        role: str,
        content: str,
        metadata: Optional[dict] = None
    ) -> UserChat:
        """
        Добавить сообщение в историю чата.
        
        Args:
            user_id: ID пользователя
            thread_id: ID треда (сессии)
            role: Роль ('user' или 'assistant')
            content: Содержимое сообщения
            metadata: Дополнительные метаданные
            
        Returns:
            UserChat: Созданное сообщение
        """
        message = UserChat(
            user_id=user_id,
            thread_id=thread_id,
            role=role,
            content=content,
            extra_metadata=metadata or {}
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def get_history(
        self,
        user_id: str,
        thread_id: str,
        limit: int = 10
    ) -> List[UserChat]:
        """
        Получить историю чата.
        
        Args:
            user_id: ID пользователя
            thread_id: ID треда
            limit: Максимальное количество сообщений
            
        Returns:
            List[UserChat]: Список сообщений (от старых к новым)
        """
        messages = (
            self.db.query(UserChat)
            .filter(
                UserChat.user_id == user_id,
                UserChat.thread_id == thread_id
            )
            .order_by(desc(UserChat.created_at))
            .limit(limit)
            .all()
        )
        
        # Возвращаем в хронологическом порядке (от старых к новым)
        return list(reversed(messages))
    
    def get_all_threads(self, user_id: str) -> List[str]:
        """
        Получить все thread_id пользователя, отсортированные по последнему сообщению.
        
        Args:
            user_id: ID пользователя
            
        Returns:
            List[str]: Список thread_id (от нового к старому)
        """
        threads = (
            self.db.query(UserChat.thread_id)
            .filter(UserChat.user_id == user_id)
            .group_by(UserChat.thread_id)
            .order_by(func.max(UserChat.created_at).desc())
            .all()
        )
        
        return [thread[0] for thread in threads]
    
    def delete_thread(self, user_id: str, thread_id: str) -> int:
        """
        Удалить всю историю треда.
        
        Args:
            user_id: ID пользователя
            thread_id: ID треда
            
        Returns:
            int: Количество удаленных сообщений
        """
        deleted_count = (
            self.db.query(UserChat)
            .filter(
                UserChat.user_id == user_id,
                UserChat.thread_id == thread_id
            )
            .delete()
        )
        
        self.db.commit()
        return deleted_count


class KnowledgeRepository:
    """Репозиторий для работы с базой знаний"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_all_documents(self) -> List[KnowledgeBase]:
        """
        Получить все документы из базы знаний.
        
        Returns:
            List[KnowledgeBase]: Список документов
        """
        return self.db.query(KnowledgeBase).all()
    
    def get_by_source(self, source: str) -> List[KnowledgeBase]:
        """
        Получить все чанки из определенного источника.
        
        Args:
            source: Название источника (например, "book.pdf")
            
        Returns:
            List[KnowledgeBase]: Список чанков
        """
        return (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.extra_metadata["source"].astext == source)
            .all()
        )
    
    def delete_by_source(self, source: str) -> int:
        """
        Удалить все чанки из определенного источника.
        
        Args:
            source: Название источника
            
        Returns:
            int: Количество удаленных чанков
        """
        deleted_count = (
            self.db.query(KnowledgeBase)
            .filter(KnowledgeBase.extra_metadata["source"].astext == source)
            .delete(synchronize_session=False)
        )
        
        self.db.commit()
        return deleted_count
    
    def get_sources_list(self) -> List[str]:
        """
        Получить список всех уникальных источников.
        
        Returns:
            List[str]: Список названий источников
        """
        # Используем JSONB оператор для извлечения source
        sources = (
            self.db.query(KnowledgeBase.extra_metadata["source"].astext)
            .distinct()
            .all()
        )
        
        return [source[0] for source in sources if source[0]]
    
    def count_chunks(self) -> int:
        """
        Подсчитать общее количество чанков в базе знаний.
        
        Returns:
            int: Количество чанков
        """
        return self.db.query(KnowledgeBase).count()
