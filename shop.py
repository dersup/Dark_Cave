"""Between-level shop for The Dark Cave.

Pops up between every floor (post-victory of levels 1..9), letting the
player turn loot into coin and pick up new gear scaled to the level
they're heading into. Stock is rolled fresh each visit using a level-
scaled rarity table -- early floors lean common, later floors slip in
epic and legendary rolls.

Generation reuses the same `generate_*_loot` functions used for monster
drops; the only twist is a temporary swap of the global `RARITY` weights
plus a "donor" mob_type whose loot pool we draw from. That way we don't
have to maintain a parallel "shop" entry in every constants table.

UI is a self-contained async screen, modelled on `Windows.show_level_up`:
flip `_ui_blocked = True`, own the pygame event pump for the duration,
restore on exit.
"""

import asyncio
import random
import sys

import pygame

import constants
import generator_
from classes import Inventory, Weapon, Armour, Staff, Healing, Throwing
from generator_ import (
    generate_armor_loot,
    generate_items_loot,
    generate_staff,
    generate_weapon_loot,
)


# ---------------------------------------------------------------------------
# Rarity weights by floor band
# ---------------------------------------------------------------------------
# Same shape as the global RARITY dict so the generators can drop it in
# unmodified. Floor 1 ~ matches the default weights; later floors push the
# distribution toward rare/epic/legendary.

def shop_rarity_weights(level: int) -> dict:
    if level <= 2:
        return {"": 80, "rare": 18, "epic": 2,  "legendary": 0}
    if level <= 4:
        return {"": 60, "rare": 30, "epic": 9,  "legendary": 1}
    if level <= 6:
        return {"": 40, "rare": 40, "epic": 17, "legendary": 3}
    if level <= 8:
        return {"": 25, "rare": 40, "epic": 28, "legendary": 7}
    return {"":     10, "rare": 30, "epic": 45, "legendary": 15}


# Mob types whose loot tables we "borrow" for shop stock. All humanoids
# with broad, balanced gear preferences -- avoids the natural-weapons /
# natural-armor short-circuit that returns anatomy as loot (slimes, troll,
# yeti, pumpkin horror).
_DONOR_WEAPON_MOBS = ("skeleton", "centaur", "minotaur", "vampire")
_DONOR_ARMOR_MOBS  = ("skeleton", "centaur", "minotaur", "vampire")
_DONOR_ITEM_MOBS   = ("skeleton", "centaur", "minotaur", "vampire")
# Staff prefs only exist for these mob types in MOB_STAFF_PREFERENCES.
_DONOR_STAFF_MOBS  = ("dark mage", "wraith", "vampire", "skeleton")


class _RarityOverride:
    """Temporarily swap RARITY everywhere it's been imported.

    The generators do `from constants import *`, which copies the binding
    into their own module namespace. Patching only `constants.RARITY` isn't
    enough -- `generator_.RARITY` is a separate name pointing at the same
    dict. We swap both for the duration and restore on exit, even if
    generation raises.
    """
    def __init__(self, weights: dict):
        self._weights = weights
        self._saved_c = None
        self._saved_g = None

    def __enter__(self):
        self._saved_c = constants.RARITY
        self._saved_g = generator_.RARITY
        constants.RARITY = self._weights
        generator_.RARITY = self._weights
        return self

    def __exit__(self, *exc):
        constants.RARITY = self._saved_c
        generator_.RARITY = self._saved_g
        return False


# ---------------------------------------------------------------------------
# Stock generation
# ---------------------------------------------------------------------------

def generate_shop_inventory(level: int) -> list:
    """Roll fresh stock for the shop. Returns a flat list of Item objects.

    Composition target (10 slots): 3 weapons, 2 staves, 3 armors, 2 consumables.
    Each call uses `shop_rarity_weights(level)` for the duration of generation.
    """
    items = []
    weights = shop_rarity_weights(level)
    with _RarityOverride(weights):
        for _ in range(3):
            items.append(generate_weapon_loot(random.choice(_DONOR_WEAPON_MOBS)))
        for _ in range(2):
            items.append(generate_staff(random.choice(_DONOR_STAFF_MOBS)))
        for _ in range(3):
            items.append(generate_armor_loot(random.choice(_DONOR_ARMOR_MOBS)))
        for _ in range(2):
            items.append(generate_items_loot(random.choice(_DONOR_ITEM_MOBS)))
    return items


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------

def buy_price(item) -> int:
    """Cost to purchase an item from the shop. Floored at 1g."""
    return max(1, int(getattr(item, "value", 0) or 0))


