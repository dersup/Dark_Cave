import pygame
import sys
import time

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
MP_COL       = ( 60, 120, 255)
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

    def __init__(self, title: str, hint: str):
        self.title   = title
        self.hint    = hint
        self.lines   = []   # list of (text, is_header)
        self.cursor  = 0
        self.visible = False

    def set_lines(self, lines: list):
        self.lines  = lines
        self.cursor = 0

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
        return self.lines[self.cursor][0]

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

        mono = pygame.font.match_font(
            "cascadiacode,consolas,jetbrainsmono,dejavusansmono,monospace"
        )
        self.font = {sz: pygame.font.Font(mono, pt) for sz, pt in FONT_SIZE.items()}

        self._camera_x = 0.0
        self._camera_y = 0.0

        self._level_str = "level: 1"
        self._hp_str    = "HP: 0/0"
        self._mp_str    = "MP: 0/0"
        self._gold_str  = "Gold: 0"
        self._info_str  = ""
        self._game_over = False
        self._go_text   = ""
        self._log       = []
        self._log_timer = []

        # All panels live here; adding a new one is one line.
        self._panels = {
            "inventory":  Panel("INVENTORY  (I to close)", "W/S:navigate  Enter/E:use"),
            "spell_list": Panel("SPELLS  (C to close)",    "W/S:navigate  Enter/E:cast"),
        }

        self._keys:      dict = {}
        self._scheduled: list = []
        self.animating_cells: list = []

    # ── Shim properties (entity.py uses win.inventory_show etc.) ─────────────

    @property
    def inventory_show(self):            return self._panels["inventory"].visible
    @inventory_show.setter
    def inventory_show(self, v):         self._panels["inventory"].visible = v

    @property
    def spell_list_show(self):           return self._panels["spell_list"].visible
    @spell_list_show.setter
    def spell_list_show(self, v):        self._panels["spell_list"].visible = v

    # ── Camera ────────────────────────────────────────────────────────────────

    @property
    def camera(self): return self._camera_x, self._camera_y

    def center_on_point(self, x, y):
        self._camera_x = self.w / 2 - x
        self._camera_y = self.h / 2 - y

    # ── Key bindings ──────────────────────────────────────────────────────────

    def bind(self, key, callback):    self._keys[key] = callback
    def unbind(self, key):            self._keys.pop(key, None)
    def unbind_all(self):             self._keys.clear()

    # ── Scheduling ────────────────────────────────────────────────────────────

    def after(self, ms, callback):
        self._scheduled.append((time.time() + ms / 1000.0, callback))

    def _fire_scheduled(self):
        now  = time.time()
        due  = [(t, cb) for t, cb in self._scheduled if t <= now]
        self._scheduled = [(t, cb) for t, cb in self._scheduled if t > now]
        for _, cb in due:
            cb()

    # ── Combat log ────────────────────────────────────────────────────────────

    def log(self, message: str):
        if not message:
            return
        self._log.append(message)
        self._log_timer.append(time.time())
        if len(self._log) > 6:
            self._log.pop(0)
            self._log_timer.pop(0)

    # ── HUD updates ───────────────────────────────────────────────────────────

    def set_level(self, lvl):
        self._level_str = f"level: {lvl}"

    def set_player_stats(self, player):
        self._hp_str   = f"HP: {player.health}/{player.max_health}"
        self._gold_str = f"Gold: {player.gold}"

    # ── Panel population ──────────────────────────────────────────────────────

    def _build_lines(self, text: str, headers: set) -> list:
        return [
            (s, s in headers)
            for line in text.replace(",","\n").split("\n")
            if (s := line.strip().strip("[").strip("]")) and s != "-------------"
        ]

    def set_inventory(self, player):
        self._panels["inventory"].set_lines(
            self._build_lines(str(player.inventory),
                              {"Equipped", "Armors", "Weapons", "Consumables"})
        )

    def set_spell_list(self, player):
        self._panels["spell_list"].set_lines(
            self._build_lines(str(list(player.get_spells().keys())), {"SPELLS"})
        )

    # ── Panel cursor / selection ──────────────────────────────────────────────

    def panel_cursor_move(self, panel_key: str, delta: int):
        text = self._panels[panel_key].move_cursor(delta)
        if text is not None:
            self._info_str = text

    def panel_selected_name(self, panel_key: str) -> str:
        return self._panels[panel_key].selected_name()

    # Legacy shims
    def inv_cursor_move(self, delta):   self.panel_cursor_move("inventory",  delta)
    def spell_cursor_move(self, delta): self.panel_cursor_move("spell_list", delta)
    def inv_selected_name(self):        return self.panel_selected_name("inventory")
    def spell_selected_name(self):      return self.panel_selected_name("spell_list")

    # ── Level-up screen (blocking sub-loop) ───────────────────────────────────

    def show_level_up(self, player):
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
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
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

    # ── Game-over screen ──────────────────────────────────────────────────────

    def show_game_over(self, player, maze, on_retry, on_quit):
        score = ((player.gold // 10) + player.kills) * maze.level
        self._game_over = True
        self._go_text   = f"SCORE: {score}\n\nGAME OVER\n\nTRY AGAIN?\n  Y)   (N"
        self.unbind_all()
        self.bind(pygame.K_y, on_retry)
        self.bind(pygame.K_n, on_quit)

    # ── Render pass ───────────────────────────────────────────────────────────

    def render(self):
        self._draw_hud()
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
        self.txt(self._mp_str,    27, 10, "md", MP_COL)
        self.txt(self._gold_str,  16, self.h - 28, "md", GOLD)
        hint = "WASD/Arrows:Move  Shift+dir:Face  E:Pick up  I:Inventory C:Cast"
        save_hint = "SAVE F5 / LOAD F6"
        self.txt(hint, self.w - 10 - self.font["sm"].size(hint)[0],
                 self.h - 20, "sm", TEXT)
        self.txt(save_hint, self.w - 10 - self.font["sm"].size(save_hint)[0],
                 self.h -10, "sm", save_hint)

    def _draw_panel(self, panel: Panel):
        """Single method draws any panel — inventory and spell list both use this."""
        pw = 300
        ph = min(self.h - 120, len(panel.lines) * 20 + 80)
        px = (self.w - pw) // 2
        py = 50

        surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
        surf.fill(PANEL)
        self.surface.blit(surf, (px, py))
        pygame.draw.rect(self.surface, BORDER, (px, py, pw, ph), 1)

        self.txt(panel.title, px + 10, py + 8, "md", LEVEL_COL)
        pygame.draw.line(self.surface, BORDER, (px, py + 30), (px + pw, py + 30), 1)

        y = py + 36
        for i, (text, is_hdr) in enumerate(panel.lines):
            if y > py + ph - 24:
                break
            for out in [" ",")","[","]"]:
                text.strip(out)
            label = text.split("(")[0]
            if is_hdr:
                self.txt(label, px + 10, y, "sm", GOLD)
            elif i == panel.cursor:
                pygame.draw.rect(self.surface, HIGHLIGHT_BG, (px + 2, y - 1, pw - 4, 18))
                self.txt(label, px + 10, y, "sm", HIGHLIGHT_FG)
            else:
                self.txt(label, px + 10, y, "sm", TEXT)
            y += 20

        if self._info_str:
            self.txt(self._info_str[:50], px + 4, py + ph - 20, "sm", MUTED)
        self.txt(panel.hint, px + 4, py + ph + 4, "sm", MUTED)

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

    # ── Frame loop ────────────────────────────────────────────────────────────

    def tick(self):
        self._fire_scheduled()
        shift = bool(pygame.key.get_mods() & pygame.KMOD_SHIFT)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.VIDEORESIZE:
                self.w, self.h = ev.w, ev.h
                self._screen   = pygame.display.set_mode((self.w, self.h), pygame.RESIZABLE)
                self.surface   = self._screen
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return False
                key = ("shift", ev.key) if shift else ev.key
                cb  = self._keys.get(key)
                if cb:
                    cb()
        return True

    def flip(self):
        pygame.display.flip()
        self.clock.tick(60)