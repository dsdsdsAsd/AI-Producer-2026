import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path="rag_backend/.env")

def seed_complete_strategy():
    db_url = os.getenv("POSTGRES_DB_URL")
    if not db_url:
        print("❌ POSTGRES_DB_URL not found in .env")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Точный текст пользователя для эталонного контекста
    full_context_text = """
МЫ СТРОИМ: AI-продюсер, который понимает этап, узкое место и какой контент нужен для продажи.
ЛОГИКА: 1. Цель -> 2. Позиционирование -> 3. Аудитория -> 4. Боли -> 5. Триггеры -> 6. Архитектура -> 7. План -> 8. Вирусные темы -> 9. Сценарии -> 10. Рекомендации.

ОБО МНЕ:
- Инженер-программист. Проектирую мультимодальные RAG-системы.
- Кейсы: E-commerce (конверсия), Voice AI (автосервис - полный цикл), EdTech (RAG по книгам), ML & CV (растения).
- Активы: YouTube, Школа, Курс (50 000 руб).
- Цель: 3-5 клиентов за 30-60 дней.
- Готов: Shorts каждый день, 1-2 длинных видео в месяц.

ВИРУСНЫЕ ТЕМЫ (ПРИМЕРЫ):
1. Ломка иллюзий: "90% людей никогда не станут AI-инженерами".
2. Поляризация: "AI - это не профессия. Это фильтр".
3. Жесткая правда: "Через 3 года junior-разработчики будут не нужны".
4. Деньги: "AI-инженер зарабатывает 400к не из-за кода".
5. Страх упустить: "2026 год - последний шанс войти в AI легко".

СТРУКТУРА SHORTS:
- Хук (3 сек): "Ты никогда не станешь AI-инженером".
- Боль: "Потому что ты смотришь ролик, но не строишь проекты".
- Инсайт: "Работодателю не важны знания - важна архитектура".
- Поляризация: "AI - это не про Python, это про..."
- CTA: Вопрос в комменты.
"""

    strategy_data = {
        "user_id": "default",
        "goals": "Получить первых 3–5 клиентов на дорогой курс (50 000 руб) в течение 30–60 дней через системный контент. KPI: 5 созвонов в месяц.",
        "positioning": "Практик-инженер (AI Architect). Угол: Реальные AI-системы, а не теория. Отличие: Показ архитектуры и логики внедрения RAG.",
        "target_audience": "Junior-разработчики, техлиды, фаундеры IT-бизнеса. Боли: нет roadmap, страх отстать, синдром самозванца.",
        "customer_pains": "Логические ( roadmap/стек), Эмоциональные (страх отстать), Скрытые (деньги/статус).",
        "triggers": "Страх будущего, Деньги, Поляризация, Авторитет, Разрушение иллюзий.",
        "cases": "- E-commerce: нейро-эксперт\n- Voice AI: агент для автосервиса (бронь)\n- EdTech: RAG по книгам\n- ML & CV: анализ растений",
        "monetization": json.dumps({
            "product": "Дорогой курс",
            "price": "50 000 руб",
            "assets": ["YouTube", "Школа", "Личный бренд"],
            "model": "Ограниченный набор + личный отбор"
        }),
        "content_architecture": json.dumps({"viral": 40, "expert": 30, "case": 20, "warmup": 10}),
        "shorts_logic": json.dumps({
            "structure": ["Хук (3 сек)", "Боль", "Инсайт", "Поляризация", "CTA"],
            "hook_examples": [
                "Ты никогда не станешь AI-инженером",
                "90% людей никогда не станут AI-инженерами",
                "AI - это не профессия. Это фильтр"
            ],
            "polarization_examples": [
                "Курсы за 20к - мусор",
                "Junior-разработчики будут не нужны"
            ]
        }),
        "full_context": full_context_text.strip()
    }

    try:
        cur.execute("SELECT id FROM user_strategy WHERE user_id = 'default'")
        exists = cur.fetchone()

        if exists:
            query = """
            UPDATE user_strategy 
            SET goals = %s, positioning = %s, target_audience = %s, 
                customer_pains = %s, triggers = %s, cases = %s, 
                monetization = %s, content_architecture = %s, 
                shorts_logic = %s, full_context = %s, updated_at = now()
            WHERE user_id = 'default'
            """
            cur.execute(query, (
                strategy_data["goals"], strategy_data["positioning"], strategy_data["target_audience"],
                strategy_data["customer_pains"], strategy_data["triggers"], strategy_data["cases"],
                strategy_data["monetization"], strategy_data["content_architecture"],
                strategy_data["shorts_logic"], strategy_data["full_context"]
            ))
            print("✅ ПОЛНАЯ СТРАТЕГИЯ (со всеми хуками и контекстом) успешно обновлена!")
        else:
            query = """
            INSERT INTO user_strategy 
            (user_id, goals, positioning, target_audience, customer_pains, triggers, cases, monetization, content_architecture, shorts_logic, full_context)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(query, (
                strategy_data["user_id"], strategy_data["goals"], strategy_data["positioning"],
                strategy_data["target_audience"], strategy_data["customer_pains"], strategy_data["triggers"],
                strategy_data["cases"], strategy_data["monetization"], strategy_data["content_architecture"],
                strategy_data["shorts_logic"], strategy_data["full_context"]
            ))
            print("✅ ПОЛНАЯ СТРАТЕГИЯ создана!")

        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_complete_strategy()
