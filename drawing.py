import pygame
from classes import *
from constants import COLOURS

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
        self._anim_dst_cell = None
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
        self.floor_type = ""
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
        self._anim_entity = None

        # sprite references (set lazily when entities are assigned)
        self._player_sprite = None
        self._enemy_sprite  = None

    # -----------------------------------------------------------------------
    # Tile Drawing
    # -----------------------------------------------------------------------
    def load_tile(self,name):
        """Return list of pygame.Surface for current level's floor tiles."""
        tile_dir = self._maze._tile_dir()
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
                tiles.append((self._tile_cache[f.name],f.name))
        if not tiles:
            raise FileNotFoundError(f"No PNG tiles found in {tile_dir}")
        return tiles

    # -----------------------------------------------------------------------
    # Visibility
    # -----------------------------------------------------------------------
    def is_visible(self,player):
        y, x = self.location
        if (y, x) in player.visible_cells:
            return 1
        if self.visited:
            return 2
        return 0

    # -----------------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------------
    def _screen(self, pt):
        """World point -> screen point given camera offset."""
        ox, oy = self._win.camera
        return int(pt.x + ox), int(pt.y + oy)

    def _wall(self, p1, p2, solid, dim=False):
        if solid:
            c = COLOURS["gray"] if dim else COLOURS["white"]
        else:
            c = COLOURS["black"]
        pygame.draw.line(
            self._win.surface, c,
            self._screen(p1), self._screen(p2), 2
        )

    def draw(self, player, start=False):
        if start:
            return   # generation phase -- don't draw individual cells

        vision = self.is_visible(player)
        if self._win.night == 1 and vision == 2:
            return
        if vision == 0:
            return

        ox, oy = self._win.camera
        sx = int(self._tl.x + ox)
        sy = int(self._tl.y + oy)

        # Floor tile
        if self.floor_tile:
            if vision == 1:
                self._win.surface.blit(self.floor_tile, (sx, sy))
            else:  # visited but not visible -- draw darkened
                dark = self.floor_tile.copy()
                dark.fill(COLOURS["gray"], special_flags=pygame.BLEND_RGBA_MULT)
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

            # Player sprite (if not mid-animation)
            if self.player_entity and self._anim_who != "player":
                animating = any(
                    c._anim_who == "player" for c in self._win.animating_cells if c is not self
                )
                if not animating:
                    # Keep sprite facing in sync with entity
                    if self._player_sprite and getattr(self.player_entity, 'facing', None):
                        self._player_sprite.set_facing(self.player_entity.facing)
                    self._draw_entity_sprite(self.cent, self._player_sprite, "player")

            # Enemy sprite (if not mid-animation)
            if self.enemy_entity and self._anim_who != "enemy":
                animating = any(
                    c._anim_dst_cell is self for c in self._win.animating_cells
                    if c._anim_who == "enemy"
                )
                if not animating:
                    if self._enemy_sprite and getattr(self.enemy_entity, 'facing', None):
                        self._enemy_sprite.set_facing(self.enemy_entity.facing)
                    self._draw_entity_sprite(self.cent, self._enemy_sprite, "enemy")

    # -----------------------------------------------------------------------
    # Sprite drawing helpers
    # -----------------------------------------------------------------------
    def _draw_entity_sprite(self, pt, sprite, who):
        """
        Draw a sprite-sheet frame centred on the cell.
        All frames are 32x32 matching the cell size.
        Falls back to a coloured dot if the sprite is unavailable.
        """
        if sprite is not None:
            frame = sprite.get_frame()
            if frame is not None:
                ox, oy = self._win.camera
                fw, fh = frame.get_size()
                draw_x = int(pt.x + ox) - fw // 2
                draw_y = int(pt.y + oy) - fh // 2
                self._win.surface.blit(frame, (draw_x, draw_y))
                return
        # Fallback coloured dot
        if who == "player":
            self._dot(pt, 7, "blue", player=self.player_entity)
        else:
            self._draw_enemy_dot(pt)

    def _dot(self, pt, r, fill, outline=None, player=None):
        cx, cy = self._screen(pt)
        if player:
            offsets = {"up": (0, -5), "down": (0, 5), "left": (-5, 0), "right": (5, 0)}
            dx, dy = offsets.get(player.facing, (0, 0))
            pygame.draw.circle(self._win.surface, "red", (cx + dx, cy + dy), 4)
        pygame.draw.circle(self._win.surface, col(fill), (cx, cy), r)
        if outline:
            pygame.draw.circle(self._win.surface, col(outline), (cx, cy), r, 3)

    def _draw_enemy_dot(self, pt):
        """Fallback dot renderer (used when sprite is unavailable)."""
        name = self.enemy_entity.name.lower()
        outline = None
        if "rare"        in name: outline = "orange"
        elif "epic"      in name: outline = "blue"
        elif "legendary" in name: outline = "gold"

        if   "skeleton"      in name: fill, r = "gray",       7
        elif "zombie"        in name: fill, r = "dark_green",  7
        elif "orc"           in name: fill, r = "dark_green", 12
        elif "goblin"        in name: fill, r = "green",       5
        elif "troll"         in name: fill, r = "brown",      12
        elif "wraith"        in name: fill, r = "white",       7
        elif "vampire"       in name: fill, r = "red",         7
        elif "dark mage"     in name: fill, r = "purple",      7
        elif "cyclops"       in name: fill, r = "brown",      12
        elif "minotaur"      in name: fill, r = "brown",      12
        elif "centaur"       in name: fill, r = "brown",      10
        elif "yeti"          in name: fill, r = "white",      12
        elif "pumpkin"       in name: fill, r = "orange",      8
        elif "slime"         in name: fill, r = "green",       6
        else:                         fill, r = "gray",       10
        self._dot(pt, r, fill, outline)

    # -----------------------------------------------------------------------
    # Animation
    # -----------------------------------------------------------------------
    def ani_move(self, target, duration=180, on_complete=None):
        import time
        self._anim_dst_cell = target
        self._anim_src = Point(self.cent.x, self.cent.y)
        self._anim_dst = Point(target.cent.x, target.cent.y)
        self._anim_pt  = Point(self.cent.x, self.cent.y)
        self._anim_t0  = time.time()
        self._anim_dur = duration / 1000.0
        self._anim_who = "player" if self.player_entity else "enemy"
        self._anim_entity = self.enemy_entity
        # Keep sprite references for animation
        self._anim_player_sprite = self._player_sprite
        self._anim_enemy_sprite  = self._enemy_sprite
        self._anim_cb  = on_complete

    def tick_anim(self, player):
        """Call once per frame. Draws moving sprite/dot; fires callback when done."""
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
            self._win.center_on_point(cx, cy)
            # Set walk state + facing during movement
            if hasattr(self, '_anim_player_sprite') and self._anim_player_sprite:
                if player and getattr(player, 'facing', None):
                    self._anim_player_sprite.set_facing(player.facing)
                self._anim_player_sprite.set_state("walk")
                self._draw_entity_sprite(pt, self._anim_player_sprite, "player")
            else:
                self._dot(pt, 7, "blue", player=player)
        elif self._anim_entity:
            real = self.cent
            self.cent = pt
            real_entity = self.enemy_entity
            self.enemy_entity = self._anim_entity
            sprite = getattr(self, '_anim_enemy_sprite', None)
            if sprite:
                if getattr(self._anim_entity, 'facing', None):
                    sprite.set_facing(self._anim_entity.facing)
                sprite.set_state("walk")
                self._draw_entity_sprite(pt, sprite, "enemy")
            else:
                self._draw_enemy_dot(pt)
            self.enemy_entity = real_entity
            self.cent = real
        if t >= 1.0:
            cb = self._anim_cb
            self._anim_t0  = None
            self._anim_who = None
            self._anim_cb  = None
            self._anim_entity = None
            # Reset sprites to idle after movement
            if hasattr(self, '_anim_player_sprite') and self._anim_player_sprite:
                self._anim_player_sprite.set_state("idle")
            if hasattr(self, '_anim_enemy_sprite') and self._anim_enemy_sprite:
                self._anim_enemy_sprite.set_state("idle")
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
        # Attach or reuse sprite
        if not hasattr(entity, '_sprite') or entity._sprite is None:
            from sprites import make_sprite
            entity._sprite = make_sprite("player")
        self._player_sprite = entity._sprite
        self._player_sprite.set_state("idle")
        # Apply facing from entity
        if getattr(entity, 'facing', None):
            self._player_sprite.set_facing(entity.facing)

    def remove_player(self):
        self.player = False
        self.player_entity = None
        self._player_sprite = None

    def set_enemy(self, entity):
        self.enemy = True
        self.enemy_entity = entity
        if not hasattr(entity, '_sprite') or entity._sprite is None:
            from sprites import make_sprite
            entity._sprite = make_sprite(entity.name)
        self._enemy_sprite = entity._sprite
        self._enemy_sprite.set_state("idle")
        if getattr(entity, 'facing', None):
            self._enemy_sprite.set_facing(entity.facing)

    def remove_enemy(self):
        self.enemy = False
        self.enemy_entity = None
        self._enemy_sprite = None

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

    def __hash__(self):
        return hash(tuple(self.location))