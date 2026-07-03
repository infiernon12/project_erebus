import sqlite3
import os
import math
from datetime import datetime, timezone

UTC = timezone.utc
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")
GLOBAL_ALEX_ID = 571505504
TESTING = False

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_connection() as conn:
        # Users registry (simple)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                opponent_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Chat Messages
        conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                message_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Alex's Emotions (Neurotransmitters & Baselines)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_emotions (
                user_id INTEGER PRIMARY KEY,
                dopamine REAL DEFAULT 0.5,
                serotonin REAL DEFAULT 0.5,
                noradrenaline REAL DEFAULT 0.4,
                acetylcholine REAL DEFAULT 0.6,
                gaba REAL DEFAULT 0.5,
                oxytocin REAL DEFAULT 0.4,
                glutamate REAL DEFAULT 0.5,
                endorphins REAL DEFAULT 0.3,
                fatigue REAL DEFAULT 0.0,
                
                base_dopamine REAL DEFAULT 0.5,
                base_serotonin REAL DEFAULT 0.5,
                base_noradrenaline REAL DEFAULT 0.3,
                base_acetylcholine REAL DEFAULT 0.5,
                base_gaba REAL DEFAULT 0.5,
                base_oxytocin REAL DEFAULT 0.3,
                base_glutamate REAL DEFAULT 0.4,
                base_endorphins REAL DEFAULT 0.15,
                
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_dream TEXT,
                dominant_focus TEXT DEFAULT NULL,
                dominant_strength REAL DEFAULT 0.0,
                expected_return TEXT DEFAULT NULL,
                leave_reason TEXT DEFAULT NULL
            )
        """)
        # Alex's Short-Term Memory (STM)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_stm (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                role TEXT,
                content TEXT,
                emotional_charge REAL DEFAULT 0.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Alex's Long-Term Memory (LTM) Nodes
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_ltm_nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                memory_text TEXT,
                embedding TEXT,  -- JSON list of float
                memory_type TEXT DEFAULT 'episodic',  -- 'biographical', 'episodic', or 'semantic'
                strength REAL DEFAULT 1.0,
                rigidity REAL DEFAULT 0.5,
                source TEXT DEFAULT 'ego',
                verified INTEGER DEFAULT 1,
                recall_count INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Alex's Long-Term Memory (LTM) Edges
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_ltm_edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                source_id INTEGER,
                target_id INTEGER,
                weight REAL DEFAULT 0.5,
                association_type TEXT DEFAULT 'semantic',  -- 'semantic', 'causal', 'temporal', 'dream_synthesis', etc.
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES alex_ltm_nodes(id) ON DELETE CASCADE,
                FOREIGN KEY (target_id) REFERENCES alex_ltm_nodes(id) ON DELETE CASCADE
            )
        """)
        # Alex's Weak Flow thoughts
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_weak_flow (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                thought TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Alex's Permanent Thought History
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_thought_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                thought TEXT,
                thought_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Alex's Active Memory (Working Memory)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_active_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                key TEXT NOT NULL,
                val TEXT NOT NULL,
                confidence REAL DEFAULT 1.0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, key)
            )
        """)
        # Alex's Hypotheses
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_hypotheses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                thought TEXT NOT NULL,  -- wait: in AIshnitza it was hypothesis_text TEXT NOT NULL
                hypothesis_text TEXT, -- let's keep both for safety
                confidence REAL DEFAULT 0.5,
                status TEXT DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Alex's Neurotransmitter History Logs
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alex_neuro_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                dopamine REAL,
                serotonin REAL,
                noradrenaline REAL,
                acetylcholine REAL,
                gaba REAL,
                oxytocin REAL,
                glutamate REAL,
                endorphins REAL,
                fatigue REAL,
                dopamine_delta REAL,
                serotonin_delta REAL,
                noradrenaline_delta REAL,
                acetylcholine_delta REAL,
                gaba_delta REAL,
                oxytocin_delta REAL,
                glutamate_delta REAL,
                endorphins_delta REAL,
                fatigue_delta REAL,
                trigger_text TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

        # Migration: add recall_count to alex_ltm_nodes if it does not exist
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(alex_ltm_nodes)")
            columns = [row["name"] for row in cursor.fetchall()]
            if "recall_count" not in columns:
                conn.execute("ALTER TABLE alex_ltm_nodes ADD COLUMN recall_count INTEGER DEFAULT 1")
                conn.commit()
                print("Database migration: Added recall_count column to alex_ltm_nodes table.")
        except Exception as e:
            print(f"Error running database migration: {e}")

def get_user(user_id: int):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return cursor.fetchone()

def get_all_users() -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username, opponent_name FROM users")
        return [dict(row) for row in cursor.fetchall()]

def register_user(user_id: int, username: str = None, opponent_name: str = None) -> bool:
    if get_user(user_id):
        return False
    if not opponent_name:
        opponent_name = "Руслан"
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO users (user_id, username, opponent_name) VALUES (?, ?, ?)",
            (user_id, username, opponent_name)
        )
        conn.commit()
    return True

def get_opponent_name(user_id: int) -> str:
    user = get_user(user_id)
    if user and user["opponent_name"]:
        return user["opponent_name"]
    return "Руслан"

def set_opponent_name(user_id: int, name: str):
    with get_connection() as conn:
        conn.execute("UPDATE users SET opponent_name = ? WHERE user_id = ?", (name, user_id))
        conn.commit()

def add_message(user_id: int, role: str, content: str) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
            (user_id, role, content)
        )
        conn.commit()
        return cursor.lastrowid

def get_chat_history(user_id: int, limit: int = 15) -> list:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM messages WHERE user_id = ? ORDER BY message_id DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        # return chronological order
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def clear_chat_history(user_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
        conn.commit()

def _get_alex_emotions_row(user_id: int) -> dict:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """SELECT dopamine, serotonin, noradrenaline, acetylcholine, gaba, oxytocin, glutamate, endorphins, fatigue,
                      base_dopamine, base_serotonin, base_noradrenaline, base_acetylcholine, base_gaba, base_oxytocin, base_glutamate, base_endorphins,
                      last_interaction, last_dream, dominant_focus, dominant_strength, expected_return, leave_reason
               FROM alex_emotions WHERE user_id = ?""", 
            (user_id,)
        )
        row = cursor.fetchone()
        if not row:
            cursor.execute(
                """INSERT INTO alex_emotions 
                   (user_id, dopamine, serotonin, noradrenaline, acetylcholine, gaba, oxytocin, glutamate, endorphins, fatigue,
                    base_dopamine, base_serotonin, base_noradrenaline, base_acetylcholine, base_gaba, base_oxytocin, base_glutamate, base_endorphins) 
                   VALUES (?, 0.5, 0.5, 0.4, 0.6, 0.5, 0.4, 0.5, 0.3, 0.0, 0.5, 0.5, 0.3, 0.5, 0.5, 0.3, 0.4, 0.15)""",
                (user_id,)
            )
            conn.commit()
            return {
                "dopamine": 0.5, "serotonin": 0.5, "noradrenaline": 0.4, "acetylcholine": 0.6, "gaba": 0.5, "oxytocin": 0.4, "glutamate": 0.5, "endorphins": 0.3, "fatigue": 0.0,
                "base_dopamine": 0.5, "base_serotonin": 0.5, "base_noradrenaline": 0.3, "base_acetylcholine": 0.5, "base_gaba": 0.5, "base_oxytocin": 0.3, "base_glutamate": 0.4, "base_endorphins": 0.15,
                "last_interaction": None, "last_dream": None, "dominant_focus": None, "dominant_strength": 0.0, "expected_return": None, "leave_reason": None
            }
        return {
            "dopamine": row[0], "serotonin": row[1], "noradrenaline": row[2], "acetylcholine": row[3], "gaba": row[4], "oxytocin": row[5], "glutamate": row[6], "endorphins": row[7], "fatigue": row[8],
            "base_dopamine": row[9], "base_serotonin": row[10], "base_noradrenaline": row[11], "base_acetylcholine": row[12], "base_gaba": row[13], "base_oxytocin": row[14], "base_glutamate": row[15], "base_endorphins": row[16],
            "last_interaction": row[17], "last_dream": row[18],
            "dominant_focus": row[19],
            "dominant_strength": row[20],
            "expected_return": row[21],
            "leave_reason": row[22]
        }

def get_alex_emotions(user_id: int) -> dict:
    if TESTING:
        return _get_alex_emotions_row(user_id)
    
    global_emotions = _get_alex_emotions_row(GLOBAL_ALEX_ID)
    if user_id == GLOBAL_ALEX_ID:
        return global_emotions
    
    relational_emotions = _get_alex_emotions_row(user_id)
    merged = dict(global_emotions)
    merged["oxytocin"] = relational_emotions["oxytocin"]
    merged["noradrenaline"] = relational_emotions["noradrenaline"]
    merged["base_oxytocin"] = relational_emotions["base_oxytocin"]
    merged["base_noradrenaline"] = relational_emotions["base_noradrenaline"]
    merged["last_interaction"] = relational_emotions["last_interaction"]
    return merged

def update_alex_leave_status(user_id: int, expected_return: str, leave_reason: str):
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        conn.execute(
            "UPDATE alex_emotions SET expected_return = ?, leave_reason = ? WHERE user_id = ?",
            (expected_return, leave_reason, user_id)
        )
        conn.commit()

def update_alex_dominant(user_id: int, focus: str, strength: float):
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        conn.execute(
            "UPDATE alex_emotions SET dominant_focus = ?, dominant_strength = ? WHERE user_id = ?",
            (focus, strength, user_id)
        )
        conn.commit()

def set_alex_last_dream(user_id: int, last_dream: str):
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        conn.execute("UPDATE alex_emotions SET last_dream = ? WHERE user_id = ?", (last_dream, user_id))
        conn.commit()

def clear_alex_last_dream(user_id: int):
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        conn.execute("UPDATE alex_emotions SET last_dream = NULL WHERE user_id = ?", (user_id,))
        conn.commit()

NEURO_BASELINES = {
    "dopamine": 0.5,
    "serotonin": 0.5,
    "noradrenaline": 0.3,
    "acetylcholine": 0.5,
    "gaba": 0.5,
    "oxytocin": 0.3,
    "glutamate": 0.4,
    "endorphins": 0.15
}

NEURO_DECAY = {
    "dopamine": 0.10,
    "serotonin": 0.10,
    "noradrenaline": 0.15,
    "acetylcholine": 0.10,
    "gaba": 0.10,
    "oxytocin": 0.08,
    "glutamate": 0.12,
    "endorphins": 0.20
}

def _update_alex_emotions_and_fatigue_raw(
    user_id: int, 
    dopamine_delta: float, 
    serotonin_delta: float, 
    noradrenaline_delta: float, 
    acetylcholine_delta: float, 
    gaba_delta: float,
    oxytocin_delta: float,
    glutamate_delta: float,
    endorphins_delta: float,
    fatigue_delta: float,
    trigger_text: str = ""
):
    current = _get_alex_emotions_row(user_id)
    
    # Calculate dt_minutes elapsed since last_interaction
    last_int_str = current.get("last_interaction")
    dt_minutes = 0.0
    if last_int_str:
        try:
            # SQLite CURRENT_TIMESTAMP is in UTC and format is 'YYYY-MM-DD HH:MM:SS'
            last_dt = datetime.strptime(last_int_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=UTC)
            now = datetime.now(UTC)
            dt_minutes = (now - last_dt).total_seconds() / 60.0
            if dt_minutes < 0:
                dt_minutes = 0.0
        except Exception:
            pass
            
    # Define decay rates per minute (from NEURO_DECAY scaled down, e.g. dopamine_decay = 0.01)
    decay_rates_per_minute = {
        "dopamine": 0.01,
        "serotonin": 0.01,
        "noradrenaline": 0.015,
        "acetylcholine": 0.01,
        "gaba": 0.01,
        "oxytocin": 0.008,
        "glutamate": 0.012,
        "endorphins": 0.02
    }
    
    def decay_value(val, base, lambda_val, dt):
        return base + (val - base) * math.exp(-lambda_val * dt)
        
    decay_da = decay_value(current["dopamine"], current["base_dopamine"], decay_rates_per_minute["dopamine"], dt_minutes)
    decay_5ht = decay_value(current["serotonin"], current["base_serotonin"], decay_rates_per_minute["serotonin"], dt_minutes)
    decay_ne = decay_value(current["noradrenaline"], current["base_noradrenaline"], decay_rates_per_minute["noradrenaline"], dt_minutes)
    decay_ach = decay_value(current["acetylcholine"], current["base_acetylcholine"], decay_rates_per_minute["acetylcholine"], dt_minutes)
    decay_gaba = decay_value(current["gaba"], current["base_gaba"], decay_rates_per_minute["gaba"], dt_minutes)
    decay_oxt = decay_value(current["oxytocin"], current["base_oxytocin"], decay_rates_per_minute["oxytocin"], dt_minutes)
    decay_glu = decay_value(current["glutamate"], current["base_glutamate"], decay_rates_per_minute["glutamate"], dt_minutes)
    decay_end = decay_value(current["endorphins"], current["base_endorphins"], decay_rates_per_minute["endorphins"], dt_minutes)
    
    new_da = max(0.0, min(1.0, decay_da + dopamine_delta))
    new_5ht = max(0.0, min(1.0, decay_5ht + serotonin_delta))
    new_ne = max(0.0, min(1.0, decay_ne + noradrenaline_delta))
    new_ach = max(0.0, min(1.0, decay_ach + acetylcholine_delta))
    new_gaba = max(0.0, min(1.0, decay_gaba + gaba_delta))
    new_oxt = max(0.0, min(1.0, decay_oxt + oxytocin_delta))
    new_glu = max(0.0, min(1.0, decay_glu + glutamate_delta))
    new_end = max(0.0, min(1.0, decay_end + endorphins_delta))
    
    new_fatigue = max(0.0, min(100.0, current["fatigue"] + fatigue_delta))
    
    with get_connection() as conn:
        conn.execute(
            """UPDATE alex_emotions 
               SET dopamine = ?, serotonin = ?, noradrenaline = ?, acetylcholine = ?, gaba = ?, oxytocin = ?, glutamate = ?, endorphins = ?, fatigue = ?, last_interaction = CURRENT_TIMESTAMP 
               WHERE user_id = ?""",
            (new_da, new_5ht, new_ne, new_ach, new_gaba, new_oxt, new_glu, new_end, new_fatigue, user_id)
        )
        conn.execute(
            """INSERT INTO alex_neuro_history 
               (user_id, dopamine, serotonin, noradrenaline, acetylcholine, gaba, oxytocin, glutamate, endorphins, fatigue,
                dopamine_delta, serotonin_delta, noradrenaline_delta, acetylcholine_delta, gaba_delta, oxytocin_delta, glutamate_delta, endorphins_delta, fatigue_delta,
                trigger_text)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, new_da, new_5ht, new_ne, new_ach, new_gaba, new_oxt, new_glu, new_end, new_fatigue,
             dopamine_delta, serotonin_delta, noradrenaline_delta, acetylcholine_delta, gaba_delta, oxytocin_delta, glutamate_delta, endorphins_delta, fatigue_delta,
             trigger_text)
        )
        conn.commit()

