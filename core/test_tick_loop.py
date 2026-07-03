# File: core/test_tick_loop.py
# Project: AIshnitza (Alex Consciousness Isolation)
# Type: Python Executable

import unittest
from bot import CognitionEngine

class TestTickLoop(unittest.TestCase):
    def test_adjust_tick_rate_active(self):
        engine = CognitionEngine()
        # Active mode: idle < 5 mins
        engine.adjust_tick_rate(2.5)
        self.assertEqual(engine.state, "ACTIVE")
        self.assertEqual(engine.tick_rate, 2.0)

    def test_adjust_tick_rate_epistemic(self):
        engine = CognitionEngine()
        # Epistemic mode: 5 <= idle < 60 mins
        engine.adjust_tick_rate(15.0)
        self.assertEqual(engine.state, "EPISTEMIC")
        self.assertEqual(engine.tick_rate, 30.0)

    def test_adjust_tick_rate_sleep(self):
        engine = CognitionEngine()
        # Sleep mode: idle >= 60 mins
        engine.adjust_tick_rate(75.0)
        self.assertEqual(engine.state, "SLEEP")
        self.assertEqual(engine.tick_rate, 1800.0)

if __name__ == "__main__":
    unittest.main()
