// GLOBAL STATE & CONSTANTS

// Pathfinding Visualizer State
let gridSize = 10;
let startNode = { x: 1, y: 1 };
let goalNode  = { x: 8, y: 8 };
let walls = new Set(); // Stores coordinates as "x,y"

let isDrawingWalls   = false;
let isMovingStart    = false;
let isMovingGoal     = false;
let isSimulating     = false;
let animationSpeed   = 50; // ms
let animationTimeoutIds = [];

// Cell cache: Map<"x,y", HTMLElement> — eliminates repeated querySelector calls
let cellCache = new Map();
let lastAgentCell = null; // Track agent cell reference directly

// Mini Game State
let gameModalActive    = false;
let currentTurn        = 'player'; // 'player' | 'enemy'
let playerAP           = 3;
let playerHealCooldown = 0;
const maxHP            = 100;

let gameState = {
    ai_hp:         maxHP,
    ai_pos:        [4, 4],
    ai_shield:     false,
    ai_heal_cd:    0,
    player_hp:     maxHP,
    player_pos:    [0, 0],
    player_shield: false
};

let gameWalls    = [];
let selectedSkill = null; // 'move' | 'attack'

// Battle grid cell cache
let battleCellCache = new Map();


// DOM REFERENCES

const mainGrid        = document.getElementById('main-grid');
const algorithmSelect = document.getElementById('algorithm-select');
const heuristicSelect = document.getElementById('heuristic-select');
const heuristicGroup  = document.getElementById('heuristic-group');
const gridSizeSelect  = document.getElementById('grid-size-select');
const speedRange      = document.getElementById('speed-range');
const speedVal        = document.getElementById('speed-val');
const btnFindPath     = document.getElementById('btn-find-path');
const btnClearPath    = document.getElementById('btn-clear-path');
const btnResetGrid    = document.getElementById('btn-reset-grid');
const btnDirectGame   = document.getElementById('btn-direct-game');
const algoDescText    = document.getElementById('algo-desc-text');

const statVisited = document.getElementById('stat-visited');
const statCost    = document.getElementById('stat-cost');
const statTime    = document.getElementById('stat-time');
const statStatus  = document.getElementById('stat-status');
const activityLog = document.getElementById('activity-log');

// Game DOM References
const gameModal          = document.getElementById('game-modal');
const gameCloseBtn       = document.getElementById('game-close-btn');
const battleGrid         = document.getElementById('battle-grid');
const turnIndicator      = document.getElementById('turn-indicator');
const turnStatusCard     = turnIndicator.closest('.turn-status-card');
const apIndicator        = document.getElementById('ap-indicator');
const playerHpBar        = document.getElementById('player-hp-bar');
const playerHpText       = document.getElementById('player-hp-text');
const enemyHpBar         = document.getElementById('enemy-hp-bar');
const enemyHpText        = document.getElementById('enemy-hp-text');
const playerShieldBadge  = document.getElementById('player-shield-badge');
const enemyShieldBadge   = document.getElementById('enemy-shield-badge');
const battleLog          = document.getElementById('battle-log');
const gameOverScreen     = document.getElementById('game-over-screen');
const gameOverTitle      = document.getElementById('game-over-title');
const gameOverMsg        = document.getElementById('game-over-msg');
const gameRestartBtn     = document.getElementById('game-restart-btn');
const gameExitBtn        = document.getElementById('game-exit-btn');
const btnEndTurn         = document.getElementById('btn-end-turn');

const skillMove             = document.getElementById('skill-move');
const skillAttack           = document.getElementById('skill-attack');
const skillShield           = document.getElementById('skill-shield');
const skillHeal             = document.getElementById('skill-heal');
const healCooldownOverlay   = document.getElementById('heal-cooldown-overlay');


// ALGORITHM DESCRIPTIONS

const algoDescriptions = {
    a_star:   'A* menemukan jalur terpendek secara efisien menggunakan heuristik jarak ke tujuan. Optimal dan cepat.',
    dijkstra: "Dijkstra menjamin jalur terpendek dengan menjelajahi semua arah berdasarkan biaya terkecil.",
    bfs:      'BFS menjelajahi secara melebar lapis demi lapis. Menjamin jalur terpendek pada graf tak berbobot.',
    dfs:      'DFS menjelajahi sedalam mungkin tiap arah. Tidak menjamin jalur terpendek, tapi hemat memori.'
};


