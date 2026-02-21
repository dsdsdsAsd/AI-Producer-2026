"""
Узлы LangGraph графа.
Каждый узел выполняет определенную функцию в агентской RAG системе.
"""

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
# # from langchain_ollama import ChatOllama

from graph.state import GraphState
from tools.intent_classifier import get_intent_classifier
from tools.rag_retriever import get_rag_retriever
from config.settings import settings
from config.prompts import GENERATOR_SYSTEM_PROMPT
from utils.llm_factory import get_llm
from utils.logger import logger


def strategy_node(state: GraphState) -> GraphState:
    """
    Узел стратегии: подгружает личную стратегию пользователя из БД.
    Это дает ИИ понимание 'Кто я', 'Что продаем', 'Какие кейсы'.
    """
    logger.info("=== Strategy Node ===")
    
    try:
        from database.connection import get_db
        from database.models import UserStrategy
        
        # Получаем сессию БД
        db_gen = get_db()
        db = next(db_gen)
        
        # Получаем стратегию (default юзер)
        strategy = db.query(UserStrategy).filter(UserStrategy.user_id == "default").first()
        
        if strategy:
            # Формируем читаемый контекст для LLM
            strategy_context = f"""
### ЭТАЛОННЫЙ КОНТЕКСТ ЭКСПЕРТА (КТО Я):
{strategy.full_context}

### СТРАТЕГИЧЕСКИЕ ДАННЫЕ:
- ЦЕЛЬ: {strategy.goals}
- КЕЙСЫ: {strategy.cases}
- ТРИГГЕРЫ: {strategy.triggers}
"""
            # Логика Shorts
            if strategy.shorts_logic:
                sl = strategy.shorts_logic
                if isinstance(sl, str):
                    try: import json; sl = json.loads(sl)
                    except: pass
                
                if isinstance(sl, dict):
                    strategy_context += f"\n### ПРАВИЛА ВАШИХ SHORTS:\n"
                    strategy_context += f"- СТРУКТУРА: {' -> '.join(sl.get('structure', []))}\n"
                    strategy_context += f"- ПРИМЕРЫ ХУКОВ ДЛЯ МОДЕЛЕЙ: {', '.join(sl.get('hook_examples', []))}\n"
            # Монетизация
            if strategy.monetization:
                m = strategy.monetization
                if isinstance(m, str):
                    try: import json; m = json.loads(m)
                    except: pass
                
                if isinstance(m, dict):
                    strategy_context += f"- МОНЕТИЗАЦИЯ: {m.get('product', 'Курс')} за {m.get('price', '50k')}\n"
                    strategy_context += f"- АКТИВЫ: {', '.join(m.get('assets', []))}\n"

            state["summary"] = (state.get("summary") or "") + "\n" + strategy_context
            logger.info("User strategy successfully loaded into context")
        else:
            logger.info("No user strategy found in DB")
            
    except Exception as e:
        logger.error(f"Error in strategy_node: {e}")
        
    return state


def router_node(state: GraphState) -> GraphState:
    """
    Узел маршрутизации: определяет намерение пользователя.
    
    Args:
        state: Текущее состояние графа
        
    Returns:
        GraphState: Обновленное состояние с intent
    """
    logger.info("=== Router Node ===")
    
    # Получаем последнее сообщение пользователя
    messages = state["messages"]
    if not messages:
        logger.warning("No messages in state")
        state["intent"] = "direct_response"
        return state
    
    last_message = messages[-1]
    user_message = last_message.content if hasattr(last_message, 'content') else str(last_message)
    
    # Формируем историю для контекста (последние 5 сообщений)
    chat_history = []
    for msg in messages[-5:]:
        if isinstance(msg, HumanMessage):
            chat_history.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            chat_history.append({"role": "assistant", "content": msg.content})
    
    # Классифицируем намерение
    classifier = get_intent_classifier()
    intent = classifier.classify(user_message, chat_history)
    
    logger.info(f"Intent classified: {intent}")
    
    # Обновляем состояние
    state["intent"] = intent
    
    return state


    return state


