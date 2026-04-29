"""
save_load.py  --  Save / Load system for The Dark Cave
======================================================
Save location is platform-dependent (see save_adapter.py):
  - Desktop:  saves/savegame.json
  - Browser:  localStorage key "dark_cave_save" (via pygbag)

    save_game(player, maze)          -> None
    load_game(win)                   -> (player, maze) | (None, None)

Every game object is converted to a plain Python dict
On load, each dict is reconstructed into the
original class by reading the "kind" tag that was written during saving.

The player's location is stored as [row, col] and re-linked on load.
Enemies' locations are re-linked the same way.
"""

from __future__ import annotations

import json
from typing import Any

from classes import Elements, Item, Healing, Weapon, Staff, Throwing, Armour, Magic, Inventory
from entity import Entity
from save_adapter import read_save, write_save, delete_save_file, save_exists_now


# ===========================================================================
#  Low-level serialisers
# ===========================================================================

def _ser_element(e: Elements) -> dict:
    return {"type": e.type, "damage": e.damage}

def _ser_elements(lst: list) -> list:
    return [_ser_element(e) for e in lst]


def _ser_magic(m: Magic) -> dict:
    return {
        "kind":             "magic",
        "name":             m.name,
        "elements":         _ser_elements(m.elements),
        "spell_description": m.spell_description,
        "cost":             m.cost,
        "distance":         m.distance,
    }


def _ser_item(item) -> dict | None:
    # Serialise any item subclass to a tagged dict.
    if item is None:
        return None

    if isinstance(item, Throwing):
        return {
            "kind":        "throwing",
            "name":        item.name,
            "gold":        item.value,
            "attack":      item.attack,
            "elements":    _ser_elements(item.elements),
            "distance":    item.distance,
            "description": getattr(item, "_description", item.description),
        }
    if isinstance(item, Staff):
        return {
            "kind":        "staff",
            "name":        item.name,
            "gold":        item.value,
            "attack":      item.attack,
            "elements":    _ser_elements(item.elements),
            "stat_bonuses": item.stat_bonuses,
            "description": getattr(item, "_description", item.description),
            "spells":      [_ser_magic(m) for m in item.spells.values()],
        }
    if isinstance(item, Weapon):
        return {
            "kind":        "weapon",
            "name":        item.name,
            "gold":        item.value,
            "attack":      item.attack,
            "elements":    _ser_elements(item.elements),
            "stat_bonuses": item.stat_bonuses,
            "description": getattr(item, "_description", item.description),
        }
    if isinstance(item, Armour):
        return {
            "kind":        "armour",
            "name":        item.name,
            "gold":        item.value,
            "resistances": item.resistances,
            "stat_bonuses": item.stat_bonuses,
            "description": getattr(item, "_description", item.description),
        }
    if isinstance(item, Healing):
        return {
            "kind":    "healing",
            "name":    item.name,
            "gold":    item.value,
            "healing": _ser_elements(item.healing),
        }
    # Generic fallback (shouldn't happen in normal play)
    return {"kind": "item", "name": item.name, "gold": item.value,
            "description": getattr(item, "description", "")}


def _ser_inventory(inv: Inventory) -> dict:
    out = {}
    for category, items in inv.items.items():
        out[category] = [_ser_item(i) for i in items]
    return out


def _ser_entity_base(ent: Entity) -> dict:
    #Serialise the fields shared by player and enemies.
    return {
        "name":        ent.name,
        "max_health":  ent.max_health,
        "health":      ent.health,
        "max_mana":    ent.max_mana,
        "mana":        ent.mana,
        "stats":       dict(ent.stats),
        "resistances": dict(ent.resistances),
        "level":       ent.level,
        "gold":        ent.gold,
        "kills":       ent.kills,
        "facing":      ent.facing,
        "inventory":   _ser_inventory(ent.inventory),
        # weapon / armor names let us re-link equipped items on load
        "weapon_name": ent.weapon.name if ent.weapon else None,
        "armor_name":  ent.armor.name  if ent.armor  else None,
    }


# ===========================================================================
#  Low-level deserialisers
# ===========================================================================

def _de_element(d: dict) -> Elements:
    return Elements(d["type"], d["damage"])

def _de_elements(lst: list) -> list:
    return [_de_element(e) for e in lst]


