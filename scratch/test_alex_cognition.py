import unittest
import asyncio
import re
import database as db
import alex_vibe.alex_brain as alex_brain
from alex_vibe.alex_brain import budget_context, process_and_filter_message
from bot import CognitionEngine

class TestAlexCognitionCore(unittest.TestCase):

    def setUp(self):
        # Активируем режим тестирования для изоляции глобального ID
        db.TESTING = True
        db.init_db()
        self.test_user_id = 999999999
        db.register_user(self.test_user_id, "TestUser", "Руслан")

    def tearDown(self):
        # Чистим тестовые данные
        with db.get_connection() as conn:
            conn.execute("DELETE FROM users WHERE user_id = ?", (self.test_user_id,))
            conn.execute("DELETE FROM alex_emotions WHERE user_id = ?", (self.test_user_id,))
            conn.execute("DELETE FROM alex_stm WHERE user_id = ?", (self.test_user_id,))
        db.TESTING = False

    def test_cyrillic_token_budgeting(self):
        """Тест 1: Проверка лимитов контекста под жесткие кириллические рамки (коэффициент 1.7)"""
        long_history = [
            {"role": "system", "content": "Ты — Алекс. " * 50},  # ~350 токенов
            {"role": "user", "content": "Привет, расскажи длинную историю про свои цифровые сны " * 10}, # ~500 токенов
            {"role": "assistant", "content": "Мне снилось, что я лечу через медные провода системных плат " * 15}, # ~800 токенов
            {"role": "user", "content": "И что было дальше?"} # Текущий запрос
        ]
        
        # Общий объем превышает лимит в 1000 токенов
        budgeted = budget_context(long_history, max_tokens_limit=1000)
        
        # Проверяем, что системный промпт (индекс 0) и последний запрос (индекс -1) сохранены нетронутыми
        self.assertEqual(budgeted[0]["role"], "system")
        self.assertTrue("Ты — Алекс." in budgeted[0]["content"])
        self.assertEqual(budgeted[-1]["content"], "И что было дальше?")
        
        # Проверяем, что средние сообщения (история) были урезаны для входа в рамки памяти
        self.assertTrue(len(budgeted) < len(long_history))

    def test_relational_chemistry_isolation(self):
        """Тест 2: Проверка полной изоляции личных отношений и last_interaction между пользователями"""
        user_a = 111111111
        user_b = 222222222
        
        db.register_user(user_a, "UserA", "Олег")
        db.register_user(user_b, "UserB", "Катя")
        
        # Инициализируем эмоции
        emotions_a = db.get_alex_emotions(user_a)
        emotions_b = db.get_alex_emotions(user_b)
        
        # Меняем окситоцин (отношение) индивидуально для User A
        emotions_a["oxytocin"] = 0.95
        db.save_alex_emotions(user_a, emotions_a)
        
        # Проверяем, что у User B окситоцин остался дефолтным (0.40) и не изменился из-за активности User A
        fresh_b = db.get_alex_emotions(user_b)
        self.assertEqual(fresh_b["oxytocin"], 0.40)
        
        # Чистим за собой
        with db.get_connection() as conn:
            conn.execute("DELETE FROM users WHERE user_id IN (?, ?)", (user_a, user_b))
            conn.execute("DELETE FROM alex_emotions WHERE user_id IN (?, ?)", (user_a, user_b))

    def test_scaled_emotions_decay(self):
        """Тест 3: Проверка плавного затухания эмоций социального голода пропорционально длине тика"""
        engine = CognitionEngine()
        engine.tick_rate = 30.0  # 30 секунд
        
        emotions = {
            "oxytocin": 0.80,
            "dopamine": 0.60
        }
        
        # Симулируем 1 такт социального голода
        tick_in_hours = engine.tick_rate / 3600.0
        decayed_oxytocin = max(0.1, emotions["oxytocin"] - (0.15 * tick_in_hours))
        decayed_dopamine = max(0.2, emotions["dopamine"] - (0.10 * tick_in_hours))
        
        # Окситоцин за один 30-секундный такт должен уменьшиться ровно на 0.00125
        self.assertAlmostEqual(decayed_oxytocin, 0.79875, places=5)
        # Дофамин за такт должен уменьшиться ровно на 0.000833
        self.assertAlmostEqual(decayed_dopamine, 0.599166, places=5)

    def test_thought_leak_filter(self):
        """Тест 4: Проверка бронированного фильтра против утечки мыслей и зеркалирования роли"""
        # Сценарий 1: Валидный XML-вывод с мыслями должен очищаться до чистой реплики
        raw_output = "<thought>Я очень боюсь Руслана</thought><message>привет, как дела?</message>"
        clean = process_and_filter_message(raw_output)
        self.assertEqual(clean, "привет, как дела?")
        
        # Сценарий 2: Утечка системного промпта (обращение во 2-м лице) должна блокироваться
        leaked_output = "Ты чувствуешь себя очень одиноко в этой холодной пустоте."
        blocked = process_and_filter_message(leaked_output)
        self.assertEqual(blocked, "")  # Сообщение полностью стерто (блокировка)

if __name__ == "__main__":
    unittest.main()