// ACTIVITY LOG HELPER

function writeLog(text, type = 'info') {
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    const ts = new Date().toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    entry.textContent = `[${ts}] ${text}`;
    activityLog.appendChild(entry);
    // Keep log from growing too large
    while (activityLog.children.length > 80) {
        activityLog.removeChild(activityLog.firstChild);
    }
    activityLog.scrollTop = activityLog.scrollHeight;
}


// SLIDER RANGE FILL VISUAL UPDATE

function updateRangeFill(el) {
    const pct = ((el.value - el.min) / (el.max - el.min)) * 100;
    el.style.background = `linear-gradient(to right, var(--accent-cyan) ${pct}%, var(--bg-tertiary) ${pct}%)`;
}


// PATHFINDING VISUALIZER CONTROLLER


// Show algorithm description dynamically
algorithmSelect.addEventListener('change', () => {
    const val = algorithmSelect.value;
    heuristicGroup.style.display = val === 'a_star' ? 'flex' : 'none';
    if (algoDescText) algoDescText.textContent = algoDescriptions[val] || '';
});

// Speed slider
speedRange.addEventListener('input', (e) => {
    animationSpeed = parseInt(e.target.value);
    speedVal.textContent = `${animationSpeed}ms`;
    updateRangeFill(e.target);
});

// Grid Size Selection
gridSizeSelect.addEventListener('change', (e) => {
    if (isSimulating) return;
    gridSize = parseInt(e.target.value);

    startNode = (gridSize <= 5) ? { x: 0, y: 0 } : { x: 1, y: 1 };
    goalNode  = (gridSize <= 5) ? { x: 4, y: 4 } : { x: gridSize - 2, y: gridSize - 2 };

    clearSimulationTimeouts();
    clearPathsAndVisited();
    walls.clear();
    initPathfinderGrid();
    writeLog(`Ukuran grid diubah menjadi ${gridSize}x${gridSize}.`, 'info');
});


// INITIALIZE PATHFINDER GRID

function initPathfinderGrid() {
    mainGrid.innerHTML = '';
    cellCache.clear();
    lastAgentCell = null;

    document.documentElement.style.setProperty('--grid-cols', gridSize);

    const fragment = document.createDocumentFragment();

    for (let y = 0; y < gridSize; y++) {
        for (let x = 0; x < gridSize; x++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.x = x;
            cell.dataset.y = y;

            cellCache.set(`${x},${y}`, cell);
            updateCellVisuals(cell, x, y);

            cell.addEventListener('mousedown', (e) => handleMouseDown(e, x, y));
            cell.addEventListener('mouseenter', () => handleMouseEnter(x, y));

            fragment.appendChild(cell);
        }
    }

    mainGrid.appendChild(fragment);

    document.onmouseup = () => {
        isDrawingWalls = false;
        isMovingStart  = false;
        isMovingGoal   = false;
    };
}

function updateCellVisuals(cell, x, y) {
    cell.classList.remove('cell-wall', 'cell-start', 'cell-goal', 'cell-visited', 'cell-path', 'cell-agent');

    if (x === startNode.x && y === startNode.y) {
        cell.classList.add('cell-start');
    } else if (x === goalNode.x && y === goalNode.y) {
        cell.classList.add('cell-goal');
    } else if (walls.has(`${x},${y}`)) {
        cell.classList.add('cell-wall');
    }
}


// MOUSE HANDLERS

function handleMouseDown(e, x, y) {
    if (isSimulating) return;
    e.preventDefault();

    if (x === startNode.x && y === startNode.y) {
        isMovingStart = true;
    } else if (x === goalNode.x && y === goalNode.y) {
        isMovingGoal = true;
    } else {
        isDrawingWalls = true;
        toggleWall(x, y);
    }
}

function handleMouseEnter(x, y) {
    if (isSimulating) return;
    if ((x === startNode.x && y === startNode.y) || (x === goalNode.x && y === goalNode.y)) return;

    if (isMovingStart) {
        if (!walls.has(`${x},${y}`) && !(x === goalNode.x && y === goalNode.y)) {
            startNode = { x, y };
            syncGridVisuals();
        }
    } else if (isMovingGoal) {
        if (!walls.has(`${x},${y}`) && !(x === startNode.x && y === startNode.y)) {
            goalNode = { x, y };
            syncGridVisuals();
        }
    } else if (isDrawingWalls) {
        toggleWall(x, y);
    }
}