def summary_node(state: GraphState) -> GraphState:
    """
    Узел Summary: подгружает "паспорт книги" (глобальный контекст).
    Это позволяет ИИ знать общее содержание книги, список глав и т.д.
    """
    logger.info("=== Summary Node ===")
    
    # Пытаемся получить паспорт книги из метаданных или специального поиска
    # Для начала просто создаем заглушку-запрос к БД для поиска метаданных
    try:
        from database.connection import get_supabase_client
        client = get_supabase_client()
        
        # Ищем чанк с типом 'summary' или 'passport'
        response = client.table("knowledge_base").select("content").filter("metadata->>type", "eq", "passport").execute()
        
        if response.data and len(response.data) > 0:
            state["summary"] = response.data[0]["content"]
            logger.info("Book passport found and loaded into state")
        else:
            # Если паспорта нет, можно попробовать вывести список источников для контекста
            logger.info("No passport found in DB")
            state["summary"] = "Глобальный паспорт книги не найден. Ассистент будет использовать только найденные фрагменты."
            
    except Exception as e:
        logger.error(f"Error in summary_node: {e}")
        state["summary"] = None
        
    return state


def rag_node(state: GraphState) -> GraphState:
    """
    Узел RAG: выполняет векторный поиск в базе знаний.
    
    Args:
        state: Текущее состояние графа
        
    Returns:
        GraphState: Обновленное состояние с context и sources
    """
    logger.info("=== RAG Node ===")
    
    # Получаем запрос из последнего сообщения
    messages = state.get("messages", [])
    if not messages:
        logger.warning("No messages in state")
        state["context"] = ""
        state["sources"] = []
        return state
    
    query = messages[-1].content if hasattr(messages[-1], 'content') else str(messages[-1])
    logger.info(f"RAG query: {query[:100]}...")
    
    # Определяем фильтры на основе персоны
    persona = state.get("persona")
    filter_metadata = {}
    
    # ФИЛЬТР: Исключаем книгу про Мурадова (type='book')
    # По умолчанию ищем только в type='shorts_transcript' или 'velizhanin'
    if persona == "velizhanin":
        filter_metadata = {"author": "Nikolay Velizhanin"}
        logger.info("Using Velizhanin isolation filter")
    elif persona == "esther":
        filter_metadata = {"author": "Esther Hicks"}
        logger.info("Using Esther Hicks isolation filter")
    else:
        # Если персона не задана, ищем во ВСЕХ транскриптах (временно отключаем фильтр для теста)
        filter_metadata = {}
        logger.info("🔍 Diagnostic mode: searching across all documents without filter")

    # Выполняем поиск (graceful fallback если embeddings недоступны)
    try:
        context, sources = retriever.retrieve_and_format(query, filter_metadata=filter_metadata, use_scores=True)
        # Временно снижаем порог вручную в retriever если нужно, но лучше просто проверить что вернет.
        
        logger.info(f"RAG retrieved {len(sources)} sources")
        if sources:
            logger.info(f"Retrieved sources: {[s.get('chapter', s.get('title', 'unknown')) for s in sources]}")
            scores = [s.get('similarity', 0.0) for s in sources]
            avg_score = sum(scores) / len(scores) if scores else 0.0
            logger.info(f"📊 Avg similarity score: {avg_score:.3f}, Scores: {[f'{s:.3f}' for s in scores]}")
            if avg_score < 0.7:
                logger.warning(f"⚠️ Low quality retrieval! Avg score {avg_score:.3f} < 0.7")
    except Exception as e:
        logger.error(f"❌ RAG retrieval failed (embeddings unavailable?): {e}")
        logger.warning("🔄 Continuing without RAG context — will respond directly via LLM")
        context = ""
        sources = []
    
    # Если ничего не найдено, добавляем информационное сообщение
    if not context:
        logger.warning("RAG node found no context.")
        context = ""
        sources = []

    state["context"] = context
    state["sources"] = sources
    
    return state


