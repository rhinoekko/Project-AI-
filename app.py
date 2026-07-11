import math
import random
import heapq
from collections import deque
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# PATHFINDING ALGORITHMS

def get_neighbors(node, grid_size, walls_set):
    x, y = node
    neighbors = []
    # Up, Down, Left, Right
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
        nx, ny = x + dx, y + dy
        if 0 <= nx < grid_size and 0 <= ny < grid_size:
            if (nx, ny) not in walls_set:
                neighbors.append((nx, ny))
    return neighbors

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    path.reverse()
    return path

def bfs_search(grid_size, start, goal, walls_set):
    """BFS menggunakan deque untuk O(1) popleft."""
    visited_order = []
    came_from = {}
    queue = deque([start])
    visited_set = {start}

    found = False
    while queue:
        current = queue.popleft()  # O(1) vs list.pop(0) yang O(n)
        visited_order.append(current)

        if current == goal:
            found = True
            break

        for neighbor in get_neighbors(current, grid_size, walls_set):
            if neighbor not in visited_set:
                visited_set.add(neighbor)
                came_from[neighbor] = current
                queue.append(neighbor)

    path = reconstruct_path(came_from, goal) if found else []
    return visited_order, path

def dfs_search(grid_size, start, goal, walls_set):
    """DFS menggunakan frontier set untuk O(1) lookup saat cek duplikat."""
    visited_order = []
    came_from = {}
    stack = [start]
    frontier_set = {start}  # Track apa yang ada di stack — O(1) lookup
    visited_set = set()

    found = False
    while stack:
        current = stack.pop()
        frontier_set.discard(current)

        if current in visited_set:
            continue

        visited_set.add(current)
        visited_order.append(current)

        if current == goal:
            found = True
            break

        # Reverse neighbors untuk eksplorasi urut atas/bawah/kiri/kanan
        neighbors = get_neighbors(current, grid_size, walls_set)
        for neighbor in reversed(neighbors):
            if neighbor not in visited_set and neighbor not in frontier_set:
                came_from[neighbor] = current
                stack.append(neighbor)
                frontier_set.add(neighbor)

    path = reconstruct_path(came_from, goal) if found else []
    return visited_order, path

def dijkstra_search(grid_size, start, goal, walls_set):
    """Dijkstra menggunakan heapq untuk O(log n) per operasi vs list.sort() O(n log n)."""
    visited_order = []
    came_from = {}

    g_score = {}
    g_score[start] = 0

    # heapq stores (cost, node) — min-heap
    heap = [(0, start)]
    visited_set = set()

    found = False
    while heap:
        current_cost, current = heapq.heappop(heap)  # O(log n)

        if current in visited_set:
            continue

        visited_set.add(current)
        visited_order.append(current)

        if current == goal:
            found = True
            break

        for neighbor in get_neighbors(current, grid_size, walls_set):
            tentative_g = current_cost + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                g_score[neighbor] = tentative_g
                came_from[neighbor] = current
                heapq.heappush(heap, (tentative_g, neighbor))  # O(log n)

    path = reconstruct_path(came_from, goal) if found else []
    return visited_order, path

def a_star_search(grid_size, start, goal, walls_set, heuristic_type='manhattan'):
    """A* menggunakan heapq untuk O(log n) per operasi vs list.sort() O(n log n)."""
    gx, gy = goal

    if heuristic_type == 'euclidean':
        def heuristic(node):
            return math.sqrt((node[0] - gx) ** 2 + (node[1] - gy) ** 2)
    else:  # manhattan
        def heuristic(node):
            return abs(node[0] - gx) + abs(node[1] - gy)

    visited_order = []
    came_from = {}

    g_score = {start: 0}
    f_score = {start: heuristic(start)}

    # heapq stores (f_score, tie_breaker, node)
    counter = 0  # Tie-breaker untuk node dengan f_score sama
    heap = [(f_score[start], counter, start)]
    open_set_nodes = {start}
    visited_set = set()

    found = False
    while heap:
        _, _, current = heapq.heappop(heap)  # O(log n)

        if current in visited_set:
            continue

        open_set_nodes.discard(current)
        visited_set.add(current)
        visited_order.append(current)

        if current == goal:
            found = True
            break

        current_g = g_score[current]
        for neighbor in get_neighbors(current, grid_size, walls_set):
            if neighbor in visited_set:
                continue

            tentative_g = current_g + 1
            if tentative_g < g_score.get(neighbor, float('inf')):
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g
                f = tentative_g + heuristic(neighbor)
                f_score[neighbor] = f

                if neighbor not in open_set_nodes:
                    open_set_nodes.add(neighbor)
                    counter += 1
                    heapq.heappush(heap, (f, counter, neighbor))  # O(log n)

    path = reconstruct_path(came_from, goal) if found else []
    return visited_order, path


