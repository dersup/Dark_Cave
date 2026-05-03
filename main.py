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
    # Arrow-key / WS selection menu, with mouse hover + click. Returns the
    # chosen string, or None if the user pressed Esc and allow_back=True.
    cursor = [initial_index % len(options)]
    hint = ("Up/Down / W/S  navigate       Enter / Click  confirm       Esc  back"
            if allow_back else
            "Up/Down / W/S  navigate       Enter / Click  confirm")

    def option_rects():
        # Wide horizontal hit-strip per row -- generous so hover targets are
        # easy to land on. Y matches the y used in win.txt below.
        rects = []
        for i in range(len(options)):
            y = win.h // 4 + 60 + i * 32
            rects.append(pygame.Rect(win.w // 2 - 200, y - 4, 400, 30))
        return rects

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

        rects = option_rects()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:        _quit_app()
            if ev.type == pygame.MOUSEMOTION:
                # Hover -> move selection cursor.
                for i, r in enumerate(rects):
                    if r.collidepoint(ev.pos):
                        cursor[0] = i
                        break
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                for i, r in enumerate(rects):
                    if r.collidepoint(ev.pos):
                        return options[i]
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
    # Single-line text entry. Enter / click Confirm submits; blank -> placeholder.
    # Returns None if user pressed Esc / clicked Back and allow_back=True.
    buf     = initial
    blink   = [True]
    timer   = [0]
    hint = ("Esc / click Back to go back        Enter / click Confirm"
            if allow_back else
            "Enter / click Confirm")

    def button_rects():
        # Confirm centred below the hint; Back to its left when allowed.
        by = win.h // 2 + 80
        confirm = pygame.Rect(win.w // 2 - 200, by, 120, 40)
        back    = pygame.Rect(win.w // 2 + 60, by, 120, 40) if allow_back else None
        return confirm, back

    while True:
        win.surface.fill(COLOURS["dark_gray"])
        win.txt(prompt, win.w // 2, win.h // 2 - 50, "lg", COLOURS["purple"], center=True)
        # if no user txt "buf", use placeholder, else place blinking cursor at end of user txt
        display = (buf or placeholder) + ("|" if blink[0] else " ")
        c = COLOURS["white"] if buf else COLOURS["gray"]
        win.txt(display, win.w // 2, win.h // 2, "md", c, center=True)
        win.txt(hint, win.w // 2, win.h // 2 + 36, "sm", COLOURS["gray"], center=True)

        # Clickable Confirm / Back buttons (drawn each frame; tint on hover)
        confirm_rect, back_rect = button_rects()
        mp = pygame.mouse.get_pos()
        c_color = COLOURS["purple"] if confirm_rect.collidepoint(mp) else COLOURS["orange"]
        pygame.draw.rect(win.surface, c_color, confirm_rect, width=2, border_radius=4)
        win.txt("Confirm", confirm_rect.centerx, confirm_rect.centery-10, "md",
                c_color, center=True)
        if back_rect is not None:
            b_color = COLOURS["purple"] if back_rect.collidepoint(mp) else COLOURS["red"]
            pygame.draw.rect(win.surface, b_color, back_rect, width=2, border_radius=4)
            win.txt("Back", back_rect.centerx, back_rect.centery-10, "md",
                    b_color, center=True)

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
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                if confirm_rect.collidepoint(ev.pos):
                    return buf.strip() or placeholder
                if back_rect is not None and back_rect.collidepoint(ev.pos):
                    return None
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
        # Brief overlay; any keypress / mouse click dismisses early
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
                if ev_.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
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

        night_y = win.h // 2
        msize_y = win.h // 2 + win.font["lg"].get_height() * 2
        exit_y  = win.h - (win.font["lg"].get_height() * 4)
        win.txt(night, win.w // 2, night_y, "lg", COLOURS["purple"], center=True)
        win.txt(m_size, win.w // 2, msize_y, "lg", COLOURS["purple"], center=True)
        win.txt(exit_text, win.w // 1.5, exit_y, "lg", COLOURS["red"], center=True)

        # Mouse hit-areas. Recomputed each frame so they track resize & retext.
        font_lg     = win.font["lg"]
        line_h      = font_lg.get_height()
        night_w, _  = font_lg.size(night)
        msize_w, _  = font_lg.size(m_size)
        exit_w, _   = font_lg.size(exit_text)
        night_rect  = pygame.Rect(win.w // 2 - night_w // 2,
                                  night_y - line_h // 2, night_w, line_h)
        msize_rect  = pygame.Rect(win.w // 2 - msize_w // 2,
                                  msize_y - line_h // 2, msize_w, line_h)
        exit_rect   = pygame.Rect(int(win.w / 1.5) - exit_w // 2,
                                  exit_y  - line_h // 2, exit_w, line_h)

        # Within the maze-size row, split the displayed dimensions into
        # width / height halves for click-to-focus. The "Maze Size          "
        # prefix has a known width; "{dis_w}", then "x", then "{dis_h}".
        msize_prefix    = ("▶ " if cursor[0] == 1 else "") + "Maze Size          "
        prefix_w        = font_lg.size(msize_prefix)[0]
        widthstr_w      = font_lg.size(dis_w)[0]
        x_glyph_w       = font_lg.size("x")[0]
        dim_left        = msize_rect.x + prefix_w
        width_rect      = pygame.Rect(dim_left, msize_rect.y, widthstr_w, line_h)
        height_left     = dim_left + widthstr_w + x_glyph_w
        height_rect     = pygame.Rect(height_left, msize_rect.y,
                                      msize_rect.right - height_left, line_h)

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
            if ev.type == pygame.MOUSEMOTION:
                if night_rect.collidepoint(ev.pos):
                    cursor[0] = 0
                elif msize_rect.collidepoint(ev.pos):
                    cursor[0] = 1
                elif exit_rect.collidepoint(ev.pos):
                    cursor[0] = 2
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Width / height hit-tests are subsets of msize_rect, so check
                # them first; fall through to the row click otherwise.
                if width_rect.collidepoint(ev.pos):
                    cursor[0]      = 1
                    side_cursor[0] = 1
                elif height_rect.collidepoint(ev.pos):
                    cursor[0]      = 1
                    side_cursor[0] = 0
                elif night_rect.collidepoint(ev.pos):
                    cursor[0]    = 0
                    box_checked *= -1
                    win.night   *= -1
                elif msize_rect.collidepoint(ev.pos):
                    cursor[0] = 1
                elif exit_rect.collidepoint(ev.pos):
                    return
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
    Left/Right (or A/D) to add/remove points from highlighted stat. Click a
    row to select, click +/- buttons to adjust, click Confirm/Back at the
    bottom (Confirm only enabled at 0 remaining).
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

    def row_rects():
        # Per row: (row_select_rect, minus_rect, plus_rect). The row rect
        # covers just the rendered text; minus/plus sit to its right.
        out = []
        font_md = win.font["md"]
        for i, stat in enumerate(stats):
            y = win.h // 6 + 55 + i * 34
            bar = "█" * values[stat] + "░" * (25 - values[stat])
            text = f"  {stat:<15} {values[stat]:>2}  {bar[:20]}"
            tw, th = font_md.size(text)
            text_x = win.w // 2 - 160
            row    = pygame.Rect(text_x, y - 4, tw, max(th, 30))
            minus  = pygame.Rect(text_x + tw + 12, y - 4, 28, 30)
            plus   = pygame.Rect(minus.right + 6,  y - 4, 28, 30)
            out.append((row, minus, plus))
        return out

    def confirm_back_rects():
        # Sit just above the keyboard hint line.
        cy = win.h * 5 // 6 - 50
        confirm = pygame.Rect(win.w // 2 - 200, cy, 120, 36)
        back    = pygame.Rect(win.w // 2 + 60, cy, 120, 36) if allow_back else None
        return confirm, back

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

        # +/- buttons next to each row
        rects = row_rects()
        mp    = pygame.mouse.get_pos()
        for ri, (row_r, minus_r, plus_r) in enumerate(rects):
            for sign, r in (("-", minus_r), ("+", plus_r)):
                hover = r.collidepoint(mp)
                col   = COLOURS["purple"] if hover else COLOURS["orange"]
                pygame.draw.rect(win.surface, col, r, width=2, border_radius=4)
                if sign == "-":
                    win.txt(sign, r.centerx, r.centery-10, "md", col, center=True)
                elif sign == "+":
                    win.txt(sign, r.centerx, r.centery-12, "md", col, center=True)


        base_hint = ("W/S/click:select    A/D ◄► +/-:adjust    Enter/Confirm: done"
                     if remaining > 0 else
                     "W/S/click:select    A/D ◄► +/-:adjust    Enter/Confirm")
        hint = base_hint + ("    Esc/Back" if allow_back else "")
        win.txt(hint, win.w // 2, win.h * 5 // 6, "sm", COLOURS["gray"], center=True)

        # Confirm + Back buttons (Confirm dimmed while remaining > 0)
        confirm_r, back_r = confirm_back_rects()
        confirm_active    = (remaining == 0)
        c_hover           = confirm_r.collidepoint(mp) and confirm_active
        c_color           = (COLOURS["purple"] if c_hover else
                             (COLOURS["orange"] if confirm_active else COLOURS["gray"]))
        pygame.draw.rect(win.surface, c_color, confirm_r, width=2, border_radius=4)
        win.txt("Confirm", confirm_r.centerx, confirm_r.centery-10, "md", c_color, center=True)
        if back_r is not None:
            b_hover = back_r.collidepoint(mp)
            b_color = COLOURS["purple"] if b_hover else COLOURS["red"]
            pygame.draw.rect(win.surface, b_color, back_r, width=2, border_radius=4)
            win.txt("Back", back_r.centerx, back_r.centery-10, "md", b_color, center=True)

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
            # `remaining` was snapshotted at frame start; recompute fresh per
            # event so that several +/− or Confirm events in the same frame
            # see the up-to-date budget.
            remaining = total - sum(values.values())
            if ev.type == pygame.QUIT: _quit_app()
            if ev.type == pygame.MOUSEMOTION:
                # Hover over a row (or its +/- buttons) -> select that stat.
                for ri, (row_r, minus_r, plus_r) in enumerate(rects):
                    if (row_r.collidepoint(ev.pos) or
                        minus_r.collidepoint(ev.pos) or
                        plus_r.collidepoint(ev.pos)):
                        cursor[0] = ri
                        break
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Confirm / Back checked first (they live below the rows).
                if confirm_r.collidepoint(ev.pos) and remaining == 0:
                    for s, v in values.items():
                        player.stats[s] = v
                    return True
                if back_r is not None and back_r.collidepoint(ev.pos):
                    return False
                # Then +/- and row select.
                for ri, (row_r, minus_r, plus_r) in enumerate(rects):
                    if minus_r.collidepoint(ev.pos):
                        cursor[0] = ri
                        if values[stats[ri]] > 0:
                            values[stats[ri]] -= 1
                        break
                    if plus_r.collidepoint(ev.pos):
                        cursor[0] = ri
                        if remaining > 0:
                            values[stats[ri]] += 1
                        break
                    if row_r.collidepoint(ev.pos):
                        cursor[0] = ri
                        break
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
    ("Exit",    409/640,   413/480,   183/640,   50/480),
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

    NOTE: play_music() is deferred until the first user KEYDOWN / mouse click
    below. Browsers block autoplay until a user gesture -- calling it here
    would silently fail and leave the game muted.
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
        # Brief overlay; any keypress / mouse click dismisses early
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
                if ev_.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
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

            # Clickable YES / NO buttons (keyboard Y/N/Enter/Esc still work)
            btn_y    = win.h // 2 + 50
            yes_rect = pygame.Rect(win.w // 2 - 130, btn_y - 18, 100, 36)
            no_rect  = pygame.Rect(win.w // 2 + 30,  btn_y - 18, 100, 36)
            mp = pygame.mouse.get_pos()
            for label, r in (("YES", yes_rect), ("NO", no_rect)):
                hover = r.collidepoint(mp)
                col   = COLOURS["purple"] if hover else COLOURS["red"]
                pygame.draw.rect(win.surface, col, r, width=2, border_radius=4)
                win.txt(label, r.centerx, r.centery-10, "md", col, center=True)

            win.clock.tick(30)
            pygame.display.flip()
            await asyncio.sleep(0)
            for ev_ in pygame.event.get():
                if ev_.type == pygame.QUIT:
                    _quit_app()
                if ev_.type == pygame.MOUSEBUTTONDOWN and ev_.button == 1:
                    if yes_rect.collidepoint(ev_.pos):
                        return True
                    if no_rect.collidepoint(ev_.pos):
                        return False
                if ev_.type == pygame.KEYDOWN:
                    if ev_.key in (pygame.K_RETURN, pygame.K_y):
                        return True
                    if ev_.key in (pygame.K_ESCAPE, pygame.K_n):
                        return False

    async def activate(label):
        # Returns ("return", value) to break out of the menu, or
        # ("stay",) to keep the menu running. Used by both the keyboard
        # (Enter) and mouse (left click) paths.
        if label == "Start":
            if save_exists():
                yn = await yes_no(
                    "Start a new game? This will overwrite your save."
                )
                if not yn:
                    return ("stay",)
                delete_save()
            return ("return", (None, None))

        if label == "Load":
            if not save_exists():
                await show_toast("No save file found.")
                return ("stay",)
            player, maze = load_game(win)
            if player and maze:
                return ("return", (player, maze))
            await show_toast("Save could not be loaded.")
            return ("stay",)

        if label == "Options":
            await options(win)
            return ("stay",)

        if label == "Exit":
            _quit_app()  # never returns
        return ("stay",)

    while True:
        draw_frame()
        pygame.display.flip()
        win.clock.tick(30)
        await asyncio.sleep(0)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                _quit_app()
            if ev.type == pygame.MOUSEMOTION:
                # Hover -> move selection cursor.
                for i, (label, rect) in enumerate(buttons):
                    if rect.collidepoint(ev.pos):
                        cursor[0] = i
                        break
            if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                # Click is a confirmed user gesture too -- start audio.
                play_music()
                for i, (label, rect) in enumerate(buttons):
                    if rect.collidepoint(ev.pos):
                        cursor[0] = i
                        result = await activate(label)
                        if result[0] == "return":
                            return result[1]
                        break
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
                    result = await activate(label)
                    if result[0] == "return":
                        return result[1]

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
        win.spell_list_show = False
        win.pause_show      = False
        win.log_show        = False
        win._log            = []
        win._log_timer      = []
        win.clear_log_history()

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
            win.show_game_over(player, maze, on_retry=_retry, on_quit=_to_menu)
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
                on_quit=_to_menu
            )

    def _quit():
        _quit_app()

    def _to_menu():
        # "N" on the game-over screen: don't close the app, return to the
        # start menu. Reuse the "retry" restart kind (player=None, maze=None)
        # so main() re-enters and falls through to the start_menu loop.
        win._restart_request = ("retry", None, None)

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

    # -- Pause menu action dispatch -------------------------------------------

    def do_pause_action(name):
        # Save/Load already log their own status messages, so return "" to
        # keep use_selected from logging a duplicate. _quit_app never returns.
        if name == "save":
            do_save()
            return ""
        if name == "load":
            do_load()
            return ""
        if name == "exit":
            _quit_app()
        return ""

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

    # Per-panel config. The cursor + selected-name logic is the same across
    # every panel (panel_cursor_move / panel_selected_name keyed by the dict
    # entry's name), so it lives in bind_panel/use_selected rather than here.
    # ends_turn=True triggers an enemy turn after the action -- inventory and
    # spell list both consume a turn; the pause menu does not.
    _PANELS = {
        "inventory": dict(
            close_key   = (pygame.K_i,pygame.K_ESCAPE),
            action_fn   = lambda name: player.use_item(name, maze),
            drop_fn     = lambda item: player.drop_item(item, player.location),
            refresh_fn  = lambda: win.set_inventory(player),
            log_prefix  = "Used: ",
            drop_prefix = "Dropped: ",
            ends_turn   = True,
        ),
        "spell_list": dict(
            close_key   = (pygame.K_c,pygame.K_ESCAPE),
            action_fn   = lambda name: player.cast_spell(name, maze),
            refresh_fn  = lambda: win.set_spell_list(player),
            log_prefix  = "",
            ends_turn   = True,
        ),
        "pause": dict(
            close_key   = pygame.K_ESCAPE,
            action_fn   = do_pause_action,
            refresh_fn  = lambda: None,
            log_prefix  = "",
            ends_turn   = False,
        ),
        # Read-only run history. action_fn=None makes Enter/E silent no-ops
        # via _do_panel_action's None-check; drop is similarly absent. Tab
        # toggles the panel; Esc also closes. ends_turn=False so opening
        # the log doesn't burn a turn.
        "log": dict(
            close_key   = (pygame.K_TAB, pygame.K_ESCAPE),
            action_fn   = None,
            refresh_fn  = lambda: win.set_log_panel(),
            log_prefix  = "",
            ends_turn   = False,
        ),
    }

    def _do_panel_action(panel, fn_key, prefix_key, by="name"):
        """Shared dispatcher for panel actions (use, drop, ...).

        Looks up the action callable under `fn_key` in the panel's config; if
        the panel doesn't define one (e.g. spell_list has no drop_fn), this is
        a silent no-op so a stray keypress can't crash anything.

        `by` controls what gets passed to the callable:
          - "name": the lowercased line label (use_item style; tolerates "3x"
            stack prefixes since use_item strips them).
          - "item": the actual Item object at the cursor (required by methods
            like drop_item / remove_item that match objects, not strings).
        """
        cfg = _PANELS[panel]
        fn  = cfg.get(fn_key)
        if fn is None:
            return
        label = win.panel_selected_name(panel)
        if not label:
            return
        if by == "item":
            arg = win.panel_selected_item(panel)
            if arg is None:
                # Cursor is on a header row, or this panel doesn't carry items.
                return
        else:
            arg = label.lower()
        prefix = cfg.get(prefix_key, "")
        if prefix:
            win.log(f"{prefix}{label}")
        result = fn(arg)
        cfg["refresh_fn"]()
        win.set_player_stats(player)
        win.log(result)
        if cfg["ends_turn"]:
            do_enemy_turn()

    def use_selected(panel="inventory"):
        _do_panel_action(panel, "action_fn", "log_prefix")

    def drop_selected(panel="inventory"):
        _do_panel_action(panel, "drop_fn", "drop_prefix", by="item")

    def open_panel(panel="inventory"):
        # The pause panel has no per-Entity setup (its lines are static), so
        # toggle it directly. The log panel is also Windows-internal -- it
        # reads from win._history, not the player -- so we populate via
        # set_log_panel and toggle visibility here. Inventory/spell_list go
        # through Entity.show_panel which also rebuilds their line data.
        if panel == "pause":
            win.pause_show = not win.pause_show
        elif panel == "log":
            # Build lines fresh each time so newly logged messages since the
            # last open are included, and scroll jumps to the bottom.
            win.set_log_panel()
            win.log_show = not win.log_show
        else:
            player.show_panel(win, panel)
        if getattr(win, f"{panel}_show"):
            bind_panel(panel)
        else:
            bind_game()

    def bind_panel(panel="inventory"):
        cfg    = _PANELS[panel]
        # All panels share the same cursor-move / selection logic, keyed by
        # the panel name. No more per-panel cursor_fn lambdas.
        cursor = lambda delta: win.panel_cursor_move(panel, delta)
        win.unbind_all()
        win.bind(pygame.K_UP,       lambda: cursor(-1))
        win.bind(pygame.K_DOWN,     lambda: cursor(1))
        win.bind(pygame.K_w,        lambda: cursor(-1))
        win.bind(pygame.K_s,        lambda: cursor(1))
        win.bind(pygame.K_d,        lambda: drop_selected(panel))
        win.bind(pygame.K_RETURN,   lambda: use_selected(panel))
        win.bind(pygame.K_e,        lambda: use_selected(panel))
        win.bind_keys(cfg["close_key"],  lambda: open_panel(panel))
        # Save/load hotkeys still work inside panels
        win.bind(pygame.K_F5,       do_save)
        win.bind(pygame.K_F9,       do_load)
        # Mouse hooks for the active panel. Right-click drop is wired up only
        # when the panel actually defines drop_fn (inventory does, spell_list
        # and pause don't), so right-clicking a spell or a pause command is a
        # no-op rather than firing a stale handler.
        win.bind_panel_actions(
            panel,
            use   = lambda: use_selected(panel),
            drop  = (lambda: drop_selected(panel)) if "drop_fn" in cfg else None,
            close = lambda: open_panel(panel),
        )
        # Enable held-key cursor auto-repeat for this panel.
        _panel_hold["cursor_fn"] = cursor
        _panel_hold["timer"]     = 0.0
        _panel_hold["last_ms"]   = pygame.time.get_ticks()

    def open_inventory():  open_panel("inventory")
    def open_spell_list(): open_panel("spell_list")
    def open_pause():      open_panel("pause")

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
        win.bind(pygame.K_TAB,   lambda: open_panel("log"))
        win.bind(pygame.K_ESCAPE, open_pause)
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