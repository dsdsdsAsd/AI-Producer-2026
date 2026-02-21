"""
FastAPI приложение для Agentic RAG системы.
Endpoints: auth, chat (SSE streaming), knowledge base upload, history.
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from langchain_core.messages import HumanMessage
from pathlib import Path
import uuid
import json
import asyncio
from typing import AsyncGenerator, List

from config.settings import settings
from database.connection import get_db, get_vector_store
from database.repositories import UserRepository, ChatRepository, KnowledgeRepository
from database.models import User, UserChat, KnowledgeBase, BoardIdea, UserStrategy
from api.schemas import (
    LoginRequest, LoginResponse, ChatRequest, ChatHistoryResponse,
    UploadResponse, KnowledgeBaseStats, ErrorResponse, ChatMessage,
    EnhanceRequest, EnhanceResponse, TrendRequest, TrendResponse,
    IdeaCreate, IdeaUpdate, BoardIdeaResponse, StrategyUpdate, StrategyResponse
)
from api.dependencies import get_current_user, get_compiled_graph
from graph.graph import get_graph
from graph.state import create_initial_state
from utils.logger import logger
from utils.document_loader import load_document, is_supported_format
from utils.monitoring import get_langfuse_callback
from utils.chunking import chunk_document

# Создаем FastAPI приложение
app = FastAPI(
    title="Agentic RAG System",
    description="Многопользовательская система для общения с документами",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Монтируем статические файлы (frontend)
frontend_path = Path(__file__).parent.parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    logger.info(f"Mounted frontend at /static from {frontend_path}")


# === Root Endpoint ===

@app.get("/")
async def root():
    """Главная страница - редирект на frontend"""
    from fastapi.responses import FileResponse
    
    index_path = frontend_path / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    else:
        return {"message": "Agentic RAG API", "docs": "/docs"}


# === Auth Endpoints ===

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Авторизация пользователя (простая session-based).
    Если пользователь существует, возвращает существующий токен.
    Если нет, создает нового пользователя.
    """
    logger.info(f"Login attempt: {request.username}")
    
    user_repo = UserRepository(db)
    
    # Проверяем, существует ли пользователь
    user = user_repo.get_by_username(request.username)
    
    if user:
        logger.info(f"Existing user: {user.username}")
    else:
        # Создаем нового пользователя
        user = user_repo.create(request.username)
        logger.info(f"Created new user: {user.username}")
    
    return LoginResponse(
        user_id=str(user.id),
        username=user.username,
        session_token=user.session_token
    )


# === Board Ideas Endpoints ===

def map_board_idea(idea):
    return {
        "id": idea.id,
        "title": idea.title,
        "content": idea.content,
        "status": idea.status,
        "cover_type": idea.cover_type,
        "metadata": idea.extra_metadata,
        "created_at": idea.created_at,
        "updated_at": idea.updated_at
    }

@app.get("/planner/ideas", response_model=List[BoardIdeaResponse])
async def get_ideas(db: Session = Depends(get_db)):
    """Получить все идеи с доски"""
    ideas = db.query(BoardIdea).order_by(BoardIdea.created_at.desc()).all()
    return [map_board_idea(idea) for idea in ideas]

@app.post("/planner/ideas", response_model=BoardIdeaResponse)
async def create_idea(request: IdeaCreate, db: Session = Depends(get_db)):
    """Создать новую идею"""
    new_idea = BoardIdea(
        title=request.title,
        content=request.content,
        status=request.status,
        cover_type=request.cover_type,
        extra_metadata=request.metadata
    )
    db.add(new_idea)
    db.commit()
    db.refresh(new_idea)
    return map_board_idea(new_idea)

