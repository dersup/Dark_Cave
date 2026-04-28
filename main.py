# /// script
# dependencies = ["pygame-ce"]
# ///
#The Dark Cave -- Pygame edition
#------------------------------
#Desktop:  python main.py

# Save / Load
#------------------------------
#  F5   Save game
#  F9   Load game  (only from the main menu or game-over screen)
#  Save file lives at  saves/savegame.json  (desktop)
#  or browser localStorage key "dark_cave_save" (web)

import pygame
import sys
import asyncio

from constants import BASE_WEAPONS, COLOURS, BASE_STAFFS
from windows    import Windows
from maze       import Maze
from entity     import Entity, next_cell, inspect
from generator_ import generate_weapon_loot, generate_armor_loot, \
    generate_items_loot, name_gen, generate_staff
from save_load  import save_game, load_game, save_exists, delete_save
from sprites import preload_sprites


# ===============================================================================
#  Shutdown helper -- pygame.quit/sys.exit behave oddly in the browser
# ===============================================================================

def _quit_app():
    """Clean shutdown that works on desktop and in pygbag."""
    if sys.platform == "emscripten":
        # In browser, SystemExit is caught by pygbag's runtime and the tab
        # returns to idle. Calling pygame.quit() here can crash the WASM heap.
        raise SystemExit
    pygame.quit()
    sys.exit()


# ===============================================================================
#  Character-creation screens
# ===============================================================================

_MUSIC_STARTED = False

def play_music():
    """Try to start background music. Browsers require a user gesture first --
    callers should invoke this only after a confirmed KEYDOWN."""
    global _MUSIC_STARTED
    if _MUSIC_STARTED:
        return
    try:
        pygame.mixer.init()
        pygame.mixer.music.load("assets/music/Iron_Descent.ogg")
        pygame.mixer.music.play(-1)
        _MUSIC_STARTED = True
    except Exception:
        # Browser hasn't authorized audio yet, or ogg unavailable.
        # Leave _MUSIC_STARTED False so a later gesture can retry.
        _MUSIC_STARTED = False

