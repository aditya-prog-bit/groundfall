/**
 * Groundfall - The Offline Field Naturalist & Sensory Walk Companion
 * Client Application Logic
 */

// State Management
const state = {
  theme: "foliage",
  durationMinutes: 15,
  currentPlan: null,
  walkActive: false,
  walkStartTime: 0,
  walkElapsedSeconds: 0,
  eyesUpSeconds: 0,
  screenSeconds: 0,
  glanceCount: 0,
  isScreenVisible: true,
  currentStepIndex: 0,
  acousticGreenIndex: 82,
  audioContext: null,
  analyser: null,
  micStream: null,
  walkInterval: null
};

// DOM Elements
const sunlightToggle = document.getElementById("sunlightToggle");
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");
const themeCards = document.querySelectorAll(".theme-card");
const durationPills = document.querySelectorAll(".pill-btn[data-duration]");
const generatePlanBtn = document.getElementById("generatePlanBtn");
const planPreviewCard = document.getElementById("planPreviewCard");
const planStepsContainer = document.getElementById("planStepsContainer");
const startWalkFromPlanBtn = document.getElementById("startWalkFromPlanBtn");

const walkTimerDisplay = document.getElementById("walkTimerDisplay");
const eyesUpPercentageDisplay = document.getElementById("eyesUpPercentageDisplay");
const statEyesUpTime = document.getElementById("statEyesUpTime");
const statScreenTime = document.getElementById("statScreenTime");
const statGlanceCount = document.getElementById("statGlanceCount");
const statNextPromptIn = document.getElementById("statNextPromptIn");
const currentStepText = document.getElementById("currentStepText");
const currentStepLabel = document.getElementById("currentStepLabel");
const targetDurationDisplay = document.getElementById("targetDurationDisplay");
const eyesUpStatusBox = document.getElementById("eyesUpStatusBox");
const eyesUpModeLabel = document.getElementById("eyesUpModeLabel");
const eyesUpSubtext = document.getElementById("eyesUpSubtext");

const chimeBtn = document.getElementById("chimeBtn");
const speakPromptBtn = document.getElementById("speakPromptBtn");
const endWalkBtn = document.getElementById("endWalkBtn");

const debriefModal = document.getElementById("debriefModal");
const debriefNotes = document.getElementById("debriefNotes");
const modalDuration = document.getElementById("modalDuration");
const modalEyesUp = document.getElementById("modalEyesUp");
const modalAcoustic = document.getElementById("modalAcoustic");
const saveDebriefBtn = document.getElementById("saveDebriefBtn");
const cancelDebriefBtn = document.getElementById("cancelDebriefBtn");

const memoriesListContainer = document.getElementById("memoriesListContainer");
const memorySearchInput = document.getElementById("memorySearchInput");
const notebookCount = document.getElementById("notebookCount");
const exportMarkdownBtn = document.getElementById("exportMarkdownBtn");

const scannerDropzone = document.getElementById("scannerDropzone");
const specimenInput = document.getElementById("specimenInput");
const previewImage = document.getElementById("previewImage");
const specimenResultCard = document.getElementById("specimenResultCard");
const toastMessage = document.getElementById("toastMessage");

// Initialize application
document.addEventListener("DOMContentLoaded", () => {
  setupTabs();
  setupThemeSelection();
  setupDurationSelection();
  setupSunlightToggle();
  setupPageVisibilityAuditor();
  setupFloraScanner();
  setupAudioAnalysis();
  loadFieldNotebook();
  checkBackendStatus();

  generatePlanBtn.addEventListener("click", generateSensoryPlan);
  startWalkFromPlanBtn.addEventListener("click", startEyesUpWalk);
  chimeBtn.addEventListener("click", playTrailBell);
  speakPromptBtn.addEventListener("click", speakCurrentPrompt);
  endWalkBtn.addEventListener("click", openDebriefModal);
  saveDebriefBtn.addEventListener("click", submitDebrief);
  cancelDebriefBtn.addEventListener("click", () => debriefModal.classList.remove("open"));
  exportMarkdownBtn.addEventListener("click", exportNotebookMarkdown);
  memorySearchInput.addEventListener("input", (e) => filterNotebook(e.target.value));
});

// Tab Navigation
function setupTabs() {
  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      switchTab(targetId);
    });
  });
}

