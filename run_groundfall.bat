@echo off
title Groundfall - The Offline Field Naturalist & Sensory Walk Companion
echo ===================================================================
echo   Groundfall - The Offline Field Naturalist & Sensory Walk Companion
echo   Built for Hacktoberfest Week 1: Touch Grass (#hf26challenge)
echo ===================================================================
echo Opening in browser at http://127.0.0.1:8000 ...
start http://127.0.0.1:8000
python -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload
pause