def update_alex_emotions_and_fatigue(
    user_id: int, 
    dopamine_delta: float, 
    serotonin_delta: float, 
    noradrenaline_delta: float, 
    acetylcholine_delta: float, 
    gaba_delta: float,
    oxytocin_delta: float,
    glutamate_delta: float,
    endorphins_delta: float,
    fatigue_delta: float,
    trigger_text: str = ""
):
    if TESTING:
        _update_alex_emotions_and_fatigue_raw(
            user_id, dopamine_delta, serotonin_delta, noradrenaline_delta,
            acetylcholine_delta, gaba_delta, oxytocin_delta, glutamate_delta,
            endorphins_delta, fatigue_delta, trigger_text
        )
        return

    if user_id == GLOBAL_ALEX_ID:
        _update_alex_emotions_and_fatigue_raw(
            user_id=GLOBAL_ALEX_ID,
            dopamine_delta=dopamine_delta,
            serotonin_delta=serotonin_delta,
            noradrenaline_delta=noradrenaline_delta,
            acetylcholine_delta=acetylcholine_delta,
            gaba_delta=gaba_delta,
            oxytocin_delta=oxytocin_delta,
            glutamate_delta=glutamate_delta,
            endorphins_delta=endorphins_delta,
            fatigue_delta=fatigue_delta,
            trigger_text=trigger_text
        )
    else:
        _update_alex_emotions_and_fatigue_raw(
            user_id=GLOBAL_ALEX_ID,
            dopamine_delta=dopamine_delta,
            serotonin_delta=serotonin_delta,
            noradrenaline_delta=0.0,
            acetylcholine_delta=acetylcholine_delta,
            gaba_delta=gaba_delta,
            oxytocin_delta=0.0,
            glutamate_delta=glutamate_delta,
            endorphins_delta=endorphins_delta,
            fatigue_delta=fatigue_delta,
            trigger_text=trigger_text
        )
        _update_alex_emotions_and_fatigue_raw(
            user_id=user_id,
            dopamine_delta=0.0,
            serotonin_delta=0.0,
            noradrenaline_delta=noradrenaline_delta,
            acetylcholine_delta=0.0,
            gaba_delta=0.0,
            oxytocin_delta=oxytocin_delta,
            glutamate_delta=0.0,
            endorphins_delta=0.0,
            fatigue_delta=0.0,
            trigger_text=trigger_text
        )

