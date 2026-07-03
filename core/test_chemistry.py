# File: core/test_chemistry.py
# Project: AIshnitza
# Type: Python Script

import unittest
from core.chemistry import calculate_sampler_params

class TestChemistrySampler(unittest.TestCase):
    def test_balanced_state(self):
        emotions = {
            "dopamine": 0.5,
            "gaba": 0.5,
            "noradrenaline": 0.3,
            "serotonin": 0.5
        }
        params = calculate_sampler_params(emotions)
        
        # Temp = 0.7 + 0.6 * 0.5 - 0.2 * 0.5 = 0.7 + 0.3 - 0.1 = 0.9
        self.assertAlmostEqual(params["temperature"], 0.9)
        
        # Top-P = 0.95 * (1.0 - 0.6 * 0.3) = 0.95 * 0.82 = 0.779
        self.assertAlmostEqual(params["top_p"], 0.779)
        
        # RepPen = 1.1 + 0.3 * abs(0.5 - 0.5) = 1.1
        self.assertAlmostEqual(params["repeat_penalty"], 1.1)

    def test_extreme_panic(self):
        emotions = {
            "dopamine": 0.5,
            "gaba": 0.5,
            "noradrenaline": 1.0,  # Max panic
            "serotonin": 0.5
        }
        params = calculate_sampler_params(emotions)
        
        # Top-P = 0.95 * (1.0 - 0.6 * 1.0) = 0.95 * 0.4 = 0.38
        self.assertAlmostEqual(params["top_p"], 0.38)
        self.assertTrue(params["top_p"] >= 0.3)

    def test_apathetic_unfocused_state(self):
        emotions = {
            "dopamine": 0.0,
            "gaba": 1.0,
            "noradrenaline": 0.0,
            "serotonin": 0.5
        }
        params = calculate_sampler_params(emotions)
        
        # Temp = 0.7 + 0.6 * 0 - 0.2 * 1.0 = 0.5
        self.assertAlmostEqual(params["temperature"], 0.5)

    def test_serotonin_extreme_rumination(self):
        # Low serotonin (depression / looping)
        emotions_low = {
            "dopamine": 0.5,
            "gaba": 0.5,
            "noradrenaline": 0.3,
            "serotonin": 0.0
        }
        params_low = calculate_sampler_params(emotions_low)
        # RepPen = 1.1 + 0.3 * abs(0.0 - 0.5) = 1.1 + 0.15 = 1.25
        self.assertAlmostEqual(params_low["repeat_penalty"], 1.25)

        # High serotonin (extreme flat / looping)
        emotions_high = {
            "dopamine": 0.5,
            "gaba": 0.5,
            "noradrenaline": 0.3,
            "serotonin": 1.0
        }
        params_high = calculate_sampler_params(emotions_high)
        # RepPen = 1.1 + 0.3 * abs(1.0 - 0.5) = 1.1 + 0.15 = 1.25
        self.assertAlmostEqual(params_high["repeat_penalty"], 1.25)

    def test_clamps(self):
        # Over the limit values
        emotions = {
            "dopamine": 2.0,       # High dopamine
            "gaba": 0.0,
            "noradrenaline": 0.0,
            "serotonin": 0.5
        }
        params = calculate_sampler_params(emotions)
        # Temp = 0.7 + 0.6 * 2.0 = 1.9 -> Clamped to 1.6
        self.assertEqual(params["temperature"], 1.6)

if __name__ == "__main__":
    unittest.main()