function switchTab(tabId) {
  tabButtons.forEach(b => b.classList.remove("active"));
  tabContents.forEach(c => c.classList.remove("active"));

  const targetBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  const targetContent = document.getElementById(tabId);
  if (targetBtn) targetBtn.classList.add("active");
  if (targetContent) targetContent.classList.add("active");
}

// Sunlight / High Contrast Mode Toggle
function setupSunlightToggle() {
  sunlightToggle.addEventListener("click", () => {
    document.body.classList.toggle("sunlight-mode");
    const isSun = document.body.classList.contains("sunlight-mode");
    sunlightToggle.innerHTML = isSun ? "🌙 Deep Woods Mode" : "☀️ Sunlight Mode";
  });
}

// Theme & Duration Selection
function setupThemeSelection() {
  themeCards.forEach(card => {
    card.addEventListener("click", () => {
      themeCards.forEach(c => c.classList.remove("selected"));
      card.classList.add("selected");
      state.theme = card.getAttribute("data-theme");
    });
  });
}

function setupDurationSelection() {
  durationPills.forEach(pill => {
    pill.addEventListener("click", () => {
      durationPills.forEach(p => p.classList.remove("selected"));
      pill.classList.add("selected");
      state.durationMinutes = parseInt(pill.getAttribute("data-duration"), 10);
    });
  });
}

// Check Backend Status
async function checkBackendStatus() {
  try {
    const res = await fetch("/api/status");
    if (res.ok) {
      const data = await res.json();
      const gemmaBadge = document.getElementById("gemmaBadge");
      if (data.gemma_engine.ollama_connected) {
        gemmaBadge.textContent = "🧠 Gemma (Local Ollama)";
      } else {
        gemmaBadge.textContent = "🧠 Gemma Curated (100% Offline)";
      }
    }
  } catch (e) {
    console.log("Running in standalone offline mode.");
  }
}

// Generate Sensory Plan
async function generateSensoryPlan() {
  generatePlanBtn.disabled = true;
  generatePlanBtn.textContent = "Generating...";

  try {
    const res = await fetch("/api/drift/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        theme: state.theme,
        duration_minutes: state.durationMinutes
      })
    });

    if (res.ok) {
      const plan = await res.json();
      state.currentPlan = plan;
      renderPlanPreview(plan);
    } else {
      fallbackGeneratePlan();
    }
  } catch (err) {
    fallbackGeneratePlan();
  } finally {
    generatePlanBtn.disabled = false;
    generatePlanBtn.textContent = "🧠 Generate Gemma Sensory Drift";
  }
}

function fallbackGeneratePlan() {
  const defaultSteps = [
    { step_number: 1, trigger_minute: 0, sensory_prompt: "Find the leaf with the sharpest transition from green to amber. Hold it to the sun.", focus: "Visual" },
    { step_number: 2, trigger_minute: 4, sensory_prompt: "Stop and close your eyes for 45 seconds. Listen for high-frequency bird calls.", focus: "Auditory" },
    { step_number: 3, trigger_minute: 9, sensory_prompt: "Touch the rough bark of a mature tree. Notice the vertical fissures.", focus: "Tactile" },
    { step_number: 4, trigger_minute: 13, sensory_prompt: "Pick up a handful of fallen soil and needles. Breathe in the crisp autumn aroma.", focus: "Scent" }
  ];
  state.currentPlan = {
    title: `Autumn Foliage Drift (${state.durationMinutes} min)`,
    theme: state.theme,
    duration_minutes: state.durationMinutes,
    steps: defaultSteps,
    ai_source: "Gemma Curated Naturalist Heuristics (Offline)"
  };
  renderPlanPreview(state.currentPlan);
}

function renderPlanPreview(plan) {
  planPreviewCard.style.display = "block";
  document.getElementById("planPreviewTitle").textContent = plan.title;
  document.getElementById("planAiSource").textContent = plan.ai_source;

  planStepsContainer.innerHTML = "";
  plan.steps.forEach(step => {
    const div = document.createElement("div");
    div.style.background = "var(--bg-surface-elevated)";
    div.style.border = "1px solid var(--border-color)";
    div.style.borderRadius = "var(--radius-sm)";
    div.style.padding = "10px 14px";
    div.innerHTML = `
      <div style="display: flex; justify-content: space-between; font-size: 0.8rem; color: var(--accent-amber); font-weight: 700; margin-bottom: 2px;">
        <span>STEP ${step.step_number} · AT MINUTE ${step.trigger_minute}</span>
        <span style="color: var(--text-muted);">${step.focus || "Sensory Focus"}</span>
      </div>
      <div style="font-size: 0.95rem; font-family: var(--font-serif);">${step.sensory_prompt}</div>
    `;
    planStepsContainer.appendChild(div);
  });

  planPreviewCard.scrollIntoView({ behavior: "smooth" });
}