def set_alex_fatigue(user_id: int, value: float):
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    get_alex_emotions(user_id)
    new_val = max(0.0, min(100.0, value))
    with get_connection() as conn:
        conn.execute("UPDATE alex_emotions SET fatigue = ?, last_interaction = CURRENT_TIMESTAMP WHERE user_id = ?", (new_val, user_id))
        conn.commit()

def update_last_interaction(user_id: int):
    # Обновляем timestamp как в глобальном ядре, так и в реляционной записи пользователя
    with get_connection() as conn:
        if not TESTING:
            conn.execute("UPDATE alex_emotions SET last_interaction = CURRENT_TIMESTAMP WHERE user_id = ?", (GLOBAL_ALEX_ID,))
        conn.execute("UPDATE alex_emotions SET last_interaction = CURRENT_TIMESTAMP WHERE user_id = ?", (user_id,))
        conn.commit()

def add_alex_stm(user_id: int, role: str, content: str, emotional_charge: float = 0.0) -> int:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO alex_stm (user_id, role, content, emotional_charge) VALUES (?, ?, ?, ?)",
            (user_id, role, content, emotional_charge)
        )
        conn.commit()
        return cursor.lastrowid

def get_users_with_pending_stm(user_ids: list[int] = None) -> set:
    """Returns a set of user IDs that have at least one pending STM entry. If user_ids is provided, restricts to those IDs."""
    if user_ids is not None and len(user_ids) == 0:
        return set()

    with get_connection() as conn:
        cursor = conn.cursor()
        if user_ids:
            # Chunk the user_ids to avoid SQLite variable limits (max 999 or 32766)
            chunk_size = 900
            result = set()
            for i in range(0, len(user_ids), chunk_size):
                chunk = user_ids[i:i+chunk_size]
                placeholders = ','.join('?' * len(chunk))
                query = f"SELECT DISTINCT user_id FROM alex_stm WHERE user_id IN ({placeholders})"
                cursor.execute(query, chunk)
                result.update({r["user_id"] for r in cursor.fetchall()})
            return result
        else:
            cursor.execute("SELECT DISTINCT user_id FROM alex_stm")
            return {r["user_id"] for r in cursor.fetchall()}