def generator_node(state: GraphState) -> GraphState:
    """
    Узел генерации: создает финальный ответ пользователю.
    
    Args:
        state: Текущее состояние графа
        
    Returns:
        GraphState: Обновленное состояние с ответом assistant
    """
    logger.info("=== Generator Node ===")
    
    # --- DEBUG LOGGING ---
    context = state.get("context") or ""
    summary = state.get("summary") or ""
    logger.info(f"Context length: {len(context)} chars")
    logger.info(f"Summary length: {len(summary)} chars")
    if context:
        logger.info(f"Context (first 500 chars): {context[:500]}")
    # --- END DEBUG LOGGING ---

    # Инициализируем LLM (OpenAI или Ollama)
    # Инициализируем LLM (OpenAI или Ollama)
    llm = get_llm(temperature=settings.temperature)
    
    # Формируем промпт
    messages = [{"role": "system", "content": GENERATOR_SYSTEM_PROMPT}]
    
    # Добавляем контекст из RAG (если есть)
    if context:
        context_message = {
            "role": "system",
            "content": f"Контекст из базы знаний:\n\n{context}"
        }
        messages.append(context_message)
    
    # Добавляем "паспорт" книги (глобальный контекст)
    if summary:
        summary_message = {
            "role": "system",
            "content": f"Глобальный контекст книги (паспорт):\n\n{summary}"
        }
        messages.append(summary_message)
    
    # Форматируем системный промпт с учетом этапа и блюпринта
    current_stage = state.get("current_stage", 1)
    blueprint = state.get("blueprint", {})
    
    # Формируем краткий обзор накопленной стратегии
    blueprint_summary = ""
    if blueprint:
        blueprint_summary = "Накопленная стратегия (ContentBlueprint):\n"
        for stage_num, data in blueprint.items():
            blueprint_summary += f"Этап {stage_num}: {data}\n"
    else:
        blueprint_summary = "Стратегия еще не начата. Мы на ЭТАПЕ 1."

    # Обновляем основной системный промпт данными
    formatted_system_prompt = GENERATOR_SYSTEM_PROMPT.format(
        current_stage=current_stage,
        blueprint_summary=blueprint_summary
    )
    
    # Заменяем первый системный промпт на отформатированный
    messages[0]["content"] = formatted_system_prompt
    
    # Добавляем историю чата (последние 10 сообщений)
    for msg in state["messages"][-10:]:
        if isinstance(msg, HumanMessage):
            messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            messages.append({"role": "assistant", "content": msg.content})
    
    logger.info(f"Final prompt message count: {len(messages)}")
    # Log the system role messages to see context presence
    for m in messages:
        if m["role"] == "system":
            logger.info(f"System message ({len(m['content'])} chars): {m['content'][:200]}...")
    
    # Генерируем ответ (без streaming для простоты, streaming будет в API)
    try:
        logger.info("Invoking LLM...")
        response = llm.invoke(messages)
        answer = response.content
        
        logger.info(f"LLM call successful. Generated answer: {len(answer)} chars")
        
        # Парсим ответ на наличие JSON-данных текущего этапа
        # Если агент выдал структурированный ответ по этапу, сохраняем его в блюпринт
        try:
            import re
            import json
            # Ищем JSON в блоках кода или просто в тексте
            json_match = re.search(r"```json\s*(.*?)\s*```", answer, re.DOTALL) or re.search(r"(\{.*?\})", answer, re.DOTALL)
            if json_match:
                stage_data = json.loads(json_match.group(1))
                stage_num = state.get("current_stage", 1)
                
                # Сохраняем данные в блюпринт
                if "blueprint" not in state or state["blueprint"] is None:
                    state["blueprint"] = {}
                
                state["blueprint"][str(stage_num)] = stage_data
                logger.info(f"✨ Stage {stage_num} data saved to blueprint")
                
                # Если этап завершен успешно, переходим к следующему
                if stage_num < 10:
                    state["current_stage"] = stage_num + 1
                    logger.info(f"🚀 Moving to Stage {state['current_stage']}")
                    
                    # Специальная метка для фронтенда о сохранении этапа
                    if "metadata" not in state: state["metadata"] = {}
                    state["metadata"]["last_saved_stage"] = stage_num
        except Exception as e:
            logger.warning(f"Failed to auto-parse stage data: {e}")

        # Добавляем ответ в messages
        state["messages"].append(AIMessage(content=answer))
        
        if "metadata" not in state:
            state["metadata"] = {}
            
        # Добавляем метаданные
        state["metadata"]["sources"] = state.get("sources", [])
        state["metadata"]["intent"] = state.get("intent")
        
    except Exception as e:
        logger.error(f"Generation error: {e}")
        # Fallback ответ
        error_message = "Извините, произошла ошибка при генерации ответа."
        state["messages"].append(AIMessage(content=error_message))
    
    return state


# Функция для определения следующего узла (conditional edge)
def route_question(state: GraphState) -> str:
    """
    Определить следующий узел на основе intent.
    
    Args:
        state: Текущее состояние графа
        
    Returns:
        str: Название следующего узла
    """
    intent = state.get("intent")
    
    logger.info(f"Routing based on intent: {intent}")
    
    # ВРЕМЕННО: Всегда идем через RAG для тестирования качества
    # Это гарантирует, что система использует знания Велижанина
    logger.info("🔥 Forcing RAG route for all queries (testing mode)")
    return "rag"
    
    # ОРИГИНАЛЬНАЯ ЛОГИКА (закомментирована):
    # if intent in ["knowledge_base_search", "creative_writing"]:
    #     return "rag"
    # else:
    #     return "generator"

