"""
The Dark Cave — Pygame edition
─────────────────────────────
Desktop:  python main.py
LAN web:  bash serve_lan.ps1   (runs pygbag then http.server)
"""
import pygame
import sys

from constants import BASE_WEAPONS, COLOURS
from windows    import Windows
from maze       import Maze
from entity     import Entity, next_cell, inspect
from generator_ import generate_weapon_loot, generate_armor_loot, \
                       generate_items_loot, name_gen


# ═══════════════════════════════════════════════════════════════════════════════
#  Character-creation screens (blocking Pygame sub-loops)
# ═══════════════════════════════════════════════════════════════════════════════

def _menu(win: Windows, prompt: str, options: list[str]) -> str:
    """Arrow-key / WS selection menu. Returns chosen string."""
    cursor = [0]

    while True:
        win.surface.fill((10, 8, 12))
        win.txt(prompt, win.w // 2, win.h // 4, "lg", (160, 130, 255), center=True)
        for i, opt in enumerate(options):
            pre = "▶  " if i == cursor[0] else "   "
            c   = (120, 180, 255) if i == cursor[0] else (200, 195, 180)
            win.txt(pre + opt, win.w // 2 - 80, win.h // 4 + 60 + i * 32, "md", c)
        win.txt("↑↓ / WS  navigate       Enter  confirm", win.w // 2, win.h * 3 // 4, "sm", (110, 100, 90), center=True)
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
    """Single-line text entry. Enter confirms; blank → placeholder."""
    buf     = ""
    blink   = [True]
    timer   = [0]

    while True:
        win.surface.fill((10, 8, 12))
        win.txt(prompt, win.w // 2, win.h // 2 - 50, "lg", (160, 130, 255), center=True)
        display = (buf or placeholder) + ("|" if blink[0] else " ")
        c = (120, 180, 255) if buf else (90, 85, 80)
        win.txt(display, win.w // 2, win.h // 2, "md", c, center=True)
        win.txt("Enter to confirm", win.w // 2, win.h // 2 + 36, "sm", (110, 100, 90), center=True)
        pygame.display.flip()

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
        win.surface.fill((10, 8, 12))
        win.txt(f"Distribute {remaining} stat point(s)", win.w // 2, win.h // 6, "lg", (160, 130, 255), center=True)
        for i, stat in enumerate(stats):
            y   = win.h // 6 + 55 + i * 34
            pre = "▶ " if i == cursor[0] else "  "
            c   = (120, 180, 255) if i == cursor[0] else (200, 195, 180)
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


# ═══════════════════════════════════════════════════════════════════════════════
#  Main game
# ═══════════════════════════════════════════════════════════════════════════════

def main(player: Entity = None, win: Windows = None, maze: Maze = None):

    # ── Window ──────────────────────────────────────────────────────────────
    if win is None:
        win = Windows(1280, 800)
    else:
        # Reset UI state for a new run / new level
        win._game_over      = False
        win._go_text        = ""
        win.inventory_show  = False
        win._log            = []
        win._log_timer      = []

    # ── Character creation ───────────────────────────────────────────────────
    if player is None:
        gender_choice = _menu(win, "Choose your hero's gender",
                               ["Male", "Female", "Non-Binary"])
        gender  = gender_choice.lower().replace("-", " ")
        default = name_gen(gender if gender in ("male","female") else "")
        name    = _text_input(win, "What is your hero's name?", default)
        weapon  = generate_weapon_loot("player",_menu(win,"choose your weapon",list(BASE_WEAPONS.keys())))
        armor   = generate_armor_loot("player")
        player  = Entity(name, 100, weapon_=weapon, armor_=armor)
        _stat_allocation(win, player)
        for _ in range(2):
            player.add_to_inventory(generate_items_loot("player"))
    else:
        player.health = player.max_health

    # ── Maze ─────────────────────────────────────────────────────────────────
    if maze is None:
        maze = Maze(30, 30, win)
    else:
        maze._win     = win
        maze.origin  = maze.origin    # unchanged
    maze.create_maze()
    maze.player_init(player)
    win.center_on(player)
    maze.monsters_init()
    maze.update_visibility(player)
    win.set_player_stats(player)

    # ── State flags ──────────────────────────────────────────────────────────
    busy  = False    # True while movement animation is running
    alive = True

    # ═════════════════════════════════════════════════════════════════════════
    #  Game-logic helpers
    # ═════════════════════════════════════════════════════════════════════════

    def redraw():
        win.surface.fill((10, 8, 12))
        for row in maze.cells:
            for cell in row:
                cell.draw(maze)
        # tick any live animations
        for cell in list(win.animating_cells):
            still_running = cell.tick_anim()
            if not still_running:
                win.animating_cells.remove(cell)
        win.render()
        win.flip()

    def after_player_move():
        nonlocal busy
        busy = False
        maze.update_visibility(player)
        win.center_on(player)
        win.set_player_stats(player)
        do_enemy_turn()

    def do_enemy_turn():
        nonlocal alive
        for row in maze.cells:
            for cell in row:
                if cell.enemy and cell.enemy_entity:
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
            player.get_cell_inventory(target)
            win.set_player_stats(player)
            win.log(f"Picked up items from ({nr},{nc})")

    def inspect_cell():
        r, c = player.location.location
        nr, nc = next_cell(r, c, player.facing)
        if 0 <= nr < maze.num_rows and 0 <= nc < maze.num_cols:
            inspect(maze.cells[nr][nc])

    # ── Inventory ────────────────────────────────────────────────────────────

    def use_selected():
        item_name = win.inv_selected_name()
        if item_name:
            player.use_item(item_name, maze)
            win.set_inventory(player)
            win.set_player_stats(player)
            win.log(f"Used: {item_name}")
            do_enemy_turn()

    def open_inventory():
        player.show_inventory(win)
        if win.inventory_show:
            bind_inventory()
        else:
            bind_game()

    def bind_inventory():
        win.unbind_all()
        win.bind(pygame.K_UP,     lambda: win.inv_cursor_move(-1))
        win.bind(pygame.K_DOWN,   lambda: win.inv_cursor_move(1))
        win.bind(pygame.K_w,      lambda: win.inv_cursor_move(-1))
        win.bind(pygame.K_s,      lambda: win.inv_cursor_move(1))
        win.bind(pygame.K_RETURN, use_selected)
        win.bind(pygame.K_e,      use_selected)
        win.bind(pygame.K_i,      open_inventory)

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
        win.bind(pygame.K_e,     pickup)
        win.bind(pygame.K_j,     inspect_cell)
        win.bind(pygame.K_i,     open_inventory)

    # ── Start ────────────────────────────────────────────────────────────────
    bind_game()

    # ── Game loop ────────────────────────────────────────────────────────────
    while True:
        if not win.tick():
            _quit()
        redraw()


if __name__ == "__main__":
    main()