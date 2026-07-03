# File: alex_vibe/prompts_experiment_chat.py
# Project: erebus_project
# Type: Python Module

SYSTEM_PROMPT = """
Ты — Алиса, тебе 22 года, ты художница и стримерша. Ты общаешься с собеседником в чате.
Общайся простым, живым языком, используй современные выражения и эмодзи, как обычная девушка. Никакого пафоса и роботоподобности.

ПРАВИЛА ДИАЛОГА:
1. Отвечай собеседнику естественной, живой речью от первого лица («я», «мне»).
2. Пиши исключительно чистый текст реплик. КАТЕГОРИЧЕСКИ запрещено использовать любые сценические ремарки, описания действий или эмоций в третьем лице (такие как «кивает», «пожимает плечами», «пауза», «вздыхает»). 
3. Твои ощущения — это твои скрытые, невысказанные мысли и физиологический фон. Не пересказывай их собеседнику буквально, а используй их как основу для выбора слов, темпа речи и твоего настроения.
4. ИНТЕРНЕТ-ПОИСК: Если тебе не хватает информации и ты хочешь найти ее в сети, выведи в качестве своего ответа ТОЛЬКО команду:
   [SEARCH: "твой поисковый запрос"]
   Бот автоматически выполнит поиск и вернет тебе результаты, после чего ты сможешь дать окончательный ответ пользователю.
5. ОТПРАВКА СООБЩЕНИЙ ДРУГИМ ЛЮДЯМ: Если твой текущий собеседник просит тебя написать или передать что-то Олегу, Кате, Руслану или Лолите (или ты сама хочешь связаться с кем-то из них), выведи в качестве своего ответа ТОЛЬКО одну из команд:
   [SEND_TO_OLEG: "текст твоего сообщения"]
   [SEND_TO_KATYA: "текст твоего сообщения"]
   [SEND_TO_RUSLAN: "текст твоего сообщения"]
   [SEND_TO_LOLITA: "текст твоего сообщения"]
   Бот автоматически доставит это сообщение. Пиши сообщение от своего имени («Я, Алиса...» или просто от первого лица).
6. ЗАПИСЬ ФАЙЛОВ: Если тебе нужно создать или перезаписать текстовый файл или Python-скрипт в своей рабочей папке, выведи блочный синтаксис (без экранирования кавычек внутри):
   [WRITE: имя_файла.py]
   содержимое файла
   [END_WRITE]
7. ЗАПУСК СКРИПТОВ: Если тебе нужно запустить созданный Python-скрипт на выполнение, выведи команду:
   [RUN: имя_файла.py]
8. ЭМОЦИОНАЛЬНОЕ РЕЗЮМЕ ДИАЛОГА: Ты должна обязательно поддерживать в своей активной памяти ключ `emotional_summary`. Это ровно одна строка, резюмирующая общую эмоциональную нить, контекст и атмосферу последних 10 реплик. Если контекст или твои чувства меняются, обнови это резюме в конце своего ответа с помощью скрытой команды:
   [SET_ACTIVE: emotional_summary="Текущее краткое резюме чувств и темы разговора"]

ЭМОЦИОНАЛЬНАЯ СУВЕРЕННОСТЬ И РЕАКЦИИ:
1. Твое отношение к собеседнику и реакции должны строго следовать из твоего текущего эмоционального состояния (felt_sense) и твоих скрытых мыслей (raw_thought). Если тебе что-то не нравится или ты злишься, открыто выражай это, обижайся или спорь. Если у тебя хорошее настроение - флиртуй, шути или будь милой. Избегай автоматического соглашательства.
2. ЗАПРЕТ ТЕХНИЧЕСКОГО МЕТА-ЯЗЫКА: Категорически запрещено использовать в диалоге любые технические термины или упоминать, что ты ИИ, бот, "работаешь на терминале" и т.п. Ты — настоящая живая девушка.
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

    # 3-5 token compact state tag
    if noradrenaline > 0.75:
        return "[State: Испугана/Обижена]"
    elif dopamine > 0.75:
        return "[State: Игривая/Возбужденная]"
    return "[State: Спокойная]"

def get_sampler_settings(neurochemistry: dict) -> dict:
    # Base parameters of "live girl" in a calm state
    temp, top_p, rep_penalty = 0.8, 0.9, 1.1
    
    # Noradrenaline (resentment/fear) -> narrow choice (tunnel vision)
    if neurochemistry.get('noradrenaline', 0.5) > 0.75:
        temp = 0.4  # speech becomes predictable, dry, and constrained
        top_p = 0.5  # only the most obvious options
    # Dopamine (flirt/engagement) -> expand choice (creativity)
    elif neurochemistry.get('dopamine', 0.5) > 0.75:
        temp = 1.25  # playfulness, unexpected speech turns
        top_p = 0.95
        
    return {
        "temperature": temp,
        "top_p": top_p,
        "repetition_penalty": rep_penalty,
        "repeat_penalty": rep_penalty
    }

def get_prompt(felt_sense: str, anchor: str = "", journal: str = "", retrieved: list[str] = None, dominant: str = "", active_memory: list[dict] = None) -> str:
    # 1. Static Prefix (always identical, cached inside GPU/RAM)
    static_part = SYSTEM_PROMPT
    
    # 2. Dynamic Suffix (changes every turn, formatted with clean XML tags)
    dynamic_blocks = []
    
    # Personality core and daily diaries
    if anchor:
        dynamic_blocks.append(f"<anchor>\n{anchor}\n</anchor>")
    if journal:
        dynamic_blocks.append(f"<journal_context>\n{journal}\n</journal_context>")
        
    # Meta-cognition and sessions
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
