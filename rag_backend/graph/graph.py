"""
Сборка LangGraph графа для Agentic RAG системы.
Граф: Router → (RAG или Direct) → Generator
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from graph.state import GraphState
from graph.nodes import router_node, strategy_node, summary_node, rag_node, generator_node, route_question
from utils.logger import logger


def create_graph():
    """
    Создать и скомпилировать LangGraph граф.
    
    Returns:
        CompiledGraph: Скомпилированный граф
    """
    logger.info("Creating LangGraph graph...")
    
    # Создаем граф с типом состояния
    workflow = StateGraph(GraphState)
    
    # Добавляем узлы
    workflow.add_node("router", router_node)
    workflow.add_node("strategy_loader", strategy_node)
    workflow.add_node("summary_loader", summary_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("generator", generator_node)
    
    # Устанавливаем точку входа
    workflow.set_entry_point("router")
    
    # Цепочка: router -> strategy_loader -> summary_loader
    workflow.add_edge("router", "strategy_loader")
    workflow.add_edge("strategy_loader", "summary_loader")
    
    # Добавляем условный переход от summary
    workflow.add_conditional_edges(
        "summary_loader",
        route_question,
        {
            "rag": "rag",
            "generator": "generator"
        }
    )
    
    # Добавляем переход от RAG к Generator
    workflow.add_edge("rag", "generator")
    
    # Добавляем переход от Generator к концу
    workflow.add_edge("generator", END)
    
    # Компилируем граф с checkpointer для памяти
    # MemorySaver сохраняет состояние в памяти (для продакшена можно использовать PostgresSaver)
    checkpointer = MemorySaver()
    graph = workflow.compile(checkpointer=checkpointer)
    
    logger.info("Graph compiled successfully")
    
    return graph


# Singleton instance графа
_graph = None


def get_graph():
    """
    Получить скомпилированный граф (singleton).
    
    Returns:
        CompiledGraph: Граф
    """
    global _graph
    
    if _graph is None:
        _graph = create_graph()
    
    return _graph


# Функция для визуализации графа (опционально, для дебага)
def visualize_graph():
    """
    Визуализировать граф в формате Mermaid.
    
    Returns:
        str: Mermaid диаграмма
    """
    graph = get_graph()
    
    try:
        # LangGraph может генерировать Mermaid диаграммы
        mermaid = graph.get_graph().draw_mermaid()
        return mermaid
    except Exception as e:
        logger.error(f"Graph visualization error: {e}")
        return None