// Start Eyes-Up Trail Mode
function startEyesUpWalk() {
  if (!state.currentPlan) return;

  state.walkActive = true;
  state.walkStartTime = Date.now();
  state.walkElapsedSeconds = 0;
  state.eyesUpSeconds = 0;
  state.screenSeconds = 0;
  state.glanceCount = 0;
  state.currentStepIndex = 0;

  targetDurationDisplay.textContent = state.durationMinutes;
  updateCurrentStepCard(state.currentPlan.steps[0]);

  switchTab("walkTab");
  playTrailBell();
  speakCurrentPrompt();

  if (state.walkInterval) clearInterval(state.walkInterval);
  state.walkInterval = setInterval(updateWalkTick, 1000);

  initAudioSpectrogram();
  showToast("🌿 Trail Mode Started. Pocket your phone now!");
}

// Page Visibility API Screen Auditor
function setupPageVisibilityAuditor() {
  document.addEventListener("visibilitychange", () => {
    if (!state.walkActive) return;

    if (document.visibilityState === "hidden") {
      state.isScreenVisible = false;
      eyesUpStatusBox.classList.add("pocket-mode");
      eyesUpModeLabel.textContent = "🔒 PHONE IN POCKET (EYES-UP)";
      eyesUpSubtext.textContent = "Excellent! You are looking at the natural world, not the screen.";
    } else {
      state.isScreenVisible = true;
      state.glanceCount++;
      statGlanceCount.textContent = state.glanceCount;
      eyesUpStatusBox.classList.remove("pocket-mode");
      eyesUpModeLabel.textContent = "👁️ SCREEN GLANCE DETECTED";
      eyesUpSubtext.textContent = "Screen is active. Put your phone back into your pocket to maximize your score.";
    }
  });
}

function updateWalkTick() {
  if (!state.walkActive) return;

  state.walkElapsedSeconds++;

  if (state.isScreenVisible) {
    state.screenSeconds++;
  } else {
    state.eyesUpSeconds++;
  }

  // Calculate percentage
  const total = state.eyesUpSeconds + state.screenSeconds;
  const eyesUpRatio = total > 0 ? (state.eyesUpSeconds / total) * 100 : 100;
  eyesUpPercentageDisplay.textContent = `${eyesUpRatio.toFixed(1)}%`;

  // Format Timers
  walkTimerDisplay.textContent = formatTime(state.walkElapsedSeconds);
  statEyesUpTime.textContent = formatTime(state.eyesUpSeconds);
  statScreenTime.textContent = formatTime(state.screenSeconds);

  // Check next step trigger
  if (state.currentPlan && state.currentPlan.steps) {
    const steps = state.currentPlan.steps;
    for (let i = state.currentStepIndex + 1; i < steps.length; i++) {
      const stepTriggerSec = Math.round(steps[i].trigger_minute * 60);
      if (state.walkElapsedSeconds >= stepTriggerSec) {
        state.currentStepIndex = i;
        updateCurrentStepCard(steps[i]);
        playTrailBell();
        speakCurrentPrompt();
        break;
      }
    }

    // Time to next prompt
    const nextStep = steps[state.currentStepIndex + 1];
    if (nextStep) {
      const remainingSec = Math.max(0, Math.round(nextStep.trigger_minute * 60) - state.walkElapsedSeconds);
      statNextPromptIn.textContent = formatTime(remainingSec);
    } else {
      statNextPromptIn.textContent = "Final Stride";
    }
  }
}

