import pygame
from classes import *

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------


def col(name):
    if isinstance(name, tuple):
        return name
    return COLOURS.get(name.lower(), COLOURS["white"])


# ---------------------------------------------------------------------------
# Geometry primitives
# ---------------------------------------------------------------------------
class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class Line:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def draw(self, surface, colour, ox=0, oy=0):
        pygame.draw.line(
            surface, col(colour),
            (int(self.p1.x + ox), int(self.p1.y + oy)),
            (int(self.p2.x + ox), int(self.p2.y + oy)),
            2
        )


# ---------------------------------------------------------------------------
# Cell
# ---------------------------------------------------------------------------
class Cell:
    def __init__(self, win, top_corner, bottom_corner,
                 top=True, bottom=True, left=True, right=True):
        self._tl = top_corner
        self._br = bottom_corner
        self._tr = Point(self._br.x, self._tl.y)
        self._bl = Point(self._tl.x, self._br.y)
        self.cent = Point(
            (self._tl.x + self._br.x) / 2,
            (self._tl.y + self._br.y) / 2,
        )
        self.size = int(self._br.x - self._tl.x)   # tile pixel size

        self.top    = top
        self.bottom = bottom
        self.left   = left
        self.right  = right

        self.location      = []
        self.floor_tile    = None   # pygame.Surface set by Maze
        self.visited       = False
        self.enemy_entity  = None
        self.player_entity = None
        self.player  = False
        self.enemy   = False
        self.ent     = False
        self.exit    = False
        self.inventory = Inventory()
        self.gold    = 0

        self._win = win

        # smooth-move animation
        self._anim_pt  = None    # current draw Point during animation
        self._anim_src = None
        self._anim_dst = None
        self._anim_t0  = None
        self._anim_dur = 0.18    # seconds
        self._anim_who = None    # "player" | "enemy"
        self._anim_cb  = None

    # -----------------------------------------------------------------------
    # Visibility
    # -----------------------------------------------------------------------
    def is_visible(self, maze):
        y, x = self.location
        if (y, x) in maze.visible_cells:
            return 1
        if self.visited:
            return 2
        return 0

    # -----------------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------------
    def _screen(self, pt):
        """World point → screen point given camera offset."""
        ox, oy = self._win.camera
        return int(pt.x + ox), int(pt.y + oy)

    def _wall(self, p1, p2, solid, dim=False):
        if solid:
            c = (80, 75, 70) if dim else (200, 195, 185)
        else:
            c = (0, 0, 0)
        pygame.draw.line(
            self._win.surface, c,
            self._screen(p1), self._screen(p2), 2
        )

    def draw(self, maze, start=False):
        if start:
            return   # generation phase — don't draw individual cells

        vision = self.is_visible(maze)
        if vision == 0:
            return

        ox, oy = self._win.camera
        sx = int(self._tl.x + ox)
        sy = int(self._tl.y + oy)

        # Floor tile
        if self.floor_tile:
            if vision == 1:
                self._win.surface.blit(self.floor_tile, (sx, sy))
            else:  # visited but not visible — draw darkened
                dark = self.floor_tile.copy()
                dark.fill((0, 0, 0, 170), special_flags=pygame.BLEND_RGBA_MULT)
                self._win.surface.blit(dark, (sx, sy))

        # Walls
        dim = (vision == 2)
        self._wall(self._tr, self._tl, self.top,    dim)
        self._wall(self._br, self._bl, self.bottom, dim)
        self._wall(self._tl, self._bl, self.left,   dim)
        self._wall(self._br, self._tr, self.right,  dim)

        if vision == 1:
            # Items on floor
            if self.inventory.length():
                self._dot(self.cent, 3, "gold")

            # Player / enemy (if not mid-animation)
            if self.player_entity and self._anim_who != "player":
                self._dot(self.cent, 5, "blue")
            if self.enemy_entity and self._anim_who != "enemy":
                self._draw_enemy_dot(self.cent)

    def _dot(self, pt, r, fill, outline=None):
        cx, cy = self._screen(pt)
        pygame.draw.circle(self._win.surface, col(fill), (cx, cy), r)
        if outline:
            pygame.draw.circle(self._win.surface, col(outline), (cx, cy), r, 2)

    def _draw_enemy_dot(self, pt):
        name = self.enemy_entity.name.lower()
        outline = None
        if "rare"        in name: outline = "orange"
        elif "epic"      in name: outline = "blue"
        elif "legendary" in name: outline = "gold"

        if   "skeleton"  in name: fill, r = "gray",       5
        elif "orc"       in name: fill, r = "dark green", 5
        elif "goblin"    in name: fill, r = "green",      3
        elif "troll"     in name: fill, r = "brown",      5
        elif "wraith"    in name: fill, r = "white",      5
        elif "vampire"   in name: fill, r = "red",        3
        elif "dark mage" in name: fill, r = "purple",     3
        else:                     fill, r = "gray",       4
        self._dot(pt, r, fill, outline)

    # -----------------------------------------------------------------------
    # Animation
    # -----------------------------------------------------------------------
    def ani_move(self, target, duration=180, on_complete=None):
        import time
        self._anim_src = Point(self.cent.x, self.cent.y)
        self._anim_dst = Point(target.cent.x, target.cent.y)
        self._anim_pt  = Point(self.cent.x, self.cent.y)
        self._anim_t0  = time.time()
        self._anim_dur = duration / 1000.0
        self._anim_who = "player" if self.player_entity else "enemy"
        self._anim_cb  = on_complete

    def tick_anim(self):
        """Call once per frame. Draws moving dot; fires callback when done."""
        import time
        if self._anim_t0 is None:
            return False
        t = min((time.time() - self._anim_t0) / self._anim_dur, 1.0)
        # ease-out quad
        t_ease = 1 - (1 - t) ** 2
        cx = self._anim_src.x + (self._anim_dst.x - self._anim_src.x) * t_ease
        cy = self._anim_src.y + (self._anim_dst.y - self._anim_src.y) * t_ease
        pt = Point(cx, cy)
        if self._anim_who == "player":
            self._dot(pt, 5, "blue")
        elif self.enemy_entity:
            # temporarily swap cent for the dot helper
            real = self.cent
            self.cent = pt
            self._draw_enemy_dot(pt)
            self.cent = real
        if t >= 1.0:
            cb = self._anim_cb
            self._anim_t0  = None
            self._anim_who = None
            self._anim_cb  = None
            if cb:
                cb()
            return False
        return True

    # -----------------------------------------------------------------------
    # Movement validation
    # -----------------------------------------------------------------------
    def can_move(self, direction, maze, is_enemy=False):
        row, col = self.location
        if direction == "up":
            if row == 0:
                if self.ent  and not self.top:  return "you can't go back that way."
                if self.exit and not self.top:  return "you continue deeper...."
            if row > 0 and maze.cells[row-1][col].enemy and is_enemy:
                return "bump"
            return "bump" if self.top else "move"

        if direction == "down":
            if row == maze.num_rows - 1:
                if self.ent  and not self.bottom: return "you can't go back that way."
                if self.exit and not self.bottom: return "you continue deeper...."
            if row < maze.num_rows-1 and maze.cells[row+1][col].enemy and is_enemy:
                return "bump"
            return "bump" if self.bottom else "move"

        if direction == "left":
            if col == 0:
                if self.ent  and not self.left: return "you can't go back that way."
                if self.exit and not self.left: return "you continue deeper...."
            if col > 0 and maze.cells[row][col-1].enemy and is_enemy:
                return "bump"
            return "bump" if self.left else "move"

        if direction == "right":
            if col == maze.num_cols - 1:
                if self.ent  and not self.right: return "you can't go back that way."
                if self.exit and not self.right: return "you continue deeper...."
            if col < maze.num_cols-1 and maze.cells[row][col+1].enemy and is_enemy:
                return "bump"
            return "bump" if self.right else "move"

        return "bump"

    # -----------------------------------------------------------------------
    # Entity setters
    # -----------------------------------------------------------------------
    def set_player(self, entity):
        self.player = True
        self.player_entity = entity

    def remove_player(self):
        self.player = False
        self.player_entity = None

    def set_enemy(self, entity):
        self.enemy = True
        self.enemy_entity = entity

    def remove_enemy(self):
        self.enemy = False
        self.enemy_entity = None

    # -----------------------------------------------------------------------
    # Inventory helpers
    # -----------------------------------------------------------------------
    def add_to_inventory(self, item_):
        key = ("Weapons"     if isinstance(item_, Weapon)
               else "Armors" if isinstance(item_, Armour)
               else "Consumables")
        self.inventory.items[key].append(item_)

    def add_items_to_inventory(self, items):
        for item in items:
            self.add_to_inventory(item)

    def remove_inventory(self):
        self.inventory = Inventory()

    def __eq__(self, other):
        if not isinstance(other, Cell):
            return NotImplemented
        return self.location == other.location