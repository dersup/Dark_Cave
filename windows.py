import pygame
import sys
import time
import asyncio

# ---------------------------------------------------------------------------
# Palette & typography
# ---------------------------------------------------------------------------
BG           = ( 10,   8,  12)
PANEL        = ( 22,  18,  28, 220)
BORDER       = ( 70,  55,  90)
TEXT         = (220, 215, 200)
MUTED        = (120, 110, 100)
GOLD         = (255, 210,  50)
HP_COL       = (210,  55,  55)
MP_COL       = (60, 120, 255)
LEVEL_COL    = (160, 130, 255)
HIGHLIGHT_BG = ( 55,  45,  75)
HIGHLIGHT_FG = (120, 180, 255)
GAMEOVER_COL = (180,  30,  30)

FONT_SIZE = {"lg": 22, "md": 16, "sm": 13}


# ---------------------------------------------------------------------------
# Panel descriptor
# ---------------------------------------------------------------------------
class Panel:
    """All state for a single scrollable list panel."""

    def __init__(self, title: str, hint: str, *,
                 show_info_pane: bool = True,
                 show_cursor: bool = True,
                 width: int = 300):
        self.title   = title
        self.hint    = hint
        self.lines   = []   # list of (text, is_header, item_obj | None)
        self.cursor  = 0
        self.visible = False
        self.info = None
        # If False, _draw_panel skips the right-side item-info pane (used by
        # the pause menu, where each line is a command, not an inspectable item)
        self.show_info_pane = show_info_pane
        # If False, rows render without highlight and W/S/Up/Down scroll the
        # viewport instead of moving a cursor (used by the log panel, which
        # is read-only -- no row is "selected" because no row is actionable).
        self.show_cursor = show_cursor
        # Panel width in pixels. Lets the log panel be wider than the
        # inventory/spells panels for better message readability.
        self.width = width

        # -- Scrolling --------------------------------------------------------
        # `scroll`  = index of the first line currently rendered.
        # `_visible_count` is recomputed every draw based on panel height,
        # then used by _ensure_cursor_visible / _clamp_scroll. Keyboard nav
        # adjusts scroll automatically; mouse wheel adjusts it directly.
        self.scroll          = 0
        self._visible_count  = 0

        # -- Layout cached during draw, used by mouse hit-testing -------------
        # row_rects: [(pygame.Rect, line_index), ...] for currently-drawn rows.
        # All four reset to empty / None at the top of _draw_panel.
        self.row_rects       = []
        self.close_rect      = None
        self.track_rect      = None
        self.thumb_rect      = None

        # Active scrollbar drag: pixel offset between mouse-y and thumb-top
        # when the drag started. None when not dragging.
        self._drag_offset    = None


    def set_lines(self, lines: list):
        self.lines  = lines
        self.cursor = 0
        self.scroll = 0
        # Old layout is now stale; clear it so any in-flight mouse events
        # processed before the next draw don't hit phantom rows.
        self.row_rects  = []
        self.close_rect = None
        self.track_rect = None
        self.thumb_rect = None

    def move_cursor(self, delta: int):
        n = len(self.lines)
        if not n:
            return None
        new = max(0, min(self.cursor + delta, n - 1))
        # skip header rows
        while 0 <= new < n and self.lines[new][1]:
            new += delta
        if 0 <= new < n:
            self.cursor = new
        self._ensure_cursor_visible()
        return self.lines[self.cursor][0]

    # -- Scroll helpers --------------------------------------------------------

    def _ensure_cursor_visible(self):
        """Adjust scroll so the cursor row sits inside the visible window."""
        if self._visible_count <= 0:
            return
        if self.cursor < self.scroll:
            self.scroll = self.cursor
        elif self.cursor >= self.scroll + self._visible_count:
            self.scroll = self.cursor - self._visible_count + 1
        self._clamp_scroll()

    def _clamp_scroll(self):
        max_scroll = max(0, len(self.lines) - max(1, self._visible_count))
        self.scroll = max(0, min(self.scroll, max_scroll))

    def scroll_by(self, delta_lines: int):
        """Scroll the view by N lines without moving the cursor (used by the
        mouse wheel and scrollbar arrows / paging)."""
        self.scroll += delta_lines
        self._clamp_scroll()

    def selected_item(self):
        """Return the item object at the cursor, or None for headers/spells."""
        if 0 <= self.cursor < len(self.lines):
            entry = self.lines[self.cursor]
            return entry[2] if len(entry) > 2 else None
        return None

    def selected_name(self) -> str:
        if 0 <= self.cursor < len(self.lines):
            return self.lines[self.cursor][0].split("(")[0].strip()
        return ""

    def toggle(self) -> bool:
        self.visible = not self.visible
        return self.visible


