import * as api from './api.js';
import * as render from './render.js';

let state = null;
let manualReveal = false;
let autoInterval = null;

async function sync() {
    render.renderGrid(state, manualReveal);
    render.updateSidebar(state);
    
    if (state.status !== "running") {
        stopAuto();
        render.toggleOverlay(true, state.status === "won" ? "Victory!" : "Defeat");
    }
}

async function step() {
    state = await api.postStep();
    sync();
}

async function reset() {
    stopAuto();
    render.toggleOverlay(false);
    state = await api.postReset();
    sync();
}

function toggleAuto() {
    if (autoInterval) {
        stopAuto();
    } else {
        autoInterval = setInterval(step, 800);
        document.getElementById("autoBtn").textContent = "Stop";
    }
}

function stopAuto() {
    clearInterval(autoInterval);
    autoInterval = null;
    document.getElementById("autoBtn").textContent = "Auto";
}

document.getElementById("stepBtn").addEventListener("click", step);
document.getElementById("resetBtn").addEventListener("click", reset);
document.getElementById("playAgainBtn").addEventListener("click", reset);
document.getElementById("autoBtn").addEventListener("click", toggleAuto);

document.getElementById("revealBtn").addEventListener("click", () => {
    manualReveal = !manualReveal;
    sync();
});

// Init
(async () => {
    state = await api.getState();
    sync();
})();
