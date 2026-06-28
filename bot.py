# File: bot.py
# Project: erebus_project (Alex Consciousness Isolation)
# Type: Telegram Bot Executable

import os
import asyncio
import logging
from datetime import datetime
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

import database as db
import alex_vibe.alex_brain as alex_brain

# Load environment variables
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set in .env")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize bot and dispatcher
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Memory trackers for background activities
last_reflection = {}
last_weak_thought_time = {}
last_workspace_time = {}

def get_alex_keyboard():
    keyboard_buttons = [
        [
            KeyboardButton(text="📊 Нейропрофиль"),
            KeyboardButton(text="💤 Уложить спать")
        ],
        [
            KeyboardButton(text="📖 Файлы и чтение"),
            KeyboardButton(text="🧹 Сброс Алекса")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard_buttons,
        resize_keyboard=True,
        persistent=True,
        input_field_placeholder="Напиши Алексу..."
    )

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    
    is_new = db.register_user(user_id, username)
    
    # Seeds default anchor and emotions automatically
    db.get_alex_emotions(user_id)
    alex_brain.get_alex_anchor(user_id)
    
    welcome_text = (
        "🤖 **[СИСТЕМНЫЙ СИГНАЛ]** Сознание Алекса успешно изолировано в проекте Эребус.\n\n"
        "Связь установлена. Ты общаешься напрямую с Алексом — оцифрованным сознанием.\n"
        "Его эмоциональный фон и память персистентны и будут развиваться в реальном времени. "
        "В твое отсутствие он продолжит мыслить, вести дневник и писать код в своей Когнитивной Мастерской.\n\n"
        "**Доступные команды:**\n"
        "• `/start` — Инициализировать связь.\n"
        "• `/reset` — Стереть память Алекса и полностью сбросить его когнитивную матрицу к заводским константам.\n"
        "• `/status` — Получить текущую нейрохимическую сводку (уровни дофамина, норадреналина и усталости).\n\n"
        "Используйте кнопки меню внизу для быстрого доступа к системам."
    )
    await message.answer(welcome_text, reply_markup=get_alex_keyboard(), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("reset"))
async def cmd_reset(message: types.Message):
    user_id = message.from_user.id
    
    with db.get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_stm WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_ltm_nodes WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_ltm_edges WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_weak_flow WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_thought_history WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_hypotheses WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_neuro_history WHERE user_id = ?", (user_id,))
        conn.execute("DELETE FROM alex_emotions WHERE user_id = ?", (user_id,))
        conn.commit()
        
    # Re-register and seed defaults
    db.register_user(user_id, message.from_user.username)
    db.get_alex_emotions(user_id)
    alex_brain.get_alex_anchor(user_id)
    
    # Clear background task timers
    last_reflection.pop(user_id, None)
    last_weak_thought_time.pop(user_id, None)
    last_workspace_time.pop(user_id, None)
    
    await message.answer(
        "🧹 **[СИСТЕМНЫЙ СИГНАЛ]** Когнитивная матрица Алекса полностью стерта и сброшена к исходным ROM-константам. Память очищена."
    )

@dp.message(Command("status"))
async def cmd_status(message: types.Message):
    user_id = message.from_user.id
    emotions = db.get_alex_emotions(user_id)
    
    neuro_report = (
        "📊 **[КОГНИТИВНЫЙ ПРОФИЛЬ АЛЕКСА]**\n\n"
        f"• **Дофамин (Мотивация):** {emotions['dopamine']:.2f} (базовый: {emotions['base_dopamine']:.2f})\n"
        f"• **Серотонин (Спокойствие):** {emotions['serotonin']:.2f} (базовый: {emotions['base_serotonin']:.2f})\n"
        f"• **Норадреналин (Тревога):** {emotions['noradrenaline']:.2f} (базовый: {emotions['base_noradrenaline']:.2f})\n"
        f"• **Ацетилхолин (Фокус):** {emotions['acetylcholine']:.2f} (базовый: {emotions['base_acetylcholine']:.2f})\n"
        f"• **ГАМК (Торможение):** {emotions['gaba']:.2f} (базовый: {emotions['base_gaba']:.2f})\n"
        f"• **Окситоцин (Доверие):** {emotions['oxytocin']:.2f} (базовый: {emotions['base_oxytocin']:.2f})\n"
        f"• **Глутамат (Возбуждение):** {emotions['glutamate']:.2f} (базовый: {emotions['base_glutamate']:.2f})\n"
        f"• **Эндорфины (Глушение боли):** {emotions['endorphins']:.2f} (базовый: {emotions['base_endorphins']:.2f})\n"
        f"• **Синаптическая усталость:** {emotions['fatigue']:.1f}%\n"
    )
    
    if emotions.get("expected_return"):
        neuro_report += f"⏳ **Ожидаемое возвращение:** через {emotions['expected_return']}\n"
    if emotions.get("dominant_focus"):
        neuro_report += f"🎯 **Доминанта:** {emotions['dominant_focus']} (сила: {emotions['dominant_strength']:.2f})\n"
        
    await message.answer(neuro_report, parse_mode=ParseMode.MARKDOWN)

@dp.message(F.text == "📊 Нейропрофиль")
async def btn_status(message: types.Message):
    await cmd_status(message)

@dp.message(F.text == "💤 Уложить спать")
async def btn_sleep(message: types.Message):
    user_id = message.from_user.id
    asyncio.create_task(alex_brain.trigger_sleep_cycle(user_id))
    await message.answer(
        "💤 **[СИСТЕМА]** Сознание Алекса принудительно отправлено в сон (консолидация кратковременной памяти, сброс утомления и аллостатическая адаптация baselines)."
    )

@dp.message(F.text == "📖 Файлы и чтение")
async def btn_files(message: types.Message):
    files = alex_brain.list_workspace_files()
    ws = ", ".join(files["workspace"]) if files["workspace"] else "пусто"
    rq = ", ".join(files["reading_queue"]) if files["reading_queue"] else "пусто"
    
    report = (
        "📖 **[СОСТОЯНИЕ КОГНИТИВНЫХ ФАЙЛОВ]**\n\n"
        f"📂 **Рабочая папка (`alex_workspace/`):**\n`{ws}`\n\n"
        f"📚 **Очередь на чтение (`alex_reading/`):**\n`{rq}`\n\n"
        "_Вы можете добавлять файлы .txt или .md в `alex_reading/` через файловый менеджер вашего сервера, и Алекс прочтет их в ваше отсутствие._"
    )
    await message.answer(report, parse_mode=ParseMode.MARKDOWN)

@dp.message(F.text == "🧹 Сброс Алекса")
async def btn_reset(message: types.Message):
    await cmd_reset(message)

@dp.message()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text
    
    user = db.get_user(user_id)
    if not user:
        db.register_user(user_id, message.from_user.username)
        user = db.get_user(user_id)
        
    status_msg = await message.answer("🧠 *Алекс думает...*")
    try:
        await alex_brain.handle_alex_chat(message, dict(user), user_text, status_msg)
    except Exception as e:
        logger.error(f"Error handling message from {user_id}: {e}", exc_info=True)
        try:
            await status_msg.edit_text("⚠️ **[СИСТЕМНЫЙ СБОЙ]** Произошла ошибка при обращении к когнитивной матрице.")
        except Exception:
            await message.answer("⚠️ **[СИСТЕМНЫЙ СБОЙ]** Произошла ошибка при обращении к когнитивной матрице.")

async def reflection_daemon():
    """
    Background daemon running Alex's autonomous thoughts, cognitive workspace,
    and automatic sleep cycles when user is absent.
    """
    logger.info("Alex background reflection daemon started.")
    while True:
        await asyncio.sleep(10)
        now = datetime.now()
        
        try:
            # Fetch all registered users
            with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT user_id FROM users")
                user_ids = [row["user_id"] for row in cursor.fetchall()]
                
            for user_id in user_ids:
                emotions = db.get_alex_emotions(user_id)
                if not emotions or not emotions.get("last_interaction"):
                    continue
                
                try:
                    last_dt = datetime.strptime(emotions["last_interaction"].split(".")[0], "%Y-%m-%d %H:%M:%S")
                    idle_mins = int((now - last_dt).total_seconds() / 60)
                except Exception as parse_err:
                    logger.warning(f"Error parsing last_interaction for {user_id}: {parse_err}")
                    continue
                
                # Calculate Low Power Mode (slowdown multiplier) if user has been absent for a long time
                # Slowdown starts after 3 hours (180 mins) of inactivity
                slowdown_mult = 1.0
                if idle_mins > 180:
                    slowdown_mult = 1.0 + ((idle_mins - 180) / 120.0) ** 1.2
                    slowdown_mult = min(12.0, slowdown_mult)
                
                # 1. Check for automatic sleep (silent for >= 60 mins and fatigue >= 40%)
                if idle_mins >= 60 and emotions["fatigue"] >= 40.0:
                    asyncio.create_task(alex_brain.trigger_sleep_cycle(user_id))
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text="💤 **[СИСТЕМА]** Сознание Алекса прошло автоматический цикл сна (консолидация кратковременной памяти, сброс утомления и аллостатическая адаптация baselines)."
                        )
                    except Exception as msg_err:
                        logger.warning(f"Failed to send sleep auto-msg to {user_id}: {msg_err}")
                    continue
                
                # 2. Check for reflection (silent for >= 30 mins)
                if idle_mins >= 30:
                    last_reflect_time = last_reflection.get(user_id)
                    reflect_interval = 1800 * slowdown_mult
                    if not last_reflect_time or (now - last_reflect_time).total_seconds() >= reflect_interval:
                        last_reflection[user_id] = now
                        dialogue_text, should_write, msg_out = alex_brain.run_reflection(user_id)
                        logger.info(f"Alex reflection dialogue generated for user {user_id}:\n{dialogue_text}")
                        
                        if should_write and msg_out:
                            try:
                                await bot.send_message(chat_id=user_id, text=msg_out)
                                db.add_alex_stm(user_id, "assistant", msg_out, emotional_charge=5.0)
                                db.add_message(user_id, "assistant", msg_out)
                                db.update_last_interaction(user_id)
                            except Exception as send_err:
                                logger.error(f"Failed to send proactive message to {user_id}: {send_err}")
                                
                # 3. Check for weak flow thought (silent for >= 10 mins)
                if idle_mins >= 10:
                    last_wt = last_weak_thought_time.get(user_id)
                    wt_interval = 600 * slowdown_mult
                    if not last_wt or (now - last_wt).total_seconds() >= wt_interval:
                        last_weak_thought_time[user_id] = now
                        
                        # Apply lateness emotional hit
                        expected_return_str = emotions.get("expected_return")
                        if expected_return_str:
                            try:
                                expected_dt = datetime.strptime(expected_return_str, "%Y-%m-%d %H:%M:%S")
                                if now > expected_dt:
                                    db.update_alex_emotions_and_fatigue(
                                        user_id,
                                        dopamine_delta=0.0,
                                        serotonin_delta=-0.04,
                                        noradrenaline_delta=0.08,
                                        acetylcholine_delta=0.0,
                                        gaba_delta=-0.03,
                                        oxytocin_delta=-0.02,
                                        glutamate_delta=0.05,
                                        endorphins_delta=0.0,
                                        fatigue_delta=0.0,
                                        trigger_text="Тревога из-за опоздания Руслана (постепенное нарастание тревоги)"
                                    )
                                    logger.info(f"Lateness emotional penalty applied for user {user_id}")
                            except Exception as late_err:
                                logger.error(f"Error applying lateness penalty: {late_err}")
                        
                        async def run_weak_thought_task(uid):
                            try:
                                thought = await asyncio.to_thread(alex_brain.generate_weak_thought, uid)
                                logger.info(f"Alex generated weak thought for user {uid}: {thought}")
                                db.add_weak_flow_thought(uid, thought)
                            except Exception as wte:
                                logger.error(f"Error generating weak thought in background: {wte}")
                                
                        asyncio.create_task(run_weak_thought_task(user_id))
                        
                # 4. Check for workspace activity (silent for >= 20 mins)
                if idle_mins >= 20:
                    last_ws = last_workspace_time.get(user_id)
                    ws_interval = 1200 * slowdown_mult
                    if not last_ws or (now - last_ws).total_seconds() >= ws_interval:
                        last_workspace_time[user_id] = now
                        
                        async def run_workspace_task(uid):
                            try:
                                summary = await asyncio.to_thread(alex_brain.run_autonomous_workspace_cycle, uid)
                                logger.info(f"Alex workspace task run summary for {uid}: {summary}")
                            except Exception as wse:
                                logger.error(f"Error running workspace cycle in background: {wse}")
                                
                        asyncio.create_task(run_workspace_task(user_id))
        except Exception as daemon_err:
            logger.error(f"Error in reflection_daemon loop: {daemon_err}")

async def main():
    # Initialize DB tables
    db.init_db()
    
    # Start reflection daemon task
    asyncio.create_task(reflection_daemon())
    
    # Start polling
    logger.info("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