def get_alex_stm(user_id: int, limit: int = 15) -> list:

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT role, content FROM alex_stm WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

def get_all_users_stm(limit: int = 200) -> dict:
    """
    Fetch STMs for all users up to a certain limit per user.
    Returns a dict mapping user_id -> list of STM dicts [{"role": ..., "content": ...}]
    The list is ordered chronologically (oldest first) just like get_alex_stm.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        # Use window function to limit rows per user
        cursor.execute("""
            SELECT user_id, role, content
            FROM (
                SELECT user_id, role, content,
                       ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY id DESC) as rn
                FROM alex_stm
            )
            WHERE rn <= ?
            ORDER BY user_id, rn DESC
        """, (limit,))

        rows = cursor.fetchall()

        result = {}
        for r in rows:
            uid = r["user_id"]
            if uid not in result:
                result[uid] = []
            result[uid].append({"role": r["role"], "content": r["content"]})

        return result

def clear_alex_stm(user_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM alex_stm WHERE user_id = ?", (user_id,))
        conn.commit()

def add_ltm_node(user_id: int, memory_text: str, embedding: str, memory_type: str, strength: float = 1.0, rigidity: float = 0.5, source: str = 'ego', verified: int = 1) -> int:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO alex_ltm_nodes (user_id, memory_text, embedding, memory_type, strength, rigidity, source, verified)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (user_id, memory_text, embedding, memory_type, strength, rigidity, source, verified)
        )
        conn.commit()
        return cursor.lastrowid

def get_ltm_nodes_by_user(user_id: int) -> list[dict]:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, memory_text, embedding, memory_type, strength, rigidity, source, verified, recall_count, created_at FROM alex_ltm_nodes WHERE user_id = ?",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def update_ltm_node_verified(node_id: int, verified: int):
    with get_connection() as conn:
        conn.execute("UPDATE alex_ltm_nodes SET verified = ? WHERE id = ?", (verified, node_id))
        conn.commit()

def update_ltm_node_strength(node_id: int, new_strength: float):
    new_strength = max(0.0, min(1.0, new_strength))
    with get_connection() as conn:
        conn.execute("UPDATE alex_ltm_nodes SET strength = ? WHERE id = ?", (new_strength, node_id))
        conn.commit()

def increment_ltm_node_recall(node_id: int):
    with get_connection() as conn:
        conn.execute("UPDATE alex_ltm_nodes SET recall_count = recall_count + 1 WHERE id = ?", (node_id,))
        conn.commit()

def update_ltm_node_rigidity(node_id: int, new_rigidity: float):
    new_rigidity = max(0.0, min(1.0, new_rigidity))
    with get_connection() as conn:
        conn.execute("UPDATE alex_ltm_nodes SET rigidity = ? WHERE id = ?", (new_rigidity, node_id))
        conn.commit()

def update_ltm_node_text(node_id: int, new_text: str):
    with get_connection() as conn:
        conn.execute("UPDATE alex_ltm_nodes SET memory_text = ? WHERE id = ?", (new_text, node_id))
        conn.commit()

def update_ltm_node_embedding(node_id: int, new_embedding: str):
    with get_connection() as conn:
        conn.execute("UPDATE alex_ltm_nodes SET embedding = ? WHERE id = ?", (new_embedding, node_id))
        conn.commit()

def delete_ltm_node(node_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM alex_ltm_nodes WHERE id = ?", (node_id,))
        conn.commit()

def add_ltm_edge(user_id: int, source_id: int, target_id: int, weight: float = 0.5, association_type: str = 'semantic') -> int:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO alex_ltm_edges (user_id, source_id, target_id, weight, association_type)
               VALUES (?, ?, ?, ?, ?)""",
            (user_id, source_id, target_id, weight, association_type)
        )
        conn.commit()
        return cursor.lastrowid