def _de_magic(d: dict) -> Magic:
    return Magic(
        name             = d["name"],
        elements         = _de_elements(d["elements"]),
        spell_description= d["spell_description"],
        cost             = d["cost"],
        distance         = d["distance"],
    )


def _de_item(d: dict | None):
    """Reconstruct an item from its serialised dict."""
    if d is None:
        return None
    kind = d.get("kind", "item")

    if kind == "throwing":
        t = Throwing(
            in_name  = d["name"],
            distance = d["distance"],
            gold     = d["gold"],
            elements = _de_elements(d["elements"]),
            attack   = d.get("attack", 0),
            description = d.get("description", ""),
        )
        return t

    if kind == "staff":
        spells_list = [_de_magic(m) for m in d.get("spells", [])]
        spells_dict = {m.name.lower(): m for m in spells_list}
        s = Staff(
            in_name     = d["name"],
            gold        = d["gold"],
            attack      = d.get("attack", -1),
            elements    = _de_elements(d["elements"]),
            spells      = spells_dict,
            description = d.get("description", ""),
        )
        s.stat_bonuses = d.get("stat_bonuses", s.stat_bonuses)
        s.description  = f"({s.elements})({s.stat_bonuses}) ({s._description})"
        return s

    if kind == "weapon":
        w = Weapon(
            in_name     = d["name"],
            gold        = d["gold"],
            attack      = d.get("attack", -1),
            elements    = _de_elements(d["elements"]),
            description = d.get("description", ""),
        )
        w.stat_bonuses = d.get("stat_bonuses", w.stat_bonuses)
        w.description  = f"({w.elements})({w.stat_bonuses}) ({w._description})"
        return w

    if kind == "armour":
        a = Armour(in_name=d["name"], gold=d["gold"],
                   description=d.get("description", ""))
        a.resistances  = d.get("resistances",  a.resistances)
        a.stat_bonuses = d.get("stat_bonuses", a.stat_bonuses)
        # Rebuild the formatted description now that resistances/stat_bonuses are restored
        a.description  = f"({a.resistances}) ({a.stat_bonuses}) ({a._description})"
        return a

    if kind == "healing":
        return Healing(
            in_name = d["name"],
            healing = _de_elements(d["healing"]),
            gold    = d["gold"],
        )

    # Generic Item fallback
    return Item(d["name"], d.get("gold", 0), d.get("description", ""))


def _de_inventory(d: dict) -> Inventory:
    inv = Inventory()
    for category, items in d.items():
        inv.items[category] = [_de_item(i) for i in items]
    return inv


def _relink_equipped(ent: Entity, weapon_name: str | None, armor_name: str | None):
    if weapon_name:
        for item in ent.inventory.items["Equipped"]:
            if isinstance(item, Weapon) and item.name == weapon_name:
                ent.weapon = item
                break
        else:
            # Equipped list might be in Weapons too (bare load)
            for item in ent.inventory.items["Weapons"]:
                if isinstance(item, Weapon) and item.name == weapon_name:
                    ent.weapon = item
                    break

    if armor_name:
        for item in ent.inventory.items["Equipped"]:
            if isinstance(item, Armour) and item.name == armor_name:
                ent.armor = item
                break
        else:
            for item in ent.inventory.items["Armors"]:
                if isinstance(item, Armour) and item.name == armor_name:
                    ent.armor = item
                    break


# ===========================================================================
#  Player serialise / deserialise
# ===========================================================================

def _ser_player(player: Entity) -> dict:
    d = _ser_entity_base(player)
    d["is_player"]   = True
    d["location_rc"] = player.location.location if player.location else None
    return d


def _de_player(d: dict) -> Entity:
#   Reconstruct a player Entity.
    p = Entity.__new__(Entity)
    p.name        = d["name"]
    p.max_health  = d["max_health"]
    p.health      = d["health"]
    p.max_mana    = d["max_mana"]
    p.mana        = d["mana"]
    p.stats       = d["stats"]
    p.resistances = d["resistances"]
    p.level       = d["level"]
    p.gold        = d["gold"]
    p.kills       = d["kills"]
    p.facing      = d.get("facing", "down")
    p.is_player   = True
    p.id_         = None
    p.location    = None          # linked later
    p.weapon      = None
    p.armor       = None
    p.inventory   = _de_inventory(d["inventory"])
    _relink_equipped(p, d.get("weapon_name"), d.get("armor_name"))
    return p


