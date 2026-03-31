from classes import *
import time

class Point:
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y


class Line:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def draw(self, canvas, colour, offset_x=0, offset_y=0, tag=("world",)):
        canvas.create_line(
            self.p1.x + offset_x, self.p1.y + offset_y,
            self.p2.x + offset_x, self.p2.y + offset_y,
            fill=colour, width=2, tags=tag)


class Cell:
    def __init__(self, window, top_corner, bottom_corner, top=True, bottom=True, left=True, right=True):
        self.__tlcor = top_corner
        self.__brcor = bottom_corner
        self.__trcor = Point(self.__brcor.x, self.__tlcor.y)
        self.__blcor = Point(self.__tlcor.x, self.__brcor.y)
        self.cent = Point((self.__trcor.x - self.__tlcor.x) / 2 + self.__tlcor.x, (self.__brcor.y - self.__trcor.y) / 2 + self.__trcor.y)
        self.top = top
        self.bottom = bottom
        self.left = left
        self.right = right
        self.location = []
        self.icon = "assets/floors/1-3/texture_16px 1.png"
        self.icon_id = None
        self.floor = None
        self.__win = window
        self.visited = False
        self.enemy_entity = None
        self.player_entity = None
        self.player = False
        self.enemy = False
        self.ent = False
        self.exit = False
        self.inventory = Inventory()
        self.gold = 0

    def is_visible(self, maze):
        y, x = self.location
        if (y, x) in maze.visible_cells:
            return 1
        elif self.visited:
            return 2
        return 0

    def _draw_walls(self,wall_color="white"):
        self.__win.draw_line(Line(self.__trcor, self.__tlcor), wall_color if self.top else "black")
        self.__win.draw_line(Line(self.__brcor, self.__blcor), wall_color if self.bottom else "black")
        self.__win.draw_line(Line(self.__tlcor, self.__blcor), wall_color if self.left else "black")
        self.__win.draw_line(Line(self.__brcor, self.__trcor), wall_color if self.right else "black")

    def draw_floors(self):
        self.floor, self.icon_id = self.__win.place_floor(self.cent, self.icon)

    def draw(self, maze, start=False):
        vision = self.is_visible(maze)
        if not start:
            if vision ==1:
                self._draw_walls()
                self.draw_floors()
                if self.inventory.length():
                    self.__win.draw_circle(self.cent, 5, "gold")
                self.player_tracking()
                self.enemy_tracking()
            if vision == 2:
                self.draw_floors()
                self._draw_walls("gray")


    def player_tracking(self):
        if self.player_entity:
            if not self.player_entity.id_:
                self.player_entity.id_ = self.__win.draw_circle(self.cent, 5, "blue")
            else:
                self.__win.canvas.coords(self.player_entity.id_,
                                         self.cent.x - 5,
                                         self.cent.y - 5,
                                         self.cent.x + 5,
                                         self.cent.y + 5)
            if self.player_entity.health <= 0:
                return

    def enemy_tracking(self):
        if self.enemy_entity:
            if not self.enemy_entity.id_:
                outline = ""
                if "rare" in self.enemy_entity.name.lower():
                    outline = "orange"
                elif "epic" in self.enemy_entity.name.lower():
                    outline = "blue"
                elif "legendary" in self.enemy_entity.name.lower():
                    outline = "gold"
                if "skeleton" in self.enemy_entity.name:
                    self.enemy_entity.id_ = self.__win.draw_circle(self.cent, 5, "gray",outline=outline)
                if "orc" in self.enemy_entity.name:
                    self.enemy_entity.id_ = self.__win.draw_circle(self.cent, 5, "dark green",outline=outline)
                if "goblin" in self.enemy_entity.name:
                    self.enemy_entity.id_ = self.__win.draw_circle(self.cent, 3, "green",outline=outline)
                if "troll" in self.enemy_entity.name:
                    self.enemy_entity.id_ = self.__win.draw_circle(self.cent, 5, "brown",outline=outline)
                if "wraith" in self.enemy_entity.name:
                    self.enemy_entity.id_ = self.__win.draw_circle(self.cent, 5, "white",outline=outline)
                if "vampire" in self.enemy_entity.name:
                    self.enemy_entity.id_ = self.__win.draw_circle(self.cent, 3, "red",outline=outline)
                if "dark mage" in self.enemy_entity.name:
                    self.enemy_entity.id_ = self.__win.draw_circle(self.cent, 3, "purple",outline=outline)

            else:
                self.__win.canvas.coords(
                    self.enemy_entity.id_,
                    self.cent.x - 5,
                    self.cent.y - 5,
                    self.cent.x + 5,
                    self.cent.y + 5
                )

    def remove_player(self):
        if self.player_entity:
            self.player_entity.id_ = None
        self.player = False
        self.player_entity = None

    def set_player(self, entity_):
        self.player = True
        self.player_entity = entity_

    def set_enemy(self, entity_):
        self.enemy = True
        self.enemy_entity = entity_

    def remove_enemy(self):
        if self.enemy_entity:
            self.enemy_entity.id_ = None
        self.enemy = False
        self.enemy_entity = None

    def can_move(self, direction, maze, is_enemy=False):
        row, col = self.location

        if direction == "up":
            if row == 0:  # on top boundary
                if self.ent and not self.top:   # top wall is the entrance
                    return "you can\'t go back that way."
                if self.exit and not self.top:  # top wall is the exit
                    return "you continue deeper...."
            if row > 0 and maze.cells[row - 1][col].enemy and is_enemy:
                return "bump"
            return "bump"if self.top else "move"

        if direction == "down":
            if row == maze.num_rows - 1:
                if self.ent and not self.bottom:
                    return "you can\'t go back that way."
                if self.exit and not self.bottom:
                    return "you continue deeper...."
            if row < maze.num_rows - 1 and maze.cells[row + 1][col].enemy and is_enemy:
                return "bump"
            return "bump"if self.bottom else "move"

        if direction == "left":
            if col == 0:
                if self.ent and not self.left:
                    return "you can\'t go back that way."
                if self.exit and not self.left:
                    return "you continue deeper...."
            if col > 0 and maze.cells[row][col - 1].enemy and is_enemy:
                return "bump"
            return "bump"if self.left else "move"

        if direction == "right":
            if col == maze.num_cols - 1:
                if self.ent and not self.right:
                    return "you can\'t go back that way."
                if self.exit and not self.right:
                    return "you continue deeper...."
            if col < maze.num_cols - 1 and maze.cells[row][col + 1].enemy and is_enemy:
                return "bump"
            return "bump"if self.right else "move"

        return "bump"

    def ani_move(self, target, duration=200, fps=60, on_complete=None):
        mx = self.cent.x + self.__win.offset_x
        my = self.cent.y + self.__win.offset_y
        tx = target.cent.x + self.__win.offset_x
        ty = target.cent.y + self.__win.offset_y
        item = None
        if self.enemy_entity:
            item = self.enemy_entity.id_
        elif self.player_entity:
            item = self.player_entity.id_
        if not item:
            if on_complete:
                on_complete()
            return
        start_time = time.time()
        end_time = start_time + duration / 1000

        def step():
            try:
                bbox = self.__win.canvas.bbox(item)
            except Exception:
                if on_complete:
                    on_complete()
                return
            if bbox is None:
                if on_complete:
                    on_complete()
                return
            now = time.time()
            t = min((now - start_time) / (end_time - start_time), 1.0)
            cx = mx + (tx - mx) * t
            cy = my + (ty - my) * t
            x1, y1, x2, y2 = bbox
            self.__win.canvas.move(item, cx - (x1 + x2) / 2, cy - (y1 + y2) / 2)
            self.player_tracking()
            self.enemy_tracking()
            if t < 1.0:
                self.__win.canvas.after(1000 // fps, step)
            elif on_complete:
                on_complete()

        step()

    def add_to_inventory(self, item_):
        key = "Weapons" if isinstance(item_, Weapon) else "Armors" if isinstance(item_, Armour) else "Consumables"
        if not key:
            print(f"not able to put {item_} in inventory")
            return
        else:
            self.inventory.items[key].append(item_)

    def add_items_to_inventory(self, items):
        if len(items) == 1:
            self.add_to_inventory(items[0])
            return
        else:
            for item in items:
                self.add_to_inventory(item)

    def remove_inventory(self):
        self.inventory = Inventory()





    def __eq__(self, other):
        if not isinstance(other, Cell):
            return NotImplemented
        return self.location[0] == other.location[0] and self.location[1] == other.location[1]
