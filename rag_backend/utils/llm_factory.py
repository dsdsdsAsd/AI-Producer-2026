from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama
from config.settings import settings
from utils.logger import logger

def get_llm(temperature: float = None):
    """
    Получить экземпляр LLM (OpenAI или Ollama) на основе настроек.
    Используется фабричный метод для избежания циклических импортов.
    """
    temp = temperature if temperature is not None else settings.temperature
    
    if settings.use_ollama:
        logger.info(f"Using Ollama model: {settings.ollama_model}")
        try:
            return ChatOllama(
                model=settings.ollama_model,
                temperature=temp,
                base_url=settings.ollama_base_url,
            )
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChatOllama: {str(e)}", exc_info=True)
            logger.warning("Falling back to OpenAI with placeholder key.")
            return ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=temp,
                openai_api_key="sk-proj-placeholder",
            )
    else:
        logger.info(f"Using OpenAI model: {settings.llm_model}")
        return ChatOpenAI(
            model=settings.llm_model,
            temperature=temp,
            max_tokens=settings.max_tokens,
            openai_api_key=settings.openai_api_key,
        )
