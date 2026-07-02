# File: core/test_vsa.py
# Project: AIshnitza
# Type: Python Script

import unittest
import numpy as np
from core.vsa_memory import vsa_index

class TestVSAMemory(unittest.TestCase):
    def test_encode_dimensions_and_values(self):
        text = "Тестовое воспоминание Алекса для верификации VSA."
        vector = vsa_index.encode(text)
        
        self.assertEqual(vector.shape[0], 10000)
        self.assertTrue(np.all(np.isin(vector, [-1, 1])))

    def test_encode_deterministic(self):
        text = "Один и тот же текст должен кодироваться одинаково."
        v1 = vsa_index.encode(text)
        v2 = vsa_index.encode(text)
        
        self.assertTrue(np.array_equal(v1, v2))

    def test_similarity(self):
        text1 = "Привет, Руслан!"
        text2 = "Привет, Руслан!"
        text3 = "Совершенно другая мысль, не связанная с приветствием."
        
        v1 = vsa_index.encode(text1)
        v2 = vsa_index.encode(text2)
        v3 = vsa_index.encode(text3)
        
        sim12 = vsa_index.similarity(v1, v2)
        sim13 = vsa_index.similarity(v1, v3)
        
        self.assertAlmostEqual(sim12, 1.0)
        self.assertTrue(sim13 < 0.8)  # Different vectors should have significantly lower similarity than 1.0
        self.assertTrue(sim12 > sim13) # Exact match similarity must be greater than non-match

    def test_decay(self):
        text = "Воспоминание о сегодняшнем дне."
        vector = vsa_index.encode(text)
        
        decayed = vsa_index.apply_decay(vector, rate=0.10)  # Flip 10% bits
        
        sim = vsa_index.similarity(vector, decayed)
        
        # Expected similarity after 10% flip: 1.0 - 2 * 0.10 = 0.80 (with small variance)
        self.assertTrue(0.75 <= sim <= 0.85)

if __name__ == "__main__":
    unittest.main()
