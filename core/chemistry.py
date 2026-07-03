# File: core/chemistry.py
# Project: AIshnitza
# Type: Python Module

import logging

logger = logging.getLogger("AIshnitza.Chemistry")

def calculate_sampler_params(emotions: dict) -> dict:
    """
    Translates Alex's 8-neurotransmitter chemical state into sampler parameters
    by delegating to prompts_experiment_chat.get_sampler_settings.
    """
    from alisa_vibe.prompts_experiment_chat import get_sampler_settings
    params = get_sampler_settings(emotions)
    
    # Ensure both keys are present for compatibility
    if "repetition_penalty" in params and "repeat_penalty" not in params:
        params["repeat_penalty"] = params["repetition_penalty"]
    elif "repeat_penalty" in params and "repetition_penalty" not in params:
        params["repetition_penalty"] = params["repeat_penalty"]
        
    logger.debug(
        f"Dynamic neurochemistry parameters calculated: {params}"
    )
    return params

