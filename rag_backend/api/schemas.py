"""
Pydantic схемы для валидации запросов и ответов API.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


# === Auth Schemas ===

class LoginRequest(BaseModel):
    """Запрос на авторизацию"""
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")


class LoginResponse(BaseModel):
    """Ответ на авторизацию"""
    user_id: str
    username: str
    session_token: str
    message: str = "Login successful"


# === Chat Schemas ===

class ChatRequest(BaseModel):
    """Запрос на отправку сообщения"""
    message: str = Field(..., min_length=1, description="Сообщение пользователя")
    thread_id: Optional[str] = Field(None, description="ID треда (если не указан, создается новый)")


class ChatMessage(BaseModel):
    """Сообщение в чате"""
    role: str = Field(..., description="Роль: user или assistant")
    content: str = Field(..., description="Содержимое сообщения")
    created_at: datetime
    metadata: Optional[Dict[str, Any]] = None


class ChatHistoryResponse(BaseModel):
    """Ответ с историей чата"""
    messages: List[ChatMessage]
    total: int
    thread_id: str


# === Knowledge Base Schemas ===

class UploadResponse(BaseModel):
    """Ответ на загрузку документа"""
    status: str = "success"
    filename: str
    chunks_count: int
    message: str


class DocumentInfo(BaseModel):
    """Информация о документе"""
    source: str
    chunks_count: int
    created_at: Optional[datetime] = None


class KnowledgeBaseStats(BaseModel):
    """Статистика базы знаний"""
    total_chunks: int
    total_documents: int
    documents: List[DocumentInfo]


# === Error Schemas ===

class ErrorResponse(BaseModel):
    """Ответ с ошибкой"""
    error: str
    detail: Optional[str] = None
    status_code: int


# === SSE Schemas ===

class StreamChunk(BaseModel):
    """Чанк для SSE стриминга"""
    type: str = Field(..., description="Тип: token, sources, done, error")
    content: Optional[str] = None
    sources: Optional[List[Dict[str, Any]]] = None
    metadata: Optional[Dict[str, Any]] = None


# === Planner Schemas ===

class EnhanceRequest(BaseModel):
    """Запрос на улучшение идеи"""
    title: str
    content: str
    focus: Optional[str] = "viral_shorts"  # viral_shorts, educational, story
    persona: Optional[str] = "velizhanin"  # velizhanin, esther, etc.

class EnhanceResponse(BaseModel):
    """Ответ с улучшенной идеей"""
    hook: str
    value_proposition: str
    call_to_action: str
    script_outline: str
    suggested_title: str

class IdeaCandidate(BaseModel):
    """Кандидат на идею из трендов"""
    title: str
    description: str

class TrendRequest(BaseModel):
    """Запрос на поиск трендов"""
    topic: Optional[str] = None

class TrendResponse(BaseModel):
    """Ответ с трендовыми идеями"""
    ideas: List[IdeaCandidate]


# === Board Idea Schemas ===

class IdeaCreate(BaseModel):
    """Запрос на создание идеи"""
    title: str = Field(..., min_length=1, max_length=255)
    content: Optional[str] = None
    status: Optional[str] = "todo"
    cover_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class IdeaUpdate(BaseModel):
    """Запрос на обновление идеи"""
    title: Optional[str] = None
    content: Optional[str] = None
    status: Optional[str] = None
    cover_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BoardIdeaResponse(BaseModel):
    """Ответ с данными идеи"""
    id: Any # UUID
    title: str
    content: Optional[str]
    status: str
    cover_type: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# === Strategy Schemas ===

class StrategyUpdate(BaseModel):
    """Запрос на обновление стратегии"""
    positioning: Optional[str] = None
    target_audience: Optional[str] = None
    customer_pains: Optional[str] = None
    triggers: Optional[str] = None
    goals: Optional[str] = None
    content_architecture: Optional[Dict[str, Any]] = None
    shorts_structure: Optional[Dict[str, Any]] = None
    cases: Optional[str] = None
    monetization: Optional[Dict[str, Any]] = None
    shorts_logic: Optional[Dict[str, Any]] = None
    full_context: Optional[str] = None
    content_plan_config: Optional[Dict[str, Any]] = None

class StrategyResponse(BaseModel):
    """Ответ со стратегией"""
    positioning: Optional[str]
    target_audience: Optional[str]
    customer_pains: Optional[str]
    triggers: Optional[str]
    goals: Optional[str]
    content_architecture: Optional[Dict[str, Any]]
    shorts_structure: Optional[Dict[str, Any]]
    cases: Optional[str]
    monetization: Optional[Dict[str, Any]]
    shorts_logic: Optional[Dict[str, Any]]
    full_context: Optional[str]
    content_plan_config: Optional[Dict[str, Any]]
    updated_at: datetime

    class Config:
        from_attributes = True
