import re
import streamlit as st
import streamlit.components.v1 as components

# ─────────────────────────────────────────────
# Page config
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Navigasi Agen Cerdas & Mini-Game Strategi",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide Streamlit chrome so the custom UI fills the viewport
st.markdown(
    """
    <style>
        #MainMenu, footer, header { visibility: hidden; }
        .block-container { padding: 0 !important; max-width: 100% !important; }
        iframe { border: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# Read external assets (paths relative to repo root)
# ─────────────────────────────────────────────
with open("static/css/style.css", encoding="utf-8") as f:
    CSS = f.read()

with open("static/js/main.js", encoding="utf-8") as f:
    ORIGINAL_JS = f.read()

# ─────────────────────────────────────────────
# Browser-side algorithm implementations
# These replace the Flask /api/* endpoints by
# intercepting fetch() calls inside the iframe.
# ─────────────────────────────────────────────
ALGO_JS = r"""
// ================================================================
// PATHFINDING ALGORITHMS  (browser-side, mirrors Python backend)
// ================================================================

function getNeighbors(node, gridSize, wallsSet) {
    const [x, y] = node;
    const neighbors = [];
    for (const [dx, dy] of [[0,-1],[0,1],[-1,0],[1,0]]) {
        const nx = x + dx, ny = y + dy;
        if (nx >= 0 && nx < gridSize && ny >= 0 && ny < gridSize) {
            if (!wallsSet.has(nx + "," + ny)) neighbors.push([nx, ny]);
        }
    }
    return neighbors;
}

function reconstructPath(cameFrom, current) {
    const path = [current];
    while (cameFrom.has(String(current))) {
        current = cameFrom.get(String(current));
        path.push(current);
    }
    path.reverse();
    return path;
}

function bfsSearch(gridSize, start, goal, wallsSet) {
    const visitedOrder = [];
    const cameFrom = new Map();
    const queue = [start];
    const visitedSet = new Set([String(start)]);
    let found = false;

    while (queue.length) {
        const current = queue.shift();
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        for (const nb of getNeighbors(current, gridSize, wallsSet)) {
            const key = String(nb);
            if (!visitedSet.has(key)) {
                visitedSet.add(key);
                cameFrom.set(key, current);
                queue.push(nb);
            }
        }
    }
    return { visited: visitedOrder, path: found ? reconstructPath(cameFrom, goal) : [] };
}

function dfsSearch(gridSize, start, goal, wallsSet) {
    const visitedOrder = [];
    const cameFrom = new Map();
    const stack = [start];
    const frontierSet = new Set([String(start)]);
    const visitedSet = new Set();
    let found = false;

    while (stack.length) {
        const current = stack.pop();
        const cKey = String(current);
        frontierSet.delete(cKey);
        if (visitedSet.has(cKey)) continue;
        visitedSet.add(cKey);
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        const neighbors = getNeighbors(current, gridSize, wallsSet);
        for (let i = neighbors.length - 1; i >= 0; i--) {
            const nb = neighbors[i];
            const nKey = String(nb);
            if (!visitedSet.has(nKey) && !frontierSet.has(nKey)) {
                cameFrom.set(nKey, current);
                stack.push(nb);
                frontierSet.add(nKey);
            }
        }
    }
    return { visited: visitedOrder, path: found ? reconstructPath(cameFrom, goal) : [] };
}

function dijkstraSearch(gridSize, start, goal, wallsSet) {
    const visitedOrder = [];
    const cameFrom = new Map();
    const gScore = new Map([[String(start), 0]]);
    const heap = [[0, start]];
    const visitedSet = new Set();
    let found = false;

    while (heap.length) {
        heap.sort((a, b) => a[0] - b[0]);
        const [cost, current] = heap.shift();
        const cKey = String(current);
        if (visitedSet.has(cKey)) continue;
        visitedSet.add(cKey);
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        for (const nb of getNeighbors(current, gridSize, wallsSet)) {
            const tentG = cost + 1;
            const nKey = String(nb);
            if (tentG < (gScore.get(nKey) !== undefined ? gScore.get(nKey) : Infinity)) {
                gScore.set(nKey, tentG);
                cameFrom.set(nKey, current);
                heap.push([tentG, nb]);
            }
        }
    }
    return { visited: visitedOrder, path: found ? reconstructPath(cameFrom, goal) : [] };
}

function aStarSearch(gridSize, start, goal, wallsSet, heuristicType) {
    heuristicType = heuristicType || 'manhattan';
    const gx = goal[0], gy = goal[1];
    const heuristic = heuristicType === 'euclidean'
        ? function(n) { return Math.sqrt((n[0]-gx)*(n[0]-gx) + (n[1]-gy)*(n[1]-gy)); }
        : function(n) { return Math.abs(n[0]-gx) + Math.abs(n[1]-gy); };

    const visitedOrder = [];
    const cameFrom = new Map();
    const gScore = new Map([[String(start), 0]]);
    let counter = 0;
    const heap = [[heuristic(start), counter++, start]];
    const openSetNodes = new Set([String(start)]);
    const visitedSet = new Set();
    let found = false;

    while (heap.length) {
        heap.sort(function(a, b) { return a[0] - b[0] || a[1] - b[1]; });
        const item = heap.shift();
        const current = item[2];
        const cKey = String(current);
        if (visitedSet.has(cKey)) continue;
        openSetNodes.delete(cKey);
        visitedSet.add(cKey);
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        const curG = gScore.get(cKey);
        for (const nb of getNeighbors(current, gridSize, wallsSet)) {
            const nKey = String(nb);
            if (visitedSet.has(nKey)) continue;
            const tentG = curG + 1;
            if (tentG < (gScore.get(nKey) !== undefined ? gScore.get(nKey) : Infinity)) {
                cameFrom.set(nKey, current);
                gScore.set(nKey, tentG);
                const f = tentG + heuristic(nb);
                if (!openSetNodes.has(nKey)) {
                    openSetNodes.add(nKey);
                    heap.push([f, counter++, nb]);
                }
            }
        }
    }
    return { visited: visitedOrder, path: found ? reconstructPath(cameFrom, goal) : [] };
}

// ================================================================
// MINI GAME AI ENGINE  (browser-side, mirrors Python backend)
// ================================================================

const GAME_GRID_SIZE = 5;

function gameDist(p1, p2) {
    return Math.abs(p1[0] - p2[0]) + Math.abs(p1[1] - p2[1]);
}

function evaluateState(aiHp, aiPos, aiShield, aiHealCd, playerHp, playerPos, playerShield) {
    if (playerHp <= 0) return 5000;
    if (aiHp <= 0)    return -5000;
    const dist = gameDist(aiPos, playerPos);
    const hpDiff = aiHp * 2.0 - playerHp * 2.5;
    let distUtility = 0;
    if (aiHp > 35) {
        distUtility = dist === 1 ? 50 : -dist * 10;
    } else {
        distUtility = dist * 15;
    }
    const shieldVal  = aiShield ? 15 : 0;
    const dangerVal  = (dist === 1 && !aiShield) ? -30 : 0;
    return hpDiff + distUtility + shieldVal + dangerVal;
}

function generateActionCombinations(aiHealCd) {
    const basicActions = [
        ['shield', 1], ['attack', 2], ['heal', 2],
        ['move_up', 1], ['move_down', 1], ['move_left', 1], ['move_right', 1]
    ];
    const combos = [];
    function build(seq, ap) {
        if (ap > 3) return;
        if (seq.length) combos.push(seq);
        for (let i = 0; i < basicActions.length; i++) {
            const act = basicActions[i][0], cost = basicActions[i][1];
            if (ap + cost <= 3) {
                if (act === 'heal' && aiHealCd > 0) continue;
                build(seq.concat([act]), ap + cost);
            }
        }
    }
    build([], 0);
    return combos;
}

function simulateSequence(sequence, initialState, wallsSet) {
    const state = {
        ai_hp:      initialState.ai_hp,
        ai_pos:     initialState.ai_pos.slice(),
        ai_shield:  initialState.ai_shield,
        ai_heal_cd: initialState.ai_heal_cd,
        player_hp:  initialState.player_hp,
        player_pos: initialState.player_pos.slice(),
        player_shield: initialState.player_shield
    };
    const actualActions = [];

    for (let i = 0; i < sequence.length; i++) {
        const action = sequence[i];
        if (action.indexOf('move_') === 0) {
            const dir = action.split('_')[1];
            let dx = 0, dy = 0;
            if (dir === 'up')    dy = -1;
            if (dir === 'down')  dy =  1;
            if (dir === 'left')  dx = -1;
            if (dir === 'right') dx =  1;
            const nx = state.ai_pos[0] + dx;
            const ny = state.ai_pos[1] + dy;
            if (nx < 0 || nx >= GAME_GRID_SIZE || ny < 0 || ny >= GAME_GRID_SIZE) return { valid: false };
            if (wallsSet.has(nx + "," + ny)) return { valid: false };
            if (nx === state.player_pos[0] && ny === state.player_pos[1]) return { valid: false };
            state.ai_pos = [nx, ny];
            actualActions.push({ type: 'move', target: [nx, ny] });

        } else if (action === 'attack') {
            const dx = Math.abs(state.ai_pos[0] - state.player_pos[0]);
            const dy = Math.abs(state.ai_pos[1] - state.player_pos[1]);
            if (Math.max(dx, dy) > 1) return { valid: false };
            const damage = Math.floor(Math.random() * 6) + 20;
            const actualDmg = state.player_shield ? Math.floor(damage / 2) : damage;
            state.player_hp = Math.max(0, state.player_hp - actualDmg);
            actualActions.push({ type: 'attack', damage: actualDmg });

        } else if (action === 'shield') {
            state.ai_shield = true;
            actualActions.push({ type: 'shield' });

        } else if (action === 'heal') {
            if (state.ai_heal_cd > 0) return { valid: false };
            state.ai_hp = Math.min(100, state.ai_hp + 25);
            state.ai_heal_cd = 3;
            actualActions.push({ type: 'heal', amount: 25 });
        }
    }
    return { valid: true, state: state, actions: actualActions };
}

function computeBestAiTurn(gameState, walls) {
    const wallsSet = new Set();
    for (let i = 0; i < walls.length; i++) {
        wallsSet.add(walls[i][0] + "," + walls[i][1]);
    }
    const combos = generateActionCombinations(gameState.ai_heal_cd);

    let bestActions = [];
    let bestUtility = -Infinity;
    let bestFinalState = null;

    for (let i = 0; i < combos.length; i++) {
        const result = simulateSequence(combos[i], gameState, wallsSet);
        if (result.valid) {
            const score = evaluateState(
                result.state.ai_hp, result.state.ai_pos, result.state.ai_shield,
                result.state.ai_heal_cd, result.state.player_hp, result.state.player_pos,
                result.state.player_shield
            ) + (Math.random() * 2 - 1);

            if (score > bestUtility) {
                bestUtility = score;
                bestActions = result.actions;
                bestFinalState = result.state;
            }
        }
    }

    if (!bestActions.length) {
        bestActions = [{ type: 'shield' }];
        bestFinalState = {
            ai_hp:      gameState.ai_hp,
            ai_pos:     gameState.ai_pos.slice(),
            ai_shield:  true,
            ai_heal_cd: gameState.ai_heal_cd,
            player_hp:  gameState.player_hp,
            player_pos: gameState.player_pos.slice(),
            player_shield: gameState.player_shield
        };
    }

    // Decrement cooldown (mirrors Python backend response)
    bestFinalState.ai_heal_cd = Math.max(0, bestFinalState.ai_heal_cd - 1);

    return { actions: bestActions, game_state: bestFinalState };
}

// ================================================================
// INTERCEPT fetch() so original main.js works without modification
// ================================================================
(function() {
    var _originalFetch = window.fetch.bind(window);

    window.fetch = function(url, options) {
        if (typeof url === 'string' && url.indexOf('/api/pathfind') !== -1) {
            var body = JSON.parse(options.body);
            var gridSize   = body.grid_size;
            var start      = body.start;
            var goal       = body.goal;
            var walls      = body.walls;
            var algorithm  = body.algorithm;
            var heuristic  = body.heuristic;

            var wallsSet = new Set();
            for (var i = 0; i < walls.length; i++) {
                wallsSet.add(walls[i][0] + "," + walls[i][1]);
            }

            var t0 = performance.now();
            var result;
            if      (algorithm === 'bfs')      result = bfsSearch(gridSize, start, goal, wallsSet);
            else if (algorithm === 'dfs')      result = dfsSearch(gridSize, start, goal, wallsSet);
            else if (algorithm === 'dijkstra') result = dijkstraSearch(gridSize, start, goal, wallsSet);
            else                               result = aStarSearch(gridSize, start, goal, wallsSet, heuristic);
            var execMs = +(performance.now() - t0).toFixed(3);

            var responseData = {
                visited:          result.visited,
                path:             result.path,
                execution_time_ms: execMs,
                cost:             result.path.length > 0 ? result.path.length - 1 : 0
            };
            return Promise.resolve(new Response(JSON.stringify(responseData), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            }));
        }

        if (typeof url === 'string' && url.indexOf('/api/game/ai-move') !== -1) {
            var body = JSON.parse(options.body);
            var responseData = computeBestAiTurn(body.game_state, body.walls);
            return Promise.resolve(new Response(JSON.stringify(responseData), {
                status: 200,
                headers: { 'Content-Type': 'application/json' }
            }));
        }

        return _originalFetch(url, options);
    };
})();
"""

# ─────────────────────────────────────────────
# Load and patch the HTML template
# ─────────────────────────────────────────────
with open("templates/index.html", encoding="utf-8") as f:
    HTML_TEMPLATE = f.read()

# Strip Flask Jinja2 template tags that reference static files
HTML_TEMPLATE = re.sub(
    r"<link[^>]+style\.css[^>]*>",
    "",
    HTML_TEMPLATE,
)
HTML_TEMPLATE = re.sub(
    r'<script[^>]+main\.js[^>]*></script>',
    "",
    HTML_TEMPLATE,
)

# Inline CSS inside <head>
HTML_TEMPLATE = HTML_TEMPLATE.replace(
    "</head>",
    "<style>\n" + CSS + "\n</style>\n</head>",
)

# Inject algorithm JS first, then original main.js, before </body>
HTML_TEMPLATE = HTML_TEMPLATE.replace(
    "</body>",
    "<script>\n" + ALGO_JS + "\n</script>\n"
    "<script>\n" + ORIGINAL_JS + "\n</script>\n"
    "</body>",
)

# ─────────────────────────────────────────────
# Render the self-contained app inside Streamlit
# ─────────────────────────────────────────────
components.html(HTML_TEMPLATE, height=920, scrolling=True)