def sell_price(item) -> int:
    """What the shop pays for one of the player's items. Half value, floored
    at 1g so even a `destroyed` / `broken` piece is worth picking up."""
    return max(1, int(getattr(item, "value", 0) or 0) // 2)


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------

def _category_for(item) -> str:
    """Match Inventory._category so we put items in the right bucket."""
    if isinstance(item, Weapon):
        return "Weapons"
    if isinstance(item, Armour):
        return "Armors"
    return "Consumables"


def _shop_lines(stock: list) -> list:
    """Build the display rows for the shop side.

    Returns a list of dicts: {kind: 'header'|'item', text, item, price}.
    Headers carry no item / price; items always do.
    """
    lines = []
    by_cat = {"Weapons": [], "Armors": [], "Consumables": []}
    for it in stock:
        by_cat[_category_for(it)].append(it)
    for cat in ("Weapons", "Armors", "Consumables"):
        if not by_cat[cat]:
            continue
        lines.append({"kind": "header", "text": cat, "item": None, "price": None})
        for it in by_cat[cat]:
            lines.append({"kind": "item", "text": it.name,
                          "item": it, "price": buy_price(it)})
    return lines


def _player_lines(player) -> list:
    """Build the display rows for the player's sellable inventory.

    Skips Equipped (selling worn gear would need an unequip step; we
    keep it simple and require the player to swap out before selling).
    Stacks identical items as "Nx Name" and tracks the underlying list
    so a sell removes one specific instance.
    """
    lines = []
    for cat in ("Weapons", "Armors", "Consumables"):
        items = player.inventory.items.get(cat, [])
        if not items:
            continue
        # Group by Item equality (preserves first-seen order).
        groups = []
        seen = {}
        for it in items:
            if it in seen:
                seen[it]["count"] += 1
            else:
                bucket = {"sample": it, "count": 1}
                seen[it] = bucket
                groups.append(bucket)
        lines.append({"kind": "header", "text": cat,
                      "item": None, "price": None, "category": cat})
        for g in groups:
            it, n = g["sample"], g["count"]
            label = f"{n}x {it.name}" if n > 1 else it.name
            lines.append({"kind": "item", "text": label,
                          "item": it, "price": sell_price(it),
                          "category": cat, "count": n})
    return lines


def _first_item_index(lines: list, after: int = -1) -> int:
    """Return the index of the first non-header row at or after `after+1`."""
    for i in range(after + 1, len(lines)):
        if lines[i]["kind"] == "item":
            return i
    return -1


def _clamp_cursor(lines: list, cursor: int) -> int:
    """Snap the cursor back onto a real item row (skips headers, end-of-list)."""
    if not lines:
        return 0
    cursor = max(0, min(cursor, len(lines) - 1))
    if lines[cursor]["kind"] == "item":
        return cursor
    # Search downward, then upward, for an item row.
    for i in range(cursor + 1, len(lines)):
        if lines[i]["kind"] == "item":
            return i
    for i in range(cursor - 1, -1, -1):
        if lines[i]["kind"] == "item":
            return i
    return cursor


def _move_cursor(lines: list, cursor: int, delta: int) -> int:
    """Step the cursor by `delta`, skipping headers, clamped to bounds."""
    if not lines:
        return 0
    n = len(lines)
    new = cursor + delta
    while 0 <= new < n and lines[new]["kind"] != "item":
        new += delta
    if 0 <= new < n:
        return new
    return cursor  # walked off the end -- stay put


# ---------------------------------------------------------------------------
# Shop screen
# ---------------------------------------------------------------------------

# Local copies of the windows.py palette + font sizes so we don't have to
# expose them. If you ever recolor the panels in windows.py, keep this in
# sync (or import the module-level constants directly).
_PANEL        = ( 22,  18,  28, 220)
_BORDER       = ( 70,  55,  90)
_TEXT         = (220, 215, 200)
_MUTED        = (120, 110, 100)
_GOLD         = (255, 210,  50)
_HIGHLIGHT_BG = ( 55,  45,  75)
_HIGHLIGHT_FG = (120, 180, 255)
_LEVEL_COL    = (160, 130, 255)
_BG           = ( 10,   8,  12)
_GREEN        = ( 80, 210, 100)
_DIM          = ( 80,  75,  70)


def _quit_app():
    """Mirror main.py's quit helper -- WASM-safe shutdown."""
    if sys.platform == "emscripten":
        raise SystemExit
    pygame.quit()
    sys.exit()


async def show_shop(win, player, level: int):
    """Run the between-level shop until the player presses Continue / Esc.

    Owns the event pump for the duration: sets `_ui_blocked = True` so the
    main game loop pauses its own `tick()` / `redraw()`. Restores the prior
    keyboard bindings on exit so the gameplay loop picks up unchanged.
    """
    # -- Setup --------------------------------------------------------------
    win._ui_blocked = True
    saved_keys = dict(win._keys)
    win._keys.clear()

    stock          = generate_shop_inventory(level)
    shop_rows      = _shop_lines(stock)
    player_rows    = _player_lines(player)

    # Active side: "shop" | "player". Cursors live per side.
    side           = "shop" if shop_rows else "player"
    cursors        = {"shop":   _first_item_index(shop_rows),
                      "player": _first_item_index(player_rows)}
    scrolls        = {"shop": 0, "player": 0}
    # Transient feedback line shown beneath the lists ("Bought X for Yg" /
    # "Not enough gold." etc.). Cleared after a couple of seconds.
    feedback       = ["", 0]   # [text, expires_at_ms]

    # -- Helpers --------------------------------------------------------------
    def set_feedback(msg: str, ms: int = 1800):
        feedback[0] = msg
        feedback[1] = pygame.time.get_ticks() + ms

    def current_lines():
        return shop_rows if side == "shop" else player_rows

    def selected_row():
        rows = current_lines()
        c = cursors[side]
        if 0 <= c < len(rows) and rows[c]["kind"] == "item":
            return rows[c]
        return None

    def rebuild_player_rows(prev_cursor: int):
        nonlocal player_rows
        player_rows = _player_lines(player)
        cursors["player"] = _clamp_cursor(player_rows, prev_cursor)

    def rebuild_shop_rows(prev_cursor: int):
        nonlocal shop_rows
        shop_rows = _shop_lines(stock)
        cursors["shop"] = _clamp_cursor(shop_rows, prev_cursor)

    def do_buy():
        row = selected_row()
        if side != "shop" or row is None:
            return
        item = row["item"]
        price = row["price"]
        if player.gold < price:
            set_feedback(f"Not enough gold. (Need {price}g)")
            return
        # Move ownership: deduct gold, drop from stock, add to inventory.
        player.gold -= price
        try:
            stock.remove(item)
        except ValueError:
            # Defensive: shouldn't happen, but if the row's item doesn't
            # match by identity, find one by equality and remove it.
            for s in stock:
                if s == item:
                    stock.remove(s)
                    break
        player.add_to_inventory(item)
        win.set_player_stats(player)
        prev_cur = cursors["shop"]
        rebuild_shop_rows(prev_cur)
        rebuild_player_rows(cursors["player"])
        set_feedback(f"Bought {item.name} for {price}g")

    def do_sell():
        row = selected_row()
        if side != "player" or row is None:
            return
        item = row["item"]
        cat  = row["category"]
        price = row["price"]
        # Remove ONE instance of this item (matched by Item equality, which
        # is stricter than identity -- two freshly-rolled items can compare
        # equal if their stats line up). Inventory.items[cat] is a plain
        # list so list.remove takes the first match.
        bucket = player.inventory.items.get(cat, [])
        try:
            bucket.remove(item)
        except ValueError:
            set_feedback("Couldn't sell that item.")
            return
        player.gold += price
        win.set_player_stats(player)
        prev_cur = cursors["player"]
        rebuild_player_rows(prev_cur)
        set_feedback(f"Sold {item.name} for {price}g")

    def switch_side():
        nonlocal side
        other = "player" if side == "shop" else "shop"
        # Don't switch into an empty side -- nothing to focus.
        if (other == "shop" and not any(r["kind"] == "item" for r in shop_rows)) \
        or (other == "player" and not any(r["kind"] == "item" for r in player_rows)):
            return
        side = other
        cursors[side] = _clamp_cursor(current_lines(), cursors[side])

    def move(delta: int):
        rows = current_lines()
        cursors[side] = _move_cursor(rows, cursors[side], delta)

    # -- Layout ---------------------------------------------------------------
    # All measurements recomputed each frame so resizes Just Work.
    def layout():
        margin = 20
        title_h = 90    # title + gold line + spacing
        bottom_h = 60   # hint + continue button
        col_w = max(220, (win.w - margin * 4) // 3)
        top = title_h
        list_h = win.h - title_h - bottom_h - margin
        shop_x   = margin
        player_x = shop_x + col_w + margin
        info_x   = player_x + col_w + margin
        return {
            "margin":   margin,
            "col_w":    col_w,
            "top":      top,
            "list_h":   list_h,
            "shop_x":   shop_x,
            "player_x": player_x,
            "info_x":   info_x,
            "info_w":   win.w - info_x - margin,
        }

    def draw_panel(side_key: str, x: int, y: int, w: int, h: int,
                   title: str, rows: list,
                   row_rects_out: list, mp):
        # Background + border
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill(_PANEL)
        win.surface.blit(surf, (x, y))
        pygame.draw.rect(win.surface, _BORDER, (x, y, w, h), 1)
        # Title bar
        title_col = _HIGHLIGHT_FG if side == side_key else _LEVEL_COL
        win.txt(title, x + 10, y + 8, "md", title_col)
        pygame.draw.line(win.surface, _BORDER, (x, y + 30), (x + w, y + 30), 1)

        # Visible window of rows (basic vertical clipping; no scrollbar UI
        # in v1 -- keeps the screen uncluttered. The cursor pulls the view
        # along with it via _ensure_visible below.)
        list_top = y + 36
        list_bot = y + h - 6
        row_h    = 20
        visible  = max(1, (list_bot - list_top) // row_h)

        # Adjust scroll so the cursor sits inside the window
        cur = cursors[side_key]
        scr = scrolls[side_key]
        if cur < scr:
            scr = cur
        elif cur >= scr + visible:
            scr = cur - visible + 1
        scr = max(0, min(scr, max(0, len(rows) - visible)))
        scrolls[side_key] = scr

        ry = list_top
        for i in range(scr, min(len(rows), scr + visible)):
            row = rows[i]
            row_rect = pygame.Rect(x + 2, ry - 1, w - 4, row_h - 2)
            row_rects_out.append((row_rect, side_key, i))

            if row["kind"] == "header":
                win.txt(row["text"], x + 10, ry, "sm", _GOLD)
            else:
                # Selected row: full-width highlight stripe + bright text.
                is_sel = (side == side_key and i == cursors[side_key])
                if is_sel:
                    pygame.draw.rect(win.surface, _HIGHLIGHT_BG,
                                     (x + 2, ry - 1, w - 4, row_h - 2))
                # Dim the row if the player can't afford it (shop only).
                fg = _TEXT
                if side_key == "shop" and player.gold < row["price"]:
                    fg = _DIM
                if is_sel and fg is not _DIM:
                    fg = _HIGHLIGHT_FG
                # Item name + price, right-aligned.
                price_str = f"{row['price']}g"
                price_col = _GOLD if side_key == "shop" else _GREEN
                # Reserve room for the price on the right.
                pw, _ = win.font["sm"].size(price_str)
                win.txt(row["text"], x + 10, ry, "sm", fg)
                win.txt(price_str, x + w - pw - 10, ry, "sm",
                        _DIM if fg is _DIM else price_col)
            ry += row_h

    def draw_info_pane(x: int, y: int, w: int, h: int):
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill(_PANEL)
        win.surface.blit(surf, (x, y))
        pygame.draw.rect(win.surface, _BORDER, (x, y, w, h), 1)
        row = selected_row()
        if row is None:
            win.txt("(nothing selected)", x + 10, y + 12, "sm", _MUTED)
            return
        item = row["item"]
        win.txt(item.name, x + 10, y + 8, "md", _LEVEL_COL)
        pygame.draw.line(win.surface, _BORDER, (x, y + 30), (x + w, y + 30), 1)
        # Reuse the inventory panel's renderer for full stat detail.
        info_rows = win._build_item_rows(item, w - 24)
        iy = y + 38
        for r in info_rows:
            if iy > y + h - 18:
                break
            kind = r.get("kind", "text")
            if kind == "divider":
                pygame.draw.line(win.surface, _BORDER,
                                 (x + 8, iy + 6), (x + w - 8, iy + 6), 1)
                iy += 14
                continue
            if kind == "kv":
                kw, _ = win.txt(r["key"] + ": ", x + 10, iy, "sm", _MUTED)
                win.txt(r["val"], x + 10 + kw, iy, "sm", r.get("col", _TEXT))
            else:  # text
                win.txt(r["text"], x + 10, iy, "sm", r.get("col", _TEXT))
            iy += 18

    # The Continue button rect, recomputed each frame in render() and stashed
    # here for the click path.
    cont_rect_holder = [pygame.Rect(0, 0, 0, 0)]

    def render():
        win.surface.fill(_BG)
        L = layout()

        # Title + gold bar
        win.txt(f"SHOP - Level {level}", win.w // 2, 16,
                "lg", _LEVEL_COL, center=True)
        win.txt(f"Gold: {player.gold}", win.w // 2, 50,
                "md", _GOLD, center=True)

        # The two list panels + info pane
        row_rects = []
        draw_panel("shop",   L["shop_x"],   L["top"], L["col_w"], L["list_h"],
                   "SHOP STOCK",   shop_rows,   row_rects, pygame.mouse.get_pos())
        draw_panel("player", L["player_x"], L["top"], L["col_w"], L["list_h"],
                   "YOUR ITEMS",   player_rows, row_rects, pygame.mouse.get_pos())
        draw_info_pane(L["info_x"], L["top"], L["info_w"], L["list_h"])

        # Feedback line (transient)
        if feedback[0] and pygame.time.get_ticks() < feedback[1]:
            win.txt(feedback[0], win.w // 2,
                    L["top"] + L["list_h"] + 8, "sm", _GOLD, center=True)

        # Continue button (right side) + hint (left side)
        hint = ("Tab/A/D switch    W/S nav    Enter buy/sell    "
                "Esc / Continue: leave")
        win.txt(hint, L["margin"], win.h - 22, "sm", _MUTED)

        cb_w, cb_h = 140, 36
        cb_x = win.w - cb_w - L["margin"]
        cb_y = win.h - cb_h - 12
        cont_rect = pygame.Rect(cb_x, cb_y, cb_w, cb_h)
        cont_rect_holder[0] = cont_rect
        hover = cont_rect.collidepoint(pygame.mouse.get_pos())
        col = _HIGHLIGHT_FG if hover else _LEVEL_COL
        pygame.draw.rect(win.surface, col, cont_rect, width=2, border_radius=4)
        win.txt("Continue", cont_rect.centerx, cont_rect.centery - 10,
                "md", col, center=True)

        return row_rects, cont_rect

    # -- Main loop ------------------------------------------------------------
    # `done` flips to True when the player presses Esc / clicks Continue.
    done = False
    try:
        while not done:
            row_rects, cont_rect = render()
            pygame.display.flip()
            win.clock.tick(30)
            await asyncio.sleep(0)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    _quit_app()

                if ev.type == pygame.VIDEORESIZE and sys.platform != "emscripten":
                    win.w, win.h = ev.w, ev.h
                    win._screen = pygame.display.set_mode(
                        (win.w, win.h), pygame.RESIZABLE)
                    win.surface = win._screen

                if ev.type == pygame.MOUSEMOTION:
                    # Hover over a row -> move cursor to it (and switch
                    # active side if the user moved across).
                    for rect, which, idx in row_rects:
                        if rect.collidepoint(ev.pos):
                            rows = shop_rows if which == "shop" else player_rows
                            if 0 <= idx < len(rows) and rows[idx]["kind"] == "item":
                                side = which
                                cursors[side] = idx
                            break

                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if cont_rect.collidepoint(ev.pos):
                        done = True
                        break
                    # Click on a row: select + immediately buy/sell.
                    handled = False
                    for rect, which, idx in row_rects:
                        if rect.collidepoint(ev.pos):
                            rows = shop_rows if which == "shop" else player_rows
                            if 0 <= idx < len(rows) and rows[idx]["kind"] == "item":
                                side = which
                                cursors[side] = idx
                                if side == "shop":
                                    do_buy()
                                else:
                                    do_sell()
                                handled = True
                            break
                    if handled:
                        continue

                if ev.type == pygame.MOUSEWHEEL:
                    # Scroll the panel currently under the mouse, no
                    # cursor movement.
                    mp = pygame.mouse.get_pos()
                    for rect, which, _idx in row_rects:
                        if rect.collidepoint(mp):
                            scrolls[which] = max(0, scrolls[which] - ev.y * 3)
                            break

                if ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        done = True
                        break
                    if ev.key in (pygame.K_TAB,):
                        switch_side()
                    elif ev.key in (pygame.K_a, pygame.K_LEFT):
                        if side != "shop":
                            switch_side()
                    elif ev.key in (pygame.K_d, pygame.K_RIGHT):
                        if side != "player":
                            switch_side()
                    elif ev.key in (pygame.K_w, pygame.K_UP):
                        move(-1)
                    elif ev.key in (pygame.K_s, pygame.K_DOWN):
                        move(1)
                    elif ev.key in (pygame.K_RETURN, pygame.K_e):
                        if side == "shop":
                            do_buy()
                        else:
                            do_sell()
    finally:
        # Restore the previous game-loop bindings so movement / panels work
        # again the moment the shop closes.
        win._keys.update(saved_keys)
        win._ui_blocked = False