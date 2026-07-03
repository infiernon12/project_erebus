# File: scratch/test_incremental_trust.py
# Project: EREBUS
# Type: Python Script

import sys
import os
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from datetime import datetime, timedelta, timezone

# Add parent directory to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database as db
from alisa_vibe.alisa_brain import process_user_return

def run_test():
    user_id = 571505504
    
    # 1. Initialize DB and reset emotions
    db.init_db()
    
    # Force reset emotions to standard baselines
    db.update_alisa_emotions_and_fatigue(
        user_id,
        dopamine_delta=0.5 - db.get_alisa_emotions(user_id).get("dopamine", 0.5),
        serotonin_delta=0.5 - db.get_alisa_emotions(user_id).get("serotonin", 0.5),
        noradrenaline_delta=0.4 - db.get_alisa_emotions(user_id).get("noradrenaline", 0.4),
        acetylcholine_delta=0.6 - db.get_alisa_emotions(user_id).get("acetylcholine", 0.6),
        gaba_delta=0.5 - db.get_alisa_emotions(user_id).get("gaba", 0.5),
        oxytocin_delta=0.4 - db.get_alisa_emotions(user_id).get("oxytocin", 0.4),
        glutamate_delta=0.5 - db.get_alisa_emotions(user_id).get("glutamate", 0.5),
        endorphins_delta=0.3 - db.get_alisa_emotions(user_id).get("endorphins", 0.3),
        fatigue_delta=-db.get_alisa_emotions(user_id).get("fatigue", 0.0),
        trigger_text="Reset for trust test"
    )
    
    # Clean old hypotheses
    with db.get_connection() as conn:
        conn.execute("DELETE FROM alisa_hypotheses WHERE user_id = ?", (user_id,))
        conn.commit()

    print("=== STARTING INCREMENTAL TRUST TEST ===")
    emotions = db.get_alisa_emotions(user_id)
    print(f"Initial Oxytocin: {emotions['oxytocin']:.3f}")
    print(f"Initial Serotonin: {emotions['serotonin']:.3f}\n")

    # Perform 4 consecutive on-time returns
    for i in range(1, 5):
        # Set expected return to current UTC time (0 delay)
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
        db.update_alisa_leave_status(user_id, now_str, "test")
        
        # Load current emotions (which includes expected_return)
        emotions = db.get_alisa_emotions(user_id)
        
        # Process user return
        updated = process_user_return(user_id, emotions)
        
        # Retrieve time hypothesis confidence
        hyps = db.get_alisa_hypotheses(user_id, status=None)
        hyp_str = "None"
        for h in hyps:
            if "вернулся" in h["hypothesis_text"].lower() or "возвращ" in h["hypothesis_text"].lower():
                hyp_str = f"'{h['hypothesis_text']}' (status={h['status']}, conf={h['confidence']:.2f})"
        
        print(f"Cycle {i} (On-time return):")
        print(f"  -> Oxytocin: {updated.get('oxytocin', 0.0):.3f}")
        print(f"  -> Serotonin: {updated.get('serotonin', 0.0):.3f}")
        print(f"  -> Active Hypothesis: {hyp_str}\n")

    # Now simulate a late arrival (e.g. 40 minutes late)
    print("=== SIMULATING LATE ARRIVAL ===")
    expected_late = datetime.now(timezone.utc) - timedelta(minutes=40)
    db.update_alisa_leave_status(user_id, expected_late.strftime("%Y-%m-%d %H:%M:%S"), "test")
    
    emotions = db.get_alisa_emotions(user_id)
    updated = process_user_return(user_id, emotions)
    
    hyps = db.get_alisa_hypotheses(user_id, status=None)
    hyp_str = "None"
    for h in hyps:
        if "вернулся" in h["hypothesis_text"].lower() or "возвращ" in h["hypothesis_text"].lower():
            hyp_str = f"'{h['hypothesis_text']}' (status={h['status']}, conf={h['confidence']:.2f})"
            
    print("Cycle 5 (40 minutes late return):")
    print(f"  -> Oxytocin: {updated.get('oxytocin', 0.0):.3f}")
    print(f"  -> Serotonin: {updated.get('serotonin', 0.0):.3f}")
    print(f"  -> Active Hypothesis: {hyp_str}\n")

if __name__ == "__main__":
    run_test()
