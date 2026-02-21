from langfuse.langchain import CallbackHandler
from config.settings import settings

def get_langfuse_callback(user_id: str = None, thread_id: str = None):
    """
    Создает CallbackHandler для Langfuse.
    Если ключи не настроены, возвращает None.
    """
    if not settings.langfuse_public_key or not settings.langfuse_secret_key:
        return None
        
    return CallbackHandler(
        publicKey=settings.langfuse_public_key,
        secretKey=settings.langfuse_secret_key,
        baseUrl=settings.langfuse_host,
        userId=user_id,
        sessionId=thread_id
    )

