"""
Groundfall - The Offline Field Naturalist & Sensory Walk Companion
Built for Hacktoberfest Open-Source AI Challenge Week 1: Touch Grass
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from gemma_engine import GemmaEngine
from memory_store import MemoryStore

app = FastAPI(
    title="Groundfall",
    description="The Offline Field Naturalist & Sensory Walk Companion (Hacktoberfest Week 1: Touch Grass)",
    version="1.0.0"
)

# Enable CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
STATIC_DIR.mkdir(parents=True, exist_ok=True)

gemma_engine = GemmaEngine()
memory_store = MemoryStore()

# Botanical taxonomy knowledge base for offline flora & bio-classifier
BOTANICAL_KNOWLEDGE = {
    "maple": {
        "common_name": "Sugar Maple (Acer saccharum)",
        "season_phase": "Peak Autumn Senescence",
        "foliage_note": "Brilliant anthocyanin red and carotenoid amber hues. Veins retain sugars before winter abscission.",
        "touch_grass_cue": "Gently hold the leaf blade up to the sun to see the capillary network delivering nutrients to the stem.",
        "ecology": "Provides crucial winter bark forage for deer and nesting cavities for screech owls."
    },
    "oak": {
        "common_name": "Northern Red Oak (Quercus rubra)",
        "season_phase": "Late Autumn Mast Seeding",
        "foliage_note": "Pointed lobes with bristle tips turning deep russet-brown. Tannins protect leaves from early microbial decay.",
        "touch_grass_cue": "Look at the ground beneath the canopy for acorn caps. Heavy acorn production indicates a 'mast year'.",
        "ecology": "Key keystone species supporting over 500 species of lepidoptera and forest birds."
    },
    "pine": {
        "common_name": "Eastern White Pine (Pinus strobus)",
        "season_phase": "Evergreen Resin Dormancy",
        "foliage_note": "Soft needles in bundles of five. Releases aromatic alpha-pinene terpenes that reduce cortisol in humans.",
        "touch_grass_cue": "Crush a fallen brown needle between your fingertips and inhale the crisp resinous aroma.",
        "ecology": "Acts as windbreaks, preserving sub-canopy microclimates in winter storms."
    },
    "birch": {
        "common_name": "Paper Birch (Betula papyrifera)",
        "season_phase": "Autumn Defoliation",
        "foliage_note": "Horizontal lenticels on chalky white exfoliating bark that curls into paper-thin waterproof scrolls.",
        "touch_grass_cue": "Feel the papery curls without peeling them off live wood. Notice how smooth the outer bark feels.",
        "ecology": "Pioneer species stabilizing disturbed soils and riverbanks."
    },
    "moss": {
        "common_name": "Velvet Sheet Moss (Hypnum cupressiforme)",
        "season_phase": "Hydrated Micro-Colony",
        "foliage_note": "Non-vascular bryophyte absorbing moisture and nutrients directly from autumn dew and rainfall.",
        "touch_grass_cue": "Place the palm of your hand against the moss patch. Feel the natural cooling thermal insulation.",
        "ecology": "Filters rainwater, prevents topsoil erosion, and hosts thousands of micro-invertebrates per square foot."
    },
    "fern": {
        "common_name": "Bracken / Wood Fern (Dryopteris marginalis)",
        "season_phase": "Autumn Frond Rusting",
        "foliage_note": "Feathery pinnate fronds shifting from forest emerald to antique bronze as temperatures drop.",
        "touch_grass_cue": "Check the underside of a frond for sori—the tiny spore packets that reproduce without flowers or seeds.",
        "ecology": "Forms protective ground-cover shelter for amphibians and ground-nesting birds."
    },
    "fungus": {
        "common_name": "Turkey Tail / Bracket Polypore (Trametes versicolor)",
        "season_phase": "Active Decomposer Phase",
        "foliage_note": "Concentric bands of brown, tan, and cream velvety zones growing horizontally off fallen timber.",
        "touch_grass_cue": "Touch the stiff, leathery concentric ridges. It breaks down tough lignin that almost nothing else can digest.",
        "ecology": "Primary forest recycler, returning minerals back to the subsoil."
    }
}

class DriftRequest(BaseModel):
    theme: str
    duration_minutes: int

class JournalRequest(BaseModel):
    duration_minutes: int
    eyes_up_percentage: float
    acoustic_green_index: int
    theme: str
    user_notes: str

class FloraIdentifyRequest(BaseModel):
    label_hint: Optional[str] = "maple"

@app.get("/api/status")
def get_status():
    ollama_online = gemma_engine.is_ollama_available()
    memories = memory_store.get_all_memories()
    return {
        "status": "online",
        "app": "Groundfall",
        "version": "1.0.0",
        "gemma_engine": {
            "model": gemma_engine.model_name,
            "ollama_connected": ollama_online,
            "mode": "Local Ollama LLM" if ollama_online else "Resilient On-Device Heuristic Engine (100% Offline)"
        },
        "backboard_memory": {
            "active": True,
            "total_entries": len(memories),
            "storage_path": ".backboard/field_memories.json"
        },
        "capabilities": [
            "Eyes-Up Phone-in-Pocket Screen Auditor",
            "Real-Time Bio-Acoustic Spectrogram Meter",
            "On-Device Open Vision Flora Classifier",
            "Naturalist Field Journal & Memory Persistence"
        ]
    }

@app.post("/api/drift/generate")
def generate_drift(req: DriftRequest):
    if req.duration_minutes < 1 or req.duration_minutes > 120:
        raise HTTPException(status_code=400, detail="Duration must be between 1 and 120 minutes.")
    
    plan = gemma_engine.generate_drift_prompts(req.theme, req.duration_minutes)
    return plan

@app.post("/api/journal/synthesize")
def synthesize_journal(req: JournalRequest):
    walk_data = {
        "duration_minutes": req.duration_minutes,
        "eyes_up_percentage": req.eyes_up_percentage,
        "acoustic_green_index": req.acoustic_green_index,
        "theme": req.theme
    }
    journal = gemma_engine.synthesize_field_journal(walk_data, req.user_notes)
    saved = memory_store.save_memory(journal)
    return {
        "journal": journal,
        "memory_entry": saved
    }

@app.get("/api/journal/history")
def get_journal_history():
    return memory_store.get_all_memories()

@app.get("/api/journal/search")
def search_journal(q: str = ""):
    return memory_store.search_memories(q)

@app.post("/api/flora/identify")
def identify_flora(req: FloraIdentifyRequest):
    hint = (req.label_hint or "maple").lower()
    
    # Match keyword in botanical knowledge
    matched_key = "maple"
    for k in BOTANICAL_KNOWLEDGE.keys():
        if k in hint:
            matched_key = k
            break
            
    botany_info = BOTANICAL_KNOWLEDGE[matched_key]
    return {
        "query": hint,
        "botany": botany_info,
        "offline_verified": True
    }

# Mount static assets
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return HTMLResponse("<h1>Groundfall is starting...</h1>")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
