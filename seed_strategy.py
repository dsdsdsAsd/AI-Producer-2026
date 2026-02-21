import os
import psycopg2
import json
from dotenv import load_dotenv

load_dotenv(dotenv_path="rag_backend/.env")

def seed_user_data():
    db_url = os.getenv("POSTGRES_DB_URL")
    if not db_url:
        print("❌ POSTGRES_DB_URL not found in .env")
        return

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    # Данные пользователя из его запроса
    strategy_data = {
        "user_id": "default",
        "goals": "Получить первых 3–5 клиентов на дорогой курс (50 000 руб) в течение 30–60 дней через системный контент. KPI: 5 созвонов в месяц.",
        "positioning": "Инженер-программист. Роль: Практик-инженер. Угол: Проектирование и внедрение реальных мультимодальных RAG-систем для автоматизации бизнеса. Отличие: Показ архитектуры и логики, а не хайпа.",
        "target_audience": "Junior-разработчики, техлиды, фаундеры IT-бизнеса, люди которые хотят в AI, но боятся не успеть и перегружены инфошумом.",
        "customer_pains": "Логические: нет roadmap, не знают стек. Эмоциональные: боятся отстать, синдром самозванца. Скрытые: хотят денег, статус, чувствовать себя умными.",
        "triggers": "Страх будущего, Деньги (400k+), Поляризация (курсы за 20к - мусор), Авторитет (реальные кейсы), Разрушение иллюзий.",
        "cases": "- E-commerce: нейро-эксперт для конверсии\n- Voice AI: агент для автосервиса (бронирование)\n- EdTech: мультиагентный RAG по книгам\n- ML & CV: анализ растений",
        "monetization": json.dumps({
            "product": "Дорогой курс / Личная работа",
            "price": "50 000 руб",
            "assets": ["YouTube-канал", "Онлайн-школа", "Личный бренд в процессе"],
            "model": "Ограниченный набор + личный отбор"
        }),
        "content_architecture": json.dumps({"viral": 40, "expert": 30, "case": 20, "warmup": 10})
    }

    try:
        # Сначала проверим, есть ли запись
        cur.execute("SELECT id FROM user_strategy WHERE user_id = 'default'")
        exists = cur.fetchone()

        if exists:
            # Обновляем
            query = """
            UPDATE user_strategy 
            SET goals = %s, positioning = %s, target_audience = %s, 
                customer_pains = %s, triggers = %s, cases = %s, 
                monetization = %s, content_architecture = %s, updated_at = now()
            WHERE user_id = 'default'
            """
            cur.execute(query, (
                strategy_data["goals"], strategy_data["positioning"], strategy_data["target_audience"],
                strategy_data["customer_pains"], strategy_data["triggers"], strategy_data["cases"],
                strategy_data["monetization"], strategy_data["content_architecture"]
            ))
            print("✅ Стратегия пользователя успешно обновлена данными из запроса!")
        else:
            # Создаем новую
            query = """
            INSERT INTO user_strategy 
            (user_id, goals, positioning, target_audience, customer_pains, triggers, cases, monetization, content_architecture)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cur.execute(query, (
                strategy_data["user_id"], strategy_data["goals"], strategy_data["positioning"],
                strategy_data["target_audience"], strategy_data["customer_pains"], strategy_data["triggers"],
                strategy_data["cases"], strategy_data["monetization"], strategy_data["content_architecture"]
            ))
            print("✅ Новая стратегия пользователя создана и заполнена!")

        conn.commit()
    except Exception as e:
        print(f"❌ Ошибка при сидировании: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed_user_data()