function toggleWall(x, y) {
    const key = `${x},${y}`;
    if (walls.has(key)) {
        walls.delete(key);
    } else {
        walls.add(key);
    }
    // Only update the affected cell, not the whole grid
    const cell = cellCache.get(key);
    if (cell) updateCellVisuals(cell, x, y);
}

// Full grid re-sync (used only during start/goal drag)
function syncGridVisuals() {
    const sKey = `${startNode.x},${startNode.y}`;
    const gKey = `${goalNode.x},${goalNode.y}`;

    for (const [key, cell] of cellCache) {
        if (key === sKey) {
            cell.className = 'grid-cell cell-start';
        } else if (key === gKey) {
            cell.className = 'grid-cell cell-goal';
        } else if (walls.has(key)) {
            cell.className = 'grid-cell cell-wall';
        } else {
            // Keep path/visited classes intact during drag
            cell.classList.remove('cell-start', 'cell-goal', 'cell-wall', 'cell-agent');
        }
    }
}

function clearPathsAndVisited() {
    for (const cell of cellCache.values()) {
        cell.classList.remove('cell-visited', 'cell-path', 'cell-agent');
    }
    if (lastAgentCell) {
        lastAgentCell.classList.remove('cell-agent');
        lastAgentCell = null;
    }
    statVisited.textContent = '0';
    statCost.textContent    = '0';
    statTime.textContent    = '0 ms';
}

function clearSimulationTimeouts() {
    for (const id of animationTimeoutIds) clearTimeout(id);
    animationTimeoutIds = [];
}

// Get cell from cache instead of querySelector
function getCellElement(x, y) {
    return cellCache.get(`${x},${y}`) || null;
}


// PATHFINDING API TRIGGER

btnFindPath.addEventListener('click', () => {
    if (isSimulating) return;

    clearSimulationTimeouts();
    clearPathsAndVisited();

    const algorithm    = algorithmSelect.value;
    const heuristic    = heuristicSelect.value;
    const wallArray    = Array.from(walls).map(w => w.split(',').map(Number));

    // Loading state on button
    const btnLabel = btnFindPath.querySelector('.btn-label');
    const origText = btnLabel ? btnLabel.textContent : 'Temukan Jalur';
    if (btnLabel) btnLabel.textContent = 'Memproses...';
    btnFindPath.disabled = true;

    statStatus.textContent = 'RUNNING';
    statStatus.style.color = 'var(--accent-yellow)';
    isSimulating = true;
    writeLog(`Menjalankan algoritma ${algorithm.replace('_', ' ').toUpperCase()}...`, 'info');

    fetch('/api/pathfind', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            grid_size: gridSize,
            start:     [startNode.x, startNode.y],
            goal:      [goalNode.x,  goalNode.y],
            walls:     wallArray,
            algorithm: algorithm,
            heuristic: heuristic
        })
    })
    .then(res => res.json())
    .then(data => {
        // Restore button
        if (btnLabel) btnLabel.textContent = origText;
        btnFindPath.disabled = false;
        animatePathfinding(data.visited, data.path, data.execution_time_ms, data.cost);
    })
    .catch(err => {
        console.error(err);
        if (btnLabel) btnLabel.textContent = origText;
        btnFindPath.disabled = false;
        isSimulating = false;
        statStatus.textContent = 'ERROR';
        statStatus.style.color = '#ef4444';
        writeLog('Gagal menghubungkan ke backend API!', 'error');
    });
});


// PATHFINDING ANIMATION

function animatePathfinding(visited, path, timeMs, cost) {
    if (visited.length === 0) {
        isSimulating = false;
        statStatus.textContent = 'NO PATH';
        statStatus.style.color = '#ef4444';
        writeLog('Jalur tidak ditemukan!', 'error');
        return;
    }

    let step = 0;
    const visitedLen = visited.length;

    function drawVisitedNode() {
        if (step < visitedLen) {
            const [vx, vy] = visited[step];
            if (!(vx === startNode.x && vy === startNode.y) && !(vx === goalNode.x && vy === goalNode.y)) {
                const cell = getCellElement(vx, vy);
                if (cell) cell.classList.add('cell-visited');
            }
            statVisited.textContent = step + 1;
            step++;
            animationTimeoutIds.push(setTimeout(drawVisitedNode, animationSpeed));
        } else {
            if (path.length > 0) {
                animatePath(path, timeMs, cost);
            } else {
                isSimulating = false;
                statStatus.textContent = 'NO PATH';
                statStatus.style.color = '#ef4444';
                writeLog('Jalur terhalang sepenuhnya oleh dinding!', 'warning');
            }
        }
    }

    drawVisitedNode();
}