def get_ltm_edges_by_user(user_id: int) -> list[dict]:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, source_id, target_id, weight, association_type, created_at FROM alex_ltm_edges WHERE user_id = ?",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def update_ltm_edge_weight(edge_id: int, new_weight: float):
    new_weight = max(0.0, min(1.0, new_weight))
    with get_connection() as conn:
        conn.execute("UPDATE alex_ltm_edges SET weight = ? WHERE id = ?", (new_weight, edge_id))
        conn.commit()

def get_associated_edges_for_node(node_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, user_id, source_id, target_id, weight, association_type, created_at FROM alex_ltm_edges WHERE source_id = ? OR target_id = ?",
            (node_id, node_id)
        )
        return [dict(row) for row in cursor.fetchall()]

def delete_ltm_edge(edge_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM alex_ltm_edges WHERE id = ?", (edge_id,))
        conn.commit()

def add_weak_flow_thought(user_id: int, thought: str) -> int:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO alex_weak_flow (user_id, thought) VALUES (?, ?)",
            (user_id, thought)
        )
        conn.commit()
        return cursor.lastrowid

def add_thought_history(user_id: int, thought: str, thought_type: str):
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO alex_thought_history (user_id, thought, thought_type) VALUES (?, ?, ?)",
            (user_id, thought, thought_type)
        )
        conn.commit()