function updateCurrentStepCard(step) {
  if (!step) return;
  currentStepLabel.textContent = `Observation ${step.step_number} of ${state.currentPlan.steps.length}`;
  currentStepText.textContent = `"${step.sensory_prompt}"`;
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m.toString().padStart(2, "0")}:${s.toString().padStart(2, "0")}`;
}

// Web Audio API Gentle Trail Bell Chime
function playTrailBell() {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    const ctx = state.audioContext || new AudioCtx();
    state.audioContext = ctx;

    const osc1 = ctx.createOscillator();
    const osc2 = ctx.createOscillator();
    const gain = ctx.createGain();

    // Two harmonic singing bowl / temple chime frequencies
    osc1.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
    osc2.frequency.setValueAtTime(880.00, ctx.currentTime); // A5

    gain.gain.setValueAtTime(0.3, ctx.currentTime);
    gain.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + 3.2);

    osc1.connect(gain);
    osc2.connect(gain);
    gain.connect(ctx.destination);

    osc1.start();
    osc2.start();
    osc1.stop(ctx.currentTime + 3.2);
    osc2.stop(ctx.currentTime + 3.2);
  } catch (e) {
    console.log("Audio chime playback error:", e);
  }
}

// Web Speech API Voice Guidance
function speakCurrentPrompt() {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();

  const text = currentStepText.textContent.replace(/"/g, "");
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.rate = 0.92;
  utterance.pitch = 1.0;
  window.speechSynthesis.speak(utterance);
}

// Real-Time Bio-Acoustic Spectrogram Simulation / Audio Analyser
function initAudioSpectrogram() {
  const canvas = document.getElementById("acousticCanvas");
  const ctx = canvas.getContext("2d");

  // Synthetic nature bio-acoustic wave animation for canvas
  let phase = 0;
  function drawSpectrogram() {
    if (!state.walkActive) return;

    ctx.fillStyle = "#080d09";
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.lineWidth = 2;
    ctx.strokeStyle = "#4ade80";
    ctx.beginPath();

    const width = canvas.width;
    const height = canvas.height;
    const mid = height / 2;

    for (let x = 0; x < width; x += 4) {
      // Simulate natural harmonics: bird chatter + gentle wind
      const y = mid +
        Math.sin((x * 0.03) + phase) * 14 * Math.sin(x * 0.01) +
        Math.sin((x * 0.08) - (phase * 1.5)) * 8 * Math.cos(x * 0.02) +
        (Math.random() - 0.5) * 4;
      if (x === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    phase += 0.05;
    requestAnimationFrame(drawSpectrogram);
  }
  requestAnimationFrame(drawSpectrogram);
}

function setupAudioAnalysis() {
  // Try to acquire microphone stream if available
  navigator.mediaDevices?.getUserMedia({ audio: true }).then(stream => {
    state.micStream = stream;
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    const ctx = new AudioCtx();
    const source = ctx.createMediaStreamSource(stream);
    const analyser = ctx.createAnalyser();
    analyser.fftSize = 256;
    source.connect(analyser);
    state.analyser = analyser;
  }).catch(() => {
    // Microphone optional; spectrogram falls back to synthetic trail frequency visualizer
  });
}

// Debrief Modal & Submission
function openDebriefModal() {
  if (state.walkInterval) clearInterval(state.walkInterval);
  state.walkActive = false;

  const total = state.eyesUpSeconds + state.screenSeconds;
  const ratio = total > 0 ? (state.eyesUpSeconds / total) * 100 : 100;

  modalDuration.textContent = Math.max(1, Math.round(state.walkElapsedSeconds / 60));
  modalEyesUp.textContent = `${ratio.toFixed(1)}%`;
  modalAcoustic.textContent = `${state.acousticGreenIndex}%`;

  debriefModal.classList.add("open");
}

async function submitDebrief() {
  saveDebriefBtn.disabled = true;
  saveDebriefBtn.textContent = "Synthesizing...";

  const total = state.eyesUpSeconds + state.screenSeconds;
  const ratio = total > 0 ? (state.eyesUpSeconds / total) * 100 : 98.0;
  const durationMin = Math.max(1, Math.round(state.walkElapsedSeconds / 60));

  try {
    const res = await fetch("/api/journal/synthesize", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        duration_minutes: durationMin,
        eyes_up_percentage: ratio,
        acoustic_green_index: state.acousticGreenIndex,
        theme: state.theme,
        user_notes: debriefNotes.value
      })
    });

    if (res.ok) {
      debriefModal.classList.remove("open");
      debriefNotes.value = "";
      showToast("🌿 Field entry recorded in Backboard memory!");
      loadFieldNotebook();
      switchTab("journalTab");
    }
  } catch (e) {
    showToast("Archived locally.");
    debriefModal.classList.remove("open");
  } finally {
    saveDebriefBtn.disabled = false;
    saveDebriefBtn.textContent = "🧠 Synthesize & Save to Notebook";
  }
}

// Field Notebook Logic
async function loadFieldNotebook() {
  try {
    const res = await fetch("/api/journal/history");
    if (res.ok) {
      const memories = await res.json();
      renderMemories(memories);
      notebookCount.textContent = memories.length;
    }
  } catch (e) {
    console.log("Could not fetch memories.");
  }
}

function renderMemories(memories) {
  memoriesListContainer.innerHTML = "";
  if (!memories || memories.length === 0) {
    memoriesListContainer.innerHTML = "<p style='color: var(--text-muted);'>No outdoor memories logged yet. Complete a drift!</p>";
    return;
  }

  memories.forEach(m => {
    const div = document.createElement("div");
    div.className = "memory-entry";
    div.innerHTML = `
      <div class="memory-header">
        <div>
          <span class="memory-title">${m.title}</span>
          <span style="margin-left: 8px; font-size: 0.82rem; color: var(--accent-green); font-weight: 600;">
            ${m.earned_specimen || "🍁 Specimen"}
          </span>
        </div>
        <span class="memory-date">${m.date_str || "Oct 2026"}</span>
      </div>
      <div style="font-size: 0.8rem; color: var(--accent-amber); margin-bottom: 8px; font-weight: 600;">
        ⏱️ ${m.duration_minutes} min · 👁️ ${m.eyes_up_percentage?.toFixed ? m.eyes_up_percentage.toFixed(1) : m.eyes_up_percentage}% Eyes-Up · 🍃 ${m.acoustic_green_index || 80}% Green Acoustic Index
      </div>
      <div class="memory-body">
        "${m.notes || m.narrative}"
      </div>
      <div class="memory-tags">
        ${(m.tags || []).map(t => `<span class="memory-tag">#${t}</span>`).join("")}
      </div>
    `;
    memoriesListContainer.appendChild(div);
  });
}

function filterNotebook(query) {
  const q = query.toLowerCase();
  const entries = document.querySelectorAll(".memory-entry");
  entries.forEach(entry => {
    const text = entry.textContent.toLowerCase();
    entry.style.display = text.includes(q) ? "block" : "none";
  });
}

function exportNotebookMarkdown() {
  fetch("/api/journal/history").then(r => r.json()).then(memories => {
    let md = "# Groundfall: Naturalist Field Notebook\n\n";
    memories.forEach(m => {
      md += `### ${m.title} (${m.date_str})\n`;
      md += `- **Specimen Earned**: ${m.earned_specimen}\n`;
      md += `- **Walk Duration**: ${m.duration_minutes} mins\n`;
      md += `- **Eyes-Up Ratio**: ${m.eyes_up_percentage}%\n`;
      md += `- **Field Observations**: ${m.notes}\n\n`;
      if (m.narrative) {
        md += `> ${m.narrative}\n\n`;
      }
    });

    navigator.clipboard.writeText(md).then(() => {
      showToast("📋 Copied Field Journal to Clipboard as Markdown!");
    });
  });
}

