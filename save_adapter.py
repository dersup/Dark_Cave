"""
Save-path adapter: desktop writes to ./saves/, browser writes to
localStorage via pygbag's platform.window shim.

On desktop  : saves go to saves/savegame.json (created next to main.py).
On browser  : saves go to localStorage key "dark_cave_save" -- survives
              page reloads, no filesystem access needed.
"""
import sys
from pathlib import Path

IS_BROWSER = sys.platform == "emscripten"

# Desktop-only path. Not consulted in the browser.
SAVE_DIR  = Path("saves")
SAVE_FILE = SAVE_DIR / "savegame.json"

_LS_KEY = "dark_cave_save"


# ---------------------------------------------------------------------------
# Browser helpers (pygbag's platform.window exposes the JS window object)
# ---------------------------------------------------------------------------

def _browser_read() -> str | None:
    try:
        import platform  # pygbag-provided shim in browser
        return platform.window.localStorage.getItem(_LS_KEY)
    except Exception as e:
        print(f"[save] localStorage read failed: {e}")
        return None


def _browser_write(text: str) -> None:
    try:
        import platform
        platform.window.localStorage.setItem(_LS_KEY, text)
    except Exception as e:
        print(f"[save] localStorage write failed: {e}")


def _browser_delete() -> None:
    try:
        import platform
        platform.window.localStorage.removeItem(_LS_KEY)
    except Exception as e:
        print(f"[save] localStorage delete failed: {e}")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def read_save() -> str | None:
    if IS_BROWSER:
        return _browser_read()
    if not SAVE_FILE.exists():
        return None
    return SAVE_FILE.read_text(encoding="utf-8")


def write_save(text: str) -> None:
    if IS_BROWSER:
        # Skip the /tmp write entirely -- it's wiped on reload and a failed
        # mkdir would bypass the localStorage mirror.
        _browser_write(text)
        return
    SAVE_DIR.mkdir(exist_ok=True, parents=True)
    SAVE_FILE.write_text(text, encoding="utf-8")


def delete_save_file() -> bool:
    if IS_BROWSER:
        existed = _browser_read() is not None
        _browser_delete()
        return existed
    if SAVE_FILE.exists():
        SAVE_FILE.unlink()
        return True
    return False


def save_exists_now() -> bool:
    if IS_BROWSER:
        return _browser_read() is not None
    return SAVE_FILE.exists()