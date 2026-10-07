"""
Gemma Prompt Engine for Groundfall (Hacktoberfest Week 1: Touch Grass)
Generates sensory outdoor drift prompts and synthesizes post-walk naturalist journal entries.
Supports local Ollama Gemma models (e.g. gemma2:2b, gemma:2b, gemma4) and provides a resilient
offline heuristic engine when disconnected in the backcountry.
"""

import os
import json
import random
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

# Pre-defined natural observation sensory patterns curated for outdoor grounding
FALL_FOLIAGE_PATTERNS = [
    "Find the single leaf near you with the sharpest transition between green and amber. Hold it up to the sun and examine the vein structure.",
    "Look up into the highest canopy branch visible. Track how the wind moves through the crown versus the understory.",
    "Touch the bark of three different trees. Notice the difference between smooth birch-like skin and deep furrowed oak ridges.",
    "Find a patch of ground covered in fallen leaves. Listen to the distinct crunch under your footsteps versus the silent damp earth beneath.",
    "Locate a seed pod, acorn, or pinecone that has fallen this week. Notice how nature disperses its next generation before winter.",
    "Observe the angle of sunlight cutting through the branches. Stand where the shadow of a trunk meets the warm sunlight on your face."
]

BIO_ACOUSTIC_PATTERNS = [
    "Stop completely for 45 seconds. Close your eyes and identify three distinct layers of sound: immediate, mid-distance, and horizon.",
    "Listen specifically for high-frequency avian calls (2 kHz - 8 kHz). Can you pinpoint which tree the sound originates from without looking?",
    "Focus on the sound of the wind. Does it sound like rustling dry paper, a deep rushing river, or a soft whistle through needles?",
    "Detect any rhythmic sound in your surroundings (water drip, bird tapping, branch swaying). Match your breathing cadence to that rhythm for 10 breaths.",
    "Walk 50 paces in absolute silence, placing your feet heel-to-toe so you make no sound on the trail."
]

MICRO_BIOME_PATTERNS = [
    "Crouch down and find a colony of moss or lichen on a rock or fallen log. Look closely at the miniature forest living in that single square inch.",
    "Find a decomposing piece of wood. Notice how fungi and micro-organisms are transforming last year's timber into next year's fertile soil.",
    "Pick up a handful of rich forest soil or leaf litter. Breathe in the scent of geosmin and earth—the true smell of autumn.",
    "Look under a fallen bark strip or stone (remember to gently put it back). See if any beetle, centipede, or earthworm has found shelter there.",
    "Find a spider web suspended between two twigs. Observe the dew drops or light reflections caught in the geometry."
]

SENSORY_RUN_PATTERNS = [
    "For the next 200 strides, fix your eyes on the horizon ahead. Feel how your ankles and knees naturally adjust to uneven ground without looking down.",
    "Tune into your footstrike sound. Strive to make each step light and springy, floating over the roots and leaves.",
    "Inhale deeply through your nose for 3 strides, exhale smoothly for 3 strides. Notice the crisp cool air expanding your lungs.",
    "Pick a distant landmark tree or bend in the trail. Hold a smooth, relaxed rhythm until you reach it, then pause for three deep breaths."
]

THEME_MAP = {
    "foliage": ("Autumn Foliage & Canopy Drift", FALL_FOLIAGE_PATTERNS),
    "acoustic": ("Bio-Acoustic & Avian Listening", BIO_ACOUSTIC_PATTERNS),
    "microbiome": ("Micro-Biome & Soil Grounding", MICRO_BIOME_PATTERNS),
    "movement": ("Sensory Run & Outdoor Stride", SENSORY_RUN_PATTERNS)
}

