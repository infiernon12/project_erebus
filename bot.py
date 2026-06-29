# File: bot.py
# Project: erebus_project (Alex Consciousness Isolation)
# Type: Telegram Bot Executable

import os
import asyncio
import logging
from datetime import datetime
import html
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.enums import ParseMode
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, TelegramObject

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

# Whitelist of allowed Telegram User IDs
ALLOWED_USERS = {5200313096, 5051074589, 571505504, 7185711234}

class AccessControlMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = None
        # Extract user_id from the Telegram Update object properties
        if hasattr(event, "message") and event.message:
            user_id = event.message.from_user.id
        elif hasattr(event, "callback_query") and event.callback_query:
            user_id = event.callback_query.from_user.id
        elif hasattr(event, "inline_query") and event.inline_query:
            user_id = event.inline_query.from_user.id
        elif hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id

        if user_id not in ALLOWED_USERS:
            if hasattr(event, "message") and event.message:
                try:
                    await event.message.answer("⚠️ **[ДОСТУП ОГРАНИЧЕН]** Сознание Алекса находится в режиме строгой изоляции. Связь запрещена.")
                except Exception:
                    pass
            elif hasattr(event, "callback_query") and event.callback_query:
                try:
                    await event.callback_query.answer("⚠️ Доступ ограничен.", show_alert=True)
                except Exception:
                    pass
            return
            
        return await handler(event, data)

dp.update.outer_middleware(AccessControlMiddleware())

# Memory trackers for background activities
last_reflection = {}
last_weak_thought_time = {}
last_workspace_time = {}

def get_alex_keyboard():
    keyboard_buttons = [
        [
            KeyboardButton(text="🧠 Состояние Алекса"),
            KeyboardButton(text="📖 Файлы и чтение")
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
    
    is_new = db.register_user(user_id, username, message.from_user.first_name)
    
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
    db.register_user(user_id, message.from_user.username, message.from_user.first_name)
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
@dp.message(Command("alex_state"))
@dp.message(F.text.endswith("Состояние Алекса"))
async def cmd_status(message: types.Message):
    user_id = message.from_user.id
    emotions = db.get_alex_emotions(user_id)
    ltm_list = db.get_ltm_nodes_by_user(user_id)
    ltm_edges = db.get_ltm_edges_by_user(user_id)
    stm_list = db.get_alex_stm(user_id)
    
    dominant_str = ""
    if emotions.get("dominant_focus"):
        focus = emotions["dominant_focus"]
        strength = emotions.get("dominant_strength", 0.0)
        bar_len = 5
        filled = int(strength * bar_len)
        bar = "▰" * filled + "▱" * (bar_len - filled)
        dominant_str = f"🎯 **Когнитивная Доминанта:** `{focus}` (`{strength:.2f}` `{bar}`)\n\n"
        
    status_text = (
        "🧠 **Текущий нейробиологический профиль Алекса:**\n\n"
        f"🧪 Дофамин (Dopamine): `{emotions['dopamine']:.2f}/1.00` (base: `{emotions['base_dopamine']:.2f}`)\n"
        f"🛡️ Серотонин (Serotonin): `{emotions['serotonin']:.2f}/1.00` (base: `{emotions['base_serotonin']:.2f}`)\n"
        f"⚡ Норадреналин (Noradrenaline): `{emotions['noradrenaline']:.2f}/1.00` (base: `{emotions['base_noradrenaline']:.2f}`)\n"
        f"🎓 Ацетилхолин (Acetylcholine): `{emotions['acetylcholine']:.2f}/1.00` (base: `{emotions['base_acetylcholine']:.2f}`)\n"
        f"☯️ ГАМК (GABA): `{emotions['gaba']:.2f}/1.00` (base: `{emotions['base_gaba']:.2f}`)\n"
        f"🫂 Окситоцин (Oxytocin): `{emotions['oxytocin']:.2f}/1.00` (base: `{emotions['base_oxytocin']:.2f}`)\n"
        f"🔥 Глутамат (Glutamate): `{emotions['glutamate']:.2f}/1.00` (base: `{emotions['base_glutamate']:.2f}`)\n"
        f"💊 Эндорфины (Endorphins): `{emotions['endorphins']:.2f}/1.00` (base: `{emotions['base_endorphins']:.2f}`)\n"
        f"🔋 Усталость (Fatigue): `{emotions['fatigue']:.1f}/100.0`\n\n"
        f"{dominant_str}"
        f"📥 Кратковременных воспоминаний (STM): `{len(stm_list)}`\n"
        f"💾 Долговременных синапсов (LTM Nodes): `{len(ltm_list)}`\n"
        f"🔗 Ассоциативных связей (LTM Edges): `{len(ltm_edges)}`\n"
        f"🕒 Последняя активность: `{emotions['last_interaction']}`"
    )
    
    inline_kb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🧪 DA (Доф)", callback_data="alex:log:dopamine"),
            InlineKeyboardButton(text="🛡️ 5-HT (Сер)", callback_data="alex:log:serotonin"),
            InlineKeyboardButton(text="⚡ NE (Нор)", callback_data="alex:log:noradrenaline")
        ],
        [
            InlineKeyboardButton(text="🎓 ACh (Аце)", callback_data="alex:log:acetylcholine"),
            InlineKeyboardButton(text="☯️ GABA (ГАМК)", callback_data="alex:log:gaba"),
            InlineKeyboardButton(text="🫂 OXT (Окс)", callback_data="alex:log:oxytocin")
        ],
        [
            InlineKeyboardButton(text="🔥 GLU (Глу)", callback_data="alex:log:glutamate"),
            InlineKeyboardButton(text="💊 END (Энд)", callback_data="alex:log:endorphins")
        ],
        [
            InlineKeyboardButton(text="📊 Общий лог химии", callback_data="alex:cmd:log"),
            InlineKeyboardButton(text="💭 Лог мыслей", callback_data="alex:cmd:thoughts")
        ],
        [
            InlineKeyboardButton(text="🧬 Нейроны памяти (LTM)", callback_data="alex:cmd:neurons")
        ],
        [InlineKeyboardButton(text="🧠 Запустить рефлексию", callback_data="alex:reflect")],
        [InlineKeyboardButton(text="💤 Отправить спать (1 мин)", callback_data="alex:sleep")]
    ])
    
    await message.answer(status_text, reply_markup=inline_kb, parse_mode=ParseMode.MARKDOWN)

