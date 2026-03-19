from time import sleep
from windows import *
from maze import *
from generator_ import *


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
    name = input("What is the name of your hero?: ") or name_gen()
    weapon_ = weapon_choice()
    armour = Armour("leather jerkin", PLAYER_STARTING_GEAR["armor"]["leather jerkin"]["value"],PLAYER_STARTING_GEAR["armor"]["leather jerkin"]["AC"])
    player = Entity(name, 100, armour, weapon_)
    for i in range(2):
        player.add_to_inventory(generate_items_loot("player"))

    win = Windows(800, 800)
    maze_ = Maze(30, 30, win)
    maze_.create_maze()
    maze_.player_init(player)
    win.center_on(player)
    maze_.monsters_init()
    maze_.update_visibility(player)
    win.player_labels(player)

    state = {"moving": False}
    inv_state = {"num": 2, "looking": False}  # moved outside on_use_item, persists between openings
    prev_keys = set()

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

        def inventory_keys():
            if not inv_state["looking"]:
                return
            if "<Up>" in win.keys_held: increment(-1)
            elif "<Down>" in win.keys_held: increment(1)
            elif "e" in win.keys_held: get_item()
            elif "w" in win.keys_held: increment(-1)
            elif "s" in win.keys_held: increment(1)
            elif "<Enter>" in win.keys_held: get_item()
            win.update_loop(inventory_keys)

        win.highlight_line(inv_state["num"], player)
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

    def loop():
        nonlocal prev_keys
        just_pressed = win.keys_held - prev_keys

        if "i" in just_pressed:
            on_show_inv()

        if not win.inventory_show and not state["moving"]:
            if "<Shift>" in win.keys_held:
                if "<Up>" in win.keys_held: turn("up")
                elif "<Down>" in win.keys_held: turn("down")
                elif "<Left>" in win.keys_held: turn("left")
                elif "<Right>" in win.keys_held: turn("right")
                elif "w" in win.keys_held: turn("up")
                elif "s" in win.keys_held: turn("down")
                elif "a" in win.keys_held: turn("left")
                elif "d" in win.keys_held: turn("right")
            elif "<Up>" in win.keys_held: on_move("up")
            elif "<Down>" in win.keys_held: on_move("down")
            elif "<Left>" in win.keys_held: on_move("left")
            elif "<Right>" in win.keys_held: on_move("right")
            elif "w" in win.keys_held: on_move("up")
            elif "s" in win.keys_held: on_move("down")
            elif "a" in win.keys_held: on_move("left")
            elif "d" in win.keys_held: on_move("right")
            elif "j" in just_pressed: inspect_cell()
            elif "e" in just_pressed: pickup()

        prev_keys = set(win.keys_held)
        win.update_loop(loop)
    loop()
    redraw_all()
    win.wait_for_close()


if __name__ == "__main__":
    main()
