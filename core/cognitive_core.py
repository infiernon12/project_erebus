import os
import gc
import logging

logger = logging.getLogger(__name__)

class CognitiveTransformerCore:
    def __init__(self, model_path: str = None, n_ctx: int = 4096):
        # Default model is Qwen-2.5-Coder 1.5B GGUF
        self.model_path = model_path or os.path.join("models", "Qwen2.5-Coder-1.5B-Instruct-GGUF.gguf")
        self.n_ctx = n_ctx
        self._model = None

    def load_model(self) -> bool:
        if self._model is not None:
            return True
            
        if os.path.exists(self.model_path):
            from llama_cpp import Llama
            logger.info(f"Dynamically loading cognitive model from {self.model_path}...")
            try:
                # 1. Try to load with GPU acceleration
                self._model = Llama(
                    model_path=self.model_path,
                    n_ctx=self.n_ctx,
                    n_threads=4,
                    n_gpu_layers=-1,
                    verbose=False
                )
                logger.info("Cognitive model loaded successfully with GPU offload.")
                return True
            except Exception as gpu_err:
                logger.warning(f"Failed to load model on GPU: {gpu_err}. Falling back to CPU.")
                try:
                    # 2. Fall back to pure CPU
                    self._model = Llama(
                        model_path=self.model_path,
                        n_ctx=self.n_ctx,
                        n_threads=4,
                        n_gpu_layers=0,
                        verbose=False
                    )
                    logger.info("Cognitive model loaded successfully on CPU.")
                    return True
                except Exception as cpu_err:
                    logger.error(f"Failed to load cognitive model even on CPU: {cpu_err}")
                    self._model = None
                    return False
        else:
            logger.warning(f"Cognitive model file not found at {self.model_path}. Running in simulation mode.")
            return False

    def unload_model(self):
        if self._model is not None:
            logger.info("Unloading cognitive model to free up RAM...")
            self._model = None
            # Force Python garbage collector to release memory
            gc.collect()
            logger.info("Cognitive model unloaded.")

    def is_available(self) -> bool:
        return os.path.exists(self.model_path)

    def generate(self, messages: list, max_tokens: int = 512, temperature: float = 0.5, top_p: float = 0.9, repeat_penalty: float = 1.1) -> str:
        # Mock behavior for testing if model file does not exist
        if not self.is_available():
            logger.warning("Cognitive model weights are missing. Running in simulation mode.")
            user_msg = messages[-1]["content"] if messages else ""
            return (
                f"# Simulated Qwen-Coder Output\n"
                f"# Request context: {user_msg[:60]}\n"
                f"def run_task():\n"
                f"    print('Simulated successful execution of task.')\n"
                f"    return True\n"
                f"run_task()"
            )

        if not self.load_model():
            raise RuntimeError("Cognitive model could not be loaded")

        try:
            logger.info("Running inference on cognitive core...")
            response = self._model.create_chat_completion(
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                repeat_penalty=repeat_penalty,
                cache_prompt=True
            )
            result = response["choices"][0]["message"]["content"]
            return result
        except Exception as e:
            logger.error(f"Error during cognitive generation: {e}")
            raise e