function animatePath(path, timeMs, cost) {
    let step = 0;
    const pathLen = path.length;

    function drawPathNode() {
        if (step < pathLen) {
            const [px, py] = path[step];
            if (!(px === startNode.x && py === startNode.y) && !(px === goalNode.x && py === goalNode.y)) {
                const cell = getCellElement(px, py);
                if (cell) cell.classList.add('cell-path');
            }
            step++;
            animationTimeoutIds.push(setTimeout(drawPathNode, animationSpeed * 1.5));
        } else {
            animateAgentMovement(path, timeMs, cost);
        }
    }

    drawPathNode();
}

function animateAgentMovement(path, timeMs, cost) {
    let step = 0;
    const pathLen = path.length;
    writeLog('Jalur ditemukan! Agen mulai bergerak.', 'success');

    function moveAgentStep() {
        if (step < pathLen) {
            // Clear previous agent position using cached reference
            if (lastAgentCell) {
                lastAgentCell.classList.remove('cell-agent');
            }

            const [ax, ay] = path[step];
            const cell = getCellElement(ax, ay);
            if (cell) {
                cell.classList.add('cell-agent');
                lastAgentCell = cell;
            }
            step++;
            animationTimeoutIds.push(setTimeout(moveAgentStep, 140));
        } else {
            isSimulating = false;
            statStatus.textContent = 'ARRIVED';
            statStatus.style.color = 'var(--accent-green)';
            statCost.textContent   = cost;
            statTime.textContent   = `${timeMs} ms`;
            writeLog(`Agen sukses mencapai tujuan dalam ${cost} langkah (${timeMs}ms)! Memulai Mini Game...`, 'success');

            animationTimeoutIds.push(setTimeout(() => {
                openMiniGame();
            }, 600));
        }
    }

    moveAgentStep();
}


// CONTROL BUTTON EVENTS

btnClearPath.addEventListener('click', () => {
    if (isSimulating) return;
    clearSimulationTimeouts();
    clearPathsAndVisited();
    statStatus.textContent = 'IDLE';
    statStatus.style.color = 'var(--accent-cyan)';
    writeLog('Layar simulasi dibersihkan.', 'info');
});

btnResetGrid.addEventListener('click', () => {
    if (isSimulating) return;
    clearSimulationTimeouts();
    clearPathsAndVisited();
    walls.clear();

    startNode = (gridSize <= 5) ? { x: 0, y: 0 } : { x: 1, y: 1 };
    goalNode  = (gridSize <= 5) ? { x: 4, y: 4 } : { x: gridSize - 2, y: gridSize - 2 };

    initPathfinderGrid();
    statStatus.textContent = 'IDLE';
    statStatus.style.color = 'var(--accent-cyan)';
    writeLog('Grid direset ke kondisi awal.', 'warning');
});


// KEYBOARD SHORTCUTS

document.addEventListener('keydown', (e) => {
    // Don't trigger shortcuts inside input/select elements
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'SELECT') return;

    switch (e.key.toUpperCase()) {
        case 'F':
            if (!gameModalActive && !isSimulating) btnFindPath.click();
            break;
        case 'C':
            if (!gameModalActive && !isSimulating) btnClearPath.click();
            break;
        case 'R':
            if (!gameModalActive && !isSimulating) btnResetGrid.click();
            break;
        case 'ESCAPE':
            if (gameModalActive) closeMiniGame();
            break;
        case ' ':
            e.preventDefault(); // Prevent page scroll
            if (gameModalActive && currentTurn === 'player' && !gameOverScreen.classList.contains('active')) {
                endPlayerTurn();
            }
            break;
    }
});


// MINI GAME STATE & ENGINE


btnDirectGame.addEventListener('click', () => {
    if (isSimulating) return;
    openMiniGame();
});

gameCloseBtn.addEventListener('click', closeMiniGame);

btnEndTurn.addEventListener('click', () => {
    if (currentTurn !== 'player' || gameOverScreen.classList.contains('active')) return;
    endPlayerTurn();
});

