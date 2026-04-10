
#The Dark Cave — Pygame edition
#------------------------------
#Desktop:  python main.py

# Save / Load
#------------------------------
#  F5   Save game
#  F9   Load game  (only from the main menu or game-over screen)
#  Save file lives at  saves/savegame.json

import pygame
import sys

from constants import BASE_WEAPONS, COLOURS, BASE_STAFFS
from windows    import Windows
from maze       import Maze
from entity     import Entity, next_cell, inspect
from generator_ import generate_weapon_loot, generate_armor_loot, \
    generate_items_loot, name_gen, generate_staff
from save_load  import save_game, load_game, save_exists, delete_save


# ===============================================================================
#  Character-creation screens
# ===============================================================================

def _menu(win: Windows, prompt: str, options: list[str]) -> str:
    # Arrow-key / WS selection menu. Returns chosen string.
    cursor = [0]

    while True:
        win.surface.fill(COLOURS["dark_gray"])
        win.txt(prompt, win.w // 2, win.h // 4, "lg", COLOURS["purple"], center=True)
        # highlight selection and place visible cursor at cursor positon
        for i, opt in enumerate(options):
            pre = "▶  " if i == cursor[0] else "   "
            c   = COLOURS["purple"] if i == cursor[0] else COLOURS["orange"]
            win.txt(pre + opt, win.w // 2 - 80, win.h // 4 + 60 + i * 32, "md", c)
        win.txt("Up/Down / W/S  navigate       Enter  confirm", win.w // 2, win.h * 3 // 4, "sm", COLOURS["gray"], center=True)
        pygame.display.flip()
        win.clock.tick(30)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:        pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    cursor[0] = (cursor[0] - 1) % len(options)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    cursor[0] = (cursor[0] + 1) % len(options)
                elif ev.key == pygame.K_RETURN:
                    return options[cursor[0]]


def _text_input(win: Windows, prompt: str, placeholder: str = "") -> str:
    # Single-line text entry. Enter confirms; blank → placeholder.
    buf     = ""
    blink   = [True]
    timer   = [0]

    while True:
        win.surface.fill(COLOURS["dark_gray"])
        win.txt(prompt, win.w // 2, win.h // 2 - 50, "lg", COLOURS["purple"], center=True)
        # if no user txt "buf", use placeholder, else place blinking cursor at end of user txt
        display = (buf or placeholder) + ("|" if blink[0] else " ")
        c = COLOURS["white"] if buf else COLOURS["gray"]
        win.txt(display, win.w // 2, win.h // 2, "md", c, center=True)
        win.txt("Enter to confirm", win.w // 2, win.h // 2 + 36, "sm", COLOURS["gray"], center=True)
        pygame.display.flip()
        # blinking
        dt       = win.clock.tick(30)
        timer[0] += dt
        if timer[0] >= 500:
            blink[0]  = not blink[0]
            timer[0]  = 0

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:        pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    return buf.strip() or placeholder
                elif ev.key == pygame.K_BACKSPACE:
                    buf = buf[:-1]
                elif ev.unicode and ev.unicode.isprintable():
                    buf += ev.unicode


def _stat_allocation(win: Windows, player: Entity):
    """
    Point-buy stat screen.
    Left/Right (or A/D) to add/remove points from highlighted stat.
    Enter when all 25 points spent.
    """
    stats    = ["attack", "defence", "luck",
                "magic_defence", "magic_attack", "agility"]
    values   = {s: 0 for s in stats}
    total    = 25
    cursor   = [0]

    while True:
        remaining = total - sum(values.values())
        win.surface.fill(COLOURS["black"])
        win.txt(f"Distribute {remaining} stat point(s)", win.w // 2, win.h // 6, "lg", COLOURS["purple"], center=True)
        for i, stat in enumerate(stats):
            # window's cursor
            y   = win.h // 6 + 55 + i * 34
            pre = "▶ " if i == cursor[0] else "  "
            c   = COLOURS["purple"] if i == cursor[0] else COLOURS["orange"]
            # visual bar
            bar = "█" * values[stat] + "░" * (25 - values[stat])
            win.txt(f"{pre}{stat:<15} {values[stat]:>2}  {bar[:20]}", win.w // 2 - 160, y, "md", c)
        hint = ("W/S:navigate    A/D or ◄►:remove/add    Enter:confirm (when 0 left)"
                if remaining > 0 else
                "W/S:navigate    A/D or ◄►:adjust    Enter:confirm")
        win.txt(hint, win.w // 2, win.h * 5 // 6, "sm", COLOURS["gray"], center=True)
        pygame.display.flip()
        win.clock.tick(30)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:        pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    cursor[0] = (cursor[0] - 1) % len(stats)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    cursor[0] = (cursor[0] + 1) % len(stats)
                elif ev.key in (pygame.K_RIGHT, pygame.K_d):
                    if remaining > 0:
                        values[stats[cursor[0]]] += 1
                elif ev.key in (pygame.K_LEFT, pygame.K_a):
                    if values[stats[cursor[0]]] > 0:
                        values[stats[cursor[0]]] -= 1
                elif ev.key == pygame.K_RETURN:
                    if remaining == 0:
                        for s, v in values.items():
                            player.stats[s] = v
                        return


# ===============================================================================
#  Start menu  (new game / continue)
# ===============================================================================

def start_menu(win: Windows) -> tuple:
#    Show the start screen.
#    Returns (player, maze) where either or both may be None
#    (None, None  → new game;  (player, maze) → loaded save).
    def yes_no(message):
        x = win.w // 2
        y = win.h // 2
        while True:
            win.txt(message,x, y+8, "md", COLOURS["gray"], center=True)
            win.txt("Y/N",x,y+70,"md",COLOURS["red"],center=True)
            win.clock.tick(30)
            pygame.display.flip()
            for ev_ in pygame.event.get():
                if ev_.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev_.type == pygame.KEYDOWN:
                    if ev_.key in (pygame.K_RETURN, pygame.K_y):
                        return True
                    if ev_.key in (pygame.K_ESCAPE, pygame.K_n):
                        return False
    has_save = save_exists()
    options  = ["Continue", "New Game", "Quit"] if has_save \
               else ["New Game", "Quit"]
    cursor = [0]

    while True:
        win.surface.fill(COLOURS["dark_gray"])
        win.txt("THE DARK CAVE", win.w // 2, win.h // 5, "lg", COLOURS["purple"], center=True)
        if has_save:
            win.txt("A save file was found.", win.w // 2, win.h // 5 + 36, "sm", COLOURS["gray"], center=True)
        win.txt("F9 — Load save    F5 — (in-game save)", win.w // 2, win.h * 4 // 5, "sm", COLOURS["gray"], center=True)

        for i, opt in enumerate(options):
            pre = "▶  " if i == cursor[0] else "   "
            c   = COLOURS["purple"] if i == cursor[0] else COLOURS["orange"]
            win.txt(pre + opt, win.w // 2 - 60, win.h // 3 + i * 40, "md", c)

        pygame.display.flip()
        win.clock.tick(30)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    cursor[0] = (cursor[0] - 1) % len(options)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    cursor[0] = (cursor[0] + 1) % len(options)
                elif ev.key == pygame.K_RETURN:
                    choice = options[cursor[0]]
                    if choice == "Continue":
                        player, maze = load_game(win)
                        if player and maze:
                            return player, maze
                        # Corrupted / missing — fall through to new game
                        win.log("Save file could not be loaded. Starting new game.")
                        return None, None

                    if choice == "New Game":
                        if has_save:
                            yn = yes_no("are you sure you want to start a new game?, this will overwrite your save.")
                            if yn:
                                delete_save()
                            else:
                                continue
                        return None, None

                    if choice == "Quit":
                        pygame.quit(); sys.exit()


# ==============================================================================
#  Main game
# ==============================================================================

def main(player: Entity = None, win: Windows = None, maze: Maze = None):

    # -- Window ---------------------------------------------------------
    if win is None:
        win = Windows(1280, 800)
    else:
        # Reset UI state for a new run / new level
        win._game_over      = False
        win._go_text        = ""
        win.inventory_show  = False
        win._log            = []
        win._log_timer      = []

    # -- Start menu (only on very first call) --------------------------------
    if player is None and maze is None:
        loaded_player, loaded_maze = start_menu(win)
        if loaded_player:
            player = loaded_player
            maze   = loaded_maze

    # -- Character creation (only when no save was loaded) -------------------
    if player is None:
        gender_choice = _menu(win, "Choose your hero's gender",
                               ["Male", "Female", "Non-Binary"])
        gender  = gender_choice.lower().replace("-", " ")
        default = name_gen(gender if gender in ("male","female") else "")
        name    = _text_input(win, "What is your hero's name?", default)
        available = list(BASE_WEAPONS.keys())
        available.append(list(BASE_STAFFS.keys())[0])
        weapon  = _menu(win,"choose your weapon", available)
        if weapon == "apprentice staff":
            weapon = generate_staff("player","apprentice staff")
        else:
            weapon = generate_weapon_loot("player",weapon)
        armor   = generate_armor_loot("player")
        player  = Entity(name, 100, 100, armor_=armor, weapon_=weapon)
        _stat_allocation(win, player)
        for _ in range(2):
            player.add_to_inventory(generate_items_loot("player"))

    # -- Maze (skip rebuild when loaded from save) ----------------------------
    if maze is None:
        maze = Maze(10, 10, win)
        maze.create_maze()
        maze.player_init(player)
        maze.monsters_init()
    else:
        # Resuming: maze already fully rebuilt by load_game or next_level
        maze._win = win
        player.health = player.health   # keep loaded health (don't reset)
        win.set_level(maze.level)

    x, y = player.location.cent.x, player.location.cent.y
    win.center_on_point(x, y)
    maze.update_visibility(player)
    win.set_player_stats(player)

    # -- State flags --------------------------------------------------
    busy  = False    # True while movement animation is running
    alive = True

    # =========================================================================
    #  Game-logic helpers
    # =========================================================================
    def redraw():
        win.surface.fill((10, 8, 12))
        for row in maze.cells:
            for cell in row:
                cell.draw(player)
        # tick any live animations
        for cell in list(win.animating_cells):
            still_running = cell.tick_anim(player)
            if not still_running:
                win.animating_cells.remove(cell)
        win.render()
        win.flip()

    def after_player_move():
        nonlocal busy
        busy = False
        maze.update_visibility(player)
        x_,y_ = player.location.cent.x, player.location.cent.y
        win.center_on_point(x_, y_)
        win.set_player_stats(player)
        do_enemy_turn()

    def do_enemy_turn():
        py,px = player.location.location
        nonlocal alive
        for row in maze.cells:
            for cell in row:
                if cell.enemy and cell.enemy_entity:
                    y_,x_ = cell.location
                    if abs(x_ - px)+abs(y_ - py)<=5:
                        maze.update_visibility(cell.enemy_entity,4)
                    else:
                        cell.enemy_entity.visible_cells = set()
                    cell.enemy_entity.enemy_turn(player, maze)
        win.set_player_stats(player)
        if player.health <= 0:
            alive = False
            win.show_game_over(
                player, maze,
                on_retry=lambda: main(win=win, maze=maze),
                on_quit=_quit
            )

    def _quit():
        pygame.quit()
        sys.exit()

    def move(direction):
        nonlocal busy
        if busy or not alive or not direction:
            return
        busy = True
        old_cell = player.location
        message = player.move(direction, maze, on_complete=after_player_move)
        win.log(message)
        # register source cell for animation ticking
        if old_cell not in win.animating_cells:
            win.animating_cells.append(old_cell)

    def turn(direction):
        player.facing = direction

    def pickup():
        r, c = player.location.location
        nr, nc = next_cell(r, c, player.facing)
        if 0 <= nr < maze.num_rows and 0 <= nc < maze.num_cols:
            target = maze.cells[nr][nc]
            items, gold = player.get_cell_inventory(target)
            if not isinstance(items, list):
                items = [items]
            win.set_player_stats(player)
            for item in items:
                win.log(f"{item}")
            win.log(gold)

    def inspect_cell():
        r, c = player.location.location
        nr, nc = next_cell(r, c, player.facing)
        if 0 <= nr < maze.num_rows and 0 <= nc < maze.num_cols:
            win.log(inspect(maze.cells[nr][nc]))

    # -- Save / Load in-game --------------------------------------------------

    def do_save():
        msg = save_game(player, maze)
        win.log(msg)

    def do_load():
        loaded_p, loaded_m = load_game(win)
        if loaded_p and loaded_m:
            win.log("Save loaded — restarting from save point.")
            main(player=loaded_p, win=win, maze=loaded_m)
        else:
            win.log("No save file found.")

    # -- Inventory ------------------------------------------------------------

    _PANELS = {
        "inventory": dict(
            close_key   = pygame.K_i,
            cursor_fn   = lambda delta: win.inv_cursor_move(delta),
            selected_fn = lambda: win.inv_selected_name(),
            action_fn   = lambda name: player.use_item(name, maze),
            refresh_fn  = lambda: win.set_inventory(player),
            log_prefix  = "Used: ",
        ),
        "spell_list": dict(
            close_key   = pygame.K_c,
            cursor_fn   = lambda delta: win.spell_cursor_move(delta),
            selected_fn = lambda: win.spell_selected_name(),
            action_fn   = lambda name: player.cast_spell(name, maze),
            refresh_fn  = lambda: win.set_spell_list(player),
            log_prefix  = "",
        ),
    }

    def use_selected(panel="inventory"):
        cfg       = _PANELS[panel]
        item_name = cfg["selected_fn"]().lower()
        if not item_name:
            return
        if cfg["log_prefix"]:
            win.log(f"{cfg['log_prefix']}{item_name}")
        action = cfg["action_fn"](item_name)
        cfg["refresh_fn"]()
        win.set_player_stats(player)
        win.log(action)
        do_enemy_turn()

    def open_panel(panel="inventory"):
        player.show_panel(win, panel)
        if getattr(win, f"{panel}_show"):
            bind_panel(panel)
        else:
            bind_game()

    def bind_panel(panel="inventory"):
        cfg    = _PANELS[panel]
        cursor = cfg["cursor_fn"]
        win.unbind_all()
        win.bind(pygame.K_UP,       lambda: cursor(-1))
        win.bind(pygame.K_DOWN,     lambda: cursor(1))
        win.bind(pygame.K_w,        lambda: cursor(-1))
        win.bind(pygame.K_s,        lambda: cursor(1))
        win.bind(pygame.K_RETURN,   lambda: use_selected(panel))
        win.bind(pygame.K_e,        lambda: use_selected(panel))
        win.bind(cfg["close_key"],  lambda: open_panel(panel))
        # Save/load still works inside panels
        win.bind(pygame.K_F5,       do_save)
        win.bind(pygame.K_F9,       do_load)

    def open_inventory():  open_panel("inventory")
    def open_spell_list(): open_panel("spell_list")

    def bind_game():
        win.unbind_all()
        # Turning (shift + direction)
        win.bind(("shift", pygame.K_UP),    lambda: turn("up"))
        win.bind(("shift", pygame.K_DOWN),  lambda: turn("down"))
        win.bind(("shift", pygame.K_LEFT),  lambda: turn("left"))
        win.bind(("shift", pygame.K_RIGHT), lambda: turn("right"))
        win.bind(("shift", pygame.K_w),     lambda: turn("up"))
        win.bind(("shift", pygame.K_s),     lambda: turn("down"))
        win.bind(("shift", pygame.K_a),     lambda: turn("left"))
        win.bind(("shift", pygame.K_d),     lambda: turn("right"))
        # Movement
        win.bind(pygame.K_UP,    lambda: move("up"))
        win.bind(pygame.K_DOWN,  lambda: move("down"))
        win.bind(pygame.K_LEFT,  lambda: move("left"))
        win.bind(pygame.K_RIGHT, lambda: move("right"))
        win.bind(pygame.K_w,     lambda: move("up"))
        win.bind(pygame.K_s,     lambda: move("down"))
        win.bind(pygame.K_a,     lambda: move("left"))
        win.bind(pygame.K_d,     lambda: move("right"))
        # Actions
        win.bind(pygame.K_c,     open_spell_list)
        win.bind(pygame.K_e,     pickup)
        win.bind(pygame.K_j,     inspect_cell)
        win.bind(pygame.K_i,     open_inventory)
        # Save / Load
        win.bind(pygame.K_F5,    do_save)
        win.bind(pygame.K_F9,    do_load)

    # -- Start ----------------------------------------------------------------
    bind_game()

    # -- Game loop ------------------------------------------------------------
    while True:
        if not win.tick():
            _quit()
        redraw()


if __name__ == "__main__":
    main()