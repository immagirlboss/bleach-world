import random
import os
from collections import deque
from flask import Flask, jsonify, render_template, request
from pyswip import Prolog

app = Flask(__name__)

# Basic setup for Prolog
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROLOG_FILE = os.path.join(BASE_DIR, "prolog/kb.pl")
engine = Prolog()
engine.consult(PROLOG_FILE)

TRACE = deque(maxlen=30)

def pl_query(q):
    """Simple wrapper for prolog status check"""
    res = bool(list(engine.query(q)))
    TRACE.append(f"?- {q}. -> {str(res).lower()}")
    return res

def pl_fetch(q, var="Cell"):
    """Get all matches for a variable"""
    res = list(engine.query(q))
    return [r[var] for r in res]

def pl_info(q):
    """Get first result dict"""
    res = list(engine.query(q))
    return res[0] if res else None

# Helpers for KB updates - list() forces generator execution
def mark_visited(r, c): list(engine.query(f"assert_vis(cell({r},{c}))"))
def add_percept(r, c, t): list(engine.query(f"assert_p(cell({r},{c}), {t})"))
def mark_captain(r, c): list(engine.query(f"assert_cap(cell({r},{c}))"))
def mark_dead(r, c): list(engine.query(f"assert_kill(cell({r},{c}))"))

GRID_SIZE = 5

def get_neighbors(r, c):
    res = []
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < GRID_SIZE and 0 <= nc < GRID_SIZE:
            res.append((nr, nc))
    return res

def check_solvable(goal, caps, rifts):
    q = deque([(0, 0)])
    seen = {(0, 0)}
    blocks = set(caps.keys()) | rifts
    while q:
        curr = q.popleft()
        if curr == goal: return True
        for n in get_neighbors(*curr):
            if n not in seen and n not in blocks:
                seen.add(n)
                q.append(n)
    return False

def make_world(ncaps, nrifts):
    # Try multiple times to find a fair map
    for _ in range(100):
        cells = [(r, c) for r in range(GRID_SIZE) for c in range(GRID_SIZE)]
        safe_start = {(0,0)} | set(get_neighbors(0,0))
        
        pool = [c for c in cells if c not in safe_start]
        random.shuffle(pool)
        
        caps = {c: random.choice(["kenpachi", "byakuya", "toshiro"]) for c in pool[:ncaps]}
        rifts = set(pool[ncaps:ncaps+nrifts])
        
        remaining = pool[ncaps+nrifts:]
        # Goal should be at least somewhat far
        goal_pool = [c for c in remaining if (abs(c[0]) + abs(c[1])) >= 4]
        goal = goal_pool[0] if goal_pool else remaining[0]
        
        if check_solvable(goal, caps, rifts):
            return caps, rifts, goal
    return {}, set(), (0,0)

