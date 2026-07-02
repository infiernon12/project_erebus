# File: core/chemistry.py
# Project: AIshnitza
# Type: Python Module

import logging

logger = logging.getLogger("AIshnitza.Chemistry")

def calculate_sampler_params(emotions: dict) -> dict:
    """
    Translates Alex's 8-neurotransmitter chemical state into sampler parameters.
    
    Formula mappings:
    - Temperature: temp_base + 0.6 * Dopamine - 0.2 * GABA. Clamped to [0.2, 1.6].
    - Top-P: topp_base * (1.0 - 0.6 * Noradrenaline). Clamped to [0.3, 0.95].
    - Repetition Penalty: 1.1 + 0.3 * (0.5 - |Serotonin - 0.5|). Clamped to [1.0, 1.5].
    """
    da = float(emotions.get("dopamine", 0.5))
    gaba = float(emotions.get("gaba", 0.5))
    ne = float(emotions.get("noradrenaline", 0.3))
    ser = float(emotions.get("serotonin", 0.5))
    
    # 1. Temperature: Dopamine drives exploration/entropy; GABA dampens it.
    temp = 0.7 + 0.6 * da - 0.2 * gaba
    temp = max(0.2, min(1.6, temp))
    
    # 2. Top-P: Noradrenaline drives panic and focus narrowing.
    top_p = 0.95 * (1.0 - 0.6 * ne)
    top_p = max(0.3, min(0.95, top_p))
    
    # 3. Repetition Penalty: Serotonin extremes (0.0 or 1.0) reduce penalty, allowing looping/rumination.
    rep_pen = 1.1 + 0.3 * (0.5 - abs(ser - 0.5))
    rep_pen = max(1.0, min(1.5, rep_pen))
    
    logger.debug(
        f"Neurochemistry to Sampler mapping: "
        f"DA={da:.2f}, GABA={gaba:.2f}, NE={ne:.2f}, 5HT={ser:.2f} -> "
        f"Temp={temp:.2f}, Top-P={top_p:.2f}, RepPen={rep_pen:.2f}"
    )
    
    return {
        "temperature": temp,
        "top_p": top_p,
        "repeat_penalty": rep_pen
    }
