import os
import logging
import numpy as np

logger = logging.getLogger(__name__)

class LimbicSSMCore:
    def __init__(self, model_path: str = None, strategy: str = "cpu fp32"):
        self.model_path = model_path or os.path.join("models", "RWKV-x060-World-1B6-v2.1-20240328-ctx4096.pth")
        self.strategy = strategy
        self.model = None
        self.pipeline = None
        self.state = None
        
        # Check if model exists
        if os.path.exists(self.model_path):
            try:
                # RWKV settings for JIT and CPU execution
                os.environ["RWKV_JIT_ON"] = "1"
                os.environ["RWKV_CUDA_ON"] = "0"
                
                from rwkv.model import RWKV
                from rwkv.utils import PIPELINE
                
                logger.info(f"Loading RWKV model from {self.model_path} with strategy {self.strategy}...")
                self.model = RWKV(model=self.model_path, strategy=self.strategy)
                
                # Check for vocabulary file in the same directory, fallback to default
                vocab_path = os.path.join(os.path.dirname(self.model_path), "rwkv_vocab_v20230424.txt")
                if not os.path.exists(vocab_path):
                    vocab_path = "rwkv_vocab_v20230424"
                
                self.pipeline = PIPELINE(self.model, vocab_path)
                self.state = None
                logger.info("RWKV model loaded successfully.")
            except Exception as e:
                logger.error(f"Failed to load RWKV model: {e}")
                self.model = None
        else:
            logger.warning(f"RWKV model file not found at {self.model_path}. Core running in simulation mode.")

    def is_available(self) -> bool:
        return self.model is not None

    def init_state(self):
        self.state = None
        return self.state

    def save_state(self, filepath: str):
        if self.state is not None:
            try:
                import torch
                # Ensure directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                torch.save(self.state, filepath)
                logger.info(f"Saved SSM state to {filepath}")
            except Exception as e:
                logger.error(f"Failed to save SSM state: {e}")

    def load_state(self, filepath: str):
        if os.path.exists(filepath):
            try:
                import torch
                self.state = torch.load(filepath)
                logger.info(f"Loaded SSM state from {filepath}")
            except Exception as e:
                logger.error(f"Failed to load SSM state from {filepath}: {e}")
                self.init_state()
        else:
            logger.warning(f"SSM state file {filepath} not found. Initializing new state.")
            self.init_state()

    def generate(self, prompt: str, max_tokens: int = 150, temperature: float = 0.7, top_p: float = 0.85, repeat_penalty: float = 1.1) -> str:
        if not self.is_available():
            logger.warning("SSM model not available, returning simulated response.")
            return f"[Simulated SSM Response for prompt: '{prompt[:40]}...']"
        
        from rwkv.utils import PIPELINE_ARGS
        
        alpha = max(0.0, 0.2 * (repeat_penalty - 1.0))
        args = PIPELINE_ARGS(
            temperature=temperature,
            top_p=top_p,
            alpha_frequency=alpha,
            alpha_presence=alpha,
            token_ban=[],
            token_stop=[0]  # End of text token
        )
        
        try:
            ctx = prompt
            tokens = self.pipeline.encode(ctx)
            
            all_tokens = []
            out_last = 0
            out_str = ''
            occurrence = {}
            
            state = self.state
            
            for i in range(max_tokens):
                t_input = tokens if i == 0 else [token]
                while len(t_input) > 0:
                    out, state = self.model.forward(t_input[:args.chunk_len], state)
                    t_input = t_input[args.chunk_len:]
                    
                for n in args.token_ban:
                    out[n] = -float('inf')
                for n in occurrence:
                    out[n] -= (args.alpha_presence + occurrence[n] * args.alpha_frequency)
                
                token = self.pipeline.sample_logits(out, temperature=args.temperature, top_p=args.top_p, top_k=args.top_k)
                if token in args.token_stop:
                    break
                all_tokens += [token]
                for xxx in occurrence:
                    occurrence[xxx] *= args.alpha_decay
                
                ttt = self.pipeline.decode([token])
                www = 1
                if ttt in ' \t0123456789':
                    www = 0
                if token not in occurrence:
                    occurrence[token] = www
                else:
                    occurrence[token] += www
                
                tmp = self.pipeline.decode(all_tokens[out_last:])
                if '\ufffd' not in tmp:
                    out_str += tmp
                    out_last = i + 1
            
            self.state = state
            return out_str
        except Exception as e:
            logger.error(f"Error during RWKV generation: {e}")
            raise e