def get_thought_history(user_id: int, limit: int = 10) -> list[dict]:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT thought, thought_type, created_at FROM alex_thought_history WHERE user_id = ? ORDER BY id DESC LIMIT ?",
            (user_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

def get_weak_flow_thoughts(user_id: int, limit: int = 5) -> list[str]:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT thought FROM alex_weak_flow WHERE user_id = ? ORDER BY id ASC LIMIT ?",
            (user_id, limit)
        )
        return [row["thought"] for row in cursor.fetchall()]

def clear_weak_flow_thoughts(user_id: int):
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        conn.execute("DELETE FROM alex_weak_flow WHERE user_id = ?", (user_id,))
        conn.commit()

def add_alex_hypothesis(user_id: int, hypothesis_text: str, confidence: float = 0.5) -> int:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO alex_hypotheses (user_id, hypothesis_text, confidence) VALUES (?, ?, ?)",
            (user_id, hypothesis_text, confidence)
        )
        conn.commit()
        return cursor.lastrowid

def get_alex_hypotheses(user_id: int, status: str = None) -> list[dict]:
    if not TESTING:
        user_id = GLOBAL_ALEX_ID
    with get_connection() as conn:
        cursor = conn.cursor()
        if status:
            cursor.execute(
                "SELECT id, user_id, hypothesis_text, confidence, status, created_at FROM alex_hypotheses WHERE user_id = ? AND status = ?",
                (user_id, status)
            )
        else:
            cursor.execute(
                "SELECT id, user_id, hypothesis_text, confidence, status, created_at FROM alex_hypotheses WHERE user_id = ?",
                (user_id,)
            )
        return [dict(row) for row in cursor.fetchall()]

