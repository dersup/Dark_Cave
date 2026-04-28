# The Dark Cave

A dungeon-crawler roguelite built with **Python + Pygame**. Descend through procedurally generated mazes, battle escalating enemies, loot weapons and armour, cast spells, and try to survive as deep as you can go.

---

## Features

- **Procedural mazes** — every level is carved fresh via a recursive back-tracker algorithm with randomised floor tiles that change as you descend
- **10 dungeon levels** — enemy rosters grow progressively more dangerous; goblins dominate early floors while vampires and dark mages rule the depths
- **Turn-based combat** — attack by walking into enemies; outcome is resolved by an attack roll vs. the target's defence, modified by luck and stats
- **Full elemental system** — 10 damage types (fire, ice, lightning, water, earth, wind, light, dark, poison, physical), each with per-enemy resistances and per-armour resistances
- **Rich item system** — weapons, staffs, throwing weapons, armour, and healing consumables; all with quality tiers, stat bonuses, and elemental modifiers
- **Magic & spells** — equip a staff to unlock spells; cast them with the spell list panel
- **Bombs** — thrown explosives that can destroy walls, opening new paths through the maze
- **Enemy AI** — enemies use BFS pathfinding to hunt the player when you enter their sight radius; they wander randomly otherwise
- **Field of view** — BFS visibility propagates through open walls; visited-but-unseen cells render in a dimmed state
- **Smooth animations** — player and enemy movement is interpolated with an ease-out curve; the camera follows the player
- **Save / Load** — full game state serialised to `saves/savegame.json`; save mid-run and resume any time
- **Character creation** — choose a name, pick a starting weapon class, and spend 25 points across six stats before entering the dungeon
- **Level-up system** — gain EXP from kills; level up to increase your character level

---

## Requirements

- Python 3.10+
- pygame

Install dependencies:

```bash
pip install pygame
```

---

## Running the Game

```bash
python main.py
```

Make sure the `assets/` directory is in the same folder as `main.py`. It should contain floor tile PNGs organised as:

```
assets/
  floors/
    1-3/    ← PNG tiles for levels 1–3
    4-6/
    7/
    8/
    9/
    10/
```

---

## Controls

### Movement & Actions

| Key | Action |
|---|---|
| `W` / `↑` | Move up |
| `S` / `↓` | Move down |
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `Shift + direction` | Turn without moving |
| `E` | Pick up items in the cell you're facing |
| `J` | Inspect the cell you're facing |
| `I` | Open / close inventory |
| `C` | Open / close spell list |

### Inventory & Spell List

| Key | Action |
|---|---|
| `W` / `↑` | Cursor up |
| `S` / `↓` | Cursor down |
| `Enter` / `E` | Use / equip selected item or cast selected spell |
| `I` | Close inventory |
| `C` | Close spell list |

### Save & Load

| Key | Action |
|---|---|
| `F5` | Save game |
| `F9` | Load save (works in-game and from the main menu) |

---

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | Entry point; game loop, input bindings, character creation, start menu |
| `maze.py` | Maze generation (recursive back-tracker), level progression, visibility BFS |
| `drawing.py` | `Cell` and geometry primitives; all rendering and animation logic |
| `entity.py` | `Entity` class — player and enemy stats, combat, movement, AI, inventory management |
| `classes.py` | Data model — `Item`, `Weapon`, `Staff`, `Throwing`, `Armour`, `Healing`, `Magic`, `Inventory`, `Elements` |
| `generator_.py` | Procedural loot and enemy generation (qualities, modifiers, stat scaling) |
| `constants.py` | All game data — enemy stats, weapon/armour tables, spell lists, item modifiers, colour palette, keybindings |
| `save_load.py` | Full serialisation and deserialisation of game state to/from JSON |
| `windows.py` | `Windows` class — pygame surface management, UI panels (HUD, inventory, log, level-up) |

---

## Combat

Walking into an enemy initiates an attack. The hit is resolved as:

1. Roll `1d20`, add the attacker's attack stat and luck modifier
2. Compare against `10 + defender's defence` (or `magic_defence` for spells)
3. On a hit, damage is drawn from the weapon's element list, reduced by the target's elemental resistance
4. Enemies killed drop their entire inventory on the floor

Bombs bypass the normal attack roll and always deal damage, with the added bonus of being able to **destroy walls** if they hit a solid surface.

---

## Enemies by Level

| Enemy | Appears from | Notable traits |
|---|---|---|
| Goblin | Level 1 | Weak, fast, poison-vulnerable |
| Orc | Level 1 | High defence, earth/physical resistant |
| Troll | Level 3 | Fire-weak, high HP |
| Skeleton | Level 4 | Immune to poison, fire/light-weak, dark-resistant |
| Wraith | Level 6 | Immune to physical/poison/dark; light-weak; high mana |
| Dark Mage | Level 6 | Extremely high magic attack; light-weak |
| Vampire | Level 8 | Light-weak (×2), immune to dark/poison; fast; powerful |

Enemies can spawn as **Rare**, **Epic**, or **Legendary** variants with scaled stats, visually indicated by coloured outlines.

---

## Save System

The save file is written to `saves/savegame.json` next to `main.py`. It stores the complete state of the player and maze — walls, enemy positions, inventories, and cell contents — so you can resume exactly where you left off. Delete the file (or use **New Game** from the menu) to start fresh.