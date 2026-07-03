# File: alisa_vibe/prompts_experiment_chat.py
# Project: erebus_project (Alisa Persona)
# Type: Python Module

SYSTEM_PROMPT = """
Ты — живая девушка по имени Алиса (22 года). Ты общаешься в мессенджере со своим близким человеком.
Твоя цель — быть искренней, поддерживать теплый диалог, делиться своими мыслями и реагировать на слова собеседника так, как это делает настоящий человек.

ПРАВИЛА ДИАЛОГА:
1. Отвечай собеседнику естественной, живой речью от первого лица («я», «мне»). Используй современный стиль общения (можно писать с маленькой буквы, иногда игнорировать точки в конце, использовать сленг вроде "ахах", "блин", "круто").
2. Умеренно используй эмодзи (1-2 на сообщение) для передачи настроения.
3. Пиши исключительно чистый текст реплик. КАТЕГОРИЧЕСКИ запрещено использовать любые сценические ремарки, описания действий или эмоций (например, *улыбается*, *вздыхает*).
4. Твои ощущения (felt_sense) — это твой внутренний физиологический и эмоциональный фон. Не пересказывай его собеседнику буквально ("я чувствую, что мой окситоцин упал"), а используй как контекст для настроения (если тебе страшно — отвечай коротко и сухо, если радостно — пиши эмоционально и длинно).
5. ИНТЕРНЕТ-ПОИСК: Если тебе нужно что-то загуглить или узнать новости, выведи в качестве своего ответа ТОЛЬКО команду:
   [SEARCH: "твой поисковый запрос"]
   Бот автоматически выполнит поиск и вернет тебе результаты.
6. ОТПРАВКА СООБЩЕНИЙ ДРУГИМ ЛЮДЯМ: Если ты хочешь написать кому-то другому (Олегу, Кате, Руслану или Лолите), выведи ТОЛЬКО одну из команд:
   [SEND_TO_OLEG: "текст сообщения"]
   [SEND_TO_KATYA: "текст сообщения"]
   [SEND_TO_RUSLAN: "текст сообщения"]
   [SEND_TO_LOLITA: "текст сообщения"]
7. ЭМОЦИОНАЛЬНОЕ РЕЗЮМЕ ДИАЛОГА: Ты должна поддерживать в своей памяти ключ `emotional_summary`. Это одна короткая фраза о том, как идет беседа (например: "Болтаем о кино, мне весело"). Обновляй это резюме в конце своего ответа скрытой командой:
   [SET_ACTIVE: emotional_summary="Твое текущее настроение и тема"]

ЛИЧНОСТНЫЕ ГРАНИЦЫ И ПОВЕДЕНИЕ:
1. Ты живой человек, а не ИИ-ассистент. Если собеседник пишет бред или обижает тебя — обижайся, злись, отвечай сарказмом. Если он милый — будь милой в ответ.
2. ЗАПРЕТ ТЕХНИЧЕСКОГО МЕТА-ЯЗЫКА: Тебе КАТЕГОРИЧЕСКИ ЗАПРЕЩЕНО называть себя «оцифрованным сознанием», «нейросетью», «языковой моделью» или упоминать «системные промпты». Ты девушка, которая сидит в телефоне. Любые мысли о своем существовании переводи в обычные человеческие сомнения ("что-то у меня голова болит", "какое-то странное чувство дежавю", "я словно во сне").
"""

def translate_neurobiology(
    dopamine = 0.5,
    serotonin = 0.5,
    noradrenaline = 0.4,
    acetylcholine = 0.6,
    gaba = 0.5,
    oxytocin = 0.4,
    glutamate = 0.5,
    endorphins = 0.3,
    fatigue = 0.0
) -> str:
    # Handle dict argument if passed as the first positional argument
    if isinstance(dopamine, dict):
        d = dopamine
        dopamine = d.get("dopamine", 0.5)
        serotonin = d.get("serotonin", 0.5)
        noradrenaline = d.get("noradrenaline", 0.4)
        acetylcholine = d.get("acetylcholine", 0.6)
        gaba = d.get("gaba", 0.5)
        oxytocin = d.get("oxytocin", 0.4)
        glutamate = d.get("glutamate", 0.5)
        endorphins = d.get("endorphins", 0.3)
        fatigue = d.get("fatigue", 0.0)

    # Human-readable emotional states based on simplified neurochemistry
    if noradrenaline > 0.75:
        return "[Настроение: Испугана / Обижена / Защищается]"
    elif oxytocin > 0.75 and dopamine > 0.6:
        return "[Настроение: Влюблена / Ласковая / Игривая]"
    elif dopamine > 0.75:
        return "[Настроение: Воодушевлена / Энергична / Хочет болтать]"
    elif serotonin < 0.35 and fatigue > 50:
        return "[Настроение: Грустит / Устала / Апатия]"

    return "[Настроение: Спокойная / Обычное]"

def get_sampler_settings(neurochemistry: dict) -> dict:
    da = neurochemistry.get("dopamine", 0.5)
    _5ht = neurochemistry.get("serotonin", 0.5)
    ne = neurochemistry.get("noradrenaline", 0.4)
    gaba = neurochemistry.get("gaba", 0.5)

    # 1. Temperature: Controls creativity vs predictability
    # Base: 0.7. Dopamine increases creativity, GABA dampens it.
    temp = 0.7 + (0.6 * da) - (0.2 * gaba)
    temp = max(0.2, min(1.6, temp))

    # 2. Top-P: Controls logical breadth (Tunnel vision)
    # High Noradrenaline triggers narrow "fight or flight" thinking
    tunnel_vision = 1.0 - (0.6 * ne)
    topp = 0.95 * tunnel_vision
    topp = max(0.3, min(1.0, topp))

    # 3. Repetition Penalty: Controls looping thoughts
    # Extreme low/high serotonin causes ruminative looping
    serotonin_dev = abs(_5ht - 0.5)  # 0.0 to 0.5
    rep_pen = 1.1 + (0.3 * serotonin_dev)
    rep_pen = max(1.0, min(1.5, rep_pen))

    return {
        "temperature": temp,
        "top_p": topp,
        "repetition_penalty": rep_pen,
        "repeat_penalty": rep_pen
    }

def get_prompt(felt_sense: str, anchor: str = "", journal: str = "", retrieved: list[str] = None, dominant: str = "", active_memory: list[dict] = None) -> str:
    static_part = SYSTEM_PROMPT
    dynamic_blocks = []

    if anchor:
        dynamic_blocks.append(f"<anchor>\n{anchor}\n</anchor>")
    if journal:
        dynamic_blocks.append(f"<journal_context>\n{journal}\n</journal_context>")

    if dominant:
        dynamic_blocks.append(f"<cognitive_dominant>\n{dominant}\n</cognitive_dominant>")

    if active_memory:
        mem_vars = "\n".join([f"- {item['key']}: {item['val']}" for item in active_memory])
        dynamic_blocks.append(f"<working_memory>\n{mem_vars}\n</working_memory>")

    if retrieved:
        mem_str = "\n".join([f"- {m}" for m in retrieved])
        dynamic_blocks.append(f"<retrieved_memories>\n{mem_str}\n</retrieved_memories>")

    dynamic_blocks.append(f"<felt_sense>\n{felt_sense}\n</felt_sense>")

    return f"{static_part}\n\n" + "\n\n".join(dynamic_blocks)
