# File: core/vsa_memory.py
# Project: AIshnitza
# Type: Python Module

import os
import logging
import numpy as np

logger = logging.getLogger("AIshnitza.VSA")

class VSAMemoryIndex:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VSAMemoryIndex, cls).__new__(cls, *args, **kwargs)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, dense_dim=384, hyper_dim=10000, seed=42):
        if self._initialized:
            return
        
        self.dense_dim = dense_dim
        self.hyper_dim = hyper_dim
        self.seed = seed
        self.model = None  # Lazy loading SentenceTransformer
        
        # Initialize fixed projection matrix W using constant seed
        rng = np.random.default_rng(self.seed)
        self.W = rng.choice([-1, 1], size=(self.dense_dim, self.hyper_dim))
        
        self._initialized = True
        logger.info(f"VSA Memory Index initialized (dimensions: {self.dense_dim} -> {self.hyper_dim}, seed={self.seed})")

    def _load_model(self):
        if self.model is None:
            logger.info("Loading SentenceTransformer model 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'...")
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(
                'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2',
                local_files_only=True
            )
            logger.info("SentenceTransformer model loaded successfully.")
        return self.model

    def encode(self, text: str) -> np.ndarray:
        """
        Projects text into 10,000-dimensional bipolar VSA vector.
        """
        if not text.strip():
            return np.zeros(self.hyper_dim, dtype=np.int8)

        # 1. Get 384-dimensional dense embedding
        model = self._load_model()
        dense_vector = model.encode(text, convert_to_numpy=True)

        # 2. Random projection
        v_high = np.dot(dense_vector, self.W)

        # 3. Binarize to bipolar vector {-1, 1}
        v_bip = np.sign(v_high)
        # Handle zeros (sign function returns 0 for exactly 0, replace with 1)
        v_bip[v_bip == 0] = 1
        
        return v_bip.astype(np.int8)

    def apply_decay(self, v_bip: np.ndarray, rate: float = 0.10) -> np.ndarray:
        """
        Applies organic sleep decay (bit-flipping noise).
        Flips rate% of values randomly in-place.
        """
        mask = np.random.choice([1, -1], size=self.hyper_dim, p=[1 - rate, rate])
        decayed = v_bip * mask
        return decayed.astype(np.int8)

    def similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        """
        Computes cosine similarity between two bipolar vectors.
        """
        return float(np.dot(v1.astype(np.int32), v2.astype(np.int32))) / self.hyper_dim

# Global instance
vsa_index = VSAMemoryIndex()
