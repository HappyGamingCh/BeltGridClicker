# BeltGridClicker

An auto-clicker for grid UIs (e.g., game inventories) that holds **Shift** and clicks every cell using **3-point calibration**, **human-like timing**, and flexible **scan orders** — all configurable via `config.txt`.

> ⚠️ **Disclaimer:** Automation may violate a game’s Terms of Service. Use at your own risk. This tool drives your real mouse/keyboard—keep the target window focused and test carefully.

---

## Features

- ✅ **3-point calibration** (precise):
  - **p00** = top-left of the first (top-left) cell  
  - **pTR** = top-right of the top-right cell  
  - **pBL** = bottom-left of the bottom-left cell
- ✅ Clicks the **center** of each cell with small random **jitter**
- ✅ **Human-like timing** (+ occasional micro-rests) with **speed preset**
- ✅ **Scan order** options:
  1. **Top → Bottom**, then **Left → Right** (column-major)
  2. **Left → Right**, then **Top → Bottom** (row-major)
  3. **Random** (every cell clicked exactly once in a shuffled order)
- ✅ Runtime configuration via **`config.txt`** + **hot reload** (`Ctrl+Alt+R`)
- ✅ **Emergency stop** (`Ctrl+Alt+9`) + **PyAutoGUI failsafe** (slam mouse to top-left screen corner)
- ✅ Works best in windowed/borderless modes

---

## Usage

1) **Focus** the target window (e.g., inventory screen).
2) **Calibrate** 3 points (hover the mouse; press the hotkeys):
   - `Ctrl+Alt+1` → **p00** (top-left of the first cell)  
   - `Ctrl+Alt+2` → **pTR** (top-right of the top-right cell)  
   - `Ctrl+Alt+3` → **pBL** (bottom-left of the bottom-left cell)
3) **Start**: `Ctrl+Alt+0`  
   The app will wait briefly, hold **Shift**, and click all cells per the configured scan order.
4) **Emergency stop**: `Ctrl+Alt+9` (or use the PyAutoGUI failsafe by moving the mouse to the top-left screen corner).
5) **Change runtime settings**: edit `config.txt`, then press `Ctrl+Alt+R` to reload (applies to the **next run**).

<p align="center">
  <img src="https://raw.githubusercontent.com/HappyGamingCh/BeltGridClicker/main/3-point%20position.JPG" alt="3-point calibration" width="600">
</p>

---

## Hotkeys

- `Ctrl+Alt+1` — Save **p00** (top-left of first cell)  
- `Ctrl+Alt+2` — Save **pTR** (top-right of top-right cell)  
- `Ctrl+Alt+3` — Save **pBL** (bottom-left of bottom-left cell)  
- `Ctrl+Alt+0` — **Start** (holds Shift; clicks all cells)  
- `Ctrl+Alt+9` — **Emergency stop**  
- `Ctrl+Alt+R` — **Reload `config.txt`** (takes effect next run)

---

## Configuration (`config.txt`)

`config.txt` lives next to the `.exe` and is read at startup (and on `Ctrl+Alt+R`).

```ini
# grid size
columns=12
rows=24

# speed: 1 = human-like (default), 2 = ~2x faster
speed=1

# scan_order:
#   1 = Top→Bottom then Left→Right  (column-major)
#   2 = Left→Right then Top→Bottom  (row-major)
#   3 = Random (each cell clicked once in a shuffled order)
scan_order=1
```
---

## Disclaimer

- This tool does **not modify, inject into, or read any game files**. It only simulates mouse/keyboard input at the operating-system level.
- Use at your own risk. **We are not responsible** for any damages, bans, data loss, or other consequences resulting from the use of this software.
- Automation may violate a game’s Terms of Service. **You are solely responsible** for checking and complying with all applicable rules.

## License
MIT © 2025 Pednoi