function openMiniGame() {
    gameModalActive = true;
    gameModal.classList.add('active');
    initMiniGame();
    writeLog('Mini game dimulai!', 'info');
}

function closeMiniGame() {
    gameModalActive = false;
    gameModal.classList.remove('active');
    writeLog('Mini game ditutup.', 'info');
}


// INIT MINI GAME

function initMiniGame() {
    gameOverScreen.classList.remove('active');
    battleLog.innerHTML = '<div class="battle-log-entry" style="color: var(--color-text-muted);">Duel dimulai! Gunakan AP Anda dengan bijak.</div>';

    gameState = {
        ai_hp:         maxHP,
        ai_pos:        [4, 4],
        ai_shield:     false,
        ai_heal_cd:    0,
        player_hp:     maxHP,
        player_pos:    [0, 0],
        player_shield: false
    };

    playerAP           = 3;
    playerHealCooldown = 0;
    currentTurn        = 'player';
    selectedSkill      = null;

    // Generate 3 random wall obstacles
    const possibleWalls = [
        [1, 1], [1, 2], [1, 3],
        [2, 2],
        [3, 1], [3, 2], [3, 3],
        [2, 0], [2, 4]
    ];
    const shuffled = [...possibleWalls].sort(() => 0.5 - Math.random());
    gameWalls = shuffled.slice(0, 3);

    renderBattleGrid();
    updateGameHUD();
}


// RENDER BATTLE GRID

function renderBattleGrid() {
    battleGrid.innerHTML = '';
    battleCellCache.clear();

    const fragment = document.createDocumentFragment();

    for (let y = 0; y < 5; y++) {
        for (let x = 0; x < 5; x++) {
            const cell = document.createElement('div');
            cell.className = 'arena-cell';
            cell.dataset.x = x;
            cell.dataset.y = y;

            battleCellCache.set(`${x},${y}`, cell);

            if (isGameWall(x, y)) {
                cell.style.backgroundColor = 'var(--bg-tertiary)';
                cell.style.borderColor = 'rgba(255,255,255,0.08)';
                cell.textContent = '⚙';
                cell.style.fontSize = '1.2rem';
            } else if (x === gameState.player_pos[0] && y === gameState.player_pos[1]) {
                const char = document.createElement('div');
                char.className = 'game-char char-player';
                char.textContent = '🤖';
                if (gameState.player_shield) char.classList.add('shield-active');
                cell.appendChild(char);
            } else if (x === gameState.ai_pos[0] && y === gameState.ai_pos[1]) {
                const char = document.createElement('div');
                char.className = 'game-char char-enemy';
                char.textContent = '👾';
                if (gameState.ai_shield) char.classList.add('shield-active');
                cell.appendChild(char);
            }

            cell.addEventListener('click', () => handleBattleCellClick(x, y));
            fragment.appendChild(cell);
        }
    }

    battleGrid.appendChild(fragment);
}

function isGameWall(x, y) {
    return gameWalls.some(w => w[0] === x && w[1] === y);
}

// Use cache instead of querySelector
function getBattleCellElement(x, y) {
    return battleCellCache.get(`${x},${y}`) || null;
}


// UPDATE GAME HUD

