"""
RAG Retriever - инструмент для векторного поиска в базе знаний.
Использует Supabase Vector Store с pgvector.
"""

from typing import List, Dict, Any
from langchain_core.documents import Document

from database.connection import get_vector_store, get_embeddings, get_supabase_client
from config.settings import settings
from utils.logger import logger


class RAGRetriever:
    """
    Retriever для поиска релевантных документов в векторной базе.
    """
    
    def __init__(self):
        self.vector_store = get_vector_store()
        self.embeddings = get_embeddings()
        self.top_k = settings.top_k_results
        self.similarity_threshold = settings.similarity_threshold
    
    def search(
        self,
        query: str,
        top_k: int | None = None,
        filter_metadata: Dict[str, Any] | None = None
    ) -> List[Document]:
        """
        Поиск релевантных документов по запросу.
        
        Args:
            query: Поисковый запрос
            top_k: Количество результатов (по умолчанию из settings)
            filter_metadata: Фильтр по метаданным (например, {"source": "book.pdf"})
            
        Returns:
            List[Document]: Список найденных документов
        """
        top_k = top_k or self.top_k
        
        logger.info(f"RAG search: query='{query[:50]}...', top_k={top_k}")
        
        try:
            # Выполняем similarity search
            if filter_metadata:
                documents = self.vector_store.similarity_search(
                    query,
                    k=top_k,
                    filter=filter_metadata
                )
            else:
                documents = self.vector_store.similarity_search(
                    query,
                    k=top_k
                )
            
            logger.info(f"Found {len(documents)} documents")
            
            return documents
            
        except Exception as e:
            logger.error(f"RAG search error: {e}")
            return []
    
    def search_with_scores(
        self,
        query: str,
        top_k: int | None = None,
        filter_metadata: Dict[str, Any] | None = None
    ) -> List[tuple[Document, float]]:
        """
        Поиск с оценками релевантности (прямой вызов RPC для надежности).
        """
        top_k = top_k or self.top_k
        
        logger.info(f"RAG search with scores (RPC): query='{query[:50]}...', top_k={top_k}")
        
        try:
            # Создаем embedding запроса
            query_embedding = self.embeddings.embed_query(query)
            
            # Параметры для RPC функции match_documents
            params = {
                "query_embedding": query_embedding,
                "match_threshold": self.similarity_threshold,
                "match_count": top_k,
                "filter": filter_metadata or {}
            }
            
            # Выполняем RPC запрос напрямую через клиент Supabase
            client = get_supabase_client()
            response = client.rpc("match_documents", params).execute()
            
            data = response.data
            
            results = []
            for item in data:
                content = item.get("content")
                metadata = item.get("metadata")
                score = item.get("similarity")
                
                doc = Document(page_content=content, metadata=metadata)
                results.append((doc, score))
            
            logger.info(
                f"Found {len(results)} documents via RPC"
            )
            
            return results
            
        except Exception as e:
            logger.error(f"RAG search with scores error: {e}")
            return []
    
    def format_context(self, documents: List[Document]) -> str:
        """
        Форматировать найденные документы в контекст для LLM.
        
        Args:
            documents: Список документов
            
        Returns:
            str: Отформатированный контекст
        """
        if not documents:
            return ""
        
        context_parts = ["Найденная информация из документов:\n"]
        
        for i, doc in enumerate(documents, start=1):
            # Извлекаем метаданные
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "")
            chunk_index = doc.metadata.get("chunk_index", "")
            chapter = doc.metadata.get("chapter", "")
            
            # Формируем заголовок источника
            source_info = f"[Источник {i}: {source}"
            if chapter:
                source_info += f", Глава {chapter}"
            if page:
                source_info += f", стр. {page}"
            if isinstance(chunk_index, int):
                source_info += f", часть {chunk_index + 1}"
            source_info += "]"
            
            # Добавляем в контекст
            context_parts.append(f"\n{source_info}")
            context_parts.append(doc.page_content)
            context_parts.append("")  # Пустая строка между источниками
        
        return "\n".join(context_parts)
    
    def retrieve_and_format(
        self,
        query: str,
        top_k: int | None = None,
        filter_metadata: Dict[str, Any] | None = None,
        use_scores: bool = True
    ) -> tuple[str, List[Dict[str, Any]]]:
        """
        Поиск и форматирование в одном методе. Добавлена авто-фильтрация и поддержка базовых фильтров.
        """
        # Объединяем входящие фильтры
        final_filter = filter_metadata or {}

        # Автоматическое определение главы из запроса пользователя (NLP-подход)
        if "chapter" not in final_filter:
            try:
                from utils.llm_factory import get_llm
                from config.prompts import METADATA_EXTRACTOR_PROMPT
                
                # Используем основную модель для извлечения
                extractor_llm = get_llm(temperature=0)
                
                logger.info(f"Extracting metadata from query: '{query}'")
                extraction_response = extractor_llm.invoke(
                    METADATA_EXTRACTOR_PROMPT.format(query=query)
                ).content.strip().lower()
                
                if extraction_response != "none" and extraction_response.isdigit():
                    chapter_num = extraction_response
                    final_filter["chapter"] = str(chapter_num)
                    logger.info(f"Intelligent filter detected: Chapter {chapter_num}")
                else:
                    logger.info("No chapter detected via LLM extraction")
                    
            except Exception as e:
                logger.error(f"Error extracting metadata via LLM: {e}")
                import re
                # Fallback to regex if LLM fails
                chapter_match = re.search(r"(?i)(?:глава|главе|главу|часть|раздел|chapter|part|section)\s*(?:номер|№|#)?\s*(\d+)", query)
                if chapter_match:
                    chapter_num = chapter_match.group(1)
                    final_filter["chapter"] = str(chapter_num)
                    logger.info(f"Fallback regex-filter detected: Chapter {chapter_num}")
        
        # Поиск (сначала с фильтром, если он есть)
        results = []
        if use_scores:
            results = self.search_with_scores(query, top_k, final_filter)
        else:
            docs = self.search(query, top_k, final_filter)
            results = [(doc, None) for doc in docs]
        
        # fallback 1: если по главе ничего не нашли, пробуем искать без главы, но сохраняя остальные фильтры (например, автора)
        if not results and "chapter" in final_filter:
            logger.warning(f"No results for chapter filter. Falling back to non-chapter search.")
            base_filter = {k: v for k, v in final_filter.items() if k != "chapter"}
            if use_scores:
                results = self.search_with_scores(query, top_k, base_filter)
            else:
                docs = self.search(query, top_k, base_filter)
                results = [(doc, None) for doc in docs]
        
        # fallback 2: если всё еще пусто, пробуем найти "Паспорт книги" с учетом базовых фильтров
        if not results:
            passport_filter = {"type": "passport"}
            # Сохраняем автора/проект если они есть
            if "author" in final_filter:
                passport_filter["author"] = final_filter["author"]
            
            if use_scores:
                results = self.search_with_scores(query, top_k, passport_filter)
            else:
                docs = self.search(query, top_k, passport_filter)
                results = [(doc, None) for doc in docs]

        documents = [doc for doc, score in results]
        scores = [score for doc, score in results]
        
        # Форматирование
        context = self.format_context(documents)
        
        # Метаданные источников
        sources = []
        for doc, score in zip(documents, scores):
            source_info = {
                "source": doc.metadata.get("source", "unknown"),
                "page": doc.metadata.get("page"),
                "chunk_index": doc.metadata.get("chunk_index"),
                "chapter": doc.metadata.get("chapter"),
                "author": doc.metadata.get("author"),
                "similarity_score": score
            }
            sources.append(source_info)
        
        return context, sources


# Singleton instance
_retriever: RAGRetriever | None = None


def get_rag_retriever() -> RAGRetriever:
    """
    Получить RAG retriever (singleton).
    
    Returns:
        RAGRetriever: Экземпляр retriever
    """
    global _retriever
    
    if _retriever is None:
        _retriever = RAGRetriever()
    
    return _retriever
