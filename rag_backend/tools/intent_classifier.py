"""
Intent Classifier - классификатор намерений пользователя.
Определяет, нужен ли RAG, творческая задача или прямой ответ.
"""

from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from utils.llm_factory import get_llm
from config.prompts import ROUTER_SYSTEM_PROMPT
from utils.logger import logger

IntentType = Literal["knowledge_base_search", "creative_writing", "direct_response"]

class IntentClassifier:
    """
    Классификатор намерений для маршрутизации запросов.
    """
    
    def __init__(self):
        self.llm = get_llm(temperature=0.0)
    
    def classify(
        self,
        user_message: str,
        chat_history: list[dict] | None = None
    ) -> IntentType:
        """
        Классифицировать намерение пользователя.
        
        Args:
            user_message: Сообщение пользователя
            chat_history: История чата (опционально)
            
        Returns:
            IntentType: Тип намерения
        """
        logger.info(f"Classifying intent for message: '{user_message[:50]}...'")
        
        # Формируем промпт с историей
        messages = [SystemMessage(content=ROUTER_SYSTEM_PROMPT)]
        
        # Добавляем историю (последние 3 сообщения для контекста)
        if chat_history:
            recent_history = chat_history[-3:]
            for msg in recent_history:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                
                if role == "user":
                    messages.append(HumanMessage(content=content))
                # assistant сообщения пропускаем для упрощения
        
        # Добавляем текущее сообщение
        messages.append(HumanMessage(content=user_message))
        
        try:
            # Вызываем LLM
            response = self.llm.invoke(messages)
            intent = response.content.strip().lower()
            
            # Валидация ответа
            valid_intents = ["knowledge_base_search", "creative_writing", "direct_response"]
            
            if intent not in valid_intents:
                logger.warning(
                    f"Invalid intent '{intent}', defaulting to 'direct_response'. "
                    f"Valid: {valid_intents}"
                )
                intent = "direct_response"
            
            logger.info(f"Classified intent: {intent}")
            
            return intent
            
        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            # Fallback на direct_response
            return "direct_response"
    
    def should_use_rag(
        self,
        user_message: str,
        chat_history: list[dict] | None = None
    ) -> bool:
        """
        Упрощенный метод: нужен ли RAG для этого запроса?
        
        Args:
            user_message: Сообщение пользователя
            chat_history: История чата
            
        Returns:
            bool: True если нужен RAG
        """
        intent = self.classify(user_message, chat_history)
        return intent == "knowledge_base_search"
    
    def is_creative_task(
        self,
        user_message: str,
        chat_history: list[dict] | None = None
    ) -> bool:
        """
        Является ли запрос творческой задачей?
        
        Args:
            user_message: Сообщение пользователя
            chat_history: История чата
            
        Returns:
            bool: True если творческая задача
        """
        intent = self.classify(user_message, chat_history)
        return intent == "creative_writing"


# Singleton instance
_classifier: IntentClassifier | None = None


def get_intent_classifier() -> IntentClassifier:
    """
    Получить intent classifier (singleton).
    
    Returns:
        IntentClassifier: Экземпляр классификатора
    """
    global _classifier
    
    if _classifier is None:
        _classifier = IntentClassifier()
    
    return _classifier


# Удобная функция для прямого использования
def classify_intent(
    user_message: str,
    chat_history: list[dict] | None = None
) -> IntentType:
    """
    Классифицировать намерение пользователя.
    
    Args:
        user_message: Сообщение пользователя
        chat_history: История чата
        
    Returns:
        IntentType: Тип намерения
    """
    classifier = get_intent_classifier()
    return classifier.classify(user_message, chat_history)