# ---------------------------------------------------------------------------
# Windows
# ---------------------------------------------------------------------------
class Windows:
    def __init__(self, width=1280, height=800):
        pygame.init()
        self.w = width
        self.h = height
        self._screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("The Dark Cave")
        self.surface = self._screen
        self.clock   = pygame.time.Clock()

        FONT_PATH = "assets/fonts/ttf/JetBrainsMono-Regular.ttf"
        self.font = {sz: pygame.font.Font(FONT_PATH, pt) for sz, pt in FONT_SIZE.items()}
        self._camera_x = 0.0
        self._camera_y = 0.0

        self._level_str = "level: 1"
        self._hp_str    = "HP: 0/0"
        self._mp_str    = "MP: 0/0"
        self._gold_str  = "Gold: 0"
        self._game_over = False
        self._go_text   = ""
        self._log       = []
        self._log_timer = []
        # Persistent log of every message from this run -- distinct from
        # _log/_log_timer above, which are the fading 6-message HUD overlay.
        # The Tab-toggled log panel reads from this, so nothing scrolls off.
        self._history: list = []

        # All panels live here; adding a new one is one line.
        self._panels = {
            "inventory":  Panel("INVENTORY  (I to close)",
                                "WS/Hover  Enter/Click:use  D/RClick:drop"),
            "spell_list": Panel("SPELLS  (C to close)",
                                "WS/Hover  Enter/Click:cast"),
            "pause":      Panel("PAUSED  (Esc to close)",
                                "WS/Hover  Enter/Click:select",
                                show_info_pane=False),
            "log":        Panel("LOG  (Tab to close)",
                                "WS/Up/Down/Wheel: scroll",
                                show_info_pane=False,
                                show_cursor=False,
                                width=600),
        }
        # Pause menu is a static command list, populated once at construction.
        self._panels["pause"].set_lines([
            ("Save", False, None),
            ("Load", False, None),
            ("Exit", False, None),
        ])

        self._keys:      dict = {}
        # Mouse callbacks per panel: {panel_key: {"use", "drop", "close"}}.
        # main.py registers these via bind_panel_actions when a panel opens;
        # _dispatch_panel_mouse looks them up to fire the matching game action.
        self._panel_actions: dict = {}
        self._scheduled: list = []
        self.animating_cells: list = []
        self._ui_blocked = False
        self.maze_size = (10,10)
        self.night = -1

    # -- Shim properties (entity.py uses win.inventory_show etc.) -------------

    @property
    def inventory_show(self):            return self._panels["inventory"].visible
    @inventory_show.setter
    def inventory_show(self, v):         self._panels["inventory"].visible = v

    @property
    def spell_list_show(self):           return self._panels["spell_list"].visible
    @spell_list_show.setter
    def spell_list_show(self, v):        self._panels["spell_list"].visible = v

    @property
    def pause_show(self):                return self._panels["pause"].visible
    @pause_show.setter
    def pause_show(self, v):             self._panels["pause"].visible = v

    @property
    def log_show(self):                  return self._panels["log"].visible
    @log_show.setter
    def log_show(self, v):               self._panels["log"].visible = v

    # -- Camera ----------------------------------------------------------------

    @property
    def camera(self): return self._camera_x, self._camera_y

    def center_on_point(self, x, y):
        self._camera_x = self.w / 2 - x
        self._camera_y = self.h / 2 - y

    # -- Key bindings ----------------------------------------------------------
    def bind(self, key, callback):    self._keys[key] = callback
    def bind_keys(self,keys:tuple,callback):
        if isinstance(keys, tuple):
            for key in keys: self.bind(key,callback)
        else:
            self.bind(keys,callback)
    def unbind(self, key):            self._keys.pop(key, None)
    def unbind_all(self):             self._keys.clear()

    # -- Panel mouse-action bindings ------------------------------------------
    # Mirrors bind/unbind for keyboard, but for the per-panel mouse dispatcher.
    # `use`  fires on left-click of a row (or close/scroll-track miss-fall-through)
    # `drop` fires on right-click of a row (set to None to disable, e.g. spells)
    # `close` fires on click of the panel's X button.
    def bind_panel_actions(self, panel_key, *, use=None, drop=None, close=None):
        self._panel_actions[panel_key] = {"use": use, "drop": drop, "close": close}

    def unbind_panel_actions(self, panel_key=None):
        if panel_key is None:
            self._panel_actions.clear()
        else:
            self._panel_actions.pop(panel_key, None)

    # -- Scheduling ------------------------------------------------------------

    def after(self, ms, callback):
        self._scheduled.append((pygame.time.get_ticks() + ms, callback))

    def _fire_scheduled(self):
        now = pygame.time.get_ticks()
        due = [(t, cb) for t, cb in self._scheduled if t <= now]
        self._scheduled = [(t, cb) for t, cb in self._scheduled if t > now]
        for _, cb in due:
            cb()

    # -- Combat log ------------------------------------------------------------

    def log(self, message: str):
        if not message:
            return
        self._log.append(message)
        self._log_timer.append(time.time())
        if len(self._log) > 6:
            self._log.pop(0)
            self._log_timer.pop(0)
        # Persistent run history -- never trimmed; viewed via Tab.
        self._history.append(message)

    def clear_log_history(self):
        """Wipe the persistent log. Call when starting a fresh run."""
        self._history = []

    def set_log_panel(self):
        """Populate the log panel with every message from this run, word-
        wrapped to the panel's width, and jump the view to the bottom so the
        most recent messages are on screen."""
        panel = self._panels["log"]
        max_w = panel.width - 24  # match left/right padding used in _draw_panel
        lines: list = []
        for msg in self._history:
            for sub in self._wrap_text(msg, max_w, size="sm"):
                lines.append((sub, False, None))
        panel.set_lines(lines)
        # Jump to the bottom. _visible_count is recomputed each draw, so we
        # set scroll high and let _clamp_scroll pull it to the right value.
        panel.scroll = len(lines)
        panel.cursor = max(0, len(lines) - 1)

    # -- HUD updates -----------------------------------------------------------

    def set_level(self, lvl):
        self._level_str = f"level: {lvl}"

    def set_player_stats(self, player):
        self._hp_str   = f"HP: {player.health}/{player.max_health}"
        self._mp_str = f"MP: {player.mana}/{player.max_mana}"
        self._gold_str = f"Gold: {player.gold}"


    # -- Panel population ------------------------------------------------------

    def set_inventory(self, player):
        """Build inventory lines as (display_text, is_header, item_obj | None)."""
        lines = []
        for category, items in player.inventory.items.items():
            if not items:
                continue
            lines.append((category, True, None))
            counts: dict = {}
            for item in items:
                counts[item] = counts.get(item, 0) + 1
            for item, count in counts.items():
                label = f"{count}x {item.name}" if count > 1 else item.name
                lines.append((label, False, item))
        self._panels["inventory"].set_lines(lines)

    def set_spell_list(self, player):
        # Store the Magic object on each line (third tuple element), mirroring
        # set_inventory. This lets _draw_panel hand the spell to
        # _build_item_rows, which already knows how to render MP cost, cast
        # range, elements, and the spell description.
        lines = [(name, False, spell)
                 for name, spell in player.get_spells().items()]
        self._panels["spell_list"].set_lines(lines)

    # -- Panel cursor / selection ----------------------------------------------

    def panel_cursor_move(self, panel_key: str, delta: int):
        panel = self._panels[panel_key]
        # Read-only panels (log) have no cursor concept -- W/S/Up/Down
        # scrolls the viewport directly. The held-key auto-repeat in main.py
        # routes through here too, so holding the key just keeps scrolling.
        if not panel.show_cursor:
            panel.scroll_by(delta)
        else:
            panel.move_cursor(delta)

    def panel_selected_name(self, panel_key: str) -> str:
        return self._panels[panel_key].selected_name()

    def panel_selected_item(self, panel_key: str):
        """Return the Item object at the panel's cursor, or None for headers
        / panels that don't store items (spell list, pause menu)."""
        return self._panels[panel_key].selected_item()

    # -- Level-up screen (blocking sub-loop) -----------------------------------

    async def show_level_up(self, player):
        self._ui_blocked = True
        options = ["attack", "defence", "luck",
                   "magic_defence", "magic_attack", "agility"]
        cursor = [0]
        points = [3]

        def render():
            self.surface.fill(BG)
            self.txt(f"LEVEL UP!  Now level {player.level}",
                     self.w // 2, self.h // 4, "lg", LEVEL_COL, center=True)
            self.txt(f"  {points[0]} point(s) remaining — choose a stat:",
                     self.w // 2, self.h // 4 + 40, "md", TEXT, center=True)
            for i, stat in enumerate(options):
                y   = self.h // 4 + 85 + i * 30
                pre = "▶ " if i == cursor[0] else "  "
                c   = HIGHLIGHT_FG if i == cursor[0] else TEXT
                self.txt(f"{pre}{stat}: {player.stats[stat]}",
                         self.w // 2 - 80, y, "md", c)
            self.txt("W/up S/down navigate    Enter/E to pick",
                     self.w // 2, self.h * 3 // 4, "sm", MUTED, center=True)
            pygame.display.flip()
            self.clock.tick(30)

        render()
        while points[0] > 0:
            await asyncio.sleep(0)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    # Browser-safe shutdown: SystemExit is caught cleanly by
                    # pygbag's runtime. Calling pygame.quit() in WASM can
                    # corrupt the heap.
                    if sys.platform == "emscripten":
                        raise SystemExit
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN:
                    if ev.key in (pygame.K_UP, pygame.K_w):
                        cursor[0] = (cursor[0] - 1) % len(options)
                    elif ev.key in (pygame.K_DOWN, pygame.K_s):
                        cursor[0] = (cursor[0] + 1) % len(options)
                    elif ev.key in (pygame.K_RETURN, pygame.K_e):
                        player.stats[options[cursor[0]]] += 1
                        points[0] -= 1
            render()
        self._ui_blocked = False

    # -- Game-over screen ------------------------------------------------------

    def show_game_over(self, player, maze, on_retry, on_quit):
        score = ((player.gold // 10) + player.kills) * maze.level
        self._game_over = True
        self._go_text   = f"SCORE: {score}\n\nGAME OVER\n\nTRY AGAIN?\n  Y)   (N"
        # Make sure nothing left _ui_blocked set -- if it is, the main loop
        # will skip redraw() and the game-over overlay will never appear.
        self._ui_blocked = False
        self.unbind_all()
        self.bind(pygame.K_y, on_retry)
        self.bind(pygame.K_n, on_quit)
        self.bind(pygame.K_ESCAPE, on_quit)


    def show_win(self, player, maze, on_retry, on_quit):
        score = 1000 + ((player.gold // 10) + player.kills) * maze.level
        self._game_over = True
        self._go_text = f"SCORE: {score}\n\nYOU WON!!!\n\nTRY AGAIN?\n  Y)   (N"
        self._ui_blocked = False
        self.unbind_all()
        self.bind(pygame.K_y, on_retry)
        self.bind(pygame.K_n, on_quit)
        self.bind(pygame.K_ESCAPE, on_quit)

    # -- Render pass -----------------------------------------------------------

    def render(self):
        self._draw_hud()
        # Dim the game world behind the pause menu so it reads as modal.
        if self._panels["pause"].visible:
            dim = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 140))
            self.surface.blit(dim, (0, 0))
        for panel in self._panels.values():
            if panel.visible:
                self._draw_panel(panel)
        self._draw_log()
        if self._game_over:
            self._draw_game_over()

    def txt(self, text, x, y, size="md", colour=TEXT, center=False):
        surf = self.font[size].render(text, True, colour)
        if center:
            x -= surf.get_width() // 2
        self.surface.blit(surf, (x, y))
        return surf.get_width(), surf.get_height()

    def _draw_hud(self):
        self.txt(self._level_str, self.w // 2, 10, "md", LEVEL_COL, center=True)
        self.txt(self._hp_str,    16, 10, "md", HP_COL)
        self.txt(self._mp_str,    32 + self.font["md"].size(self._hp_str)[0], 10, "md", MP_COL)
        self.txt(self._gold_str,  16, self.h - 28, "md", GOLD)
        hint = "WASD/Arrows:Move  Shift+dir:Face  E:Pick up  I:Inventory C:Cast  Tab:Log"
        save_hint = "SAVE F5 / LOAD F9"
        self.txt(hint, self.w - 10 - self.font["md"].size(hint)[0],
                 self.h - 20, "md", TEXT)
        self.txt(save_hint, self.w - 10 - self.font["sm"].size(save_hint)[0],
                 10, "sm", TEXT)

    def _wrap_text(self, text: str, max_w: int, size="sm") -> list:
        """Word-wrap text into lines no wider than max_w pixels."""
        words = text.split()
        lines, current = [], ""
        for word in words:
            test = current + word + " "
            if self.font[size].size(test)[0] <= max_w:
                current = test
            else:
                if current:
                    lines.append(current.rstrip())
                current = word + " "
        if current.strip():
            lines.append(current.rstrip())
        return lines or [""]

    def _build_item_rows(self, item, max_w: int) -> list:
        """Build display rows directly from an item object -- no repr parsing."""
        from classes import Weapon, Armour, Healing, Magic, Staff, Throwing

        rows = []

        def kv(key, val, col=TEXT):
            rows.append({"kind": "kv", "key": key, "val": val, "col": col})

        def divider():
            if rows and rows[-1]["kind"] != "divider":
                rows.append({"kind": "divider"})

        def text_rows(txt, col=TEXT):
            for line in self._wrap_text(txt.strip(), max_w):
                rows.append({"kind": "text", "text": line, "col": col})

        def nonzero_dict(d):
            return [(k, v) for k, v in d.items() if v not in (0, 0.0, "0", "0.0", "0.00")]

        # -- Value -------------------------------------------------------------
        if hasattr(item, "value") and item.value:
            kv("Value", f"{item.value} G", GOLD)

        # -- Attack ------------------------------------------------------------
        if isinstance(item, Weapon) and item.attack != -1:
            kv("Attack", str(item.attack), HP_COL)

        # -- Throw / cast range ------------------------------------------------
        if isinstance(item, Throwing):
            kv("Range", str(item.distance))
        elif isinstance(item, Magic):
            kv("MP Cost", str(item.cost), MP_COL)
            kv("Cast Range", str(item.distance))

        # -- Elements / damage types -------------------------------------------
        if isinstance(item, Magic):
            elements = item.elements
        elif isinstance(item, Weapon):
            elements = item.elements
        else:
            elements = []

        seen = set()
        elem_list = []
        for e in elements:
            key = (e.type.lower(), e.damage)
            if key not in seen:
                seen.add(key)
                elem_list.append(e)

        if elem_list:
            divider()
            rows.append({"kind": "text", "text": "Damage Types", "col": GOLD})
            for e in elem_list:
                kv("  " + e.type.capitalize(), str(e.damage), HIGHLIGHT_FG)

        # -- Healing -----------------------------------------------------------
        if isinstance(item, Healing) and item.healing:
            divider()
            rows.append({"kind": "text", "text": "Heals", "col": GOLD})
            for e in item.healing:
                kv("  " + e.type.capitalize(), "+" + str(e.damage), (80, 210, 100))

        # -- Spells on staff ---------------------------------------------------
        if isinstance(item, Staff) and item.spells:
            divider()
            rows.append({"kind": "text", "text": "Spells", "col": GOLD})
            for spell_name in item.spells:
                rows.append({"kind": "text", "text": "  " + spell_name, "col": MP_COL})

        # -- Stat bonuses ------------------------------------------------------
        if hasattr(item, "stat_bonuses"):
            nz = nonzero_dict(item.stat_bonuses)
            if nz:
                divider()
                rows.append({"kind": "text", "text": "Stat Bonuses", "col": GOLD})
                for k, v in nz:
                    label = k.replace("_", " ").title()
                    col   = (HP_COL if "attack" in k else
                             MP_COL if "magic"  in k else HIGHLIGHT_FG)
                    prefix = "+" if v >= 0 else ""
                    kv("  " + label, f"{prefix}{v}", col)

        # -- Resistances -------------------------------------------------------
        if isinstance(item, Armour):
            nz = nonzero_dict(item.resistances)
            if nz:
                divider()
                rows.append({"kind": "text", "text": "Resistances", "col": GOLD})
                for k, v in nz:
                    kv("  " + k.capitalize(), f"{v:.0%}", HIGHLIGHT_FG)

        # -- Description -------------------------------------------------------
        desc = getattr(item, "_description", None)
        if desc is None:
            desc = getattr(item, "description", "") or ""
        # For Magic, use spell_description
        if isinstance(item, Magic):
            desc = getattr(item, "spell_description", "") or desc
        if desc:
            divider()
            for line in self._wrap_text(desc, max_w):
                rows.append({"kind": "text", "text": line, "col": MUTED})

        if not rows:
            text_rows(item.name)

        return rows


    def _draw_panel(self, panel: Panel):
        """Single method draws any panel -- inventory and spell list both use this."""
        pw = panel.width
        ph = min(self.h - 120, len(panel.lines) * 20 + 80)
        px = (self.w - pw) // 1.5
        py = 50

        # Reset cached layout -- _dispatch_panel_mouse iterates these, so any
        # stale entries from a previous frame would mis-route hits.
        panel.row_rects  = []
        panel.close_rect = None
        panel.track_rect = None
        panel.thumb_rect = None

        # Geometry of the scrollable list area (between title divider and hint)
        list_top    = py + 36
        list_bottom = py + ph - 4
        avail_h     = max(0, list_bottom - list_top)
        # How many 20px rows fit in the viewport this frame.
        panel._visible_count = max(1, avail_h // 20)
        panel._clamp_scroll()

        needs_scrollbar = len(panel.lines) > panel._visible_count
        # Reserve a 14px gutter for the scrollbar so highlights / row hit
        # rects don't sit underneath it.
        sb_gutter   = 14 if needs_scrollbar else 0
        list_right  = px + pw - sb_gutter

        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        surf.fill(PANEL)
        self.surface.blit(surf, (px, py))
        pygame.draw.rect(self.surface, BORDER, (px, py, pw, ph), 1)
        self.txt(panel.title, px + 10, py + 8, "md", LEVEL_COL)
        pygame.draw.line(self.surface, BORDER, (px, py + 30), (px + pw, py + 30), 1)

        # -- Close button (X) in the top-right of the title bar ---------------
        mp = pygame.mouse.get_pos()
        close_size = 20
        cx = px + pw - close_size - 4
        cy = py + 4
        panel.close_rect = pygame.Rect(cx, cy, close_size, close_size)
        close_hover = panel.close_rect.collidepoint(mp)
        close_col = HP_COL if close_hover else MUTED
        pygame.draw.rect(self.surface, close_col, panel.close_rect,
                         width=1, border_radius=3)
        # Draw the X as two crossed lines (cleaner than a glyph at this size)
        pad = 5
        pygame.draw.line(self.surface, close_col,
                         (cx + pad, cy + pad),
                         (cx + close_size - pad, cy + close_size - pad), 2)
        pygame.draw.line(self.surface, close_col,
                         (cx + close_size - pad, cy + pad),
                         (cx + pad, cy + close_size - pad), 2)

        # -- Scrollable list of lines -----------------------------------------
        start = panel.scroll
        end   = min(len(panel.lines), start + panel._visible_count)
        y = list_top
        for i in range(start, end):
            text, is_hdr = panel.lines[i][0], panel.lines[i][1]
            # Row hit-test rect spans the full visible row width (minus the
            # scrollbar gutter). Stored so _dispatch_panel_mouse can map a
            # click position back to a line index.
            row_rect = pygame.Rect(px + 2, y - 1,
                                   list_right - (px + 2) - 2, 20)
            panel.row_rects.append((row_rect, i))

            if is_hdr:
                self.txt(text, px + 10, y, "sm", GOLD)
            elif i == panel.cursor and panel.show_cursor:
                pygame.draw.rect(self.surface, HIGHLIGHT_BG,
                                 (px + 2, y - 1,
                                  list_right - (px + 2) - 2, 18))
                self.txt(text, px + 10, y, "sm", HIGHLIGHT_FG)
            else:
                self.txt(text, px + 10, y, "sm", TEXT)
            y += 20

        # -- Scrollbar (only when content overflows) --------------------------
        if needs_scrollbar:
            track_x = px + pw - 11
            track_y = list_top
            track_w = 7
            track_h = avail_h
            panel.track_rect = pygame.Rect(track_x, track_y, track_w, track_h)
            pygame.draw.rect(self.surface, (40, 35, 50),
                             panel.track_rect, border_radius=3)
            # Thumb height is proportional to fraction visible; min size keeps
            # it grabbable for very long lists.
            thumb_h = max(20, int(track_h * panel._visible_count / len(panel.lines)))
            max_scroll = max(1, len(panel.lines) - panel._visible_count)
            thumb_y = track_y + int((track_h - thumb_h) * panel.scroll / max_scroll)
            panel.thumb_rect = pygame.Rect(track_x, thumb_y, track_w, thumb_h)
            thumb_hover = (panel.thumb_rect.collidepoint(mp)
                           or panel._drag_offset is not None)
            thumb_col = HIGHLIGHT_FG if thumb_hover else BORDER
            pygame.draw.rect(self.surface, thumb_col,
                             panel.thumb_rect, border_radius=3)

        # -- Right-side info pane (unchanged behavior) ------------------------
        cur_item = panel.selected_item()
        if not panel.show_info_pane:
            # Pause menu (and any future command-list panels) skip the right pane.
            item_title = None
            rows = []
        elif cur_item is not None:
            item_title = cur_item.name
            rows = self._build_item_rows(cur_item, pw - 24)
        elif panel.lines:
            # No item object on this row (e.g. spell list): drive the title
            # straight from the panel's cursor so it's correct on first open,
            # not just after the user has pressed W/S.
            name = panel.selected_name()
            item_title = name or None
            rows = [{"kind": "text", "text": name, "col": TEXT}] if name else []
        else:
            item_title = None
            rows = []

        if item_title:

            ix = px + pw
            iy = py
            ih = min(self.h - 120, len(rows) * 20 + 80)
            info_surf = pygame.Surface((pw, ih), pygame.SRCALPHA)
            info_surf.fill(PANEL)
            self.surface.blit(info_surf, (ix, iy))
            pygame.draw.rect(self.surface, BORDER, (ix, iy, pw, ih), 1)
            self.txt(item_title, ix + 10, iy + 8, "md", LEVEL_COL)
            pygame.draw.line(self.surface, BORDER, (ix, iy + 30), (ix + pw, iy + 30), 1)

            y = iy + 36
            for row in rows:
                if y > iy + ih - 20:
                    break
                kind = row.get("kind", "text")
                if kind == "divider":
                    pygame.draw.line(self.surface, BORDER,
                                     (ix + 8, y + 8), (ix + pw - 8, y + 8), 1)
                    y += 16
                    continue
                elif kind == "kv":
                    key_w, _ = self.txt(row["key"] + ": ", ix + 10, y, "sm", MUTED)
                    self.txt(row["val"], ix + 10 + key_w, y, "sm", row.get("col", TEXT))
                elif kind == "text":
                    self.txt(row["text"], ix + 10, y, "sm", row.get("col", TEXT))
                y += 20



        self.txt(panel.hint, px + 4, py + ph + 4, "sm", TEXT)

    def _draw_log(self):
        now  = time.time()
        x, y = 16, self.h // 2
        for msg, t in zip(self._log, self._log_timer):
            alpha = max(0, int(255 * (1 - (now - t) / 4.0)))
            if not alpha:
                continue
            surf = self.font["sm"].render(msg, True, TEXT)
            surf.set_alpha(alpha)
            self.surface.blit(surf, (x, y))
            y += 18

    def _draw_game_over(self):
        overlay = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        self.surface.blit(overlay, (0, 0))
        y = self.h // 3
        for line in self._go_text.split("\n"):
            c  = GAMEOVER_COL if ("GAME OVER" in line or "SCORE" in line) else TEXT
            sz = "lg" if "GAME OVER" in line else "md"
            self.txt(line, self.w // 2, y, sz, c, center=True)
            y += FONT_SIZE[sz] + 10

    # -- Frame loop ------------------------------------------------------------

    def tick(self):
        self._fire_scheduled()
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

        # Find the visible panel for mouse routing. Only one panel is open
        # at a time per the state machine in main.py, but if that ever
        # changes the first-found wins (matches dict iteration order).
        active_panel_key = None
        for k, p in self._panels.items():
            if p.visible:
                active_panel_key = k
                break

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.VIDEORESIZE and sys.platform != "emscripten":
                self.w, self.h = ev.w, ev.h
                self._screen = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
                self.surface = self._screen
            if ev.type == pygame.KEYDOWN:
                # ESC is no longer hard-wired to quit; the game binds it to
                # open the pause menu, and the pause menu binds it to close.
                key = ("shift", ev.key) if shift else ev.key
                cb  = self._keys.get(key)
                if cb:
                    cb()
            # Mouse events route to whichever panel is open, if any.
            if active_panel_key is not None and ev.type in (
                pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN,
                pygame.MOUSEBUTTONUP, pygame.MOUSEWHEEL,
            ):
                self._dispatch_panel_mouse(active_panel_key, ev)
        return True

    def _dispatch_panel_mouse(self, panel_key: str, ev):
        """Route a single mouse event to the panel identified by `panel_key`.

        Order of precedence on a left click:
          1. Close button (X)
          2. Scrollbar thumb -> begin drag (handled in MOUSEMOTION too)
          3. Scrollbar track  -> page up / page down toward the click
          4. List row         -> set cursor to that row + fire `use` action
        Right click on a row fires `drop` if the panel registered one.
        Mouse wheel scrolls the list (3 lines per notch) without moving the
        cursor -- it's a viewport-only operation.
        """
        panel   = self._panels[panel_key]
        actions = self._panel_actions.get(panel_key, {})

        if ev.type == pygame.MOUSEMOTION:
            # If a thumb-drag is in progress, route motion straight to scroll.
            if panel._drag_offset is not None and panel.track_rect and panel.thumb_rect:
                track    = panel.track_rect
                thumb_h  = panel.thumb_rect.height
                avail    = max(1, track.height - thumb_h)
                rel_y    = ev.pos[1] - track.y - panel._drag_offset
                ratio    = max(0.0, min(1.0, rel_y / avail))
                max_scr  = max(0, len(panel.lines) - panel._visible_count)
                panel.scroll = int(round(ratio * max_scr))
                panel._clamp_scroll()
                return
            # Read-only panels (log) ignore row hover -- there's no cursor to
            # move and no row-level action to telegraph.
            if not panel.show_cursor:
                return
            # Otherwise: hover -> move cursor to the hovered row (skip headers).
            for rect, line_idx in panel.row_rects:
                if rect.collidepoint(ev.pos):
                    if 0 <= line_idx < len(panel.lines) and not panel.lines[line_idx][1]:
                        panel.cursor = line_idx
                    break
            return

        if ev.type == pygame.MOUSEBUTTONUP:
            # Always release the drag, regardless of which button -- this
            # avoids a "stuck" thumb if the user right-clicks mid-drag.
            panel._drag_offset = None
            return

        if ev.type == pygame.MOUSEWHEEL:
            # Wheel up (ev.y > 0) -> show content above -> scroll value down.
            panel.scroll_by(-ev.y * 3)
            return

        if ev.type == pygame.MOUSEBUTTONDOWN:
            if ev.button == 1:
                # 1) Close (X)
                if panel.close_rect and panel.close_rect.collidepoint(ev.pos):
                    cb = actions.get("close")
                    if cb:
                        cb()
                    return
                # 2) Thumb -> start drag
                if panel.thumb_rect and panel.thumb_rect.collidepoint(ev.pos):
                    panel._drag_offset = ev.pos[1] - panel.thumb_rect.y
                    return
                # 3) Track (above/below thumb) -> page scroll toward click
                if panel.track_rect and panel.track_rect.collidepoint(ev.pos):
                    if panel.thumb_rect and ev.pos[1] < panel.thumb_rect.y:
                        panel.scroll_by(-panel._visible_count)
                    else:
                        panel.scroll_by(panel._visible_count)
                    return
                # 4) Row -> select + use
                # Read-only panels (log) skip this -- the X / scrollbar /
                # mouse wheel above still work.
                if not panel.show_cursor:
                    return
                for rect, line_idx in panel.row_rects:
                    if rect.collidepoint(ev.pos):
                        if 0 <= line_idx < len(panel.lines) and not panel.lines[line_idx][1]:
                            panel.cursor = line_idx
                            cb = actions.get("use")
                            if cb:
                                cb()
                        return
            elif ev.button == 3:
                # Right click -> drop (only if the panel registered a drop_fn)
                drop_fn = actions.get("drop")
                if drop_fn is None:
                    return
                if not panel.show_cursor:
                    return
                for rect, line_idx in panel.row_rects:
                    if rect.collidepoint(ev.pos):
                        if 0 <= line_idx < len(panel.lines) and not panel.lines[line_idx][1]:
                            panel.cursor = line_idx
                            drop_fn()
                        return

    def flip(self):
        pygame.display.flip()
        self.clock.tick(60)