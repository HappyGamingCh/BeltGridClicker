# belt.py
# ------------------------------------------------------------
# Grid click macro (e.g., POE belt upgrades) with config.txt
#
# Calibration (mouse to the exact corner, then press the hotkey):
#   Ctrl+Alt+1 -> p00 = TOP-LEFT of the FIRST (top-left) cell
#   Ctrl+Alt+2 -> pTR = TOP-RIGHT of the TOP-RIGHT cell
#   Ctrl+Alt+3 -> pBL = BOTTOM-LEFT of the BOTTOM-LEFT cell
#
# Run:
#   Ctrl+Alt+0 -> start (waits START_DELAY), holds Shift, clicks all cells
#
# Stop:
#   Ctrl+Alt+9 -> emergency stop (panic)
#   (Plus PyAutoGUI failsafe: moving mouse to TOP-LEFT of the screen aborts.)
#
# Config file (config.txt) keys (case-insensitive):
#   columns=<int>          # number of columns in your grid (default 24)
#   rows=<int>             # number of rows in your grid (default 12)
#   speed=<1|2>            # 1 = human-like (default), 2 = ~2x faster
#   scan_order=<1|2|3>     # 1 = top→bottom then left→right  (column-major)
#                          # 2 = left→right then top→bottom  (row-major)
#                          # 3 = random (all cells shuffled once per run)
#
# Utilities:
#   Ctrl+Alt+R -> reload config.txt at any time (takes effect next run)
#
# Notes:
#   - Clicks target the CENTER of each cell with small jitter.
#   - Human-like delays + occasional rests to look natural.
#   - Make sure your window is focused before starting.
# ------------------------------------------------------------

import os
import time
import random
import pyautogui as pag
import keyboard

CONFIG_PATH = "config.txt"

# ---------- Defaults (overridden by config.txt) ----------
CFG = {
    "columns": 12,
    "rows": 24,
    "speed": 1,        # 1=human-like, 2=~2x faster
    "scan_order": 1,   # 1=col-major, 2=row-major, 3=random
}

# Base human-like timing profile (speed=1). If speed=2, these get scaled down.
BASE_CLICK_DELAY_MIN = 0.11
BASE_CLICK_DELAY_MAX = 0.18
BASE_MOVE_DURATION_MIN = 0.02
BASE_MOVE_DURATION_MAX = 0.06

# Occasional longer rests (burst behavior), not scaled by speed
BURST_MIN = 24
BURST_MAX = 48
BURST_REST_MIN = 0.40
BURST_REST_MAX = 0.90

# Rest after unit (row or column) depending on scan order; not scaled by speed
UNIT_REST_MIN = 0.30
UNIT_REST_MAX = 0.70

START_DELAY = 3.0        # seconds to wait before starting after hotkey
RANDOM_JITTER = 2        # ± pixels jitter on x/y to look natural

# ---------- Runtime state ----------
state = {
    # Calibration points:
    # p00: top-left of the first (top-left) cell
    # pTR: top-right of the top-right cell
    # pBL: bottom-left of the bottom-left cell
    "p00": None,
    "pTR": None,
    "pBL": None,
    "running": False,
}

# ---------- Logging ----------
def info(msg: str): print(f"[INFO] {msg}")
def warn(msg: str): print(f"[WARN] {msg}")

