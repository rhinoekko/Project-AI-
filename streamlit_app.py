import streamlit as st
import streamlit.components.v1 as components


# Page config

st.set_page_config(
    page_title="Navigasi Agen Cerdas & Mini-Game Strategi",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Hide default Streamlit chrome so the custom UI fills the viewport
st.markdown(
    unsafe_allow_html=True,
)


# Read external assets

with open("static/css/style.css", encoding="utf-8") as f:
    CSS = f.read()

with open("static/js/main.js", encoding="utf-8") as f:
    ORIGINAL_JS = f.read()


# Extra JavaScript: pathfinding & AI algorithms
# ported to run entirely in the browser
# (replaces the Flask /api/* endpoints)

ALGO_JS = r"""

// PATHFINDING ALGORITHMS (browser-side, mirrors Python backend)


function getNeighbors(node, gridSize, wallsSet) {
    const [x, y] = node;
    const neighbors = [];
    for (const [dx, dy] of [[0,-1],[0,1],[-1,0],[1,0]]) {
        const nx = x + dx, ny = y + dy;
        if (nx >= 0 && nx < gridSize && ny >= 0 && ny < gridSize) {
            if (!wallsSet.has(`${nx},${ny}`)) neighbors.push([nx, ny]);
        }
    }
    return neighbors;
}

function reconstructPath(cameFrom, current) {
    const path = [current];
    while (cameFrom.has(`${current}`)) {
        current = cameFrom.get(`${current}`);
        path.push(current);
    }
    path.reverse();
    return path;
}

function bfsSearch(gridSize, start, goal, wallsSet) {
    const visitedOrder = [];
    const cameFrom = new Map();
    const queue = [start];
    const visitedSet = new Set([`${start}`]);
    let found = false;

    while (queue.length) {
        const current = queue.shift();
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        for (const nb of getNeighbors(current, gridSize, wallsSet)) {
            const key = `${nb}`;
            if (!visitedSet.has(key)) {
                visitedSet.add(key);
                cameFrom.set(key, current);
                queue.push(nb);
            }
        }
    }
    const path = found ? reconstructPath(cameFrom, goal) : [];
    return { visited: visitedOrder, path };
}

function dfsSearch(gridSize, start, goal, wallsSet) {
    const visitedOrder = [];
    const cameFrom = new Map();
    const stack = [start];
    const frontierSet = new Set([`${start}`]);
    const visitedSet = new Set();
    let found = false;

    while (stack.length) {
        const current = stack.pop();
        const cKey = `${current}`;
        frontierSet.delete(cKey);
        if (visitedSet.has(cKey)) continue;
        visitedSet.add(cKey);
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        const neighbors = getNeighbors(current, gridSize, wallsSet);
        for (let i = neighbors.length - 1; i >= 0; i--) {
            const nb = neighbors[i];
            const nKey = `${nb}`;
            if (!visitedSet.has(nKey) && !frontierSet.has(nKey)) {
                cameFrom.set(nKey, current);
                stack.push(nb);
                frontierSet.add(nKey);
            }
        }
    }
    const path = found ? reconstructPath(cameFrom, goal) : [];
    return { visited: visitedOrder, path };
}

function dijkstraSearch(gridSize, start, goal, wallsSet) {
    const visitedOrder = [];
    const cameFrom = new Map();
    const gScore = new Map([[`${start}`, 0]]);
    // Min-heap via simple sorted array (small grids, acceptable)
    const heap = [[0, start]];
    const visitedSet = new Set();
    let found = false;

    while (heap.length) {
        heap.sort((a, b) => a[0] - b[0]);
        const [cost, current] = heap.shift();
        const cKey = `${current}`;
        if (visitedSet.has(cKey)) continue;
        visitedSet.add(cKey);
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        for (const nb of getNeighbors(current, gridSize, wallsSet)) {
            const tentG = cost + 1;
            const nKey = `${nb}`;
            if (tentG < (gScore.get(nKey) ?? Infinity)) {
                gScore.set(nKey, tentG);
                cameFrom.set(nKey, current);
                heap.push([tentG, nb]);
            }
        }
    }
    const path = found ? reconstructPath(cameFrom, goal) : [];
    return { visited: visitedOrder, path };
}

function aStarSearch(gridSize, start, goal, wallsSet, heuristicType = 'manhattan') {
    const [gx, gy] = goal;
    const heuristic = heuristicType === 'euclidean'
        ? ([x, y]) => Math.sqrt((x - gx) ** 2 + (y - gy) ** 2)
        : ([x, y]) => Math.abs(x - gx) + Math.abs(y - gy);

    const visitedOrder = [];
    const cameFrom = new Map();
    const gScore = new Map([[`${start}`, 0]]);
    const fScore = new Map([[`${start}`, heuristic(start)]]);
    let counter = 0;
    const heap = [[fScore.get(`${start}`), counter++, start]];
    const openSetNodes = new Set([`${start}`]);
    const visitedSet = new Set();
    let found = false;

    while (heap.length) {
        heap.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
        const [, , current] = heap.shift();
        const cKey = `${current}`;
        if (visitedSet.has(cKey)) continue;
        openSetNodes.delete(cKey);
        visitedSet.add(cKey);
        visitedOrder.push(current);
        if (current[0] === goal[0] && current[1] === goal[1]) { found = true; break; }
        const curG = gScore.get(cKey);
        for (const nb of getNeighbors(current, gridSize, wallsSet)) {
            if (visitedSet.has(`${nb}`)) continue;
            const tentG = curG + 1;
            const nKey = `${nb}`;
            if (tentG < (gScore.get(nKey) ?? Infinity)) {
                cameFrom.set(nKey, current);
                gScore.set(nKey, tentG);
                const f = tentG + heuristic(nb);
                fScore.set(nKey, f);
                if (!openSetNodes.has(nKey)) {
                    openSetNodes.add(nKey);
                    heap.push([f, counter++, nb]);
                }
            }
        }
    }
    const path = found ? reconstructPath(cameFrom, goal) : [];
    return { visited: visitedOrder, path };
}


// MINI GAME AI ENGINE (browser-side, mirrors Python backend)


const GAME_GRID_SIZE = 5;

function gameDist(p1, p2) {
    return Math.abs(p1[0] - p2[0]) + Math.abs(p1[1] - p2[1]);
}

function evaluateState(aiHp, aiPos, aiShield, aiHealCd, playerHp, playerPos, playerShield) {
    if (playerHp <= 0) return 5000;
    if (aiHp <= 0) return -5000;
    const dist = gameDist(aiPos, playerPos);
    const hpDiff = aiHp * 2.0 - playerHp * 2.5;
    let distUtility = 0;
    if (aiHp > 35) {
        distUtility = dist === 1 ? 50 : -dist * 10;
    } else {
        distUtility = dist * 15;
    }
    const shieldVal = aiShield ? 15 : 0;
    const dangerVal = (dist === 1 && !aiShield) ? -30 : 0;
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
        for (const [act, cost] of basicActions) {
            if (ap + cost <= 3) {
                if (act === 'heal' && aiHealCd > 0) continue;
                build([...seq, act], ap + cost);
            }
        }
    }
    build([], 0);
    return combos;
}

function simulateSequence(sequence, initialState, wallsSet) {
    const state = {
        ai_hp: initialState.ai_hp,
        ai_pos: [...initialState.ai_pos],
        ai_shield: initialState.ai_shield,
        ai_heal_cd: initialState.ai_heal_cd,
        player_hp: initialState.player_hp,
        player_pos: [...initialState.player_pos],
        player_shield: initialState.player_shield
    };
    const actualActions = [];

    for (const action of sequence) {
        if (action.startsWith('move_')) {
            const dir = action.split('_')[1];
            let dx = 0, dy = 0;
            if (dir === 'up')    dy = -1;
            if (dir === 'down')  dy =  1;
            if (dir === 'left')  dx = -1;
            if (dir === 'right') dx =  1;
            const nx = state.ai_pos[0] + dx;
            const ny = state.ai_pos[1] + dy;
            if (nx < 0 || nx >= GAME_GRID_SIZE || ny < 0 || ny >= GAME_GRID_SIZE) return { valid: false };
            if (wallsSet.has(`${nx},${ny}`)) return { valid: false };
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
    return { valid: true, state, actions: actualActions };
}

function computeBestAiTurn(gameState, walls) {
    const wallsSet = new Set(walls.map(w => `${w[0]},${w[1]}`));
    const combos = generateActionCombinations(gameState.ai_heal_cd);

    let bestActions = [];
    let bestUtility = -Infinity;
    let bestFinalState = null;

    for (const combo of combos) {
        const result = simulateSequence(combo, gameState, wallsSet);
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
        bestFinalState = { ...gameState, ai_shield: true, ai_pos: [...gameState.ai_pos] };
    }

    // Decrement cooldown in final state (mirrors Python backend)
    bestFinalState.ai_heal_cd = Math.max(0, bestFinalState.ai_heal_cd - 1);

    return { actions: bestActions, game_state: bestFinalState };
}


// INTERCEPT fetch() calls so original main.js works unchanged


const _originalFetch = window.fetch.bind(window);

window.fetch = async function(url, options) {
    // ── /api/pathfind ──────────────────────────────────────────
    if (typeof url === 'string' && url.includes('/api/pathfind')) {
        const body = JSON.parse(options.body);
        const { grid_size, start, goal, walls, algorithm, heuristic } = body;
        const wallsSet = new Set(walls.map(w => `${w[0]},${w[1]}`));

        const t0 = performance.now();
        let result;
        if (algorithm === 'bfs')      result = bfsSearch(grid_size, start, goal, wallsSet);
        else if (algorithm === 'dfs') result = dfsSearch(grid_size, start, goal, wallsSet);
        else if (algorithm === 'dijkstra') result = dijkstraSearch(grid_size, start, goal, wallsSet);
        else                          result = aStarSearch(grid_size, start, goal, wallsSet, heuristic);
        const execMs = +(performance.now() - t0).toFixed(3);

        const responseData = {
            visited: result.visited,
            path: result.path,
            execution_time_ms: execMs,
            cost: result.path.length > 0 ? result.path.length - 1 : 0
        };
        return new Response(JSON.stringify(responseData), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    // ── /api/game/ai-move ──────────────────────────────────────
    if (typeof url === 'string' && url.includes('/api/game/ai-move')) {
        const body = JSON.parse(options.body);
        const responseData = computeBestAiTurn(body.game_state, body.walls);
        return new Response(JSON.stringify(responseData), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
        });
    }

    // Fallthrough for any other fetch
    return _originalFetch(url, options);
};
"""


# Read and inline the HTML template,
# replacing Flask template tags with raw values

with open("templates/index.html", encoding="utf-8") as f:
    HTML_TEMPLATE = f.read()

# Replace Flask static references and build a fully self-contained page
HTML_TEMPLATE = HTML_TEMPLATE.replace(
    '{{ url_for(\'static\', filename=\'css/style.css\') }}', ''
).replace(
    '{{ url_for(\'static\', filename=\'js/main.js\') }}', ''
)

# Remove the external stylesheet link and script tag (we'll inline them)
import re
HTML_TEMPLATE = re.sub(r'<link[^>]+style\.css[^>]*>', '', HTML_TEMPLATE)
HTML_TEMPLATE = re.sub(r'<script[^>]+main\.js[^>]*></script>', '', HTML_TEMPLATE)

# Inject CSS and JS inline before </head> and before </body>
HTML_TEMPLATE = HTML_TEMPLATE.replace(
    '</head>',
    f'<style>\n{CSS}\n</style>\n</head>'
)
HTML_TEMPLATE = HTML_TEMPLATE.replace(
    '</body>',
    f'<script>\n{ALGO_JS}\n</script>\n<script>\n{ORIGINAL_JS}\n</script>\n</body>'
)


# Render inside Streamlit

components.html(HTML_TEMPLATE, height=900, scrolling=True)
