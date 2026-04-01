# The Dark Cave — Pygame Edition

A complete port of the Tkinter maze RPG to Pygame, playable as a desktop app
or served to any browser on your local network via pygbag/WebAssembly.

---

## File changes

| File | Status | Notes |
|------|--------|-------|
| `classes.py` | **unchanged** | All item/inventory logic intact |
| `constants.py` | **unchanged** | All game data intact |
| `entity.py` | **unchanged** | All combat/AI logic intact |
| `generator_.py` | **unchanged** | All loot/enemy generation intact |
| `drawing.py` | **replaced** | Tkinter Canvas → Pygame surface |
| `windows.py` | **replaced** | Tk/Label/Text → Pygame renderer + HUD |
| `maze.py` | **replaced** | Removed per-cell `redraw()` spam; uses `floor_colour()` |
| `main.py` | **replaced** | Pygame event loop; text/menu input screens |

---

## Run locally (desktop)

```bash
pip install pygame
python main.py
```

---

## Run in browser (LAN)

```bash
pip install pygame pygbag
bash serve_lan.ps1          # default port 8080
# or: bash serve_lan.ps1 9000
```

Open `http://<your-LAN-ip>:8080` from any device on the same network.

The build step (pygbag) compiles the game to WebAssembly.
It runs once and caches; subsequent serves are instant.

---

## Controls

| Key | Action |
|-----|--------|
| WASD / Arrow keys | Move |
| Shift + WASD/Arrows | Face a direction without moving |
| E | Pick up items from adjacent cell |
| I | Open/close inventory |
| ↑↓ / WS (in inventory) | Navigate |
| Enter / E (in inventory) | Use selected item |
| J | Inspect adjacent cell |
| Esc | Quit |

---

## Key design decisions

**No `time.sleep` / no `mainloop()`** — pygbag requires an async-friendly loop.
The game loop lives in `Windows.wait_for_close()` which calls `redraw()` each
frame. All "blocking" character-creation steps (name input, stat allocation) are
implemented as Pygame sub-loops that still process events normally.

**Animations** — `Cell.ani_move()` stores start/end/time rather than scheduling
Tkinter `after()` callbacks. `Cell.tick_animation()` is called each frame from
the draw pass so movement is smooth.

**Floor textures** — PNG assets are replaced with colour-coded tiles per dungeon
level (avoids file I/O issues in the browser sandbox). Swap `floor_colour()` in
`drawing.py` for real `pygame.image.load()` calls to restore artwork locally.

**Audio** — not present in the original; ALSA errors on headless Linux are safe
to ignore.
