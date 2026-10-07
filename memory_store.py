"""
Memory Store for Groundfall
Manages persistent ecological field notes, flora observations, and walks.
Provides seamless compatibility with Backboard Vector Memory format (.backboard/memories.json)
and local JSON storage.
"""

import os
import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
BACKBOARD_DIR = BASE_DIR / ".backboard"
MEMORIES_FILE = BACKBOARD_DIR / "field_memories.json"

class MemoryStore:
    def __init__(self):
        BACKBOARD_DIR.mkdir(parents=True, exist_ok=True)
        if not MEMORIES_FILE.exists():
            self._init_defaults()

    def _init_defaults(self):
        sample_memories = [
            {
                "id": "mem-001",
                "timestamp": time.time() - 86400 * 2,
                "date_str": "Oct 5, 2026",
                "title": "The Amber Drift: Autumn Foliage & Canopy Drift",
                "theme": "foliage",
                "duration_minutes": 20,
                "eyes_up_percentage": 98.2,
                "acoustic_green_index": 82,
                "notes": "Noticed brilliant scarlet maples along the northern ridge. High wind through the upper branches sounded like ocean surf.",
                "earned_specimen": "🍁 Sugar Maple",
                "tags": ["fall-foliage", "wind-rustle", "touch-grass", "backboard-memory"]
            },
            {
                "id": "mem-002",
                "timestamp": time.time() - 86400,
                "date_str": "Oct 6, 2026",
                "title": "The Whispering Stride: Bio-Acoustic & Avian Listening",
                "theme": "acoustic",
                "duration_minutes": 15,
                "eyes_up_percentage": 96.0,
                "acoustic_green_index": 88,
                "notes": "Followed a family of black-capped chickadees through a hemlock grove. Found undisturbed damp moss.",
                "earned_specimen": "🪶 Blue Jay Down",
                "tags": ["birding", "acoustics", "hemlock", "touch-grass", "backboard-memory"]
            }
        ]
        with open(MEMORIES_FILE, "w", encoding="utf-8") as f:
            json.dump(sample_memories, f, indent=2)

    def get_all_memories(self) -> List[Dict[str, Any]]:
        """Retrieve all recorded walks and field notes."""
        try:
            if MEMORIES_FILE.exists():
                with open(MEMORIES_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def save_memory(self, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Save a new walk and journal entry to persistent Backboard storage."""
        memories = self.get_all_memories()
        new_id = f"mem-{int(time.time())}"
        
        entry = {
            "id": new_id,
            "timestamp": time.time(),
            "date_str": time.strftime("%b %d, %Y %H:%M"),
            "title": memory_data.get("journal_title", "Field Drift"),
            "theme": memory_data.get("theme", "foliage"),
            "duration_minutes": memory_data.get("duration_minutes", 15),
            "eyes_up_percentage": memory_data.get("eyes_up_percentage", 95.0),
            "acoustic_green_index": memory_data.get("acoustic_green_index", 75),
            "notes": memory_data.get("user_notes", ""),
            "earned_specimen": memory_data.get("earned_specimen", "🍁 Sugar Maple"),
            "narrative": memory_data.get("naturalist_narrative", ""),
            "tags": [memory_data.get("theme", "general"), "touch-grass", "hf26challenge", "backboard-memory"]
        }
        
        memories.insert(0, entry)
        with open(MEMORIES_FILE, "w", encoding="utf-8") as f:
            json.dump(memories, f, indent=2)
            
        return entry

    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        """Simple keyword-based semantic search across recorded outdoor notes."""
        memories = self.get_all_memories()
        if not query:
            return memories
        q = query.lower()
        results = []
        for m in memories:
            text = f"{m.get('title', '')} {m.get('notes', '')} {m.get('theme', '')} {' '.join(m.get('tags', []))}".lower()
            if q in text:
                results.append(m)
        return results