# MINI GAME STRATEGY AI DECISION ENGINE

# The mini game grid is 5x5
GAME_GRID_SIZE = 5

def distance(pos1, pos2):
    return abs(pos1[0] - pos2[0]) + abs(pos1[1] - pos2[1])

def evaluate_state(ai_hp, ai_pos, ai_shield, ai_heal_cd, player_hp, player_pos, player_shield, walls):
    """
    Heuristic utility evaluation function for the state from the AI's perspective.
    Higher values are better for AI.
    """
    if player_hp <= 0:
        return 5000  # Winning move
    if ai_hp <= 0:
        return -5000  # Death is worst

    dist = distance(ai_pos, player_pos)

    # Utility components
    hp_diff = ai_hp * 2.0 - player_hp * 2.5

    # Position utility based on health status
    dist_utility = 0
    if ai_hp > 35:
        # AI wants to be close enough to attack
        if dist == 1:
            dist_utility = 50  # Ideal attacking distance
        elif dist > 1:
            dist_utility = -dist * 10  # Penalize being far away
    else:
        # AI is weak: retreat
        dist_utility = dist * 15  # Reward being far away

    # Shield value
    shield_val = 15 if ai_shield else 0
    # Add a penalty if within player's attack range (dist == 1) and no shield
    danger_val = -30 if (dist == 1 and not ai_shield) else 0

    return hp_diff + dist_utility + shield_val + danger_val

def generate_action_combinations(ai_heal_cd):
    """
    Generates all valid combinations of actions that sum up to <= 3 Action Points (AP).
    """
    possible_combos = []

    basic_actions = [
        ('shield', 1),
        ('attack', 2),
        ('heal', 2),
        ('move_up', 1),
        ('move_down', 1),
        ('move_left', 1),
        ('move_right', 1)
    ]

    # Build sequences recursively up to 3 AP
    def build_sequences(current_seq, current_ap):
        if current_ap > 3:
            return
        if current_seq:
            possible_combos.append(current_seq)

        for act_name, cost in basic_actions:
            if current_ap + cost <= 3:
                # If heal, make sure it is off cooldown
                if act_name == 'heal' and ai_heal_cd > 0:
                    continue
                build_sequences(current_seq + [act_name], current_ap + cost)

    build_sequences([], 0)
    return possible_combos

def simulate_sequence(sequence, initial_state, walls):
    """
    Simulates a sequence of actions on the game state.
    Returns (valid, final_state)
    """
    walls_set = {tuple(w) for w in walls}  # Convert to set for O(1) lookup

    state = {
        'ai_hp': initial_state['ai_hp'],
        'ai_pos': tuple(initial_state['ai_pos']),
        'ai_shield': initial_state['ai_shield'],
        'ai_heal_cd': initial_state['ai_heal_cd'],
        'player_hp': initial_state['player_hp'],
        'player_pos': tuple(initial_state['player_pos']),
        'player_shield': initial_state['player_shield']
    }

    actual_actions = []

    for action in sequence:
        if action.startswith('move_'):
            direction = action.split('_')[1]
            dx, dy = 0, 0
            if direction == 'up': dy = -1
            elif direction == 'down': dy = 1
            elif direction == 'left': dx = -1
            elif direction == 'right': dx = 1

            nx, ny = state['ai_pos'][0] + dx, state['ai_pos'][1] + dy

            # Check grid boundary
            if not (0 <= nx < GAME_GRID_SIZE and 0 <= ny < GAME_GRID_SIZE):
                return False, None
            # Check walls using O(1) set lookup
            if (nx, ny) in walls_set:
                return False, None
            # Check player position collision
            if (nx, ny) == state['player_pos']:
                return False, None

            state['ai_pos'] = (nx, ny)
            actual_actions.append({'type': 'move', 'target': [nx, ny]})

        elif action == 'attack':
            dist_x = abs(state['ai_pos'][0] - state['player_pos'][0])
            dist_y = abs(state['ai_pos'][1] - state['player_pos'][1])
            if max(dist_x, dist_y) > 1:
                return False, None  # Too far

            damage = random.randint(20, 25)
            if state['player_shield']:
                damage = damage // 2

            state['player_hp'] = max(0, state['player_hp'] - damage)
            actual_actions.append({'type': 'attack', 'damage': damage})

        elif action == 'shield':
            state['ai_shield'] = True
            actual_actions.append({'type': 'shield'})

        elif action == 'heal':
            if state['ai_heal_cd'] > 0:
                return False, None

            heal_amount = 25
            state['ai_hp'] = min(100, state['ai_hp'] + heal_amount)
            state['ai_heal_cd'] = 3
            actual_actions.append({'type': 'heal', 'amount': heal_amount})

    return True, (state, actual_actions)