def update_alex_hypothesis_status(hyp_id: int, status: str, confidence: float):
    with get_connection() as conn:
        conn.execute(
            "UPDATE alex_hypotheses SET status = ?, confidence = ? WHERE id = ?",
            (status, confidence, hyp_id)
        )
        conn.commit()

def delete_alex_hypothesis(hyp_id: int):
    with get_connection() as conn:
        conn.execute("DELETE FROM alex_hypotheses WHERE id = ?", (hyp_id,))
        conn.commit()

def set_active_memory(user_id: int, key: str, val: str, confidence: float = 1.0):
    with get_connection() as conn:
        conn.execute(
            """INSERT INTO alex_active_memory (user_id, key, val, confidence, updated_at)
               VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
               ON CONFLICT(user_id, key) DO UPDATE SET
               val = excluded.val,
               confidence = excluded.confidence,
               updated_at = CURRENT_TIMESTAMP""",
            (user_id, key, val, confidence)
        )
        conn.commit()

def get_active_memory(user_id: int) -> list[dict]:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT key, val, confidence, created_at, updated_at FROM alex_active_memory WHERE user_id = ?",
            (user_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

def delete_active_memory(user_id: int, key: str):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM alex_active_memory WHERE user_id = ? AND key = ?",
            (user_id, key)
        )
        conn.commit()

def clear_active_memory(user_id: int):
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM alex_active_memory WHERE user_id = ?",
            (user_id,)
        )
        conn.commit()

def save_alex_emotions(user_id: int, emotions: dict):
    global_id = user_id if TESTING else GLOBAL_ALEX_ID
    with get_connection() as conn:
        # Обновляем глобальное эмоциональное ядро Алекса
        conn.execute(
            """UPDATE alex_emotions 
               SET dopamine = ?, serotonin = ?, acetylcholine = ?, gaba = ?, glutamate = ?, endorphins = ?, fatigue = ?
               WHERE user_id = ?""",
            (
                emotions.get("dopamine", 0.5),
                emotions.get("serotonin", 0.5),
                emotions.get("acetylcholine", 0.6),
                emotions.get("gaba", 0.5),
                emotions.get("glutamate", 0.5),
                emotions.get("endorphins", 0.3),
                emotions.get("fatigue", 0.0),
                global_id
            )
        )
        # Обновляем индивидуальные реляционные параметры для конкретного юзера
        if not TESTING:
            conn.execute(
                """UPDATE alex_emotions 
                   SET oxytocin = ?, noradrenaline = ?
                   WHERE user_id = ?""",
                (
                    emotions.get("oxytocin", 0.4),
                    emotions.get("noradrenaline", 0.4),
                    user_id
                )
            )
        conn.commit()

def apply_sleep_decay(unverified_vector, rate: float = 0.10):
    import numpy as np
    from core.vsa_memory import vsa_index
    v = np.array(unverified_vector, dtype=np.int8)
    decayed = vsa_index.apply_decay(v, rate)
    return decayed

def get_last_message_time(user_id: int) -> float:
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM messages WHERE user_id = ? ORDER BY message_id DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if row:
            try:
                # SQLite CURRENT_TIMESTAMP is in UTC and format is 'YYYY-MM-DD HH:MM:SS'
                dt = datetime.strptime(row["created_at"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except Exception:
                pass
        # Fallback to last_interaction in emotions
        cursor.execute("SELECT last_interaction FROM alex_emotions WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row and row["last_interaction"]:
            try:
                dt = datetime.strptime(row["last_interaction"].split(".")[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                return dt.timestamp()
            except Exception:
                pass
        return 0.0

if __name__ == "__main__":
    init_db()
    print("Database initialized successfully.")