function updateGameHUD() {
    // HP Bars with dynamic colors
    const playerPct = gameState.player_hp;
    const enemyPct  = gameState.ai_hp;

    playerHpBar.style.width = `${playerPct}%`;
    playerHpText.textContent = `${gameState.player_hp} / ${maxHP} HP`;
    playerHpBar.classList.remove('hp-warning', 'hp-critical');
    if (playerPct <= 25) {
        playerHpBar.classList.add('hp-critical');
    } else if (playerPct <= 50) {
        playerHpBar.classList.add('hp-warning');
    }

    enemyHpBar.style.width = `${enemyPct}%`;
    enemyHpText.textContent = `${gameState.ai_hp} / ${maxHP} HP`;
    enemyHpBar.classList.remove('hp-warning', 'hp-critical');
    if (enemyPct <= 25) {
        enemyHpBar.classList.add('hp-critical');
    } else if (enemyPct <= 50) {
        enemyHpBar.classList.add('hp-warning');
    }

    // Shield badges
    playerShieldBadge.style.display = gameState.player_shield ? 'inline-block' : 'none';
    enemyShieldBadge.style.display  = gameState.ai_shield ? 'inline-block' : 'none';

    // Turn indicator
    const isPlayerTurn = currentTurn === 'player';
    turnIndicator.textContent = isPlayerTurn ? 'GILIRAN ANDA' : 'GILIRAN LAWAN';
    turnIndicator.className   = `turn-text ${isPlayerTurn ? 'player-turn' : 'enemy-turn'}`;
    turnStatusCard.classList.toggle('enemy-turn-active', !isPlayerTurn);

    // AP nodes
    apIndicator.innerHTML = '';
    for (let i = 0; i < 3; i++) {
        const apNode = document.createElement('div');
        if (isPlayerTurn) {
            apNode.className = `ap-node ${i < playerAP ? 'active' : ''}`;
        } else {
            apNode.className = 'ap-node enemy-active';
        }
        apIndicator.appendChild(apNode);
    }

    // Skill button states
    skillMove.classList.toggle('btn-primary', selectedSkill === 'move');
    skillAttack.classList.toggle('btn-primary', selectedSkill === 'attack');

    // Disable skill buttons on enemy turn or insufficient AP
    const isMyTurn = currentTurn === 'player';
    skillMove.disabled   = !isMyTurn || playerAP < 1;
    skillAttack.disabled = !isMyTurn || playerAP < 2;
    skillShield.disabled = !isMyTurn || playerAP < 1;
    skillHeal.disabled   = !isMyTurn || playerAP < 2 || playerHealCooldown > 0;
    btnEndTurn.disabled  = !isMyTurn;

    // Heal cooldown overlay
    if (playerHealCooldown > 0) {
        healCooldownOverlay.style.display = 'flex';
        healCooldownOverlay.textContent   = `CD: ${playerHealCooldown}`;
    } else {
        healCooldownOverlay.style.display = 'none';
    }
}


// SKILL ACTION EVENTS

skillMove.addEventListener('click', () => {
    if (currentTurn !== 'player' || playerAP < 1) return;
    selectedSkill = (selectedSkill === 'move') ? null : 'move';
    highlightTargets();
    updateGameHUD();
});

skillAttack.addEventListener('click', () => {
    if (currentTurn !== 'player' || playerAP < 2) return;
    selectedSkill = (selectedSkill === 'attack') ? null : 'attack';
    highlightTargets();
    updateGameHUD();
});

skillShield.addEventListener('click', () => {
    if (currentTurn !== 'player' || playerAP < 1) return;
    gameState.player_shield = true;
    playerAP -= 1;
    selectedSkill = null;
    logBattleEvent('Pemain mengaktifkan SHIELD! (Damage -50%)', 'player');
    triggerFloatNumber(gameState.player_pos[0], gameState.player_pos[1], 'SHIELD', 'shield-num');
    renderBattleGrid();
    highlightTargets();
    updateGameHUD();
    checkTurnAutoEnd();
});

skillHeal.addEventListener('click', () => {
    if (currentTurn !== 'player' || playerAP < 2 || playerHealCooldown > 0) return;
    gameState.player_hp = Math.min(100, gameState.player_hp + 25);
    playerAP -= 2;
    playerHealCooldown = 3;
    selectedSkill = null;
    logBattleEvent('Pemain melakukan HEAL! (+25 HP)', 'player');
    triggerFloatNumber(gameState.player_pos[0], gameState.player_pos[1], '+25 HP', 'heal-num');
    renderBattleGrid();
    highlightTargets();
    updateGameHUD();
    checkTurnAutoEnd();
});


// TARGET HIGHLIGHTING

function highlightTargets() {
    // Clear all highlights efficiently using cache
    for (const cell of battleCellCache.values()) {
        cell.classList.remove('cell-move-target', 'cell-attack-target');
    }

    if (selectedSkill === 'move') {
        const adjacent = getAdjacentGameCells(gameState.player_pos);
        for (const [ax, ay] of adjacent) {
            const cell = getBattleCellElement(ax, ay);
            if (cell) cell.classList.add('cell-move-target');
        }
    } else if (selectedSkill === 'attack') {
        const dist_x = Math.abs(gameState.player_pos[0] - gameState.ai_pos[0]);
        const dist_y = Math.abs(gameState.player_pos[1] - gameState.ai_pos[1]);
        if (Math.max(dist_x, dist_y) <= 1) {
            const cell = getBattleCellElement(gameState.ai_pos[0], gameState.ai_pos[1]);
            if (cell) cell.classList.add('cell-attack-target');
        }
    }
}