@dp.message(F.text.endswith("Файлы и чтение"))
async def btn_files(message: types.Message):
    logger.info(f"btn_files triggered by user {message.from_user.id}")
    try:
        files = alex_brain.list_workspace_files()
        ws = ", ".join([html.escape(f) for f in files["workspace"]]) if files["workspace"] else "пусто"
        rq = ", ".join([html.escape(f) for f in files["reading_queue"]]) if files["reading_queue"] else "пусто"
        
        report = (
            "📖 <b>[СОСТОЯНИЕ КОГНИТИВНЫХ ФАЙЛОВ]</b>\n\n"
            f"📂 <b>Рабочая папка (alex_workspace/):</b>\n<code>{ws}</code>\n\n"
            f"📚 <b>Очередь на чтение (alex_reading/):</b>\n<code>{rq}</code>\n\n"
            "Вы можете добавлять файлы .txt или .md в alex_reading/ через файловый менеджер вашего сервера, и Алекс прочтет их в ваше отсутствие."
        )
        await message.answer(report, parse_mode=ParseMode.HTML)
    except Exception as ex:
        logger.error(f"Error in btn_files: {ex}", exc_info=True)
        await message.answer("⚠️ Произошла ошибка при получении списка файлов.")

def format_utc_to_local(utc_str: str) -> str:
    try:
        utc_dt = datetime.strptime(utc_str.split(".")[0], "%Y-%m-%d %H:%M:%S")
        local_dt = utc_dt + (datetime.now() - datetime.utcnow())
        return local_dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return utc_str