@app.patch("/planner/ideas/{idea_id}", response_model=BoardIdeaResponse)
async def update_idea(idea_id: uuid.UUID, request: IdeaUpdate, db: Session = Depends(get_db)):
    """Обновить существующую идею"""
    idea = db.query(BoardIdea).filter(BoardIdea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "metadata":
            idea.extra_metadata = value
        else:
            setattr(idea, key, value)
    
    db.commit()
    db.refresh(idea)
    return map_board_idea(idea)

@app.delete("/planner/ideas/{idea_id}")
async def delete_idea(idea_id: uuid.UUID, db: Session = Depends(get_db)):
    """Удалить идею"""
    idea = db.query(BoardIdea).filter(BoardIdea.id == idea_id).first()
    if not idea:
        raise HTTPException(status_code=404, detail="Idea not found")
    
    db.delete(idea)
    db.commit()
    return {"status": "success", "message": "Idea deleted"}


# === User Strategy Endpoints ===

@app.get("/planner/strategy", response_model=StrategyResponse)
async def get_strategy(db: Session = Depends(get_db)):
    """Получить стратегию пользователя (пока один профиль на всю систему)"""
    strategy = db.query(UserStrategy).first()
    if not strategy:
        # Создаем пустую стратегию по умолчанию
        strategy = UserStrategy(user_id="default")
        db.add(strategy)
        db.commit()
        db.refresh(strategy)
    return strategy

@app.post("/planner/strategy", response_model=StrategyResponse)
async def update_strategy(request: StrategyUpdate, db: Session = Depends(get_db)):
    """Обновить стратегию"""
    strategy = db.query(UserStrategy).first()
    if not strategy:
        strategy = UserStrategy(user_id="default")
        db.add(strategy)
    
    update_data = request.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(strategy, key, value)
    
    db.commit()
    db.refresh(strategy)
    return strategy


# === Chat Endpoints ===

@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Отправить сообщение и получить ответ через SSE streaming.
    """
    logger.info(f"Chat request from {user.username}: {request.message[:50]}...")
    
    # Генерируем thread_id если не указан
    thread_id = request.thread_id or str(uuid.uuid4())
    
    # Сохраняем сообщение пользователя
    chat_repo = ChatRepository(db)
    chat_repo.add_message(
        user_id=str(user.id),
        thread_id=thread_id,
        role="user",
        content=request.message
    )
    
    # Создаем генератор для SSE
    async def generate() -> AsyncGenerator[str, None]:
        full_answer = ""
        try:
            logger.info("🚀 Starting chat with RAG system")
            
            # Получаем граф
            logger.info("📊 Loading LangGraph...")
            graph = get_graph()
            
            # Загружаем историю чата
            history = chat_repo.get_history(str(user.id), thread_id, limit=10)
            messages = []
            for msg in history:
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    messages.append(AIMessage(content=msg.content))
            
            # Добавляем текущее сообщение
            messages.append(HumanMessage(content=request.message))
            logger.info(f"📝 Loaded {len(messages)} messages from history")
            
            # Создаем начальное состояние
            from graph.state import GraphState
            initial_state = GraphState(
                messages=messages,
                user_id=str(user.id),
                thread_id=thread_id
            )
            
            # Конфигурация для checkpointer
            config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }
            
            # Запускаем граф
            logger.info("🔄 Invoking graph...")
            final_state = graph.invoke(initial_state, config)
            logger.info("✅ Graph completed successfully")
            
            # Получаем ответ
            answer_messages = final_state.get("messages", [])
            if answer_messages:
                last_message = answer_messages[-1]
                full_answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                full_answer = "Извините, не удалось сгенерировать ответ."
            
            logger.info(f"💬 Answer generated: {full_answer[:100]}...")
            
            # Отправляем источники (если есть)
            sources = final_state.get("sources", [])
            if sources:
                logger.info(f"📚 Found {len(sources)} sources")
                sources_data = json.dumps({
                    "type": "sources",
                    "sources": sources
                }, ensure_ascii=False)
                yield f"data: {sources_data}\n\n"
            
            # Отправляем ответ частями (эффект печати)
            words = full_answer.split()
            for i, word in enumerate(words):
                chunk_data = json.dumps({
                    "type": "token",
                    "content": word + " "
                }, ensure_ascii=False)
                yield f"data: {chunk_data}\n\n"
                
                # Небольшая задержка
                if i % 5 == 0:
                    await asyncio.sleep(0.05)
            
            # Отправляем сигнал завершения
            done_data = json.dumps({
                "type": "done",
                "metadata": {
                    "sources_count": len(sources)
                }
            }, ensure_ascii=False)
            yield f"data: {done_data}\n\n"
            
            # Сохраняем ответ в БД
            chat_repo.add_message(
                user_id=str(user.id),
                thread_id=thread_id,
                role="assistant",
                content=full_answer,
                metadata={
                    "sources": sources
                }
            )
            logger.info("💾 Answer saved to database")
            
        except Exception as e:
            logger.error(f"❌ Chat stream error: {e}", exc_info=True)
            error_data = json.dumps({
                "type": "error",
                "content": f"Произошла ошибка: {str(e)}"
            }, ensure_ascii=False)
            yield f"data: {error_data}\n\n"
            
            logger.info("Chat response completed")
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            error_data = json.dumps({
                "type": "error",
                "content": str(e)
            })
            yield f"data: {error_data}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


# Тестовый эндпоинт БЕЗ авторизации для проверки RAG
@app.post("/api/test-rag")
async def test_rag(request: ChatRequest):
    """
    Тестовый эндпоинт для проверки RAG без авторизации.
    """
    logger.info(f"🧪 Test RAG request: {request.message[:50]}...")
    
    async def generate() -> AsyncGenerator[str, None]:
        try:
            logger.info("🚀 Starting RAG test")
            
            # Получаем граф
            graph = get_graph()
            logger.info("📊 Graph loaded")
            
            # Langfuse callback для мониторинга (ВРЕМЕННО ОТКЛЮЧЕН - проблемы с API)
            # langfuse_cb = get_langfuse_callback(user_id="test_user", thread_id="test_thread")
            langfuse_cb = None
            
            # Простое сообщение без истории
            from graph.state import GraphState
            initial_state = GraphState(
                messages=[HumanMessage(content=request.message)],
                user_id="test_user",
                thread_id="test_thread"
            )
            
            # Конфигурация с Langfuse
            config = {
                "configurable": {"thread_id": "test"},
                "callbacks": [langfuse_cb] if langfuse_cb else []
            }
            
            # Запускаем граф
            logger.info("🔄 Invoking graph...")
            final_state = graph.invoke(initial_state, config)
            logger.info("✅ Graph completed")
            
            # Получаем ответ
            answer_messages = final_state.get("messages", [])
            if answer_messages:
                last_message = answer_messages[-1]
                full_answer = last_message.content if hasattr(last_message, 'content') else str(last_message)
            else:
                full_answer = "Не удалось сгенерировать ответ."
            
            logger.info(f"💬 Answer: {full_answer[:100]}...")
            
            # Детальное логирование источников
            sources = final_state.get("sources", [])
            context = final_state.get("context", "")
            
            logger.info("=" * 80)
            logger.info("📊 RAG QUALITY REPORT:")
            logger.info(f"   Sources found: {len(sources)}")
            logger.info(f"   Context length: {len(context)} chars")
            
            if sources:
                scores = [s.get('similarity', 0.0) for s in sources if isinstance(s, dict)]
                if scores:
                    avg_score = sum(scores) / len(scores)
                    logger.info(f"   Avg similarity: {avg_score:.3f}")
                    logger.info(f"   Score range: {min(scores):.3f} - {max(scores):.3f}")
                    
                    logger.info("\n   📄 Top sources:")
                    for i, source in enumerate(sources[:5], 1):
                        if isinstance(source, dict):
                            sim = source.get('similarity', 0.0)
                            title = source.get('title', source.get('chapter', 'unknown'))
                            content_preview = source.get('content', '')[:100]
                            logger.info(f"      {i}. [{sim:.3f}] {title}")
                            logger.info(f"         Preview: {content_preview}...")
                else:
                    logger.warning("   ⚠️ No similarity scores found in sources")
            else:
                logger.warning("   ⚠️ No sources returned by RAG!")
            
            logger.info("=" * 80)
            
            # Отправляем ответ
            words = full_answer.split()
            for word in words:
                chunk = json.dumps({"type": "token", "content": word + " "}, ensure_ascii=False)
                yield f"data: {chunk}\n\n"
                await asyncio.sleep(0.03)
            
            # Отправляем метрики
            metrics = {
                "type": "done",
                "sources_count": len(sources),
                "avg_similarity": sum([s.get('similarity', 0.0) for s in sources if isinstance(s, dict)]) / len(sources) if sources else 0.0
            }
            yield f"data: {json.dumps(metrics, ensure_ascii=False)}\n\n"
            
        except Exception as e:
            logger.error(f"❌ Test RAG error: {e}", exc_info=True)
            error = json.dumps({"type": "error", "content": str(e)}, ensure_ascii=False)
            yield f"data: {error}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")



@app.get("/api/chat/threads")
async def get_user_threads(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить все треды пользователя, отсортированные по дате"""
    chat_repo = ChatRepository(db)
    threads = chat_repo.get_all_threads(str(user.id))
    return {"threads": threads}


@app.get("/api/chat/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    thread_id: str,
    limit: int = 50,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить историю чата"""
    logger.info(f"Get history: user={user.username}, thread={thread_id}")
    
    chat_repo = ChatRepository(db)
    history = chat_repo.get_history(str(user.id), thread_id, limit)
    
    messages = [
        ChatMessage(
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at,
            metadata=msg.extra_metadata
        )
        for msg in history
    ]
    
    return ChatHistoryResponse(
        messages=messages,
        total=len(messages),
        thread_id=thread_id
    )


# === Knowledge Base Endpoints ===

@app.post("/api/knowledge/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Загрузить документ в базу знаний"""
    logger.info(f"Upload document: {file.filename} by {user.username}")
    
    # Проверка формата
    if not is_supported_format(file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format. Supported: PDF, DOCX, TXT"
        )
    
    # Сохраняем файл
    upload_dir = Path("data/documents")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    logger.info(f"File saved: {file_path}")
    
    try:
        # Загружаем и парсим документ
        text, file_type = load_document(file_path)
        
        # Разбиваем на чанки
        chunks = chunk_document(text, file.filename)
        
        # Сохраняем в векторную БД (параллельными батчами для скорости)
        import asyncio
        from functools import partial
        
        vector_store = get_vector_store()
        
        batch_size = 50
        texts = [chunk["content"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        
        tasks = []
        loop = asyncio.get_event_loop()
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_metadatas = metadatas[i:i + batch_size]
            # Используем to_thread (Python 3.9+) или run_in_executor для параллельности
            tasks.append(asyncio.to_thread(vector_store.add_texts, batch_texts, batch_metadatas))
            logger.info(f"Scheduled batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
        
        # Выполняем все батчи параллельно
        await asyncio.gather(*tasks)
        
        logger.info(f"Successfully added {len(chunks)} chunks to vector store total (via parallel processing)")
        
        return UploadResponse(
            filename=file.filename,
            chunks_count=len(chunks),
            message=f"Document uploaded successfully: {len(chunks)} chunks created and indexed"
        )
        
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/knowledge/graph")
async def get_knowledge_graph(
    limit: int = 100,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Получить данные для 3D графа знаний.
    Возвращает узлы (chunks) и связи (links).
    """
    logger.info(f"Fetching knowledge graph for {user.username}")
    
    # Получаем последние чанки
    from database.connection import engine
    from sqlalchemy import text
    
    sql = text("""
        SELECT id, content, metadata
        FROM knowledge_base
        WHERE metadata->>'author' = 'Nikolay Velizhanin'
        ORDER BY created_at DESC
        LIMIT :limit
    """)
    
    nodes = []
    links = []
    
    try:
        with engine.connect() as conn:
            result = conn.execute(sql, {"limit": limit})
            rows = result.fetchall()
            
            for row in rows:
                metadata = row[2] or {}
                nodes.append({
                    "id": str(row[0]),
                    "name": metadata.get("source", "Chunk"),
                    "val": 1,
                    "content": row[1][:200] + "...",
                    "color": "#4f46e5" if "vtt" in metadata.get("source", "") else "#10b981"
                })
            
            # Создаем связи на основе общего источника (source)
            # В будущем здесь можно добавить связи по семантике
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    if nodes[i]["name"] == nodes[j]["name"]:
                        links.append({
                            "source": nodes[i]["id"],
                            "target": nodes[j]["id"]
                        })
                        
    except Exception as e:
        logger.error(f"Graph fetch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
        
    return {"nodes": nodes, "links": links}


@app.get("/api/knowledge/stats", response_model=KnowledgeBaseStats)
async def get_knowledge_stats(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Получить статистику базы знаний"""
    knowledge_repo = KnowledgeRepository(db)
    
    total_chunks = knowledge_repo.count_chunks()
    sources = knowledge_repo.get_sources_list()
    
    documents = []
    for source in sources:
        chunks = knowledge_repo.get_by_source(source)
        documents.append({
            "source": source,
            "chunks_count": len(chunks),
            "created_at": chunks[0].created_at if chunks else None
        })
    
    return KnowledgeBaseStats(
        total_chunks=total_chunks,
        total_documents=len(documents),
        documents=documents
    )


# === Planner Endpoints ===

@app.post("/api/enhance-idea", response_model=EnhanceResponse)
async def enhance_idea(
    request: EnhanceRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Улучшить идею с помощью AI.
    Превращает сырую идею в структуру Hook-Value-CTA.
    """
    logger.info(f"Enhance idea for {user.username}: {request.title}")

    # Используем LangGraph для глубокого анализа с RAG
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.output_parsers import JsonOutputParser
        from api.dependencies import get_compiled_graph
        from graph.state import create_initial_state
        
        graph = get_compiled_graph()
        
        # Формируем запрос для графа
        prompt_text = f"""Улучши эту идею:
        Название: {request.title}
        Контент: {request.content}
        Фокус: {request.focus}"""
        
        # Создаем начальное состояние с указанной персоной
        initial_state = create_initial_state(
            user_id=str(user.id),
            thread_id=f"enhance_{uuid.uuid4()}",
            messages=[HumanMessage(content=prompt_text)]
        )
        initial_state["persona"] = request.persona or "velizhanin"
        
        # Конфигурация с мониторингом
        langfuse_cb = get_langfuse_callback(user_id=str(user.id), thread_id=initial_state["thread_id"])
        config = {
            "configurable": {"thread_id": initial_state["thread_id"]},
            "callbacks": [langfuse_cb] if langfuse_cb else []
        }
        
        # Запускаем граф
        logger.info(f"Invoking RAG graph (persona: {initial_state['persona']}) with monitoring")
        final_state = graph.invoke(initial_state, config)
        
        # Получаем ответ
        answer_messages = final_state.get("messages", [])
        answer_text = answer_messages[-1].content if answer_messages else ""
        
        # Если ответ не в JSON (агент мог выдать текст), просим LLM привести его к схеме
        # Но для начала попробуем распарсить напрямую
        try:
            import re
            json_match = re.search(r"\{.*\}", answer_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        except:
            pass
            
        # Fallback: Парсинг через промпт (если агент выдал просто текст)
        from api.dependencies import get_llm
        parser = JsonOutputParser(pydantic_object=EnhanceResponse)
        llm = get_llm(temperature=0)
        
        correction_prompt = ChatPromptTemplate.from_messages([
            ("system", "Convert the following AI assistant response into a valid JSON object according to the schema."),
            ("user", "{text}\n\n{format_instructions}")
        ])
        
        correction_chain = correction_prompt | llm | parser
        return correction_chain.invoke({
            "text": answer_text,
            "format_instructions": parser.get_format_instructions()
        })
        
    except Exception as e:
        logger.error(f"Enhance error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    user: User = Depends(get_current_user)
):
    """
    Стриминг чата через LangGraph.
    """
    logger.info(f"Chat stream for {user.username}: {request.message[:50]}...")
    
    from api.dependencies import get_compiled_graph
    from graph.state import create_initial_state
    
    graph = get_compiled_graph()
    
    initial_state = create_initial_state(
        user_id=str(user.id),
        thread_id=request.thread_id or f"chat_{uuid.uuid4()}",
        messages=[HumanMessage(content=request.message)]
    )
    
    config = {"configurable": {"thread_id": initial_state["thread_id"]}}
    
    async def event_generator():
        try:
            # Используем astream для получения событий в реальном времени
            async for event in graph.astream(initial_state, config, stream_mode="messages"):
                # event - это кортеж (message, metadata) в некоторых версиях или просто message
                # В текущей реализации LangGraph упростим до токенов
                if hasattr(event[0], "content") and event[0].content:
                    chunk = {"type": "token", "content": event[0].content}
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
            
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.post("/api/trend-ideas", response_model=TrendResponse)
async def generate_trend_ideas(
    request: TrendRequest,
    user: User = Depends(get_current_user)
):
    """
    Найти трендовые идеи через веб-поиск и знания Велижанина.
    """
    logger.info(f"Trend scouting for {user.username} (Topic: {request.topic})")
    
    from api.dependencies import search_web_tool, get_llm
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import JsonOutputParser
    
    # 1. Поиск в интернете
    topic_query = request.topic or "viral youtube shorts trends 2025"
    try:
        search_results = search_web_tool(f"trending YouTube Shorts topics 2025 {topic_query}")
    except Exception as e:
        logger.warning(f"Search tool failed: {e}. Using LLM internal knowledge.")
        search_results = "Data unavailable, use your internal knowledge about 2025 trends."
    
    try:
        # 2. Генерация идей на основе поиска
        llm = get_llm(temperature=0.8)
        
        parser = JsonOutputParser(pydantic_object=TrendResponse)
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """Ты - тренд-аналитик и ИИ-Продюсер. 
Твоя задача: на основе свежих данных поиска предложить 3 самых горячих и виральных темы для коротких видео (Shorts/Reels).
Темы должны быть в стиле 'Bento' или 'Nikolay Velizhanin' - четкие, бьющие в боли и обещающие результат.

Формат ответа: JSON со списком 'ideas', где у каждой идеи есть 'title' (яркий заголовок) и 'description' (краткая суть).
{format_instructions}"""),
            ("user", "Тема пользователя: {topic}\nДанные из интернета: {search_results}")
        ])
        
        chain = prompt | llm | parser
        return chain.invoke({
            "topic": topic_query,
            "search_results": search_results,
            "format_instructions": parser.get_format_instructions()
        })
        
    except Exception as e:
        logger.error(f"Trend generation error: {e}")
        # Fallback на старую логику если LLM/Parser упал
        return {
            "ideas": [
                {"title": f"Тренд: {topic_query} в 2025", "description": "Как использовать ИИ для автоматизации этой сферы."},
                {"title": "Секрет виральности в нише {topic_query}", "description": "Разбор структуры видео, которое набирает 100к+ просмотров."},
                {"title": "Ошибка новичков в {topic_query}", "description": "Почему контент не заходит и как это исправить за 15 секунд."}
            ]
        }
    except Exception as e:
        logger.error(f"Trend error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Health Check ===

@app.get("/health")
async def health_check():
    """Проверка здоровья приложения"""
    return {
        "status": "healthy",
        "environment": settings.environment,
        "llm_model": settings.llm_model
    }


# Запуск приложения
if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )
