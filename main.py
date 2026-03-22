from windows import *
from maze import *
from generator_ import *

USED_KEYS =["<Shift-KeyPress-Up>",
            "<Shift-KeyPress-Down>",
            "<Shift-KeyPress-Right>",
            "<Shift-KeyPress-Left>",
            "<Shift-KeyPress-w>",
            "<Shift-KeyPress-s>",
            "<Shift-KeyPress-d>",
            "<Shift-KeyPress-a>",
            "<Enter>",
            "<Up>",
            "<Down>",
            "<Left>",
            "<Right>",
            "w",
            "s",
            "a",
            "d",
            "e",
            "j",
            "i",
]
def stat_set(player):
    stat_points = 25
    stats = {"attack": 0,  "defence": 0, "luck": 0, "magic_defence": 0,  "magic_attack": 0,  "agility": 0}
    while stat_points >= 0:
        for stat in list(stats.keys()):
            try:
                change = min(int(input(f"allocate {stat_points}, {stat}: {stats[stat]} ")),stat_points)
            except ValueError:
                print("enter an integer")
                break
            if change < 0:
                print("enter a positive integer")
                break
            stat_points -= change
            stats[stat] += change
            print(f"{stat}: {stats[stat]}\npoints remaining: {stat_points}")
        if stat_points == 0:
            answer = input(f"{stats} does this look right?\n       (Y)(N)").lower().strip()
            if answer == "y":
                for stat in list(stats.keys()):
                    player.stats[stat] = stats[stat]
                return
            elif answer == "n":
                stat_points = 25
                for stat in list(stats.keys()):
                    stats[stat] = 0
            else:
                print("please enter either 'y' or 'n'")

def weapon_choice():
    while True:
        try:
            name = input(f"select a weapon.:{'\n'.join(map(str,list(PLAYER_STARTING_GEAR["weapon"].items())))}\n")
            if not name:
                return Weapon()
            weapon_pick = PLAYER_STARTING_GEAR["weapon"][name]
        except (KeyError, ValueError):
            print("that weapon does not exist. try again.")
            continue
        return Weapon(name, weapon_pick["value"], weapon_pick["attack"], weapon_pick["damage"])


def main():
    gender = input("what gender is your hero?\n(Male)(Female)(Non-Binary)\n").lower().strip
    name = input("What is the name of your hero?: ") or name_gen(gender)
    weapon_ = weapon_choice()
    armour = Armour("leather jerkin", PLAYER_STARTING_GEAR["armor"]["leather jerkin"]["value"])
    player = Entity(name, 100, armour, weapon_)
    for i in range(2):
        player.add_to_inventory(generate_items_loot("player"))

    win = Windows(800, 800)
    maze_ = Maze(30, 30, win)
    maze_.create_maze()
    maze_.player_init(player)
    stat_set(player)
    win.center_on(player)
    maze_.monsters_init()
    maze_.update_visibility(player)
    win.player_labels(player)

    state = {"moving": False}
    inv_state = {"num": 2, "looking": False}

    def game_over():
        win.clear()
        win.GAME_OVER(player, maze_)

    def on_move(direction):
        if state["moving"]:
            return  # ignore input during animation
        if player.health <= 0:
            game_over()
            return

        state["moving"] = True  # lock input
        maze_.update_visibility(player)
        old_cell = player.location

        def after_player_moves():
            maze_.update_visibility(player)
            win.player_labels(player)
            win.center_on(player)
            for cell in [old_cell, player.location]:
                cell.draw(maze_)
            do_enemy_turn()
            redraw_all()
            state["moving"] = False  #unlock input

        player.move(direction, maze_, on_complete=after_player_moves)

    def do_enemy_turn():
        for row in maze_.cells:
            for cell in row:
                if cell.enemy and cell.enemy_entity:
                    cell.enemy_entity.enemy_turn(player, maze_)
        if player.health <= 0:
            game_over()

    def redraw_all():
        for row in maze_.cells:
            for cell in row:
                if cell.enemy_entity:
                    cell.enemy_entity.id_ = None
                elif cell.player_entity:
                    cell.player_entity.id_ = None
        win.clear()
        win.player_labels(player)
        for row in maze_.cells:
            for cell in row:
                cell.draw(maze_)
        win.redraw()

    def on_use_item():
        inv_state["num"] = 2
        inv_state["looking"] = True  # flag that inventory_keys loop is active

        def get_item():
            item_name = win.highlight_line(inv_state["num"], player)
            print(f"using{item_name}")
            player.use_item(item_name.strip(), maze_)
            win.inventory_formatted(str(player.inventory))
            do_enemy_turn()

        def increment(change):
            new_val = inv_state["num"] + change
            if 1 < new_val < player.inventory.length() + 7:
                next_text = win.inventory_text.get(f"{new_val}.0", f"{new_val}.end")
                if next_text in list(player.inventory.items.keys())[1:] or next_text == "-------------":
                    inv_state["num"] = new_val + change * 2
                else:
                    inv_state["num"] = new_val
                win.highlight_line(inv_state["num"], player)
                win.inventory_formatted(str(player.inventory))

        def inventory_keys():
            if not inv_state["looking"]:
                for key in USED_KEYS:
                    win.unbind_key(key)
                game_keys()
                return
            win.bind_key("<Up>",lambda e:increment(-1))
            win.bind_key("<Down>",lambda e:increment(-1))
            win.bind_key("<Enter>",lambda e:get_item())
            win.bind_key("<w>",lambda e:increment(-1))
            win.bind_key("<s>",lambda e:increment(1))
            win.bind_key("<e>", lambda e: get_item())

        inventory_keys()

    def on_show_inv():
        inv_state["looking"] = False  # kill any running inventory_keys loop
        player.show_inventory(win)
        if win.inventory_show:
            on_use_item()

    def inspect_cell():
        y, x = player.location.location
        ny, nx = next_cell(y, x, player.facing)
        target = maze_.cells[ny][nx]
        inspect(target)

    def pickup():
        y, x = player.location.location
        ny, nx = next_cell(y, x, player.facing)
        target = maze_.cells[ny][nx]
        player.get_cell_inventory(target)

    def turn(direction):
        player.facing = direction

    def game_keys():
        # Turning
        win.bind_key("<Shift-KeyPress-Up>", lambda e: turn("up"))
        win.bind_key("<Shift-KeyPress-Down>", lambda e: turn("down"))
        win.bind_key("<Shift-KeyPress-Right>", lambda e: turn("right"))
        win.bind_key("<Shift-KeyPress-Left>", lambda e: turn("left"))
        win.bind_key("<Shift-KeyPress-w>", lambda e: turn("up"))
        win.bind_key("<Shift-KeyPress-s>", lambda e: turn("down"))
        win.bind_key("<Shift-KeyPress-d>", lambda e: turn("right"))
        win.bind_key("<Shift-KeyPress-a>", lambda e: turn("left"))
        # Directional keys
        win.bind_key("<Up>", lambda e: on_move("up"))
        win.bind_key("<Down>", lambda e: on_move("down"))
        win.bind_key("<Left>", lambda e: on_move("left"))
        win.bind_key("<Right>", lambda e: on_move("right"))

        # WASD
        win.bind_key("w", lambda e: on_move("up"))
        win.bind_key("s", lambda e: on_move("down"))
        win.bind_key("a", lambda e: on_move("left"))
        win.bind_key("d", lambda e: on_move("right"))

        # Actions
        win.bind_key("e", lambda e: pickup())
        win.bind_key("j", lambda e: inspect_cell())
        win.bind_key("i", lambda e: on_show_inv())

    game_keys()
    redraw_all()
    win.wait_for_close()


if __name__ == "__main__":
    main()