# ===========================================================================
#  Enemy serialise / deserialise
# ===========================================================================

def _ser_enemy(ent: Entity, row: int, col: int) -> dict:
    d = _ser_entity_base(ent)
    d["location_rc"] = [row, col]
    return d


def _de_enemy(d: dict) -> Entity:
    # Reconstruct an enemy Entity (same pattern as player).
    e = Entity.__new__(Entity)
    e.name        = d["name"]
    e.max_health  = d["max_health"]
    e.health      = d["health"]
    e.max_mana    = d["max_mana"]
    e.mana        = d["mana"]
    e.stats       = d["stats"]
    e.resistances = d["resistances"]
    e.level       = d["level"]
    e.gold        = d["gold"]
    e.kills       = d["kills"]
    e.facing      = d.get("facing")
    e.is_player   = False
    e.id_         = None
    e.location    = None
    e.weapon      = None
    e.armor       = None
    e.inventory   = _de_inventory(d["inventory"])
    _relink_equipped(e, d.get("weapon_name"), d.get("armor_name"))
    return e


# ===========================================================================
#  Maze serialise / deserialise
# ===========================================================================

def _ser_maze(maze) -> dict:
    # Serialise the maze's structural data (walls, entities, items).
    cells_data = []
    enemies    = []

    for row in maze.cells:
        row_data = []
        for cell in row:
            r, c = cell.location
            cell_d: dict[str, Any] = {
                "top":    cell.top,
                "bottom": cell.bottom,
                "left":   cell.left,
                "right":  cell.right,
                "ent":    cell.ent,
                "exit":   cell.exit,
                "gold":   cell.gold,
                "inventory": _ser_inventory(cell.inventory),
                "visited": cell.visited,
                "floor": cell.floor_type,
            }
            row_data.append(cell_d)

            if cell.enemy_entity:
                enemies.append(_ser_enemy(cell.enemy_entity, r, c))

        cells_data.append(row_data)

    return {
        "num_rows":  maze.num_rows,
        "num_cols":  maze.num_cols,
        "level":     maze.level,
        "cells":     cells_data,
        "enemies":   enemies,
    }


def _de_maze_into(maze, maze_data: dict):
    #Overwrite maze.cells walls / entities / items from saved data.
    #The cells must already exist (call maze.create_maze() first).
    cells_data = maze_data["cells"]
    for r, row_data in enumerate(cells_data):
        for c, cd in enumerate(row_data):
            cell = maze.cells[r][c]
            cell.top    = cd["top"]
            cell.bottom = cd["bottom"]
            cell.left   = cd["left"]
            cell.right  = cd["right"]
            cell.ent    = cd.get("ent",  False)
            cell.exit   = cd.get("exit", False)
            cell.gold   = cd.get("gold", 0)
            cell.inventory = _de_inventory(cd["inventory"])
            cell.visited = cd.get("visited", False)
            cell.floor_type = cd.get("floor", "")
            if cell.floor_type:
                maze._load_tile(cell,cell.floor_type)

    # Re-place enemies
    for edata in maze_data.get("enemies", []):
        r, c = edata["location_rc"]
        enemy = _de_enemy(edata)
        cell  = maze.cells[r][c]
        enemy.location = cell
        cell.set_enemy(enemy)



def save_game(player, maze) -> str:
    data = {"player": _ser_player(player), "maze": _ser_maze(maze)}
    write_save(json.dumps(data, indent=2))
    return "Game saved."

def load_game(win) -> tuple:
    text = read_save()
    if not text:
        return None, None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        win.log("Save file is corrupt.")
        return None, None
    player = _de_player(data["player"])
    player_rc = data["player"].get("location_rc")
    from maze import Maze
    maze_data = data["maze"]
    maze = Maze(maze_data["num_rows"], maze_data["num_cols"], win)
    maze.level = maze_data["level"]
    win.set_level(maze.level)
    maze.create_maze()
    _de_maze_into(maze, maze_data)
    if player_rc:
        r, c = player_rc
        cell = maze.cells[r][c]
        cell.set_player(player)
        player.location = cell
    else:
        maze.player_init(player)
    return player, maze

def delete_save() -> bool:
    return delete_save_file()

def save_exists() -> bool:
    return save_exists_now()