class Game:
    def __init__(self, ncaps=3, nrifts=3, bankai_enabled=True):
        self.ncaps = ncaps
        self.nrifts = nrifts
        self.bankai_enabled = bankai_enabled
        self.reset()

    def reset(self):
        self.caps, self.rifts, self.goal = make_world(self.ncaps, self.nrifts)
        self.pos = (0, 0)
        self.has_bankai = True
        self.visited = set()
        self.alive = True
        self.won = False
        self.defeated = set()
        self.move_type = "inferred"
        self.log = []
        self.steps = 0

        list(engine.query("reset_kb"))
        list(engine.query("assert_ready"))
        list(engine.query(f"assertz(captain_target_count({self.ncaps}))"))
        
        self.enter(0, 0)

    def enter(self, r, c):
        self.pos = (r, c)
        self.visited.add((r, c))
        mark_visited(r, c)

        if (r, c) in self.caps and (r, c) not in self.defeated:
            self.alive = False
            self.log.append(f"[dead] Hit a Captain at {(r, c)}")
            return

        if (r, c) in self.rifts:
            self.alive = False
            self.log.append(f"[rift] Fell into rift at {(r, c)}")
            return

        if (r, c) == self.goal:
            self.won = True
            self.log.append(f"[Rukia] Found Rukia at {(r, c)}!")
            return

        # Percept detection
        nbors = get_neighbors(r, c)
        pts = []
        if any(n in self.caps and n not in self.defeated for n in nbors):
            add_percept(r, c, "spiritual_pressure")
            pts.append("spiritual_pressure")
        if any(n in self.rifts for n in nbors):
            add_percept(r, c, "spatial_distortion")
            pts.append("spatial_distortion")
        if any(n == self.goal for n in nbors):
            add_percept(r, c, "golden_glistening")
            pts.append("golden_glistening")
        
        msg = f"Percepts at {(r, c)}: {', '.join(pts)}" if pts else f"{(r, c)} is clear"
        self.log.append(msg)

    def step(self):
        if not self.alive or self.won: return self.snapshot()
        self.steps += 1
        
        # 1. Update deductions
        for c in pl_fetch("inferred_captain(Cell)"):
            p = self.parse_p(c)
            if p and not pl_query(f"confirmed_captain(cell({p[0]},{p[1]}))"):
                mark_captain(*p)
                self.log.append(f"[logic] Detected Captain at {p}")

        # 2. Combat first
        if self.has_bankai and self.bankai_enabled:
            for n in get_neighbors(*self.pos):
                if pl_query(f"inferred_captain(cell({n[0]},{n[1]}))"):
                    self.use_bankai(n)
                    return self.snapshot()

        # 3. Known safe cells
        safe = [self.parse_p(c) for c in pl_fetch("safe_move(Cell)")]
        safe = [s for s in safe if s and s not in self.visited]
        if safe:
            target = self.pick_best(safe)
            self.move_type = "inferred"
            self.log.append(f"[inferred] Moving to {target}")
            self.enter(*target)
            return self.snapshot()

        # 4. Seek the goal signal
        if self.seek_rukia(): return self.snapshot()

        # 5. Last resort: guess
        self.fallback()
        return self.snapshot()

    def rand_step(self):
        """Purely random exploration baseline"""
        if not self.alive or self.won: return self.snapshot()
        self.steps += 1
        
        front = []
        for v in self.visited:
            for n in get_neighbors(*v):
                if n not in self.visited: front.append(n)
        
        if not front:
            self.log.append("Trapped!")
            return self.snapshot()
            
        target = random.choice(list(set(front)))
        self.move_type = "probabilistic" 
        self.log.append(f"[random] Jumped to {target}")
        self.enter(*target)
        return self.snapshot()

    def pick_best(self, moves):
        # pick move that explores most or gets closer to clues
        scored = []
        for m in moves:
            gain = sum(1 for n in get_neighbors(*m) if n not in self.visited)
            info = pl_info(f"rukia_score(cell({m[0]},{m[1]}), S)")
            s = info["S"] if info else 0
            dist = abs(m[0] - self.pos[0]) + abs(m[1] - self.pos[1])
            scored.append((-gain, -s, dist, m))
        return sorted(scored)[0][3]

    def seek_rukia(self):
        raw = list(engine.query("rukia_score(Cell, S)"))
        targets = []
        for r in raw:
            c = self.parse_p(r["Cell"])
            if not c or c in self.visited: continue
            # Avoid likely death
            if pl_query(f"possible_captain(cell({c[0]},{c[1]}))"): continue
            if pl_query(f"possible_rift(cell({c[0]},{c[1]}))"): continue
            targets.append((r["S"], c))
        
        if not targets: return False
        
        targets.sort(key=lambda x: (-x[0], -(abs(x[1][0]) + abs(x[1][1]))))
        self.move_type = "goal-directed"
        self.log.append(f"[goal] Tracking signal to {targets[0][1]}")
        self.enter(*targets[0][1])
        return True

    def fallback(self):
        front = []
        for v in self.visited:
            for n in get_neighbors(*v):
                if n not in self.visited: front.append(n)
        
        if not front:
            self.log.append("Trapped!")
            return

        scored = []
        for c in set(front):
            res = pl_info(f"risk_score(cell({c[0]},{c[1]}), S)")
            risk = float(res["S"]) if res else 0.0
            gain = sum(1 for n in get_neighbors(*c) if n not in self.visited)
            scored.append((risk, -gain, c))

        scored.sort()
        target = scored[0][2]
        self.move_type = "probabilistic"
        self.log.append(f"[fallback] Hazardous probe: {target}")
        self.enter(*target)

    def use_bankai(self, target):
        self.caps.pop(target, None)
        self.defeated.add(target)
        self.has_bankai = False
        mark_dead(*target)
        list(engine.query("assert_used"))
        self.move_type = "bankai"
        self.log.append(f"[bankai] Slashed Captain at {target}")

    def parse_p(self, term):
        try:
            if hasattr(term, 'args'): return (int(term.args[0]), int(term.args[1]))
            s = str(term.decode() if isinstance(term, bytes) else term).strip()
            if 'cell(' in s:
                p = s[5:-1].split(',')
                return (int(p[0]), int(p[1]))
        except: pass
        return None

    def snapshot(self):
        def get_pos(query):
            res = [self.parse_p(t) for t in pl_fetch(query)]
            return [list(p) for p in res if p]
        
        raw_p = list(engine.query("percept(C, T)"))
        return {
            "status": "won" if self.won else ("dead" if not self.alive else "running"),
            "step": self.steps, "agent": list(self.pos),
            "has_bankai": self.has_bankai, "move_type": self.move_type,
            "query_trace": list(TRACE)[-5:], "visited": [list(v) for v in self.visited],
            "log": self.log[-5:], "full_log": self.log,
            "kb": {
                "safe_cells": get_pos("confirmed_safe(Cell)"),
                "confirmed_captains": get_pos("confirmed_captain(Cell)"),
                "possible_captains": get_pos("possible_captain(Cell)"),
                "possible_rifts": get_pos("possible_rift(Cell)"),
                "defeated_captains": get_pos("defeated_captain(Cell)"),
                "percepts": [{"cell": self.parse_p(p["C"]), "type": str(p["T"])} for p in raw_p]
            },
            "world": {
                "captains": [{"pos": list(p), "name": n} for p, n in self.caps.items()],
                "defeated_captains": [list(c) for c in self.defeated],
                "rifts": [list(r) for r in self.rifts], "rukia": list(self.goal)
            }
        }

game = Game()

@app.route("/")
def index(): return render_template("index.html")

@app.route("/state")
def get_state(): return jsonify(game.snapshot())

@app.route("/step", methods=["POST"])
def next_step():
    return jsonify(game.step())

@app.route("/reset", methods=["POST"])
def reset_game():
    game.reset()
    return jsonify(game.snapshot())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)