import pygame
import random
import sys
import asyncio
from collections import deque
from pathlib import Path

from drawing import Cell, Point
from entity import Entity
from generator_ import generate_enemy
def _quit_app():
    """Clean shutdown that works on desktop and in pygbag."""
    if sys.platform == "emscripten":
        # In browser, SystemExit is caught by pygbag's runtime and the tab
        # returns to idle. Calling pygame.quit() here can crash the WASM heap.
        raise SystemExit
    pygame.quit()
    sys.exit()


class Maze:
    def __init__(self, num_rows, num_cols, win):
        self.num_rows  = num_rows
        self.num_cols  = num_cols
        self._win      = win
        self.CELL_SIZE = 32
        grid_w = num_cols * self.CELL_SIZE
        grid_h = num_rows * self.CELL_SIZE
        self.origin = Point(
            (win.w - grid_w) / 2,
            (win.h - grid_h) / 2,
        )

        self.cells         = []
        self.visible_cells = set()   # set of (row, col) tuples
        self.level         = 1

        # Tile cache: path -> pygame.Surface
        self._tile_cache: dict[str, pygame.Surface] = {}

    # -----------------------------------------------------------------------
    # Asset loading
    # -----------------------------------------------------------------------
    def _tile_dir(self):
        lvl = self.level
        if   lvl <= 3:  subdir = "1-3"
        elif lvl <= 6:  subdir = "4-6"
        elif lvl == 7:  subdir = "7"
        elif lvl == 8:  subdir = "8"
        elif lvl == 9:  subdir = "9"
        else:           subdir = "10"
        path = Path(f"assets/floors/{subdir}")
        if not path.is_dir():
            raise FileNotFoundError(
                f"Floor tile directory not found: {path}\n"
                "Make sure 'assets/' is next to main.py"
            )
        return path

    def _load_tiles(self):
        """Return list of pygame.Surface for current level's floor tiles."""
        tile_dir = self._tile_dir()
        tiles = []
        for f in sorted(tile_dir.iterdir()):
            if f.suffix.lower() == ".png":
                if f.name not in self._tile_cache:
                    img = pygame.image.load(str(f)).convert_alpha()
                    # Scale to CELL_SIZE if the PNG differs
                    if img.get_size() != (self.CELL_SIZE, self.CELL_SIZE):
                        img = pygame.transform.scale(
                            img, (self.CELL_SIZE, self.CELL_SIZE)
                        )
                    self._tile_cache[f.name] = img
                tiles.append(self._tile_cache[f.name])
        if not tiles:
            raise FileNotFoundError(f"No PNG tiles found in {tile_dir}")
        return tiles

    # -----------------------------------------------------------------------
    # Maze creation
    # -----------------------------------------------------------------------
    def create_maze(self):
        self._win.set_level(self.level)
        tiles  = self._load_tiles()
        origin = self.origin
        cs     = self.CELL_SIZE

        self.cells = []
        for row in range(self.num_rows):
            self.cells.append([])
            for col in range(self.num_cols):
                tl = Point(origin.x + col * cs, origin.y + row * cs)
                br = Point(tl.x + cs,           tl.y + cs)
                cell          = Cell(self._win, tl, br)
                cell.location = [row, col]
                cell.floor_tile = random.choice(tiles)
                self.cells[row].append(cell)

        self._carve_passages()
        self._reset_visited()

    def _carve_passages(self, row=0, col=0):
        """Iterative back-tracker maze generation.

        Previously this was recursive -- for a 10x10 maze that's 100-deep on the
        Python stack, which works on desktop CPython with a raised limit but is
        fragile in WASM (Emscripten's stack is tighter and a blown stack shows
        up as a silent tab freeze rather than a Python exception).
        """
        stack = [(row, col)]
        self.cells[row][col].visited = True
        while stack:
            r0, c0 = stack[-1]
            neighbours = []
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                r, c = r0 + dr, c0 + dc
                if 0 <= r < self.num_rows and 0 <= c < self.num_cols:
                    if not self.cells[r][c].visited:
                        neighbours.append((r, c, dr, dc))
            if not neighbours:
                stack.pop()
                continue
            r, c, dr, dc = random.choice(neighbours)
            # knock down the shared wall
            if dr == -1: self.cells[r0][c0].top    = False; self.cells[r][c].bottom = False
            if dr ==  1: self.cells[r0][c0].bottom = False; self.cells[r][c].top    = False
            if dc == -1: self.cells[r0][c0].left   = False; self.cells[r][c].right  = False
            if dc ==  1: self.cells[r0][c0].right  = False; self.cells[r][c].left   = False
            self.cells[r][c].visited = True
            stack.append((r, c))

    def _reset_visited(self):
        for row in self.cells:
            for cell in row:
                cell.visited = False

    # -----------------------------------------------------------------------
    # Entrance / exit
    # -----------------------------------------------------------------------
    def _place_entrance_exit(self, start_cell, wall):
        """
        wall: 0=top  1=bottom  2=left  3=right
        Entrance on start_cell's chosen wall; exit on opposite side.
        """
        r, c = start_cell.location
        if wall == 0:
            self.cells[r][c].ent = True;  self.cells[r][c].top    = False
            er = self.num_rows - 1;       ec = random.randint(0, self.num_cols-1)
            self.cells[er][ec].exit = True; self.cells[er][ec].bottom = False
        elif wall == 1:
            self.cells[r][c].ent = True;  self.cells[r][c].bottom = False
            er = 0;                        ec = random.randint(0, self.num_cols-1)
            self.cells[er][ec].exit = True; self.cells[er][ec].top  = False
        elif wall == 2:
            self.cells[r][c].ent = True;  self.cells[r][c].left   = False
            er = random.randint(0, self.num_rows-1); ec = self.num_cols - 1
            self.cells[er][ec].exit = True; self.cells[er][ec].right = False
        else:
            self.cells[r][c].ent = True;  self.cells[r][c].right  = False
            er = random.randint(0, self.num_rows-1); ec = 0
            self.cells[er][ec].exit = True; self.cells[er][ec].left  = False

    # -----------------------------------------------------------------------
    # Player / monster init
    # -----------------------------------------------------------------------
    def player_init(self, player):
        player.is_player = True
        wall = random.randint(0, 3)
        if wall == 0:
            col = random.randint(0, self.num_cols-1)
            cell = self.cells[0][col]
            player.facing = "down"
        elif wall == 1:
            col = random.randint(0, self.num_cols-1)
            cell = self.cells[self.num_rows-1][col]
            player.facing = "up"
        elif wall == 2:
            row = random.randint(0, self.num_rows-1)
            cell = self.cells[row][0]
            player.facing = "right"
        else:
            row = random.randint(0, self.num_rows-1)
            cell = self.cells[row][self.num_cols-1]
            player.facing = "left"

        cell.set_player(player)
        player.location = cell
        self._place_entrance_exit(cell, wall)

    def monsters_init(self):
        max_enemies = int(random.randint(self.num_rows,self.num_rows*(self.num_cols//2)))
        candidates = [
            cell for row in self.cells for cell in row
            if not cell.player
        ]
        random.shuffle(candidates)
        placed = 0
        for cell in candidates:
            if placed >= max_enemies:
                break
            if cell.enemy:
                continue
            enemy = generate_enemy(min(self.level, 10))
            enemy.location = cell
            cell.set_enemy(enemy)
            placed += 1

    # -----------------------------------------------------------------------
    # Visibility (BFS through open walls)
    # -----------------------------------------------------------------------
    def update_visibility(self, entity:Entity,radius=2):
        if self._win.night == 1:
            radius = 1
        sy, sx = entity.location.location
        if entity.is_player:
            self.cells[sy][sx].visited = True
        entity.visible_cells = set()
        queue = deque()
        queue.append((sy, sx, 0))
        dirs  = {
            "up":    (-1,  0),
            "down":  ( 1,  0),
            "left":  ( 0, -1),
            "right": ( 0,  1),
        }
        while queue:
            y, x, dist = queue.popleft()
            if (y, x) in entity.visible_cells:
                continue
            entity.visible_cells.add((y, x))
            if dist >= radius:
                continue
            for direction, (dy, dx) in dirs.items():
                if self.cells[y][x].can_move(direction, self) != "bump":
                    ny, nx = y+dy, x+dx
                    if 0 <= ny < self.num_rows and 0 <= nx < self.num_cols:
                        queue.append((ny, nx, dist+1))

    # -----------------------------------------------------------------------
    # Level progression
    # -----------------------------------------------------------------------
    async def next_level(self, player):
        def _retry():
            self._win._restart_request = ("retry", None, None)
            self._win.show_win(player, self, on_retry=_retry, on_quit=_quit_app())
        if self.level == 10:
            self._win.show_win(player,self,on_retry=_retry,on_quit=_quit_app())
        self._win.set_player_stats(player)
        self._win._ui_blocked = True
        self.level += 1
        self.cells = []
        self.visible_cells = set()
        # Yield between heavy phases so the browser frame pump can run.
        # For a 10x10 maze this is instantaneous; for larger grids these
        # awaits prevent a visible freeze during the level transition.
        self.create_maze()
        await asyncio.sleep(0)
        self.player_init(player)
        await asyncio.sleep(0)
        self.monsters_init()
        await asyncio.sleep(0)
        # Re-center camera + refresh UI in place
        x, y = player.location.cent.x, player.location.cent.y
        self._win.center_on_point(x, y)
        self.update_visibility(player)
        self._win.set_player_stats(player)
        self._win._ui_blocked = False
        # Release the transition guard set by entity.move()
        self._transitioning = False

    async def level_up(self, player):
        try:
            await self._win.show_level_up(player)
        finally:
            # Release the guard set by entity.attack_target() so the next
            # level-up trigger can fire.
            player._leveling_up = False