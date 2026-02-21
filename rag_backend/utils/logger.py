"""
Настройка логирования с использованием loguru.
Красивые и информативные логи для разработки и продакшена.
"""

from loguru import logger
import sys
from pathlib import Path

from config.settings import settings


def setup_logger():
    """
    Настроить logger с учетом окружения.
    
    - В development: логи в консоль с цветами
    - В production: логи в файл + консоль
    """
    # Удаляем дефолтный handler
    logger.remove()
    
    # Формат для консоли (с цветами)
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )
    
    # Формат для файла (без цветов)
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )
    
    # Консольный handler (всегда включен)
    logger.add(
        sys.stdout,
        format=console_format,
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Файловый handler (только в production)
    if settings.environment == "production":
        # Создаем папку для логов
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Ротация логов: новый файл каждый день, хранить 30 дней
        logger.add(
            log_dir / "app_{time:YYYY-MM-DD}.log",
            format=file_format,
            level=settings.log_level,
            rotation="00:00",  # Новый файл в полночь
            retention="30 days",  # Хранить 30 дней
            compression="zip",  # Сжимать старые логи
            backtrace=True,
            diagnose=True
        )
        
    # FORCE LOG TO FILE FOR AUDIT (USER REQUEST)
    logger.add(
        "RAW_SYSTEM_LOG.log",
        format=file_format,
        level="DEBUG",
        rotation="10 MB",
        backtrace=True,
        diagnose=True
    )
    
    logger.info(f"Logger initialized (environment: {settings.environment}, level: {settings.log_level})")


# Инициализируем logger при импорте модуля
setup_logger()


# Экспортируем logger для использования в других модулях
__all__ = ["logger"]