async def _menu(win: Windows, prompt: str, options: list[str],
                *, allow_back: bool = False, initial_index: int = 0) -> str | None:
    # Arrow-key / WS selection menu. Returns chosen string, or None if the
    # user pressed Esc and allow_back=True.
    cursor = [initial_index % len(options)]
    hint = ("Up/Down / W/S  navigate       Enter  confirm       Esc  back"
            if allow_back else
            "Up/Down / W/S  navigate       Enter  confirm")

    while True:
        win.surface.fill(COLOURS["dark_gray"])
        win.txt(prompt, win.w // 2, win.h // 4, "lg", COLOURS["purple"], center=True)
        # highlight selection and place visible cursor at cursor positon
        for i, opt in enumerate(options):
            pre = "▶  " if i == cursor[0] else "   "
            c   = COLOURS["purple"] if i == cursor[0] else COLOURS["orange"]
            win.txt(pre + opt, win.w // 2 - 80, win.h // 4 + 60 + i * 32, "md", c)
        win.txt(hint, win.w // 2, win.h * 3 // 4, "sm", COLOURS["gray"], center=True)
        pygame.display.flip()
        win.clock.tick(30)
        await asyncio.sleep(0)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:        _quit_app()
            if ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_UP, pygame.K_w):
                    cursor[0] = (cursor[0] - 1) % len(options)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    cursor[0] = (cursor[0] + 1) % len(options)
                elif ev.key == pygame.K_RETURN:
                    return options[cursor[0]]
                elif allow_back and ev.key == pygame.K_ESCAPE:
                    return None


async def _text_input(win: Windows, prompt: str, placeholder: str = "",
                      *, allow_back: bool = False, initial: str = "") -> str | None:
    # Single-line text entry. Enter confirms; blank -> placeholder.
    # Returns None if user pressed Esc and allow_back=True.
    buf     = initial
    blink   = [True]
    timer   = [0]
    hint = ("Enter to confirm        Esc to go back"
            if allow_back else
            "Enter to confirm")

    while True:
        win.surface.fill(COLOURS["dark_gray"])
        win.txt(prompt, win.w // 2, win.h // 2 - 50, "lg", COLOURS["purple"], center=True)
        # if no user txt "buf", use placeholder, else place blinking cursor at end of user txt
        display = (buf or placeholder) + ("|" if blink[0] else " ")
        c = COLOURS["white"] if buf else COLOURS["gray"]
        win.txt(display, win.w // 2, win.h // 2, "md", c, center=True)
        win.txt(hint, win.w // 2, win.h // 2 + 36, "sm", COLOURS["gray"], center=True)
        pygame.display.flip()
        # blinking
        dt       = win.clock.tick(30)
        timer[0] += dt
        if timer[0] >= 500:
            blink[0]  = not blink[0]
            timer[0]  = 0
        await asyncio.sleep(0)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:        _quit_app()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_RETURN:
                    return buf.strip() or placeholder
                elif ev.key == pygame.K_BACKSPACE:
                    buf = buf[:-1]
                elif allow_back and ev.key == pygame.K_ESCAPE:
                    return None
                elif ev.unicode and ev.unicode.isprintable():
                    buf += ev.unicode

async def options(win: Windows):
    def draw_frame(toast= None):
        bar = pygame.Surface((win.w, 60), pygame.SRCALPHA)
        bar.fill((0, 0, 0, 170))
        win.surface.blit(bar, (0, 12))
        win.txt(toast, win.w // 2, 42, "md",
                COLOURS["red"], center=True)
    async def show_toast(message, ms=1400):
        # Brief overlay; any keypress dismisses early
        pygame.event.clear()
        end = pygame.time.get_ticks() + ms
        while pygame.time.get_ticks() < end:
            draw_frame(toast=message)
            pygame.display.flip()
            win.clock.tick(30)
            await asyncio.sleep(0)
            done = False
            for ev_ in pygame.event.get():
                if ev_.type == pygame.QUIT:
                    _quit_app()
                if ev_.type == pygame.KEYDOWN:
                    done = True
                    break
            if done:
                break
        pygame.event.clear()
    box_checked = -1
    buf_w = ""
    buf_h = ""
    blink = [True]
    timer = [0]
    cursor = [0]
    side_cursor = [1]
    while True:
        win.surface.fill(COLOURS["black"])
        box = "✕" if box_checked == -1 else "✓"
        pre = "▶ "
        if not buf_w:
            dis_w = ("|" if blink[0] and side_cursor[0] else " ") + (str(win.maze_size[0]))
        elif buf_w:
            dis_w = (buf_w ) + ("|" if blink[0] and side_cursor[0] else " ")
        if not buf_h:
            dis_h = ("|" if blink[0] and not side_cursor[0] else " ") + (str(win.maze_size[1]))
        elif buf_h:
            dis_h = (buf_h) + ("|" if blink[0] and not side_cursor[0] else " ")
        night = f"Nightmare mode     {box}"
        m_size = f"Maze Size          {dis_w}x{dis_h}"
        exit_text = "EXIT"
        if cursor[0] == 0:
            night = pre + night
        if cursor[0] == 1:
            m_size = pre + m_size
        if cursor[0] == 2:
            exit_text = pre + exit_text

        win.txt(night, win.w // 2, win.h // 2, "lg", COLOURS["purple"], center=True)
        win.txt(m_size, win.w//2,win.h//2 + win.font["lg"].get_height() * 2 ,"lg", COLOURS["purple"], center=True)
        win.txt(exit_text, win.w//1.5, win.h - (win.font["lg"].get_height()* 4),"lg",COLOURS["red"], center=True)

        pygame.display.flip()
        dt = win.clock.tick(30)
        timer[0] += dt
        if timer[0] >= 500:
            blink[0] = not blink[0]
            timer[0] = 0
        await asyncio.sleep(0)
        up_keys = (pygame.K_UP, pygame.K_w)
        down_keys = (pygame.K_DOWN, pygame.K_s)
        left_keys = (pygame.K_LEFT, pygame.K_a)
        right_keys = (pygame.K_RIGHT, pygame.K_d)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: _quit_app()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return
                elif ev.key in up_keys:
                    cursor[0] = (cursor[0] - 1) % 3
                elif ev.key in down_keys:
                    cursor[0] = (cursor[0] + 1) % 3
                elif ev.key in right_keys and cursor[0] == 1:
                    side_cursor[0] = (side_cursor[0] + 1) % 2
                elif ev.key in left_keys and cursor[0] == 1:
                    side_cursor[0] = (side_cursor[0] - 1) % 2
                elif ev.key == pygame.K_RETURN:
                    if cursor[0] == 1:
                        if buf_w and buf_h:
                            win.maze_size = (int(buf_w), int(buf_h))
                            await show_toast(f"{str((buf_w, buf_h))}, saved")
                        elif buf_w:
                            win.maze_size = (int(buf_w), int(win.maze_size[1]))
                            await show_toast(f"{str((buf_w, win.maze_size[1]))}, saved")
                        elif buf_h:
                            win.maze_size = (int(win.maze_size[0]), int(buf_h))
                            await show_toast(f"{str((win.maze_size[0], buf_h))}, saved")
                        else:
                            await show_toast(f"{str((win.maze_size[0], win.maze_size[1]))}, saved")
                    elif cursor[0] == 0:
                        box_checked *= -1
                        win.night *= -1
                    elif cursor[0] == 2:
                        return
                elif ev.unicode and ev.unicode.isdigit():
                    if side_cursor[0] == 1:
                        buf_w += ev.unicode
                    elif side_cursor[0] == 0:
                        buf_h += ev.unicode
                elif ev.key == pygame.K_BACKSPACE:
                    if side_cursor[0] == 1:
                        buf_w = buf_w[:-1]
                    elif side_cursor[0] == 0:
                        buf_h = buf_h[:-1]




async def _stat_allocation(win: Windows, player: Entity, *, allow_back: bool = False) -> bool:
    """
    Point-buy stat screen.
    Left/Right (or A/D) to add/remove points from highlighted stat.
    Enter when all 25 points spent.

    Returns True when the player confirms, False if they pressed Esc to go
    back (only possible when allow_back=True). On True, player.stats is
    mutated in place; on False, player is left untouched.
    """
    stats    = ["attack", "defence", "luck",
                "magic_defence", "magic_attack", "agility"]
    values   = {s: 0 for s in stats}
    total    = 25
    cursor   = [0]
    hold_timer = 0
    HOLD_DELAY = 0.2

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
        base_hint = ("W/S:navigate    A/D or ◄►:remove/add    Enter:confirm (when 0 left)"
                     if remaining > 0 else
                     "W/S:navigate    A/D or ◄►:adjust    Enter:confirm")
        hint = base_hint + ("    Esc:back" if allow_back else "")
        win.txt(hint, win.w // 2, win.h * 5 // 6, "sm", COLOURS["gray"], center=True)
        pygame.display.flip()
        dt = win.clock.tick(30) / 1000
        await asyncio.sleep(0)
        keys = pygame.key.get_pressed()
        up_keys = (pygame.K_UP, pygame.K_w)
        down_keys = (pygame.K_DOWN, pygame.K_s)
        left_keys = (pygame.K_LEFT, pygame.K_a)
        right_keys = (pygame.K_RIGHT, pygame.K_d)
        if any(keys[k] for k in right_keys) or any(keys[k] for k in left_keys):
            hold_timer += dt
            if hold_timer >= HOLD_DELAY:
                hold_timer = 0
                if any(keys[k] for k in right_keys) and remaining > 0:
                    values[stats[cursor[0]]] += 1
                elif any(keys[k] for k in left_keys) and values[stats[cursor[0]]] > 0:
                    values[stats[cursor[0]]] -= 1
        else:
            hold_timer = 0
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT: _quit_app()
            if ev.type == pygame.KEYDOWN:
                if ev.key in up_keys:
                    cursor[0] = (cursor[0] - 1) % len(stats)
                elif ev.key in down_keys:
                    cursor[0] = (cursor[0] + 1) % len(stats)
                elif ev.key in right_keys and remaining > 0:
                    values[stats[cursor[0]]] += 1
                elif ev.key in left_keys and values[stats[cursor[0]]] > 0:
                    values[stats[cursor[0]]] -= 1
                elif ev.key == pygame.K_RETURN and remaining == 0:
                    for s, v in values.items():
                        player.stats[s] = v
                    return True
                elif allow_back and ev.key == pygame.K_ESCAPE:
                    return False


async def _character_creation(win: Windows) -> Entity | None:
    """
    Walk the player through gender -> name -> weapon -> stat allocation.
    Esc on any step returns to the previous step; Esc on the first step
    returns None so the caller can fall back to the start menu.

    Each step retains its previous selection when revisited (cursor
    position, typed name) so backing out is non-destructive. The weapon
    is rolled fresh whenever the weapon step is confirmed.
    """
    gender_options = ["Male", "Female", "Non-Binary"]
    weapon_options = list(BASE_WEAPONS.keys()) + [list(BASE_STAFFS.keys())[0]]

    gender_idx = 0
    name       = ""
    weapon_idx = 0
    weapon_obj = None   # rolled weapon, populated on weapon-step confirm

    step = 0
    while True:
        if step == 0:
            choice = await _menu(
                win, "Choose your hero's gender", gender_options,
                allow_back=True, initial_index=gender_idx,
            )
            if choice is None:
                return None
            gender_idx = gender_options.index(choice)
            step = 1

        elif step == 1:
            gender_str = gender_options[gender_idx].lower().replace("-", " ")
            default    = name_gen(gender_str if gender_str in ("male", "female") else "")
            entered    = await _text_input(
                win, "What is your hero's name?", default,
                allow_back=True, initial=name,
            )
            if entered is None:
                step = 0
                continue
            name = entered
            step = 2

        elif step == 2:
            choice = await _menu(
                win, "choose your weapon", weapon_options,
                allow_back=True, initial_index=weapon_idx,
            )
            if choice is None:
                step = 1
                continue
            weapon_idx = weapon_options.index(choice)
            if choice == "apprentice staff":
                weapon_obj = generate_staff("player", "apprentice staff")
            else:
                weapon_obj = generate_weapon_loot("player", choice)
            step = 3

        else:  # step == 3
            armor  = generate_armor_loot("player")
            player = Entity(name, 100, 100, armor_=armor, weapon_=weapon_obj)
            confirmed = await _stat_allocation(win, player, allow_back=True)
            if not confirmed:
                step = 2
                continue
            for _ in range(2):
                player.add_to_inventory(generate_items_loot("player"))
            return player


# ===============================================================================
#  Start menu  (hero artwork background)
# ===============================================================================

# Button geometry, expressed as fractions of the image (640x480). On any window size these scale to the live surface.
_HERO_BUTTONS = (
    # label,    x_frac,    y_frac,    w_frac,    h_frac
    ("Start",   408/640,   216/480,   183/640,   50/480),
    ("Load",    407/640,   281/480,   183/640,   50/480),
    ("Options", 408/640,   348/480,   183/640,   50/480),
    ("Exit",    408/640,   413/480,   183/640,   50/480),
)

# Cache: (window_w, window_h) -> scaled background Surface (or None on failure)
_HERO_IMG_CACHE = {}


def _hero_image(win):
    # Load and cache the title-screen background scaled to the window.
    key = (win.w, win.h)
    if key in _HERO_IMG_CACHE:
        return _HERO_IMG_CACHE[key]
    try:
        raw = pygame.image.load("assets/dark_cave_hero.png").convert()
    except (pygame.error, FileNotFoundError) as e:
        print(f"[start_menu] could not load assets/dark_cave_hero.png: {e}")
        _HERO_IMG_CACHE[key] = None
        return None
    _HERO_IMG_CACHE[key] = pygame.transform.smoothscale(raw, (win.w, win.h))
    return _HERO_IMG_CACHE[key]


def _hero_button_rects(win):
    # Pixel rects for each on-image button at the current window size.
    return [
        (label, pygame.Rect(
            int(fx * win.w), int(fy * win.h),
            int(fw * win.w), int(fh * win.h),
        ))
        for label, fx, fy, fw, fh in _HERO_BUTTONS
    ]


async def start_menu(win: Windows) -> tuple:
    """
    Show the title screen with dark_cave_hero.png as the background.
    A glowing border highlights the currently selected button.

    Returns (player, maze):
      (None, None)   -> begin a new game
      (player, maze) -> resume a loaded save

    NOTE: play_music() is deferred until the first user KEYDOWN below.
    Browsers block autoplay until a user gesture -- calling it here would
    silently fail and leave the game muted.
    """
    hero    = _hero_image(win)
    buttons = _hero_button_rects(win)
    cursor  = [0]

    def draw_frame(toast=None):
        # Background: hero image, with a fallback if it failed to load
        if hero is not None:
            win.surface.blit(hero, (0, 0))
        else:
            win.surface.fill(COLOURS["dark_gray"])
            win.txt("THE DARK CAVE", win.w // 2, win.h // 6, "lg",
                    COLOURS["purple"], center=True)
            for label, rect in buttons:
                pygame.draw.rect(win.surface, (0, 0, 0), rect)
                win.txt(label, rect.centerx, rect.centery, "md",
                        COLOURS["red"], center=True)

        # Selection highlight: glowing border around the chosen button
        sel_rect = buttons[cursor[0]][1]
        pad      = max(4, win.w // 200)
        glow     = sel_rect.inflate(pad * 2, pad * 2)
        pygame.draw.rect(win.surface, COLOURS["purple"], glow,
                         width=max(3, win.w // 320), border_radius=4)

        # Optional transient message, drawn over a translucent bar at top
        if toast:
            bar = pygame.Surface((win.w, 60), pygame.SRCALPHA)
            bar.fill((0, 0, 0, 170))
            win.surface.blit(bar, (0, 12))
            win.txt(toast, win.w // 2, 42, "md",
                    COLOURS["red"], center=True)

    async def show_toast(message, ms=1400):
        # Brief overlay; any keypress dismisses early
        pygame.event.clear()
        end = pygame.time.get_ticks() + ms
        while pygame.time.get_ticks() < end:
            draw_frame(toast=message)
            pygame.display.flip()
            win.clock.tick(30)
            await asyncio.sleep(0)
            done = False
            for ev_ in pygame.event.get():
                if ev_.type == pygame.QUIT:
                    _quit_app()
                if ev_.type == pygame.KEYDOWN:
                    done = True
                    break
            if done:
                break
        pygame.event.clear()

    async def yes_no(message):
        # Drain any stale events (e.g. the ENTER press that opened this dialog)
        # so the confirmation can't auto-trigger on a replayed key.
        pygame.event.clear()
        while True:
            draw_frame()
            # Translucent dim layer so the prompt stays legible over the artwork
            dim = pygame.Surface((win.w, win.h), pygame.SRCALPHA)
            dim.fill((0, 0, 0, 180))
            win.surface.blit(dim, (0, 0))
            win.txt(message, win.w // 2, win.h // 2 - 20,
                    "md", COLOURS["gray"], center=True)
            win.txt("Y/N", win.w // 2, win.h // 2 + 50,
                    "md", COLOURS["red"], center=True)
            win.clock.tick(30)
            pygame.display.flip()
            await asyncio.sleep(0)
            for ev_ in pygame.event.get():
                if ev_.type == pygame.QUIT:
                    _quit_app()
                if ev_.type == pygame.KEYDOWN:
                    if ev_.key in (pygame.K_RETURN, pygame.K_y):
                        return True
                    if ev_.key in (pygame.K_ESCAPE, pygame.K_n):
                        return False

    while True:
        draw_frame()
        pygame.display.flip()
        win.clock.tick(30)
        await asyncio.sleep(0)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                _quit_app()
            if ev.type == pygame.KEYDOWN:
                # First confirmed user gesture -- safe to start audio now.
                play_music()
                if ev.key == pygame.K_ESCAPE:
                    _quit_app()
                elif ev.key in (pygame.K_UP, pygame.K_w):
                    cursor[0] = (cursor[0] - 1) % len(buttons)
                elif ev.key in (pygame.K_DOWN, pygame.K_s):
                    cursor[0] = (cursor[0] + 1) % len(buttons)
                elif ev.key == pygame.K_RETURN:
                    label = buttons[cursor[0]][0]

                    if label == "Start":
                        if save_exists():
                            yn = await yes_no(
                                "Start a new game? This will overwrite your save."
                            )
                            if not yn:
                                continue
                            delete_save()
                        return None, None

                    if label == "Load":
                        if not save_exists():
                            await show_toast("No save file found.")
                            continue
                        player, maze = load_game(win)
                        if player and maze:
                            return player, maze
                        await show_toast("Save could not be loaded.")
                        continue

                    if label == "Options":
                        await options(win)
                        continue

                    if label == "Exit":
                        _quit_app()

# ==============================================================================
#  Main game
# ==============================================================================

async def main(player: Entity = None, win: Windows = None, maze: Maze = None):
    # -- Window ---------------------------------------------------------
    pygame.init()
    if win is None:
        info = pygame.display.Info()
        screen_width = info.current_w
        screen_height = info.current_h
        win = Windows(screen_width, screen_height)
    else:
        # Reset UI state for a new run / new level
        win._game_over      = False
        win._go_text        = ""
        win.inventory_show  = False
        win._log            = []
        win._log_timer      = []

    win._ui_blocked = False
    await preload_sprites()
    win._restart_request = None

    # -- Start menu / character creation (only on very first call) ----------
    # Backing out of character creation returns to the start menu, so wrap
    # both screens in a loop and keep going until we have a player.
    if player is None and maze is None:
        while player is None:
            loaded_player, loaded_maze = await start_menu(win)
            if loaded_player:
                player, maze = loaded_player, loaded_maze
                break
            # User chose Start (no save loaded) -> walk through char creation.
            # Returning None means they backed all the way out; loop the
            # start menu again.
            player = await _character_creation(win)

    # -- Maze (skip rebuild when loaded from save) ----------------------------
    if maze is None:
        maze = Maze(win.maze_size[1], win.maze_size[0], win)
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
    play_music()

    # -- State flags --------------------------------------------------
    busy  = False    # True while movement animation is running
    alive = True

    # =========================================================================
    #  Game-logic helpers
    # =========================================================================
    def redraw():
        win.surface.fill(COLOURS["black"])
        maze.update_visibility(player)
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
        x_,y_ = player.location.cent.x, player.location.cent.y
        win.center_on_point(x_, y_)
        win.set_player_stats(player)
        do_enemy_turn()

    def do_enemy_turn():
        def _retry():
            win._restart_request = ("retry", None, None)
            win.show_game_over(player, maze, on_retry=_retry, on_quit=_quit)
        py,px = player.location.location
        nonlocal alive
        for row in maze.cells:
            for cell in row:
                if cell.enemy and cell.enemy_entity:
                    y_,x_ = cell.location
                    if abs(x_ - px)+abs(y_ - py)<=3:
                        maze.update_visibility(cell.enemy_entity,3)
                    else:
                        cell.enemy_entity.visible_cells = set()
                    new_cell, message = cell.enemy_entity.enemy_turn(player, maze)
                    if message is not None:
                        win.log(message)
                    if new_cell:
                        source_visible = tuple(cell.location) in player.visible_cells
                        dest_visible = new_cell and tuple(new_cell.location) in player.visible_cells
                        if (source_visible or dest_visible) and cell not in win.animating_cells:
                            win.animating_cells.append(cell)
        win.set_player_stats(player)
        if player.health <= 0:
            alive = False
            win.show_game_over(
                player, maze,
                on_retry=_retry,
                on_quit=_quit
            )

    def _quit():
        _quit_app()

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
            win._restart_request = ("load", loaded_p, loaded_m)
        else:
            win.log("No save file found.")

    # -- Inventory ------------------------------------------------------------

    # Held-key cursor auto-repeat for panels (matches _stat_allocation timing).
    # The initial press is handled by bindings registered in bind_panel; this
    # state machine adds the "keep moving while held" behavior on top.
    PANEL_HOLD_DELAY = 0.2  # seconds between repeats while a direction is held
    _panel_hold = {"cursor_fn": None, "timer": 0.0, "last_ms": 0}

    def _tick_panel_hold():
        cursor_fn = _panel_hold["cursor_fn"]
        now = pygame.time.get_ticks()
        if cursor_fn is None:
            # No panel open -> keep last_ms current so the first frame after
            # a panel opens has a sensible (small) dt.
            _panel_hold["last_ms"] = now
            return
        dt = (now - _panel_hold["last_ms"]) / 1000.0
        _panel_hold["last_ms"] = now
        # If something paused the loop (animation, tab switch, breakpoint),
        # don't immediately fire a repeat once we resume.
        if dt > 0.5:
            _panel_hold["timer"] = 0.0
            return
        keys = pygame.key.get_pressed()
        up_held   = keys[pygame.K_UP]   or keys[pygame.K_w]
        down_held = keys[pygame.K_DOWN] or keys[pygame.K_s]
        if up_held or down_held:
            _panel_hold["timer"] += dt
            if _panel_hold["timer"] >= PANEL_HOLD_DELAY:
                _panel_hold["timer"] = 0.0
                cursor_fn(-1 if up_held else 1)
        else:
            _panel_hold["timer"] = 0.0

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
        # Enable held-key cursor auto-repeat for this panel.
        _panel_hold["cursor_fn"] = cursor
        _panel_hold["timer"]     = 0.0
        _panel_hold["last_ms"]   = pygame.time.get_ticks()

    def open_inventory():  open_panel("inventory")
    def open_spell_list(): open_panel("spell_list")

    def bind_game():
        win.unbind_all()
        # Disable the panel held-key auto-repeat.
        _panel_hold["cursor_fn"] = None
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
        await asyncio.sleep(0)
        if win._restart_request is not None:
            kind, p, m = win._restart_request
            win._restart_request = None
            if kind == "retry":
                # Fresh character + fresh maze, keep window
                return await main(win=win)
            if kind == "load":
                return await main(player=p, win=win, maze=m)
        if win._ui_blocked:
            continue
        if not win.tick():
            _quit()
        _tick_panel_hold()
        redraw()


asyncio.run(main())