def compute_best_ai_turn(game_state, walls):
    combos = generate_action_combinations(game_state['ai_heal_cd'])

    best_actions = []
    best_utility = float('-inf')
    best_final_state = None

    # Evaluate each combination
    for combo in combos:
        valid, result = simulate_sequence(combo, game_state, walls)
        if valid:
            simulated_state, actions = result
            score = evaluate_state(
                simulated_state['ai_hp'],
                simulated_state['ai_pos'],
                simulated_state['ai_shield'],
                simulated_state['ai_heal_cd'],
                simulated_state['player_hp'],
                simulated_state['player_pos'],
                simulated_state['player_shield'],
                walls
            )

            # Add small random factor to break ties
            score += random.uniform(-1, 1)

            if score > best_utility:
                best_utility = score
                best_actions = actions
                best_final_state = simulated_state

    # Default fall back if trapped or no choices
    if not best_actions:
        best_actions = [{'type': 'shield'}]
        best_final_state = {**game_state, 'ai_shield': True}

    return best_actions, best_final_state


# FLASK ROUTING

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/pathfind', methods=['POST'])
def pathfind():
    import time
    data = request.json
    grid_size = int(data.get('grid_size', 10))
    start = tuple(data.get('start'))
    goal = tuple(data.get('goal'))
    walls = [tuple(w) for w in data.get('walls', [])]
    walls_set = set(walls)  # Convert once to set for O(1) lookups throughout
    algorithm = data.get('algorithm', 'a_star')
    heuristic_type = data.get('heuristic', 'manhattan')

    start_time = time.perf_counter()

    if algorithm == 'bfs':
        visited, path = bfs_search(grid_size, start, goal, walls_set)
    elif algorithm == 'dfs':
        visited, path = dfs_search(grid_size, start, goal, walls_set)
    elif algorithm == 'dijkstra':
        visited, path = dijkstra_search(grid_size, start, goal, walls_set)
    else:  # a_star
        visited, path = a_star_search(grid_size, start, goal, walls_set, heuristic_type)

    end_time = time.perf_counter()
    execution_time_ms = (end_time - start_time) * 1000

    return jsonify({
        'visited': visited,
        'path': path,
        'execution_time_ms': round(execution_time_ms, 3),
        'cost': len(path) - 1 if path else 0
    })

@app.route('/api/game/ai-move', methods=['POST'])
def game_ai_move():
    data = request.json
    game_state = data.get('game_state')
    walls = data.get('walls', [])

    actions, final_state = compute_best_ai_turn(game_state, walls)

    response_state = {
        'ai_hp': final_state['ai_hp'],
        'ai_pos': list(final_state['ai_pos']),
        'ai_shield': final_state['ai_shield'],
        'ai_heal_cd': max(0, final_state['ai_heal_cd'] - 1),
        'player_hp': final_state['player_hp'],
        'player_pos': list(final_state['player_pos']),
        'player_shield': final_state['player_shield']
    }

    return jsonify({
        'actions': actions,
        'game_state': response_state
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