function getAdjacentGameCells(pos) {
    const [x, y] = pos;
    return [
        [x + 1, y], [x - 1, y], [x, y + 1], [x, y - 1]
    ].filter(([nx, ny]) =>
        nx >= 0 && nx < 5 && ny >= 0 && ny < 5 &&
        !isGameWall(nx, ny) &&
        !(nx === gameState.ai_pos[0] && ny === gameState.ai_pos[1])
    );
}


// BATTLE CELL CLICK

function handleBattleCellClick(x, y) {
    if (currentTurn !== 'player') return;

    if (selectedSkill === 'move') {
        const adjacent = getAdjacentGameCells(gameState.player_pos);
        const isValid = adjacent.some(([cx, cy]) => cx === x && cy === y);
        if (isValid) {
            gameState.player_pos = [x, y];
            playerAP -= 1;
            selectedSkill = null;
            logBattleEvent(`Pemain bergerak ke (${x}, ${y})`, 'player');
            renderBattleGrid();
            highlightTargets();
            updateGameHUD();
            checkTurnAutoEnd();
        }
    } else if (selectedSkill === 'attack') {
        if (x === gameState.ai_pos[0] && y === gameState.ai_pos[1]) {
            const dist_x = Math.abs(gameState.player_pos[0] - gameState.ai_pos[0]);
            const dist_y = Math.abs(gameState.player_pos[1] - gameState.ai_pos[1]);
            if (Math.max(dist_x, dist_y) <= 1) {
                playerAP -= 2;
                selectedSkill = null;

                let damage = Math.floor(Math.random() * 6) + 20;
                if (gameState.ai_shield) damage = Math.floor(damage / 2);

                gameState.ai_hp = Math.max(0, gameState.ai_hp - damage);
                logBattleEvent(`Serangan! Guardian terkena ${damage} damage.`, 'player');
                triggerFloatNumber(gameState.ai_pos[0], gameState.ai_pos[1], `-${damage}`, 'damage-num');

                const enemyCell = getBattleCellElement(gameState.ai_pos[0], gameState.ai_pos[1]);
                if (enemyCell) {
                    enemyCell.classList.add('shake');
                    setTimeout(() => enemyCell.classList.remove('shake'), 350);
                }

                renderBattleGrid();
                highlightTargets();
                updateGameHUD();
                if (checkGameEnd()) return;
                checkTurnAutoEnd();
            }
        }
    }
}

function checkTurnAutoEnd() {
    if (playerAP <= 0) endPlayerTurn();
}

function endPlayerTurn() {
    currentTurn   = 'enemy';
    selectedSkill = null;
    highlightTargets();
    updateGameHUD();
    logBattleEvent('Giliran Anda berakhir. AI Guardian berpikir...', 'enemy');

    setTimeout(runEnemyAI, 900);
}


// ENEMY AI SIMULATION & EXECUTION

function runEnemyAI() {
    fetch('/api/game/ai-move', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            game_state: gameState,
            walls: gameWalls
        })
    })
    .then(res => res.json())
    .then(data => {
        executeEnemyActions(data.actions, data.game_state);
    })
    .catch(err => {
        console.error(err);
        logBattleEvent('Koneksi AI gagal, Guardian bertahan.', 'enemy');
        gameState.ai_shield = true;
        currentTurn = 'player';
        replenishPlayerAP();
        renderBattleGrid();
        updateGameHUD();
    });
}

