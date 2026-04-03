import pygame
import sys
import time


# ---------------------------------------------------------------------------
# Palette & typography
# ---------------------------------------------------------------------------
BG           = ( 10,   8,  12)
PANEL        = ( 22,  18,  28, 220)   # RGBA — semi-transparent
BORDER       = ( 70,  55,  90)
TEXT         = (220, 215, 200)
MUTED        = (120, 110, 100)
GOLD         = (255, 210,  50)
HP_COL       = (210,  55,  55)
LEVEL_COL    = (160, 130, 255)
HIGHLIGHT_BG = ( 55,  45,  75)
HIGHLIGHT_FG = (120, 180, 255)
GAMEOVER_COL = (180,  30,  30)

FONT_SIZE = {"lg": 22, "md": 16, "sm": 13}


class Windows:
    def __init__(self, width=1280, height=800):
        pygame.init()
        self.w = width
        self.h = height
        self._screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("The Dark Cave")
        self.surface = self._screen
        self.clock   = pygame.time.Clock()

        # Fonts
        mono = pygame.font.match_font(
            "cascadiacode,consolas,jetbrainsmono,dejavusansmono,monospace"
        )
        self.font = {
            sz: pygame.font.Font(mono, pt)
            for sz, pt in FONT_SIZE.items()
        }

        # Camera offset (world → screen)
        self._camera_x = 0.0
        self._camera_y = 0.0

        # UI state
        self._level_str  = "level: 1"
        self._hp_str     = "HP: 0/0"
        self._gold_str   = "Gold: 0"
        self.inventory_show = False
        self.spell_list_show = False
        self.spell_list = []
        self.spell_list_cursor = 0
        self._inv_lines  = []        # list of (text, is_header)
        self._inv_cursor = 0
        self._info_str   = ""
        self._game_over  = False
        self._go_text    = ""
        self._log        = []        # recent combat messages
        self._log_timer  = []        # parallel: time each line was added

        # Key callbacks: pygame key (or ("shift", key)) → callable
        self._keys: dict = {}

        # Scheduled callbacks: [(fire_at_time, callable), ...]
        self._scheduled: list = []

        # Cells that are currently animating (checked every frame)
        self.animating_cells: list = []

    # -----------------------------------------------------------------------
    # Camera
    # -----------------------------------------------------------------------
    @property
    def camera(self):
        return self._camera_x, self._camera_y

    def center_on_point(self, x,y):
        self._camera_x = self.w / 2 - x
        self._camera_y = self.h / 2 - y

    # -----------------------------------------------------------------------
    # Key bindings  (clean pygame — no Tkinter strings)
    # -----------------------------------------------------------------------
    def bind(self, key, callback):
        """key: pygame.K_* constant, or ("shift", pygame.K_*) for shifted keys."""
        self._keys[key] = callback

    def unbind(self, key):
        self._keys.pop(key, None)

    def unbind_all(self):
        self._keys.clear()

    # -----------------------------------------------------------------------
    # Scheduling  (replaces canvas.after)
    # -----------------------------------------------------------------------
    def after(self, ms, callback):
        self._scheduled.append((time.time() + ms / 1000.0, callback))

    def _fire_scheduled(self):
        now = time.time()
        due, pending = [], []
        for (t, cb) in self._scheduled:
            (due if t <= now else pending).append((t, cb))
        self._scheduled = pending
        for _, cb in due:
            cb()

    # -----------------------------------------------------------------------
    # Combat log
    # -----------------------------------------------------------------------
    def log(self, message: str):
        self._log.append(message)
        self._log_timer.append(time.time())
        if len(self._log) > 6:
            self._log.pop(0)
            self._log_timer.pop(0)

    # -----------------------------------------------------------------------
    # HUD updates (called by game logic)
    # -----------------------------------------------------------------------
    def set_level(self, lvl):
        self._level_str = f"level: {lvl}"

    def set_player_stats(self, player):
        self._hp_str   = f"HP: {player.health}/{player.max_health}"
        self._gold_str = f"Gold: {player.gold}"

    def set_inventory(self, player):
        HEADERS = {"Equipped", "Armors", "Weapons", "Consumables"}
        self._inv_lines = []
        for line in str(player.inventory).split("\n"):
            s = line.strip()
            if not s or s == "-------------":
                continue
            self._inv_lines.append((s, s in HEADERS))

    def set_spell_list(self, player):
        HEADER = "SPELLS"
        self._inv_lines = []
        for line in str(player.get_spells()).split("\n"):
            s = line.strip()
            if not s or s == "-------------":
                continue
            self._inv_lines.append((s, s in HEADER))

    # -----------------------------------------------------------------------
    # Level-up screen (blocking sub-loop)
    # -----------------------------------------------------------------------
    def show_level_up(self, player):
        options = ["attack", "defence", "luck",
                   "magic_defence", "magic_attack", "agility"]
        cursor   = [0]
        points   = [3]

        def render():
            self.surface.fill(BG)
            self.txt(f"LEVEL UP!  Now level {player.level}", self.w // 2, self.h // 4, "lg", LEVEL_COL, center=True)
            self.txt(f"  {points[0]} point(s) remaining — choose a stat:", self.w // 2, self.h // 4 + 40, "md", TEXT,
                     center=True)
            for i, stat in enumerate(options):
                y = self.h//4 + 85 + i * 30
                pre = "▶ " if i == cursor[0] else "  "
                c = HIGHLIGHT_FG if i == cursor[0] else TEXT
                self.txt(f"{pre}{stat}: {player.stats[stat]}", self.w // 2 - 80, y, "md", c)
            self.txt("W/↑ S/↓ navigate    Enter/E to pick", self.w // 2, self.h * 3 // 4, "sm", MUTED, center=True)
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

    # -----------------------------------------------------------------------
    # Game over screen
    # -----------------------------------------------------------------------
    def show_game_over(self, player, maze, on_retry, on_quit):
        score = ((player.gold // 10) + player.kills) * maze.level
        self._game_over = True
        self._go_text   = f"SCORE: {score}\n\nGAME OVER\n\nTRY AGAIN?\n  Y)   (N"
        self.unbind_all()
        self.bind(pygame.K_y, lambda: on_retry())
        self.bind(pygame.K_n, lambda: on_quit())

    # -----------------------------------------------------------------------
    # Inventory cursor control
    # -----------------------------------------------------------------------
    def inv_cursor_move(self, delta):
        n = len(self._inv_lines)
        if n == 0:
            return
        new = self._inv_cursor + delta
        new = max(0, min(new, n - 1))
        # skip headers
        while 0 <= new < n and self._inv_lines[new][1]:
            new += delta
        if 0 <= new < n:
            self._inv_cursor = new
            text, _ = self._inv_lines[new]
            self._info_str = text

    def inv_selected_name(self):
        if 0 <= self._inv_cursor < len(self._inv_lines):
            return self._inv_lines[self._inv_cursor][0].split("(")[0].strip()
        return ""

    def spell_cursor_move(self, delta):
        n = len(self.spell_list)
        if n == 0:
            return
        new = self.spell_list_cursor + delta
        new = max(0, min(new, n - 1))
        # skip headers
        while 0 <= new < n and self.spell_list[new][1]:
            new += delta
        if 0 <= new < n:
            self.spell_list_cursor = new
            text, _ = self.spell_list[new]
            self._info_str = text

    def spell_selected_name(self):
        if 0 <= self.spell_list_cursor < len(self.spell_list):
            return self.spell_list[self.spell_list_cursor][0].split("(")[0].strip()
        return ""


    # -----------------------------------------------------------------------
    # Main render pass
    # -----------------------------------------------------------------------
    def render(self):
        """Draw HUD, inventory, log, game-over overlay on top of the world."""
        self._draw_hud()
        if self.inventory_show:
            self._draw_inventory()
        self._draw_log()
        if self._game_over:
            self._draw_game_over()
        if self.spell_list_show:
            self._draw_spell_list()

    def txt(self, text, x, y, size="md", colour=TEXT, center=False):
        surf = self.font[size].render(text, True, colour)
        if center:
            x -= surf.get_width() // 2
        self.surface.blit(surf, (x, y))
        return surf.get_width(), surf.get_height()

    def _draw_hud(self):
        # Level — top centre
        self.txt(self._level_str, self.w // 2, 10, "md", LEVEL_COL, center=True)
        # HP — top left
        self.txt(self._hp_str, 16, 10, "md", HP_COL)
        # Gold — bottom left
        self.txt(self._gold_str, 16, self.h - 28, "md", GOLD)
        # Controls hint — bottom right
        hint = "WASD/Arrows:Move  Shift+dir:Face  E:Pick up  I:Inventory"
        self.txt(hint, self.w - 10 - self.font["sm"].size(hint)[0], self.h - 22, "sm", MUTED)

    def _draw_inventory(self):
        pw, ph = 300, min(self.h - 120, len(self._inv_lines) * 20 + 80)
        px, py = (self.w - pw) // 2, 50

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(PANEL)
        self.surface.blit(panel, (px, py))
        pygame.draw.rect(self.surface, BORDER, (px, py, pw, ph), 1)

        self.txt("INVENTORY  (I to close)", px + 10, py + 8, "md", LEVEL_COL)
        pygame.draw.line(self.surface, BORDER, (px, py+30), (px+pw, py+30), 1)

        y = py + 36
        for i, (text, is_hdr) in enumerate(self._inv_lines):
            if y > py + ph - 24:
                break
            label = text.split("(")[0].strip()
            if is_hdr:
                self.txt(label, px + 10, y, "sm", GOLD)
            elif i == self._inv_cursor:
                pygame.draw.rect(self.surface, HIGHLIGHT_BG,
                                 (px+2, y-1, pw-4, 18))
                self.txt(label, px + 10, y, "sm", HIGHLIGHT_FG)
            else:
                self.txt(label, px + 10, y, "sm", TEXT)
            y += 20

        if self._info_str:
            self.txt(self._info_str[:50], px + 4, py + ph - 20, "sm", MUTED)

        self.txt("W/S:navigate  Enter/E:use", px + 4, py + ph + 4, "sm", MUTED)

    def _draw_spell_list(self):
        pw, ph = 300, min(self.h - 120, len(self.spell_list) * 20 + 80)
        px, py = (self.w - pw) // 2, 50

        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill(PANEL)
        self.surface.blit(panel, (px, py))
        pygame.draw.rect(self.surface, BORDER, (px, py, pw, ph), 1)

        self.txt("spells  (c to close)", px + 10, py + 8, "md", LEVEL_COL)
        pygame.draw.line(self.surface, BORDER, (px, py+30), (px+pw, py+30), 1)

        y = py + 36
        for i, (text, is_hdr) in enumerate(self.spell_list):
            if y > py + ph - 24:
                break
            label = text.split("(")[0].strip()
            if is_hdr:
                self.txt(label, px + 10, y, "sm", GOLD)
            elif i == self.spell_list_cursor:
                pygame.draw.rect(self.surface, HIGHLIGHT_BG,
                                 (px+2, y-1, pw-4, 18))
                self.txt(label, px + 10, y, "sm", HIGHLIGHT_FG)
            else:
                self.txt(label, px + 10, y, "sm", TEXT)
            y += 20

        if self._info_str:
            self.txt(self._info_str[:50], px + 4, py + ph - 20, "sm", MUTED)

        self.txt("W/S:navigate  Enter/E:cast", px + 4, py + ph + 4, "sm", MUTED)

    def _draw_log(self):
        """Show recent combat messages, fading after 4 s."""
        now  = time.time()
        x, y = 16, self.h // 2
        for msg, t in zip(self._log, self._log_timer):
            age   = now - t
            alpha = max(0, int(255 * (1 - age / 4.0)))
            if alpha == 0:
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
            c = GAMEOVER_COL if ("GAME OVER" in line or "SCORE" in line) else TEXT
            sz = "lg" if "GAME OVER" in line else "md"
            self.txt(line, self.w // 2, y, sz, c, center=True)
            y += FONT_SIZE[sz] + 10

    # -----------------------------------------------------------------------
    # Frame loop
    # -----------------------------------------------------------------------
    def tick(self):
        """Process events + fire scheduled callbacks. Returns False if quit."""
        self._fire_scheduled()

        mods  = pygame.key.get_mods()
        shift = bool(mods & pygame.KMOD_SHIFT)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return False
            if ev.type == pygame.VIDEORESIZE:
                self.w, self.h = ev.w, ev.h
                self._screen = pygame.display.set_mode(
                    (self.w, self.h), pygame.RESIZABLE)
                self.surface = self._screen
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