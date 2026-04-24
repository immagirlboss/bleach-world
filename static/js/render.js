const SPRITES = {
    kenpachi: "/static/img/kenpachi.png",
    byakuya: "/static/img/byakuya.png",
    toshiro: "/static/img/hitsugaya.png",
    hitsugaya: "/static/img/hitsugaya.png",
    ichigo: "/static/img/ichigo.png",
    rukia: "/static/img/rukia.png"
};

export function renderGrid(state, manualReveal) {
    const grid = document.getElementById("grid");
    grid.innerHTML = "";

    // Iterate rows from top (4) to bottom (0) to place (0,0) at bottom-left
    for (let r = 4; r >= 0; r--) {
        for (let c = 0; c < 5; c++) {
            const cell = createCell(r, c, state, manualReveal);
            grid.appendChild(cell);
        }
    }
}

function createCell(r, c, state, manualReveal) {
    const cell = document.createElement("div");
    cell.className = "cell";
    
    if (isVisited(r, c, state)) cell.classList.add("cell--visited");
    if (isAgent(r, c, state)) cell.classList.add("cell--agent");

    addCellContent(cell, r, c, state, manualReveal);
    return cell;
}

function isVisited(r, c, state) {
    return state.visited.some(v => v[0] === r && v[1] === c);
}

function isAgent(r, c, state) {
    return state.agent[0] === r && state.agent[1] === c;
}

function addCellContent(cell, r, c, state, manualReveal) {
    const isDead = state.status === "dead";
    const showHidden = manualReveal || isDead;

    // Captains
    const cap = state.world.captains.find(cap => cap.pos[0] === r && cap.pos[1] === c);
    const isDefeated = state.world.defeated_captains.some(v => v[0] === r && v[1] === c);
    if (cap && (showHidden || isDefeated)) {
        cell.innerHTML = `<img src="${SPRITES[cap.name.toLowerCase()] || SPRITES.kenpachi}" class="sprite" alt="${cap.name}">`;
    }

    // Rukia
    if ((showHidden || state.status === "won") && isRukia(r, c, state)) {
        cell.innerHTML = `<img src="${SPRITES.rukia}" class="sprite" alt="Rukia">`;
    }

    // Rifts
    if (showHidden && isRift(r, c, state)) {
        cell.innerHTML = "🌀";
    }

    // Agent
    if (isAgent(r, c, state)) {
        cell.innerHTML = `<img src="${SPRITES.ichigo}" class="sprite" alt="Ichigo">`;
        const badgeClass = state.move_type === "probabilistic" ? "badge--chance" : "badge--logic";
        cell.innerHTML += `<span class="badge ${badgeClass}">${state.move_type}</span>`;
    }
}

function isRukia(r, c, state) {
    return state.world.rukia && state.world.rukia[0] === r && state.world.rukia[1] === c;
}

function isRift(r, c, state) {
    return state.world.rifts.some(rift => rift[0] === r && rift[1] === c);
}

export function updateSidebar(state) {
    document.getElementById("info").innerHTML = `
        Position: (${state.agent[0]}, ${state.agent[1]})<br>
        Steps: ${state.step}<br>
        Bankai: ${state.has_bankai ? "Ready" : "Used"}
    `;

    renderList("log", state.log);
    renderList("trace", state.query_trace);
}

function renderList(id, items) {
    const el = document.getElementById(id);
    el.innerHTML = items.slice().reverse().map(item => `<div>${item}</div>`).join("");
}

export function toggleOverlay(show, title = "") {
    const overlay = document.getElementById("overlay");
    document.getElementById("endTitle").textContent = title;
    overlay.classList.toggle("is-active", show);
}