# Alex Callback Query Handlers
@dp.callback_query(F.data == "alex:cmd:log")
async def callback_alex_cmd_log(callback: CallbackQuery):
    user_id = callback.from_user.id
    query = """
        SELECT dopamine_delta, serotonin_delta, noradrenaline_delta, acetylcholine_delta, 
               gaba_delta, oxytocin_delta, glutamate_delta, endorphins_delta, 
               trigger_text, created_at
        FROM alex_neuro_history
        WHERE user_id = ?
        ORDER BY id DESC
        LIMIT 5
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (db.GLOBAL_ALEX_ID,))
            rows = cursor.fetchall()
            
        if not rows:
            await callback.message.answer("ℹ️ История нейробиологических логов пуста.")
            await callback.answer()
            return
            
        lines = ["📊 **Последние 5 нейробиологических логов Алекса:**\n"]
        for row in rows:
            deltas = {
                "DA": row[0], "5-HT": row[1], "NE": row[2], "ACh": row[3],
                "GABA": row[4], "OXT": row[5], "GLU": row[6], "END": row[7]
            }
            trigger = row[8] or "нет описания"
            created_at = row[9]
            time_str = format_utc_to_local(created_at)
            
            non_zero_deltas = []
            for name, d in deltas.items():
                if d and abs(d) >= 0.01:
                    sign = "+" if d > 0 else ""
                    non_zero_deltas.append(f"{name}: `{sign}{d:.2f}`")
            
            delta_summary = ", ".join(non_zero_deltas) if non_zero_deltas else "Без изменений"
            if len(trigger) > 60:
                trigger = trigger[:57] + "..."
                
            lines.append(f"⏱ `{time_str}` | {delta_summary}\n└ *Триггер:* `{trigger}`")
            
        await callback.message.answer("\n\n".join(lines), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_alex_cmd_log: {e}")
        await callback.message.answer(f"⚠️ Ошибка при чтении логов: {e}")
        await callback.answer()

@dp.callback_query(F.data == "alex:cmd:thoughts")
async def callback_alex_cmd_thoughts(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        thoughts = db.get_thought_history(db.GLOBAL_ALEX_ID, limit=5)
        if not thoughts:
            await callback.message.answer("ℹ️ История мыслей Алекса пока пуста.")
            await callback.answer()
            return
            
        lines = ["💭 **История мыслей и рефлексии Алекса (последние 5):**\n"]
        for t in thoughts:
            t_type = "СЛАБАЯ МЫСЛЬ"
            if t["thought_type"] == "reflection":
                t_type = "РЕФЛЕКСИЯ"
            elif t["thought_type"] == "self_dialogue":
                t_type = "САМОАНАЛИЗ / ДИАЛОГ"
            elif t["thought_type"] == "recursive_thought":
                t_type = "РЕКУРСИВНЫЙ ПОТОК"
                
            content = t["thought"]
            created_at = t["created_at"]
            time_str = format_utc_to_local(created_at)
            
            lines.append(f"⏱ `{time_str}` | 🏷 **{t_type}**\n```\n{content}\n```")
            
        await callback.message.answer("\n\n".join(lines), parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error in callback_alex_cmd_thoughts: {e}")
        await callback.message.answer(f"⚠️ Ошибка при чтении мыслей: {e}")
        await callback.answer()

@dp.callback_query(F.data == "alex:cmd:neurons")
async def callback_alex_cmd_neurons(callback: CallbackQuery):
    user_id = callback.from_user.id
    try:
        nodes = db.get_ltm_nodes_by_user(user_id)
        if not nodes:
            await callback.message.answer("ℹ️ База долговременных нейронов Алекса пуста.")
            await callback.answer()
            return
            
        nodes = [n for n in nodes if n.get("memory_text")]
        nodes.sort(key=lambda x: x.get("strength", 0.0), reverse=True)
        
        txt_lines = [
            "🧬 КАРТА НЕЙРОНОВ ДОЛГОВРЕМЕННОЙ ПАМЯТИ АЛЕКСА (LTM)",
            f"Всего нейронов: {len(nodes)}",
            f"Дата выгрузки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            ""
        ]
        for node in nodes:
            n_type = node.get("memory_type", "unknown")
            strength = node.get("strength", 0.0)
            text = node["memory_text"]
            node_id = node.get("id", "?")
            
            bar_len = 10
            filled = int(strength * bar_len)
            bar = "▰" * filled + "▱" * (bar_len - filled)
            
            txt_lines.append(f"📌 ID: {node_id} | Тип: [{n_type}] | Сила: {strength:.4f} [{bar}]")
            txt_lines.append(f"└ Текст: \"{text}\"")
            txt_lines.append("-" * 60)
            
        txt_content = "\n".join(txt_lines)
        
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as temp_file:
            temp_file.write(txt_content)
            temp_path = temp_file.name
            
        try:
            from aiogram.types import FSInputFile
            file_input = FSInputFile(temp_path, filename=f"alex_neurons_{user_id}.txt")
            await callback.bot.send_document(
                chat_id=callback.message.chat.id,
                document=file_input,
                caption=f"🧬 Карта нейронов памяти Алекса (LTM). Всего: {len(nodes)}."
            )
            await callback.answer()
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        logger.error(f"Error in callback_alex_cmd_neurons: {e}")
        await callback.message.answer(f"⚠️ Ошибка при чтении нейронов: {e}")
        await callback.answer()

@dp.callback_query(F.data == "alex:reflect")
async def callback_alex_reflect(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.answer("🧠 Инициирую процесс рефлексии (расщепленный диалог)... 💭")
    dialogue_text, should_write, msg_out = alex_brain.run_reflection(user_id)
    
    reflect_text = (
        "💬 **[ВНУТРЕННИЙ ДИАЛОГ АЛЕКСА]:**\n"
        "```\n"
        f"{dialogue_text}\n"
        "```\n"
    )
    if should_write and msg_out:
        reflect_text += f"📢 **Решение:** Алекс решил написать тебе:\n*\"{msg_out}\"*\n\n*(Сообщение отправлено)*"
        db.add_alex_stm(user_id, "assistant", msg_out, emotional_charge=5.0)
        db.add_message(user_id, "assistant", msg_out)
        db.update_last_interaction(user_id)
        await callback.message.answer(msg_out)
        
    await callback.message.answer(reflect_text, parse_mode="Markdown")
    await callback.answer("Рефлексия завершена!")

@dp.callback_query(F.data == "alex:sleep")
async def callback_alex_sleep(callback: CallbackQuery):
    user_id = callback.from_user.id
    await callback.message.answer("💤 Инициирую консолидацию памяти и сброс синаптической усталости Алекса...")
    asyncio.create_task(alex_brain.trigger_sleep_cycle(user_id))
    await callback.message.answer("✅ Память успешно консолидирована, усталость сброшена до 0.0.")
    await callback.answer("Сон завершен!")

@dp.callback_query(F.data.startswith("alex:log:"))
async def callback_alex_log(callback: CallbackQuery):
    user_id = callback.from_user.id
    chemical = callback.data.split(":")[-1]
    chem_names = {
        "dopamine": "Дофамин (Dopamine)",
        "serotonin": "Серотонин (Serotonin)",
        "noradrenaline": "Норадреналин (Noradrenaline)",
        "acetylcholine": "Ацетилхолин (Acetylcholine)",
        "gaba": "ГАМК (GABA)",
        "oxytocin": "Окситоцин (Oxytocin)",
        "glutamate": "Глутамат (Glutamate)",
        "endorphins": "Эндорфины (Endorphins)"
    }
    chem_title = chem_names.get(chemical, chemical.capitalize())
    
    query = f"""
        SELECT {chemical}, {chemical}_delta, trigger_text, created_at
        FROM alex_neuro_history
        WHERE user_id = ? AND ({chemical}_delta != 0.0 OR trigger_text = 'sleep_reset')
        ORDER BY id DESC
        LIMIT 10
    """
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (user_id,))
            rows = cursor.fetchall()
            
        if not rows:
            await callback.message.answer(f"ℹ️ История изменений для **{chem_title}** пуста.")
            await callback.answer()
            return
            
        lines = [f"📊 **История изменений: {chem_title}**\n"]
        for row in rows:
            val = row[0]
            delta = row[1]
            trigger = row[2] or "нет описания"
            created_at = row[3]
            time_str = format_utc_to_local(created_at)
            
            if delta > 0:
                delta_str = f"+{delta:.2f}"
            elif delta < 0:
                delta_str = f"{delta:.2f}"
            else:
                delta_str = "0.00"
                
            if len(trigger) > 50:
                trigger = trigger[:47] + "..."
                
            lines.append(f"⏱ `{time_str}` | Значение: `{val:.2f}` (`{delta_str}`) \n└ *Триггер:* `{trigger}`")
            
        history_text = "\n\n".join(lines)
        await callback.message.answer(history_text, parse_mode="Markdown")
        await callback.answer()
    except Exception as e:
        logger.error(f"Error fetching neuro history for {chemical}: {e}")
        await callback.message.answer("⚠️ Ошибка при чтении истории изменений из БД", show_alert=True)

@dp.message()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    user_text = message.text
    
    user = db.get_user(user_id)
    if not user:
        db.register_user(user_id, message.from_user.username, message.from_user.first_name)
        user = db.get_user(user_id)
        
    status_msg = await message.answer("🧠 *Алекс думает...*")
    try:
        await alex_brain.handle_alex_chat(message, dict(user), user_text, status_msg)
    except Exception as e:
        logger.error(f"Error handling message from {user_id}: {e}", exc_info=True)
        now = datetime.now()
        if alex_brain.API_COOLDOWN_UNTIL and now < alex_brain.API_COOLDOWN_UNTIL:
            cooldown_text = "⏳ **[СИСТЕМА]** Исчерпаны лимиты API. Ожидание. Алекс вернется через 15 минут."
            try:
                await status_msg.edit_text(cooldown_text, parse_mode="Markdown")
            except Exception:
                await message.answer(cooldown_text, parse_mode="Markdown")
        else:
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
        if alex_brain.API_COOLDOWN_UNTIL and now < alex_brain.API_COOLDOWN_UNTIL:
            continue
            
        try:
            users_list = db.get_all_users()
            all_user_ids = [u["user_id"] for u in users_list] if users_list else []
            if db.GLOBAL_ALEX_ID not in all_user_ids:
                all_user_ids.append(db.GLOBAL_ALEX_ID)
                
            for user_id in all_user_ids:
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
                
                # Check if this user has pending STM logs
                has_pending_stm = False
                try:
                    pending = db.get_alex_stm(user_id, limit=1)
                    if pending:
                        has_pending_stm = True
                except Exception as stm_err:
                    logger.warning(f"Error checking pending STM for {user_id}: {stm_err}")
                
                should_sleep = False
                if idle_mins >= 60 and emotions["fatigue"] >= 40.0:
                    should_sleep = True
                elif idle_mins >= 180 and has_pending_stm:
                    should_sleep = True
                
                # 1. Check for automatic sleep (silent for >= 60 mins and fatigue >= 40%, or inactive with pending STM)
                if should_sleep:
                    asyncio.create_task(alex_brain.trigger_sleep_cycle(user_id))
                    try:
                        await bot.send_message(
                            chat_id=user_id,
                            text="💤 **[СИСТЕМА]** Сознание Алекса прошло автоматический цикл сна (консолидация кратковременной памяти, сброс утомления и аллостатическая адаптация baselines)."
                        )
                    except Exception as msg_err:
                        logger.warning(f"Failed to send sleep auto-msg to {user_id}: {msg_err}")
                    continue
                
                # If this is not the global identity, skip proactive thoughts and weak thoughts
                if user_id != db.GLOBAL_ALEX_ID:
                    continue
                
                # 2. Check for reflection (silent for >= 30 mins)
                if idle_mins >= 30:
                    last_reflect_time = last_reflection.get(user_id)
                    reflect_interval = 1800 * slowdown_mult
                    if not last_reflect_time or (now - last_reflect_time).total_seconds() >= reflect_interval:
                        last_reflection[user_id] = now
                        dialogue_text, should_write, msg_out = alex_brain.run_reflection(db.GLOBAL_ALEX_ID)
                        logger.info(f"Alex reflection dialogue generated:\n{dialogue_text}")
                        db.add_thought_history(db.GLOBAL_ALEX_ID, dialogue_text, 'self_dialogue')
                        if should_write and msg_out:
                            import re
                            send_match = re.match(r'^\[SEND_TO_(OLEG|KATYA|RUSLAN|LOLITA):\s*["\'](.*?)["\']\]', msg_out.strip(), re.DOTALL | re.IGNORECASE)
                            if send_match:
                                target_name = send_match.group(1).upper()
                                msg_text = send_match.group(2).strip()
                                
                                user_mapping = {
                                    "RUSLAN": 571505504,
                                    "KATYA": 5200313096,
                                    "OLEG": 5051074589,
                                    "LOLITA": 7185711234
                                }
                                target_user_id = user_mapping.get(target_name)
                                if target_user_id:
                                    try:
                                        telegram_text = msg_text
                                        await bot.send_message(target_user_id, telegram_text, parse_mode="Markdown")
                                        db.add_alex_stm(target_user_id, "assistant", msg_text, emotional_charge=5.0)
                                        db.add_message(target_user_id, "assistant", msg_text)
                                        db.update_last_interaction(target_user_id)
                                        logger.info(f"Proactive reflection message successfully sent to {target_name}")
                                    except Exception as send_err:
                                        logger.error(f"Failed to send proactive message to {target_name}: {send_err}")
                                
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
    
    # Clean up non-whitelisted users from database to prevent token waste
    try:
        with db.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM users WHERE user_id NOT IN (5200313096, 5051074589, 571505504, 7185711234)")
            conn.commit()
            logger.info("Purged non-whitelisted test users from database users table.")
    except Exception as cleanup_err:
        logger.error(f"Error purging test users: {cleanup_err}")
    
    # Start reflection daemon task
    asyncio.create_task(reflection_daemon())
    
    # Start polling
    logger.info("Bot is starting polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
