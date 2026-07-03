import os
import logging
from core.ssm_core import LimbicSSMCore
from core.cognitive_core import CognitiveTransformerCore

logger = logging.getLogger(__name__)

# Global instances of local cores
limbic_core = LimbicSSMCore()
cognitive_core = CognitiveTransformerCore()

class LocalCompletionChoiceMessage:
    def __init__(self, content: str):
        self.content = content

class LocalCompletionChoice:
    def __init__(self, content: str):
        self.message = LocalCompletionChoiceMessage(content)

class LocalCompletionResponse:
    def __init__(self, content: str):
        self.choices = [LocalCompletionChoice(content)]

def execute_local_completion(messages: list, model: str, temperature: float = 0.8, max_tokens: int = None, user_id: int = None) -> LocalCompletionResponse:
    """
    Middleware routing chat completions to the correct local core:
    - SSM (RWKV) for monologue, dialogue, raw thoughts, and emotional/felt sense prompts.
    - Cognitive Core (Qwen-Coder) for structured tasks, JSON extractions, text editing, and code generation.
    """
    # 1. Resolve sampler parameters based on user_id neurochemistry
    emotions = None
    if user_id is not None:
        try:
            import database as db
            emotions = db.get_alex_emotions(user_id)
        except Exception as e:
            logger.error(f"Error fetching emotions for user {user_id}: {e}")

    if emotions:
        from core.chemistry import calculate_sampler_params
        sampler_params = calculate_sampler_params(emotions)
        temp = sampler_params["temperature"]
        topp = sampler_params["top_p"]
        rep_pen = sampler_params["repeat_penalty"]
        logger.info(
            f"Using neurochemically dynamic parameters: temp={temp:.2f}, top_p={topp:.2f}, rep_pen={rep_pen:.2f} "
            f"for user {user_id}"
        )
    else:
        temp = temperature
        topp = 0.95
        rep_pen = 1.1

    # 2. Extract system and user prompt contents to decide routing
    system_prompt = ""
    user_prompt = ""
    for msg in messages:
        if msg.get("role") == "system":
            system_prompt += msg.get("content", "") + "\n"
        elif msg.get("role") == "user":
            user_prompt += msg.get("content", "") + "\n"

    all_text = (system_prompt + "\n" + user_prompt).lower()
    
    # 3. Decision Logic for routing:
    # We route structured JSON extractions and coding-related prompts to the Cognitive Transformer Core (Qwen-Coder).
    # Dialogue, raw thoughts, felt sense, and identity prompts are routed to the Limbic SSM Core (RWKV).
    use_cognitive = False
    
    if model in ("llama-3.1-8b-instant", "qwen-coder", "meta-llama/llama-4-scout-17b-16e-instruct"):
        use_cognitive = True
    elif "json" in all_text or "формат ответа строго в json" in all_text:
        use_cognitive = True
    elif "write" in all_text or "run" in all_text or "код" in all_text or "python" in all_text:
        # If it's a coding workspace instruction, use Qwen-Coder
        use_cognitive = True
    elif "редактор текстов" in all_text or "correct_response" in all_text:
        # Text editing / correction task
        use_cognitive = True
        
    # 4. Executing generation
    if use_cognitive:
        logger.info("Routing completion to Cognitive Core (Qwen-Coder)...")
        response_text = cognitive_core.generate(
            messages=messages,
            max_tokens=max_tokens or 512,
            temperature=temp,
            top_p=topp,
            repeat_penalty=rep_pen
        )
    else:
        logger.info("Routing completion to Limbic SSM Core (RWKV)...")
        # Format messages list into a plain text prompt for RWKV
        prompt = ""
        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Alex: {content}\n\n"
        prompt += "Alex:"  # Prompt assistant response
        
        response_text = limbic_core.generate(
            prompt=prompt,
            max_tokens=max_tokens or 250,
            temperature=temp,
            top_p=topp,
            repeat_penalty=rep_pen
        )
        
    return LocalCompletionResponse(response_text)
