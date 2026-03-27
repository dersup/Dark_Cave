# The Dark Cave

A top-down roguelite dungeon crawler with Diablo-style procedural loot, built in Python using Tkinter.

Descend through an ever-deepening cave system, fight escalating monsters, and collect randomized gear — but death means starting over. How deep can you go?

---

## Features

**Procedurally Generated Mazes**
Each floor is a unique maze carved by a recursive backtracker algorithm. Entrances and exits are placed randomly on the borders, so no two runs play the same.

**Diablo-Style Loot System**
Weapons and armour are procedurally assembled from a base type, a quality tier, a rarity tier, and elemental modifiers:
- Quality tiers range from *broken* and *crude* up to *masterwork*, affecting damage multipliers and gold value.
- Rarity tiers (rare, epic, legendary) add elemental enchantments and stat bonuses.
- Single and dual-element weapon enchantments: *of Fire*, *of the Tempest*, *of Hellfire*, and more.
- Armour enchantments add elemental resistances: *of Flame Warding*, *of the Exorcist*, *of the Sanctified*, and more.

**Elemental Damage & Resistance**
10 elements are modelled throughout combat: fire, ice, lightning, water, earth, wind, light, dark, poison, and physical. Every enemy has unique resistances and vulnerabilities — skeletons laugh at poison but crumble to fire and light; wraiths are immune to dark but shatter against holy light.

**Enemy Roster with Weighted Spawning**
7 enemy types are in the game, each with distinct stats, resistances, and loot preferences. Enemy spawn weights shift by dungeon level — goblins dominate early floors, while vampires and dark mages rule the depths.

| Enemy | Notable Traits |
|---|---|
| Goblin | Weak, fast, poison-vulnerable, loves bombs |
| Orc | Tanky, earth- and physical-resistant |
| Skeleton | High defence, immune to poison, fire/light weakness |
| Troll | High HP, fire-weak, regenerative feel |
| Wraith | Low HP, high magic stats, immune to dark and poison |
| Dark Mage | Glass cannon, light-weak, dark-resistant |
| Vampire | Balanced threat, immune to dark/poison, light-weak |

Rare, epic, and legendary variants of each enemy spawn with bonus stats, bonus loot rolls, and coloured outlines on the map.

**Fog of War & Visibility**
The map is hidden until explored. A radius-2 BFS visibility system reveals cells through open walls in real time as you move. Previously visited cells are shown in grey.

**Turn-Based Combat**
Movement and attacks are interleaved: you act, then every visible enemy takes its turn. Enemies adjacent to you through an open wall will attack; others wander randomly. Attack rolls use a D20 system modified by your luck stat, compared against the enemy's armour class.

**Roguelite Progression**
- Levelling up grants 3 stat points to allocate across attack, defence, luck, magic defence, magic attack, and agility.
- Each new dungeon floor increases in difficulty, with more and tougher enemies.
- Death ends the run. Your score is `gold × dungeon level`.

**Inventory & Item Management**
The inventory is split into Equipped, Weapons, Armours, and Consumables. Open it mid-game, navigate with the keyboard, and use items directly from the menu. Consumables include healing potions and throwable bombs.

---

## Requirements

- Python 3.10+
- Tkinter (included in most Python distributions)

No third-party packages are required.

---

## Installation

```bash
git clone https://github.com/dersup/Dark_Cave.git
cd Dark-Cave
python main.py
```

---

## How to Play

### Character Creation
On startup you will be prompted to:
1. Choose your hero's gender (used for name generation if you skip naming).
2. Enter a name, or press Enter to generate one randomly.
3. Pick a starting weapon from the available options.
4. Allocate 25 stat points across your six ability scores.

### Controls

| Key | Action |
|---|---|
| `W` / `↑` | Move up |
| `S` / `↓` | Move down |
| `A` / `←` | Move left |
| `D` / `→` | Move right |
| `Shift + W/A/S/D` or `Shift + Arrow` | Turn to face a direction without moving |
| `E` | Pick up items from the cell ahead |
| `I` | Toggle inventory |
| `J` | Inspect the cell ahead |
| `↑` / `↓` or `W` / `S` (in inventory) | Navigate items |
| `Enter` / `E` (in inventory) | Use selected item |

### Combat
Walking into an enemy attacks them. Enemies attack you back on their turn. Use the turn keys to face a direction and throw bombs down a corridor without stepping into danger.

### Loot
Killed enemies drop their equipped weapon, armour, and any consumables they carried into the cell. Walk over the cell and press `E` to pick everything up. Items in a cell are shown as a gold dot on the map.

### Exiting a Floor
Find the exit wall (the open gap on the far side of the maze) and walk through it to descend to the next floor. You keep all your gear between floors.

---

## Project Structure

| File | Purpose |
|---|---|
| `main.py` | Entry point, game loop, input bindings |
| `maze.py` | Maze generation, visibility, monster spawning, floor transitions |
| `drawing.py` | Cell rendering, animation, wall drawing |
| `entity.py` | Player and enemy logic, combat, inventory management |
| `generator_.py` | Procedural loot and enemy generation |
| `classes.py` | Core data classes: Item, Weapon, Armour, Healing, Throwing, Inventory, Elements |
| `windows.py` | Tkinter window, UI labels, inventory display, game over screen |
| `constants.py` | All game data: enemy stats, loot tables, item modifiers, spawn weights |

---

## Scoring

Your final score on death is:

```
Score = (Gold Collected + Kills) * Maze Depth
```

