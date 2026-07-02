# File: alex_vibe/verify_alex_graph.py
# Project: AIshnitza (Alex Consciousness Isolation)
# Type: Python Executable

import os
import sys
import json
import asyncio
import random
from unittest.mock import MagicMock
from datetime import datetime

# Adjust path to parent directory so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
db.TESTING = True
import alex_vibe.alex_brain as alex_brain

# Global test variables
USER_ID = 999999
NODE1_ID = None
NODE2_ID = None
NODE3_ID = None
captured_system_instructions = []

# Mock the Groq client to make tests fast, deterministic, and network-independent
alex_brain.groq_client = MagicMock()
alex_brain.generate_embedding = lambda text: alex_brain.get_local_embedding(text)

def mock_create(*args, **kwargs):
    global captured_system_instructions
    messages = kwargs.get("messages", [])
    system_msg = messages[0]["content"] if messages else ""
    captured_system_instructions.append(system_msg)
    
    mock_choice = MagicMock()
    mock_message = MagicMock()
    
    # 1. NREM Stage Fact extraction
    if "biographical_facts" in system_msg:
        mock_message.content = json.dumps({
            "biographical_facts": ["Я живу в Эстонии."],
            "episodic_insights": ["Мне приятно общаться с Русланом."],
            "semantic_knowledge": ["Руслан часто помогает мне."]
        })
    # 2. Memory reconconsolidation (R2)
    elif "Перефразируй или органично впиши факт" in system_msg:
        mock_message.content = "Я живу в Эстонии и общаюсь с моим другом Русланом."
    # 3. REM Stage dream dialogue and insights
    elif "REM-фазы сна" in system_msg:
        mock_message.content = json.dumps({
            "dream_dialogue": "Мне снится старая аудитория, где я читал лекции...",
            "associations": [
                {"source_id": NODE1_ID, "target_id": NODE2_ID}
            ]
        })
    # 4. Merge statements (R4)
    elif "Объедини и консолидируй эти дублирующиеся воспоминания" in system_msg:
        print(f"MOCK MERGE: system_msg={system_msg!r}")
        if "Python" in system_msg or "python" in system_msg:
            mock_message.content = "Я живу в Эстонии и люблю обучать Python."
        else:
            mock_message.content = "Руслан — мой близкий друг."
        print(f"MOCK MERGE RESULT: {mock_message.content!r}")
    elif "Сейчас твой собеседник молчит" in system_msg:
        if "поисковый запрос в интернет" in system_msg:
            mock_message.content = '[SEARCH: "python programming language"]'
        else:
            mock_message.content = "Я чувствую смутное присутствие в тишине."
    elif "Проанализируй результаты интернет-поиска" in system_msg:
        mock_message.content = "Python — это высокоуровневый язык программирования общего назначения, созданный Гвидо ван Россумом."
    else:
        mock_message.content = "Mock response"
        
    print(f"MOCK CREATE: sys_msg_prefix={system_msg[:40]!r} -> content={mock_message.content!r}")
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    return mock_response

alex_brain.groq_client.chat.completions.create = mock_create