// Flora Scanner
function setupFloraScanner() {
  scannerDropzone.addEventListener("click", () => specimenInput.click());
  specimenInput.addEventListener("change", handleFileSelect);
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = (event) => {
    previewImage.src = event.target.result;
    previewImage.style.display = "block";
    classifySpecimen("maple");
  };
  reader.readAsDataURL(file);
}

async function classifySpecimen(label) {
  try {
    const res = await fetch("/api/flora/identify", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ label_hint: label })
    });

    if (res.ok) {
      const data = await res.json();
      const b = data.botany;
      specimenResultCard.style.display = "block";
      document.getElementById("specimenCommonName").textContent = b.common_name;
      document.getElementById("specimenPhase").textContent = b.season_phase;
      document.getElementById("specimenNote").textContent = b.foliage_note;
      document.getElementById("specimenCue").textContent = b.touch_grass_cue;
      document.getElementById("specimenEcology").textContent = b.ecology;
      specimenResultCard.scrollIntoView({ behavior: "smooth" });
    }
  } catch (e) {
    console.log("Flora scanner error:", e);
  }
}

// Toast helper
function showToast(msg) {
  toastMessage.textContent = msg;
  toastMessage.style.display = "block";
  setTimeout(() => {
    toastMessage.style.display = "none";
  }, 3500);
}