function executeEnemyActions(actions, nextState) {
    let index = 0;
    gameState.ai_shield = false;

    function runNextAction() {
        if (index < actions.length) {
            const action = actions[index];

            if (action.type === 'move') {
                gameState.ai_pos = action.target;
                logBattleEvent(`Guardian bergerak ke (${action.target[0]}, ${action.target[1]})`, 'enemy');
                renderBattleGrid();
            } else if (action.type === 'attack') {
                const damage = action.damage;
                gameState.player_hp = Math.max(0, gameState.player_hp - damage);
                logBattleEvent(`Guardian MENYERANG! Anda terkena ${damage} damage.`, 'enemy');
                triggerFloatNumber(gameState.player_pos[0], gameState.player_pos[1], `-${damage}`, 'damage-num');
                const playerCell = getBattleCellElement(gameState.player_pos[0], gameState.player_pos[1]);
                if (playerCell) {
                    playerCell.classList.add('shake');
                    setTimeout(() => playerCell.classList.remove('shake'), 350);
                }
                renderBattleGrid();
                updateGameHUD();
            } else if (action.type === 'shield') {
                gameState.ai_shield = true;
                logBattleEvent('Guardian mengaktifkan SHIELD!', 'enemy');
                triggerFloatNumber(gameState.ai_pos[0], gameState.ai_pos[1], 'SHIELD', 'shield-num');
                renderBattleGrid();
                updateGameHUD();
            } else if (action.type === 'heal') {
                gameState.ai_hp = Math.min(100, gameState.ai_hp + action.amount);
                logBattleEvent(`Guardian menggunakan HEAL! (+${action.amount} HP)`, 'enemy');
                triggerFloatNumber(gameState.ai_pos[0], gameState.ai_pos[1], `+${action.amount} HP`, 'heal-num');
                renderBattleGrid();
                updateGameHUD();
            }

            index++;
            setTimeout(runNextAction, 850);
        } else {
            // Sync full final state from server
            gameState = nextState;
            renderBattleGrid();
            updateGameHUD();
            if (checkGameEnd()) return;

            currentTurn = 'player';
            replenishPlayerAP();
            updateGameHUD();
            logBattleEvent('Giliran Anda! Pilih aksi di panel strategi.', 'player');
        }
    }

    runNextAction();
}

function replenishPlayerAP() {
    playerAP = 3;
    gameState.player_shield = false;
    if (playerHealCooldown > 0) playerHealCooldown--;
}


// GAME MECHANICS HELPERS

function logBattleEvent(msg, sender) {
    const entry = document.createElement('div');
    entry.className = 'battle-log-entry';

    if (sender === 'player') {
        entry.style.color = 'var(--accent-cyan)';
        entry.textContent = `▶ ${msg}`;
    } else if (sender === 'enemy') {
        entry.style.color = '#ef4444';
        entry.textContent = `◀ ${msg}`;
    } else {
        entry.style.color = 'var(--color-text-muted)';
        entry.textContent = msg;
    }

    battleLog.appendChild(entry);
    // Limit log size
    while (battleLog.children.length > 50) {
        battleLog.removeChild(battleLog.firstChild);
    }
    battleLog.scrollTop = battleLog.scrollHeight;
}

function triggerFloatNumber(x, y, text, className) {
    const cell = getBattleCellElement(x, y);
    if (!cell) return;

    const floatEl = document.createElement('span');
    floatEl.className = `floating-number ${className}`;
    floatEl.textContent = text;
    cell.appendChild(floatEl);

    setTimeout(() => floatEl.remove(), 1250);
}

function checkGameEnd() {
    if (gameState.player_hp <= 0) {
        showGameOver(false);
        return true;
    } else if (gameState.ai_hp <= 0) {
        showGameOver(true);
        return true;
    }
    return false;
}

function showGameOver(isVictory) {
    gameOverScreen.classList.add('active');
    if (isVictory) {
        gameOverTitle.textContent = 'VICTORY';
        gameOverTitle.className   = 'victory-title';
        gameOverMsg.textContent   = 'Luar biasa! Anda berhasil mengalahkan Guardian Cerdas dan mengamankan titik Goal!';
        writeLog('Pemain MEMENANGKAN mini game! 🏆', 'success');
    } else {
        gameOverTitle.textContent = 'DEFEAT';
        gameOverTitle.className   = 'defeat-title';
        gameOverMsg.textContent   = 'Sayang sekali, Anda dikalahkan oleh Guardian. Klik Main Lagi untuk bertanding ulang!';
        writeLog('Pemain DIKALAHKAN dalam mini game.', 'error');
    }
}

gameRestartBtn.addEventListener('click', initMiniGame);
gameExitBtn.addEventListener('click', closeMiniGame);


// INITIALIZE APPLICATION

document.addEventListener('DOMContentLoaded', () => {
    // Initialize grid
    initPathfinderGrid();

    // Initialize range slider fill
    updateRangeFill(speedRange);

    // Set initial algorithm description
    if (algoDescText) {
        algoDescText.textContent = algoDescriptions[algorithmSelect.value];
    }

    writeLog('Selamat datang! Mulai dengan menggambar dinding, lalu tekan "Temukan Jalur" atau tekan [F].', 'info');
});
