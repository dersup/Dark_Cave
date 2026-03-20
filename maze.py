from drawing import *
from generator_ import *
import random


class Maze:
    def __init__(self, num_rows, num_cols, win, seed=None):
        self.__cell_size_x = win.x // (num_cols + 1)
        self.__cell_size_y = win.y // (num_rows + 1)
        self.__grid_width = num_cols * self.__cell_size_x
        self.__grid_height = num_rows * self.__cell_size_y
        self.left = (win.x - self.__grid_width) / 2
        self.top = (win.y - self.__grid_height) / 2
        self.right = self.left + self.__grid_width
        self.bottom = self.top + self.__grid_height
        self.__brcor = Point(self.right, self.bottom)
        self.__tlcor = Point(self.left, self.top)
        self.num_rows = num_rows
        self.num_cols = num_cols
        self.__win = win
        self.__seed = seed or random.seed()
        self.cells = []
        self.visible_cells = set()
        self.level = 1

    def create_maze(self):
        self.__win.clear()
        self.__win.set_level(self.level)
        self.cells = []
        curr_y = self.__tlcor.y
        for i in range(self.num_rows):
            curr_x = self.__tlcor.x
            self.cells.append([])
            for j in range(self.num_cols):
                self.cells[i].append(Cell(self.__win, Point(curr_x, curr_y), Point(curr_x + self.__cell_size_x, curr_y + self.__cell_size_y)))
                self.cells[i][j].location = [i, j]
                self._draw_cell(i, j)
                curr_x += self.__cell_size_x
            curr_y += self.__cell_size_y
        self.break_walls()
        self.reset_visted()

    def _draw_cell(self, i, j):
        self.cells[i][j].draw(self, start=True)
        self.__win.redraw()

    def break_ent_exit(self, player_cell, wall):
        if wall == 0:
            self.cells[player_cell.location[0]][player_cell.location[1]].ent = True
            self.cells[player_cell.location[0]][player_cell.location[1]].top = False
            rand_location = random.randint(0, self.num_cols - 1)
            self.cells[self.num_rows - 1][rand_location].exit = True
            self.cells[self.num_rows - 1][rand_location].bottom = False
        if wall == 1:
            self.cells[player_cell.location[0]][player_cell.location[1]].ent = True
            self.cells[player_cell.location[0]][player_cell.location[1]].bottom = False
            rand_location = random.randint(0, self.num_cols - 1)
            self.cells[0][rand_location].exit = True
            self.cells[0][rand_location].top = False

        if wall == 2:
            self.cells[player_cell.location[0]][player_cell.location[1]].ent = True
            self.cells[player_cell.location[0]][player_cell.location[1]].left = False
            rand_location = random.randint(0, self.num_rows - 1)
            self.cells[rand_location][self.num_cols - 1].exit = True
            self.cells[rand_location][self.num_cols - 1].right = False
        if wall == 3:
            self.cells[player_cell.location[0]][player_cell.location[1]].ent = True
            self.cells[player_cell.location[0]][player_cell.location[1]].right = False
            rand_location = random.randint(0, self.num_rows - 1)
            self.cells[rand_location][0].exit = True
            self.cells[rand_location][0].left = False

    def break_walls(self, i=0, j=0):
        self.cells[i][j].visited = True
        while 1:
            possible = []
            picks = []
            if 0 < i < self.num_rows - 1:
                possible.extend([[i - 1, j], [i + 1, j]])
            elif i == 0:
                possible.append([i + 1, j])
            elif i == self.num_rows - 1:
                possible.append([i - 1, j])
            if 0 < j < self.num_cols - 1:
                possible.extend([[i, j + 1], [i, j - 1]])
            elif j == 0:
                possible.append([i, j + 1])
            elif j == self.num_cols - 1:
                possible.append([i, j - 1])
            for c in possible:
                if not self.cells[c[0]][c[1]].visited:
                    picks.append(c)
            if len(picks) == 0:
                self._draw_cell(i, j)
                return
            pick = random.choice(picks)
            if pick[0] < i:
                self.cells[i][j].top = False
                self.cells[pick[0]][pick[1]].bottom = False
            elif pick[0] > i:
                self.cells[i][j].bottom = False
                self.cells[pick[0]][pick[1]].top = False
            if pick[1] > j:
                self.cells[i][j].right = False
                self.cells[pick[0]][pick[1]].left = False
            elif pick[1] < j:
                self.cells[i][j].left = False
                self.cells[pick[0]][pick[1]].right = False
            self.break_walls(pick[0], pick[1])

    def reset_visted(self):
        for row in self.cells:
            for cell in row:
                cell.visited = False

    def player_init(self, player):
        player.is_player = True
        wall = random.randint(0, 3)
        if wall == 0:
            location = random.randint(0, self.num_cols - 1)
            self.cells[0][location].player = True
            player.location = self.cells[0][location]
            player.facing = "down"
            self.break_ent_exit(self.cells[0][location], wall)

        elif wall == 1:
            location = random.randint(0, self.num_cols - 1)
            self.cells[self.num_rows - 1][location].player = True
            player.location = self.cells[self.num_rows - 1][location]
            player.facing = "up"
            self.break_ent_exit(self.cells[self.num_rows - 1][location], wall)

        elif wall == 2:
            location = random.randint(0, self.num_rows - 1)
            self.cells[location][0].player = True
            player.location = self.cells[location][0]
            player.facing = "right"
            self.break_ent_exit(self.cells[location][0], wall)

        else:
            location = random.randint(0, self.num_rows - 1)
            self.cells[location][self.num_cols - 1].player = True
            player.location = self.cells[location][self.num_cols - 1]
            player.facing = "left"
            self.break_ent_exit(self.cells[location][self.num_cols - 1], wall)

    def monsters_init(self):
        possible = []
        num_enemy = min(self.level * random.randint(10, 30), (self.num_rows * self.num_cols) / 2)
        for row in self.cells:
            for cell in row:
                if not cell.player and not (cell.location[0], cell.location[1]) in self.visible_cells:
                    possible.append(cell)
        while num_enemy > 0:
            pick = random.choice(possible)
            if pick.enemy:
                continue
            else:
                self.cells[pick.location[0]][pick.location[1]].enemy = True
                self.cells[pick.location[0]][pick.location[1]].enemy_entity = generate_enemy(min(self.level, 10))
                self.cells[pick.location[0]][pick.location[1]].enemy_entity.location = self.cells[pick.location[0]][pick.location[1]]
                num_enemy -= 1

    def update_visibility(self, player):

        radius = 2
        start_y, start_x = player.location.location
        self.cells[start_y][start_x].visited = True

        # clear previous visibility
        self.visible_cells = set()
        queue = [(start_y, start_x, 0)]

        directions = {
            "up": (-1, 0),
            "down": (1, 0),
            "left": (0, -1),
            "right": (0, 1)
        }

        while queue:
            y, x, dist = queue.pop(0)

            if (y, x) in self.visible_cells:
                continue
            self.visible_cells.add((y, x))
            # stop expanding past radius
            if dist >= radius:
                continue

            curr_cell = self.cells[y][x]

            for direction, (dy, dx) in directions.items():

                if curr_cell.can_move(direction, self) != "bump":

                    ny = y + dy
                    nx = x + dx

                    if 0 <= ny < self.num_rows and 0 <= nx < self.num_cols:
                        queue.append((ny, nx, dist + 1))

    def new_maze(self,player,reset=False):
        if not reset:
            self.level += 1
        else:
            self.level = 0
        self.create_maze()
        self.player_init(player)
        self.monsters_init()

    def level_up(self, player):
        self.__win.show_level_up(player)