# ---------- Config handling ----------
def write_default_config(path: str):
    sample = (
        "# config.txt\n"
        "# number of columns/rows in your grid\n"
        "columns=24\n"
        "rows=12\n"
        "\n"
        "# speed: 1 = human-like (default), 2 = ~2x faster\n"
        "speed=1\n"
        "\n"
        "# scan_order:\n"
        "#   1 = top→bottom then left→right  (column-major)\n"
        "#   2 = left→right then top→bottom  (row-major)\n"
        "#   3 = random\n"
        "scan_order=1\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(sample)

def load_config(path: str):
    if not os.path.exists(path):
        write_default_config(path)
        info(f"Created default config at {path}")

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    loaded = {}
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        if "=" not in s:
            continue
        k, v = s.split("=", 1)
        k = k.strip().lower()
        v = v.strip().lower()
        loaded[k] = v

    def to_int(name, default, min_v=None, max_v=None):
        try:
            val = int(loaded.get(name, default))
        except:
            val = default
        if min_v is not None: val = max(min_v, val)
        if max_v is not None: val = min(max_v, val)
        return val

    CFG["columns"] = to_int("columns", CFG["columns"], 1, 9999)
    CFG["rows"] = to_int("rows", CFG["rows"], 1, 9999)
    CFG["speed"] = to_int("speed", CFG["speed"], 1, 2)
    CFG["scan_order"] = to_int("scan_order", CFG["scan_order"], 1, 3)

    info(f"Config loaded: columns={CFG['columns']}, rows={CFG['rows']}, speed={CFG['speed']}, scan_order={CFG['scan_order']}")

def reload_config_hotkey():
    load_config(CONFIG_PATH)
    info("Config reloaded (applies to next run).")

# ---------- Capture hotkeys ----------
def capture_p00():
    state["p00"] = pag.position()
    info(f"Captured p00 (top-left of first cell) = {state['p00']}")

def capture_pTR():
    state["pTR"] = pag.position()
    info(f"Captured pTR (top-right of top-right cell) = {state['pTR']}")

def capture_pBL():
    state["pBL"] = pag.position()
    info(f"Captured pBL (bottom-left of bottom-left cell) = {state['pBL']}")

# ---------- Geometry ----------
def compute_cell_size():
    """
    Compute cell width/height using:
      cell_w = (pTR.x - p00.x) / columns
      cell_h = (pBL.y - p00.y) / rows
    Assumes a regular grid with uniform pitch and screen Y increasing downward.
    """
    p00, pTR, pBL = state["p00"], state["pTR"], state["pBL"]
    if not (p00 and pTR and pBL):
        return None, None

    total_w = pTR.x - p00.x
    total_h = pBL.y - p00.y

    if total_w <= 0 or total_h <= 0:
        warn("Calibration looks invalid (non-positive width/height). Recalibrate points.")
        return None, None

    cell_w = total_w / CFG["columns"]
    cell_h = total_h / CFG["rows"]

    info(f"Cell size = {cell_w:.2f} x {cell_h:.2f} px")
    return cell_w, cell_h

# ---------- Timing ----------
def timing_profile():
    """
    Compute current timing (click delay + mouse move duration) based on speed.
    Speed 1: human-like base.
    Speed 2: approximately 2x faster (half delays, shorter moves).
    """
    speed = CFG["speed"]
    if speed == 1:
        cd_min = BASE_CLICK_DELAY_MIN
        cd_max = BASE_CLICK_DELAY_MAX
        mv_min = BASE_MOVE_DURATION_MIN
        mv_max = BASE_MOVE_DURATION_MAX
    else:  # speed == 2
        cd_min = BASE_CLICK_DELAY_MIN * 0.5
        cd_max = BASE_CLICK_DELAY_MAX * 0.5
        mv_min = max(0.0, BASE_MOVE_DURATION_MIN * 0.5)
        mv_max = max(0.0, BASE_MOVE_DURATION_MAX * 0.5)
    return (cd_min, cd_max, mv_min, mv_max)

def human_delay(cd_min, cd_max):
    """Human-like delay using triangular distribution (peaks around midpoint)."""
    return random.triangular(cd_min, cd_max, (cd_min + cd_max) / 2)

# ---------- Control ----------
def _panic():
    """Hotkey callback for Ctrl+Alt+9."""
    if state["running"]:
        state["running"] = False
        warn("Ctrl+Alt+9 pressed -> macro stopping...")

def run_macro():
    """
    Hold Shift and left-click the center of each cell in the order specified by config:
      scan_order:
        1 = top→bottom then left→right (column-major)
        2 = left→right then top→bottom (row-major)
        3 = random (all cells shuffled)
    """
    if state["running"]:
        warn("Macro is already running")
        return

    if not (state["p00"] and state["pTR"] and state["pBL"]):
        warn("Calibration incomplete. Press Ctrl+Alt+1, +2, +3 to set p00 / pTR / pBL")
        return

    cell_w, cell_h = compute_cell_size()
    if cell_w is None or cell_h is None or cell_w == 0 or cell_h == 0:
        warn("Failed to compute cell size. Check calibration points.")
        return

    cols = CFG["columns"]
    rows = CFG["rows"]
    order = CFG["scan_order"]

    cd_min, cd_max, mv_min, mv_max = timing_profile()

    info(f"Starting in {START_DELAY:.1f}s ... cell = {cell_w:.2f}×{cell_h:.2f}px | speed={CFG['speed']} | order={order}")
    time.sleep(START_DELAY)

    # Begin run
    state["running"] = True
    pag.keyDown('shift')
    try:
        clicks = 0

        # Build the sequence of (r, c) pairs based on scan order
        if order == 1:
            # column-major: top->bottom (rows) then left->right (columns)
            sequence = [(r, c) for c in range(cols) for r in range(rows)]
        elif order == 2:
            # row-major: left->right (columns) then top->bottom (rows)
            sequence = [(r, c) for r in range(rows) for c in range(cols)]
        else:
            # random: all cells once in random order
            sequence = [(r, c) for r in range(rows) for c in range(cols)]
            random.shuffle(sequence)

        # Occasional longer rests (burst) across the whole run
        next_burst_at = random.randint(BURST_MIN, BURST_MAX)

        # Click loop
        for idx, (r, c) in enumerate(sequence):
            if not state["running"]:
                break

            # Center of cell (r, c) + small jitter
            x = state["p00"].x + c * cell_w + cell_w / 2 + random.randint(-RANDOM_JITTER, RANDOM_JITTER)
            y = state["p00"].y + r * cell_h + cell_h / 2 + random.randint(-RANDOM_JITTER, RANDOM_JITTER)

            pag.moveTo(x, y, duration=random.uniform(mv_min, mv_max))
            pag.click(button='left')
            clicks += 1

            # Human-like short delay
            time.sleep(human_delay(cd_min, cd_max))

            # Occasional longer rest (burst)
            if clicks >= next_burst_at and state["running"]:
                time.sleep(random.uniform(BURST_REST_MIN, BURST_REST_MAX))
                next_burst_at = clicks + random.randint(BURST_MIN, BURST_MAX)

            # Unit rest after completing each logical unit:
            # - If order==1 (column-major): rest after each column finishes
            # - If order==2 (row-major): rest after each row finishes
            if state["running"]:
                if order == 1:
                    # end of a column if the next item starts a new column or we are at end
                    if (idx + 1 == len(sequence)) or (sequence[idx + 1][1] != c):
                        time.sleep(random.uniform(UNIT_REST_MIN, UNIT_REST_MAX))
                elif order == 2:
                    # end of a row if the next item starts a new row or we are at end
                    if (idx + 1 == len(sequence)) or (sequence[idx + 1][0] != r):
                        time.sleep(random.uniform(UNIT_REST_MIN, UNIT_REST_MAX))
                else:
                    # random order: no unit rest
                    pass

        info(f"Done. Total clicks: {clicks}")
    finally:
        pag.keyUp('shift')
        state["running"] = False

# ---------- Entry ----------
def main():
    load_config(CONFIG_PATH)

    print(f"""
================ POE Belt Upgrade Macro ================
Hotkeys:
  Ctrl+Alt+1  -> Save p00 (top-left of the first cell)
  Ctrl+Alt+2  -> Save pTR (top-right of the top-right cell)
  Ctrl+Alt+3  -> Save pBL (bottom-left of the bottom-left cell)
  Ctrl+Alt+0  -> Start clicking (waits {START_DELAY} seconds)
  Ctrl+Alt+9  -> Emergency stop (panic)
  Ctrl+Alt+R  -> Reload config.txt
Current config:
  columns={CFG['columns']}  rows={CFG['rows']}  speed={CFG['speed']}  scan_order={CFG['scan_order']}
========================================================
""")

    # Global hotkeys (available at all times)
    keyboard.add_hotkey('ctrl+alt+1', capture_p00)
    keyboard.add_hotkey('ctrl+alt+2', capture_pTR)
    keyboard.add_hotkey('ctrl+alt+3', capture_pBL)
    keyboard.add_hotkey('ctrl+alt+0', run_macro)
    keyboard.add_hotkey('ctrl+alt+9', _panic)               # panic anytime
    keyboard.add_hotkey('ctrl+alt+r', reload_config_hotkey) # reload config anytime

    # Keep the script alive until Ctrl+C
    try:
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("\nExiting")

if __name__ == "__main__":
    # PyAutoGUI failsafe: move mouse to the top-left corner of the screen to abort (in addition to Ctrl+Alt+9)
    pag.FAILSAFE = True
    main()
