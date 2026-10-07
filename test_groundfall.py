"""
Unit & Integration Test Suite for Groundfall
Verifies Gemma prompt generator, Memory Store, and core functions directly.
"""

import unittest
from gemma_engine import GemmaEngine
from memory_store import MemoryStore
from app import (
    get_status,
    generate_drift,
    synthesize_journal,
    identify_flora,
    DriftRequest,
    JournalRequest,
    FloraIdentifyRequest
)

class TestGroundfall(unittest.TestCase):

    def setUp(self):
        self.engine = GemmaEngine()
        self.store = MemoryStore()

    def test_status_endpoint(self):
        """Verify system status reports online, Backboard memory, and Gemma engine."""
        data = get_status()
        self.assertEqual(data["status"], "online")
        self.assertEqual(data["app"], "Groundfall")
        self.assertIn("gemma_engine", data)
        self.assertIn("backboard_memory", data)
        self.assertTrue(data["backboard_memory"]["active"])

    def test_gemma_drift_generation(self):
        """Verify prompt interval calculations and thematic curation."""
        plan = self.engine.generate_drift_prompts("foliage", 15)
        self.assertIn("steps", plan)
        self.assertGreaterEqual(len(plan["steps"]), 3)
        self.assertEqual(plan["theme"], "foliage")
        self.assertEqual(plan["duration_minutes"], 15)

        # First step trigger should be 0 minutes
        self.assertEqual(plan["steps"][0]["trigger_minute"], 0)

        # Step prompts should contain outdoor sensory cues
        self.assertTrue(any("leaf" in s["sensory_prompt"].lower() or "canopy" in s["sensory_prompt"].lower() or "bark" in s["sensory_prompt"].lower() for s in plan["steps"]))

    def test_gemma_acoustic_theme(self):
        """Verify bio-acoustic listening theme generation."""
        plan = self.engine.generate_drift_prompts("acoustic", 30)
        self.assertEqual(plan["theme"], "acoustic")
        self.assertGreaterEqual(len(plan["steps"]), 4)

    def test_memory_store_persistence(self):
        """Verify saving and searching Backboard vector memories."""
        test_entry = {
            "journal_title": "The Russet Solitude: Fall Foliage Test",
            "theme": "foliage",
            "duration_minutes": 20,
            "eyes_up_percentage": 97.5,
            "acoustic_green_index": 85,
            "user_notes": "Tested walking along the birch groves. Golden leaves everywhere.",
            "naturalist_narrative": "A peaceful autumn excursion into the yellow birch stand.",
            "earned_specimen": "🍁 Sugar Maple"
        }
        saved = self.store.save_memory(test_entry)
        self.assertTrue(saved["id"].startswith("mem-"))

        # Verify search retrieves it
        results = self.store.search_memories("birch")
        self.assertTrue(len(results) >= 1)
        self.assertIn("birch", results[0]["notes"].lower())

    def test_flora_identification_endpoint(self):
        """Verify botanical taxonomy knowledge retrieval."""
        req = FloraIdentifyRequest(label_hint="sugar maple leaf")
        data = identify_flora(req)
        self.assertIn("botany", data)
        self.assertIn("Sugar Maple", data["botany"]["common_name"])
        self.assertIn("touch_grass_cue", data["botany"])

    def test_journal_synthesis_endpoint(self):
        """Verify end-to-end walk debrief synthesis and memory recording."""
        req = JournalRequest(
            duration_minutes=15,
            eyes_up_percentage=99.1,
            acoustic_green_index=89,
            theme="microbiome",
            user_notes="Observed turkey tail polypore on fallen birch. High moss moisture."
        )
        data = synthesize_journal(req)
        self.assertIn("journal", data)
        self.assertIn("memory_entry", data)
        self.assertIn("earned_specimen", data["journal"])

if __name__ == "__main__":
    unittest.main()