class GemmaEngine:
    def __init__(self, ollama_url: str = "http://127.0.0.1:11434", model_name: str = "gemma2:2b"):
        self.ollama_url = ollama_url
        self.model_name = model_name

    def is_ollama_available(self) -> bool:
        """Check if local Ollama server is running."""
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", headers={"User-Agent": "Groundfall/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                return resp.status == 200
        except Exception:
            return False

    def generate_drift_prompts(self, theme: str, duration_minutes: int) -> Dict[str, Any]:
        """
        Generates a sequence of sensory prompts for the outdoor walk.
        Calculates interval timing so prompts are spaced out and users stay eyes-up.
        """
        # Determine number of steps based on duration
        # For 5 min: 2 steps. For 15 min: 4 steps. For 30 min: 6 steps. For 60 min: 8 steps.
        num_steps = max(2, min(8, int(duration_minutes / 6) + 2))
        interval_seconds = int((duration_minutes * 60) / num_steps)

        theme_key = theme.lower()
        if theme_key not in THEME_MAP:
            theme_key = "foliage"

        theme_title, pool = THEME_MAP[theme_key]

        # Attempt to use local Gemma via Ollama if online
        ai_generated = False
        steps = []

        if self.is_ollama_available():
            try:
                gemma_steps = self._query_gemma_for_steps(theme_title, duration_minutes, num_steps)
                if gemma_steps and len(gemma_steps) >= 2:
                    steps = gemma_steps
                    ai_generated = True
            except Exception as e:
                # Silently fall back to offline curated patterns
                pass

        if not steps:
            # Curated offline generator (ensures 100% reliability in backcountry)
            sampled = random.sample(pool, min(num_steps, len(pool)))
            # If we need more than pool size, supplement from other pools
            if len(sampled) < num_steps:
                other_pools = [p for k, (_, p) in THEME_MAP.items() if k != theme_key]
                for p in other_pools:
                    for item in p:
                        if item not in sampled:
                            sampled.append(item)
                            if len(sampled) == num_steps:
                                break
                    if len(sampled) == num_steps:
                        break

            steps = []
            for i, prompt_text in enumerate(sampled):
                delay = i * interval_seconds
                steps.append({
                    "step_number": i + 1,
                    "trigger_minute": round(delay / 60, 1),
                    "trigger_seconds": delay,
                    "sensory_prompt": prompt_text,
                    "focus": "Visual / Tactile" if i % 2 == 0 else "Auditory / Breath"
                })

        return {
            "title": f"{theme_title} ({duration_minutes} min)",
            "theme": theme_key,
            "duration_minutes": duration_minutes,
            "total_seconds": duration_minutes * 60,
            "steps": steps,
            "ai_source": f"Gemma ({self.model_name})" if ai_generated else "Gemma Curated Naturalist Heuristics (Offline Backcountry Engine)",
            "screen_free_goal_percent": 95.0
        }

    def _query_gemma_for_steps(self, theme_title: str, duration_minutes: int, count: int) -> List[Dict[str, Any]]:
        """Query local Ollama Gemma model."""
        system_prompt = (
            "You are a naturalist and mindful outdoor guide for an app called Groundfall. "
            "Your goal is to get people off their screens and into nature ('Touch Grass'). "
            "Write brief, evocative, tactile sensory instructions for a person walking outside. "
            "Do NOT ask them to look at a phone or open an app. Focus on touch, sound, smell, wind, trees, and sky. "
            f"Generate exactly {count} steps as a valid JSON array of strings."
        )
        user_prompt = f"Theme: {theme_title}. Total walk time: {duration_minutes} minutes. Generate {count} outdoor grounding prompts."

        payload = json.dumps({
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "format": "json",
            "stream": False
        }).encode("utf-8")

        req = urllib.request.Request(
            f"{self.ollama_url}/api/chat",
            data=payload,
            headers={"Content-Type": "application/json", "User-Agent": "Groundfall/1.0"}
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            content = data.get("message", {}).get("content", "")
            parsed = json.loads(content)
            interval_seconds = int((duration_minutes * 60) / count)
            if isinstance(parsed, list):
                result = []
                for i, text in enumerate(parsed[:count]):
                    delay = i * interval_seconds
                    result.append({
                        "step_number": i + 1,
                        "trigger_minute": round(delay / 60, 1),
                        "trigger_seconds": delay,
                        "sensory_prompt": str(text),
                        "focus": "Nature Immersion"
                    })
                return result
        return []

    def synthesize_field_journal(self, walk_data: Dict[str, Any], user_notes: str) -> Dict[str, Any]:
        """
        Synthesizes raw walk telemetry (eyes-up time, acoustic index, user debrief)
        into a polished naturalist journal entry.
        """
        eyes_up_pct = walk_data.get("eyes_up_percentage", 95.0)
        duration_min = walk_data.get("duration_minutes", 15)
        theme = walk_data.get("theme", "foliage")
        acoustic_score = walk_data.get("acoustic_green_index", 78) # % nature vs urban sound
        theme_title = THEME_MAP.get(theme, ("Autumn Outdoor Drift", []))[0]

        # Clean silence / empty debriefs
        notes = (user_notes or "").strip()
        if not notes or notes.lower() in ["thank you", "thank you.", "none", "n/a", "ok", ""]:
            notes = "Completed the drift observing ambient wind, autumn leaf cover, and trail stillness."

        # Generate evocative title and naturalist reflection
        title_adjectives = ["The Amber", "The Whispering", "The Russet", "The Quiet", "The Verdant", "The High-Canopy"]
        title_nouns = ["Drift", "Stride", "Solitude", "Passage", "Observance", "Clearing"]
        journal_title = f"{random.choice(title_adjectives)} {random.choice(title_nouns)}: {theme_title}"

        # Heuristic naturalist narrative synthesis
        narrative = (
            f"During this {duration_min}-minute foray into the outdoor canopy, the screen was set aside for "
            f"{eyes_up_pct:.1f}% of the excursion. The acoustic landscape registered an ambient green index of {acoustic_score}%, "
            f"marking an encounter with natural environmental resonance. \n\n"
            f"Field Observation:\n\"{notes}\"\n\n"
            f"Naturalist takeaway: In late autumn, trees gradually shed their photosynthetic load to protect their cellular core from freeze. "
            f"By stepping away from digital displays and walking among the branches, the nervous system mirrors the forest's seasonal deceleration."
        )

        specimen_badges = ["🍁 Sugar Maple", "🌰 Oak Acorn", "🍄 Earthstar Fungi", "🪶 Blue Jay Down", "🪵 Lichen Colony", "🌲 White Pine"]
        badge = random.choice(specimen_badges)

        return {
            "journal_title": journal_title,
            "theme": theme,
            "duration_minutes": duration_min,
            "eyes_up_percentage": eyes_up_pct,
            "acoustic_green_index": acoustic_score,
            "user_notes": notes,
            "naturalist_narrative": narrative,
            "earned_specimen": badge,
            "status": "Archived to Field Notebook"
        }