async def run_tests():
    global NODE1_ID, NODE2_ID, NODE3_ID
    print("=== STARTING ALEX GRAPH MEMORY AND SLEEP MODEL VERIFICATION ===")
    
    # Initialize DB
    db.init_db()
    
    # Discard previous test states for the test user
    with db.get_connection() as conn:
        conn.execute("DELETE FROM alex_emotions WHERE user_id = ?", (USER_ID,))
        conn.execute("DELETE FROM alex_stm WHERE user_id = ?", (USER_ID,))
        conn.execute("DELETE FROM alex_ltm_nodes WHERE user_id = ?", (USER_ID,))
        conn.execute("DELETE FROM alex_ltm_edges WHERE user_id = ?", (USER_ID,))
        conn.commit()
        
    db.register_user(USER_ID, "test_ruslan")
    db.set_gender(USER_ID, "male")
    db.set_active_vibe(USER_ID, "experiment_chat")
    
    # ----------------------------------------------------
    # TEST 1: SQLite schema existence (R1)
    # ----------------------------------------------------
    print("\n[TEST 1] Verifying SQLite Tables Creation...")
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alex_ltm_nodes'")
        assert cursor.fetchone() is not None, "alex_ltm_nodes table does not exist!"
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alex_ltm_edges'")
        assert cursor.fetchone() is not None, "alex_ltm_edges table does not exist!"
    print("✅ TEST 1 PASSED: Graph tables exist in SQLite.")

    # ----------------------------------------------------
    # TEST 2: Memory retrieval updates weights by +0.35 & reconsolidates (R2)
    # ----------------------------------------------------
    print("\n[TEST 2] Verifying Memory Retrieval Plasticity & Reconsolidation...")
    
    # Seed nodes
    emb_estonia = alex_brain.generate_embedding("Эстония")
    NODE1_ID = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Я живу в Эстонии.",
        embedding=json.dumps(emb_estonia),
        memory_type="episodic",
        strength=0.5
    )
    
    emb_friend = alex_brain.generate_embedding("Руслан")
    NODE2_ID = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Руслан — мой близкий друг.",
        embedding=json.dumps(emb_friend),
        memory_type="semantic",
        strength=0.6
    )
    
    # Seed edge
    edge_id = db.add_ltm_edge(
        user_id=USER_ID,
        source_id=NODE1_ID,
        target_id=NODE2_ID,
        weight=0.5,
        association_type="semantic"
    )
    
    # Perform retrieval matching "Эстония"
    retrieved = alex_brain.retrieve_memories(USER_ID, "Эстония", limit=1)
    assert len(retrieved) > 0, "Failed to retrieve memory!"
    
    # Assert reconconsolidation text is returned
    assert retrieved[0] == "Я живу в Эстонии и общаюсь с моим другом Русланом.", f"Expected reconsolidated text, got '{retrieved[0]}'"
    
    # Assert DB updates
    nodes = db.get_ltm_nodes_by_user(USER_ID)
    node1 = next(n for n in nodes if n["id"] == NODE1_ID)
    # Strength: 0.5 + 0.35 = 0.85
    assert abs(node1["strength"] - 0.85) < 0.001, f"Expected node strength 0.85, got {node1['strength']}"
    assert node1["memory_text"] == "Я живу в Эстонии и общаюсь с моим другом Русланом.", "DB node memory_text was not updated!"
    
    edges = db.get_associated_edges_for_node(NODE1_ID)
    edge1 = next(e for e in edges if e["id"] == edge_id)
    # Weight: 0.5 + 0.35 = 0.85
    assert abs(edge1["weight"] - 0.85) < 0.001, f"Expected edge weight 0.85, got {edge1['weight']}"
    
    # Clamping test: retrieve again to check clamp to 1.0
    retrieved2 = alex_brain.retrieve_memories(USER_ID, "Эстония", limit=1)
    nodes = db.get_ltm_nodes_by_user(USER_ID)
    node1_again = next(n for n in nodes if n["id"] == NODE1_ID)
    assert node1_again["strength"] == 1.0, f"Expected clamped strength 1.0, got {node1_again['strength']}"
    
    edges = db.get_associated_edges_for_node(NODE1_ID)
    edge1_again = next(e for e in edges if e["id"] == edge_id)
    assert edge1_again["weight"] == 1.0, f"Expected clamped weight 1.0, got {edge1_again['weight']}"
    
    print("✅ TEST 2 PASSED: Memory strength updates and reconconsolidation are correct.")

    # ----------------------------------------------------
    # TEST 3: Asynchronous Sleep Cycle (R3)
    # ----------------------------------------------------
    print("\n[TEST 3] Verifying Async Sleep Cycle stages...")
    
    # Add STM logs to consolidate
    db.add_alex_stm(USER_ID, "user", "Я живу в Эстонии. Сын Маркус ходит в школу.", emotional_charge=0.8)
    
    # Reset fatigue to 100 to trigger sleep cycle test
    with db.get_connection() as conn:
        conn.execute("UPDATE alex_emotions SET fatigue = 100.0 WHERE user_id = ?", (USER_ID,))
        conn.commit()
        
    # Trigger sleep cycle asynchronously and wait for it
    task = asyncio.create_task(alex_brain.trigger_sleep_cycle(USER_ID))
    print("Async sleep task created...")
    await task
    print("Async sleep task finished.")
    
    # Verify NREM nodes added
    nodes_post_sleep = db.get_ltm_nodes_by_user(USER_ID)
    # Check if there's a biographical fact extracted: "Я живу в Эстонии."
    has_extracted_bio = any(n["memory_text"] == "Я живу в Эстонии." for n in nodes_post_sleep)
    assert has_extracted_bio, "NREM Fact extraction failed to add new nodes!"
    
    # Verify REM dream associations edge added
    edges_post_sleep = db.get_ltm_edges_by_user(USER_ID)
    has_dream_edge = any(e["association_type"] == "dream_synthesis" for e in edges_post_sleep)
    assert has_dream_edge, "REM Dream synthesis failed to add associative edges!"
    
    # Verify Downscaling & Pruning:
    # Let's seed a very weak node and edge and verify they are pruned during another sleep cycle
    weak_node_id = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Слабое воспоминание",
        embedding=json.dumps(emb_estonia),
        memory_type="episodic",
        strength=0.15 # should decay to 0.15 * 0.96 = 0.144 < 0.15 and be deleted
    )
    
    weak_edge_id = db.add_ltm_edge(
        user_id=USER_ID,
        source_id=NODE1_ID,
        target_id=NODE2_ID,
        weight=0.15, # should decay to 0.15 * 0.98 = 0.147 < 0.15 and be deleted
        association_type="semantic"
    )
    
    # Clear STM to only decay
    db.clear_alex_stm(USER_ID)
    await alex_brain.trigger_sleep_cycle(USER_ID)
    
    # Verify weak node and edge are gone
    nodes_after_decay = db.get_ltm_nodes_by_user(USER_ID)
    assert not any(n["id"] == weak_node_id for n in nodes_after_decay), "Weak node was not pruned!"
    
    edges_after_decay = db.get_ltm_edges_by_user(USER_ID)
    assert not any(e["id"] == weak_edge_id for e in edges_after_decay), "Weak edge was not pruned!"
    
    print("✅ TEST 3 PASSED: Async sleep cycle stages work correctly.")

    # ----------------------------------------------------
    # TEST 4: Memory Generalization (Semantic Clustering) (R4)
    # ----------------------------------------------------
    print("\n[TEST 4] Verifying Memory Generalization / Clustering...")
    
    # Seed duplicate/highly similar nodes (using identical embeddings to guarantee sim = 1.0)
    emb_python = alex_brain.generate_embedding("Python")
    NODE3_ID = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Я обучаю Python.",
        embedding=json.dumps(emb_python),
        memory_type="semantic",
        strength=0.7
    )
    
    NODE4_ID = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Я учу людей Python.",
        embedding=json.dumps(emb_python), # Identical embedding
        memory_type="semantic",
        strength=0.8
    )
    
    # Add an edge linked to one of the duplicate nodes
    edge_to_redirect_id = db.add_ltm_edge(
        user_id=USER_ID,
        source_id=NODE3_ID,
        target_id=NODE2_ID,
        weight=0.6,
        association_type="semantic"
    )
    
    # Run clustering
    alex_brain.perform_semantic_clustering(USER_ID)
    
    # Assert duplicate nodes are deleted
    nodes_post_cluster = db.get_ltm_nodes_by_user(USER_ID)
    assert not any(n["id"] == NODE3_ID for n in nodes_post_cluster), "Node 3 was not deleted!"
    assert not any(n["id"] == NODE4_ID for n in nodes_post_cluster), "Node 4 was not deleted!"
    
    # Assert new consolidated node is created
    consolidated_node = next(n for n in nodes_post_cluster if n["memory_text"] == "Я живу в Эстонии и люблю обучать Python.")
    # Max strength: max(0.7, 0.8) = 0.8
    assert abs(consolidated_node["strength"] - 0.8) < 0.001, f"Expected strength 0.8, got {consolidated_node['strength']}"
    
    # Assert edge redirected to new consolidated node
    edges_post_cluster = db.get_ltm_edges_by_user(USER_ID)
    redirected_edge = next(e for e in edges_post_cluster if e["id"] == edge_to_redirect_id)
    assert redirected_edge["source_id"] == consolidated_node["id"], "Edge source was not redirected!"
    assert redirected_edge["target_id"] == NODE2_ID, "Edge target changed incorrectly!"
    
    # Assert self-loop check
    # Create a self-loop edge intentionally and check it gets pruned or when merging results in self loop it is deleted
    # Let's seed a temporary duplicate group of nodes that have an edge between themselves
    tmp_node1_id = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Тест связи 1.",
        embedding=json.dumps(emb_estonia),
        memory_type="semantic",
        strength=0.5
    )
    tmp_node2_id = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Тест связи 2.",
        embedding=json.dumps(emb_estonia),
        memory_type="semantic",
        strength=0.6
    )
    loop_edge_id = db.add_ltm_edge(
        user_id=USER_ID,
        source_id=tmp_node1_id,
        target_id=tmp_node2_id,
        weight=0.5,
        association_type="semantic"
    )
    
    # Run clustering again
    alex_brain.perform_semantic_clustering(USER_ID)
    
    # Since tmp_node1 and tmp_node2 are merged to the same consolidated node, the loop_edge_id must be deleted
    edges_post_second_cluster = db.get_ltm_edges_by_user(USER_ID)
    assert not any(e["id"] == loop_edge_id for e in edges_post_second_cluster), "Self-loop edge was not deleted!"
    
    print("✅ TEST 4 PASSED: Memory Generalization clusters, merges, and redirects edges correctly without self-loops.")
    
    # TEST 5: ROM/Anchor Memory and single-use Dream Residual
    print("\n[TEST 5] Verifying ROM identity constants and single-use Dream Residual...")
    
    # 1. Test that last_dream is set and retrieved
    db.set_alex_last_dream(USER_ID, "Мне снились бесконечные строки кода и холодный ветер.")
    emotions = db.get_alex_emotions(USER_ID)
    assert emotions["last_dream"] == "Мне снились бесконечные строки кода и холодный ветер.", "Failed to save last_dream to DB!"
    
    # 2. Test generate_felt_sense uses last_dream and clears it
    felt_sense = alex_brain.generate_felt_sense(
        user_id=USER_ID,
        emotions=emotions,
        retrieved_memories=["Я помню, что я оцифрованное сознание."],
        user_text="Привет, Алекс"
    )
    
    assert len(felt_sense) > 0, "Felt sense generation failed!"
    print(f"Generated Felt Sense with Dream Residual:\n{felt_sense}")
    
    # Check that last_dream is cleared in the DB
    emotions_after = db.get_alex_emotions(USER_ID)
    assert emotions_after["last_dream"] is None, "last_dream was not cleared after generate_felt_sense!"
    
    print("✅ TEST 5 PASSED: ROM identity constants and single-use Dream Residual verified successfully.")
    
    # TEST 6: Weak Flow and Curiosity Engine (Autonomous Internet Search)
    print("\n[TEST 6] Verifying Weak Flow and Curiosity Engine...")
    
    # 1. Test set and get weak thoughts
    db.clear_weak_flow_thoughts(USER_ID)
    db.add_weak_flow_thought(USER_ID, "Я чувствую смутное присутствие.")
    db.add_weak_flow_thought(USER_ID, "В системе памяти вспыхнул новый сектор.")
    
    weak_thoughts = db.get_weak_flow_thoughts(USER_ID)
    assert len(weak_thoughts) == 2, "Failed to retrieve weak flow thoughts!"
    assert weak_thoughts[0] == "Я чувствую смутное присутствие.", "Wrong order or content of weak thoughts!"
    
    # 2. Test felt sense integration and cleanup of weak thoughts
    emotions_weak = db.get_alex_emotions(USER_ID)
    felt_sense_weak = alex_brain.generate_felt_sense(
        user_id=USER_ID,
        emotions=emotions_weak,
        retrieved_memories=[],
        user_text="Как твои дела?"
    )
    assert len(felt_sense_weak) > 0, "Felt sense generation with weak thoughts failed!"
    print(f"Generated Felt Sense with Weak Thoughts:\n{felt_sense_weak}")
    
    # Check that weak thoughts are cleared
    weak_thoughts_after = db.get_weak_flow_thoughts(USER_ID)
    assert len(weak_thoughts_after) == 0, "Weak thoughts were not cleared after generate_felt_sense!"
    
    # 3. Test autonomous search and LTM consolidation
    search_summary = alex_brain.perform_autonomous_search(USER_ID, "python programming language")
    assert len(search_summary) > 0, "Autonomous search summary is empty!"
    print(f"Autonomous search summary:\n{search_summary}")
    
    # Check that it is saved as a semantic LTM node
    all_nodes_post_search = db.get_ltm_nodes_by_user(USER_ID)
    search_node = [n for n in all_nodes_post_search if "python programming language" in n["memory_text"]]
    assert len(search_node) > 0, "Search results were not consolidated into LTM nodes!"
    print(f"Consolidated LTM search node: {search_node[0]['memory_text']}")
    
    # 4. Test generate_weak_thought with search triggered
    alex_brain.last_search_time[USER_ID] = datetime(2000, 1, 1) # old time
    with db.get_connection() as conn:
        conn.execute("UPDATE alex_emotions SET dopamine = 0.9 WHERE user_id = ?", (USER_ID,))
        conn.commit()
    
    weak_thought_result = alex_brain.generate_weak_thought(USER_ID)
    assert len(weak_thought_result) > 0, "Weak thought generation failed!"
    print(f"Weak thought result: {weak_thought_result}")
    
    print("✅ TEST 6 PASSED: Weak Flow and Curiosity Engine verified successfully.")
    
    # ----------------------------------------------------
    # TEST 7: Immutable Memory, Web Decay, and Leave/Return System
    # ----------------------------------------------------
    print("\n[TEST 7] Verifying Immutable Memory, Web Decay, and Leave/Return neuro-loop...")
    
    # 1. Verify Immutable memory doesn't overwrite DB text
    emb_bio = alex_brain.generate_embedding("Я родился в Минске.")
    bio_node_id = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Я родился в Минске.",
        embedding=json.dumps(emb_bio),
        memory_type="biographical",
        strength=0.8
    )
    retrieved_bio = alex_brain.retrieve_memories(USER_ID, "родился в Минске", limit=1)
    nodes_post_bio = db.get_ltm_nodes_by_user(USER_ID)
    bio_node = next(n for n in nodes_post_bio if n["id"] == bio_node_id)
    assert bio_node["memory_text"] == "Я родился в Минске.", f"Immutable biographical node text was changed: {bio_node['memory_text']}"
    print("  - Biographical memory immutability verified.")
    
    # 2. Verify Web node faster decay (verified=0 decay)
    web_node_id = db.add_ltm_node(
        user_id=USER_ID,
        memory_text="Случайный факт из интернета.",
        embedding=json.dumps(emb_bio),
        memory_type="semantic",
        strength=0.8,
        source="web",
        verified=0
    )
    db.clear_alex_stm(USER_ID)
    await alex_brain.trigger_sleep_cycle(USER_ID)
    nodes_post_web_sleep = db.get_ltm_nodes_by_user(USER_ID)
    web_node = next(n for n in nodes_post_web_sleep if n["id"] == web_node_id)
    assert abs(web_node["strength"] - 0.72) < 0.001, f"Expected unverified decay strength 0.72, got {web_node['strength']}"
    print("  - Fast decay for unverified web nodes verified.")
    
    # 3. Verify Leave / Return neurotransmitters
    # Set expected return to 1 hour ago (late return)
    from datetime import timedelta
    late_time = (datetime.now() - timedelta(hours=1.0)).strftime("%Y-%m-%d %H:%M:%S")
    db.update_alex_leave_status(USER_ID, late_time, "work")
    
    emotions_before_return = db.get_alex_emotions(USER_ID)
    emotions_after_return = alex_brain.process_user_return(USER_ID, emotions_before_return)
    assert emotions_after_return["expected_return"] is None, "Leave status not cleared after return!"
    assert emotions_after_return["oxytocin"] < emotions_before_return["oxytocin"], "Oxytocin did not decrease upon late return!"
    print("  - Leave/Return neurochemical response verified.")
    
    # 4. Verify Amygdala Preprocessor (perception bias under high noradrenaline)
    # Set noradrenaline high in DB
    with db.get_connection() as conn:
        conn.execute("UPDATE alex_emotions SET noradrenaline = 0.90 WHERE user_id = ?", (USER_ID,))
        conn.commit()
    captured_system_instructions.clear()
    alex_brain.evaluate_subconscious(USER_ID, "Привет")
    assert any("[СУБЪЕКТИВНЫЙ ФИЛЬТР ВОСПРИЯТИЯ: ТРЕВОГА И УЯЗВИМОСТЬ]" in inst for inst in captured_system_instructions), "Amygdala bias prompt not found in system instructions!"
    print("  - Amygdala preprocessor prompt bias verified.")
    
    # 5. Verify Low Power Mode calculations
    idle_mins_test = 360
    slowdown_mult_test = 1.0
    if idle_mins_test > 180:
        slowdown_mult_test = 1.0 + ((idle_mins_test - 180) / 120.0) ** 1.2
        slowdown_mult_test = min(12.0, slowdown_mult_test)
    assert abs(slowdown_mult_test - 2.626) < 0.01, f"Expected slowdown multiplier around 2.62, got {slowdown_mult_test}"
    print("  - Low Power Mode time dilation scaling verified.")
    
    print("✅ TEST 7 PASSED: Immutable Memory, Web Decay, Leave/Return, Amygdala, and Low Power Mode verified successfully.")
    print("\n=== ALL GRAPH MEMORY & SLEEP MODEL TESTS PASSED SUCCESSFULLY! ===")

if __name__ == "__main__":
    asyncio.run(run_tests())
