"""
sprites.py — Sprite-sheet animation system.

Frame layout (per every `_AnimationInfo.txt` in the asset pack):
  • Every frame is 32×32 px.
  • Rows encode facing direction:
      - Row 0 (1st row, odd):  right-facing
      - Row 1 (2nd row, even): left-facing
      - Row 2 (3rd row, odd):  right-facing (variant pose)
      - Row 3 (4th row, even): left-facing  (variant pose)
  • Columns encode animation frames (played left-to-right).

Sheets with only 1 row (height == 32) have no left-facing variant —
those frames are flipped horizontally when the entity faces left.

Each AnimSprite:
  • loads the correct PNG strip from assets/
  • knows frame counts & durations per animation state
  • advances frames based on wall-clock time
  • exposes .get_frame() -> pygame.Surface (32×32)
  • responds to .set_facing("left"|"right"|"up"|"down")

Supported states:  idle | walk | attack | charged_attack | dmg | die | jump | fly
Missing states fall back gracefully to "idle".

Frame timings (from each `_AnimationInfo.txt`):
  - FAST (100 ms): attack / charged_attack / jump / fly / die / dmg
  - SLOW (200 ms): idle / walk
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Optional

import pygame

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRAME_FAST_MS = 100   # attack / jump / die / dmg
FRAME_SLOW_MS = 200   # idle / walk

FRAME_SIZE = 32       # native frame size per AnimationInfo.txt — all frames are 32×32
CELL_SIZE  = 32       # target render size (matches Maze.CELL_SIZE)

# ---------------------------------------------------------------------------
# Sprite-sheet database
#
# Tuple shape: (path, n_frames, ms)
#   path     — PNG sheet relative to project root
#   n_frames — number of animation frames (columns) at 32 px each
#   ms       — duration per frame (100 or 200, from each _AnimationInfo.txt)
#
# Row layout within a sheet (asset convention):
#   row 0 = right-facing
#   row 1 = left-facing
#   row 2+ = pose variants (unused by default)
# Single-row sheets (height == 32) are horizontally flipped for left-facing.
# ---------------------------------------------------------------------------


def _humanoid_sheets(base_dir: str, prefix: str,
                     attack_key="Attack", die_key="SpinDie",
                     idle_frames=16, walk_frames=4, attack_frames=4,
                     charged_frames=6, dmg_frames=4, die_frames=12,
                     jump_frames=4, has_charged=True, has_jump=True) -> dict:
    """State-dict for a standard humanoid sprite set (4 rows: right/left pairs)."""
    d = {
        "idle":   (f"{base_dir}/{prefix}Idle.png",          idle_frames,    FRAME_SLOW_MS),
        "walk":   (f"{base_dir}/{prefix}Walk.png",          walk_frames,    FRAME_SLOW_MS),
        "attack": (f"{base_dir}/{prefix}{attack_key}.png",  attack_frames,  FRAME_FAST_MS),
        "dmg":    (f"{base_dir}/{prefix}Dmg.png",           dmg_frames,     FRAME_FAST_MS),
        "die":    (f"{base_dir}/{prefix}{die_key}.png",     die_frames,     FRAME_FAST_MS),
    }
    if has_charged:
        d["charged_attack"] = (f"{base_dir}/{prefix}ChargedAttack.png", charged_frames, FRAME_FAST_MS)
    if has_jump:
        d["jump"] = (f"{base_dir}/{prefix}Jump.png", jump_frames, FRAME_FAST_MS)
    return d


def _monster_sheets(base_dir: str, prefix: str,
                    idle_frames=16, walk_frames=6, attack_frames=4,
                    dmg_frames=4, die_frames=14, jump_frames=6) -> dict:
    """State-dict for a large-frame monster sprite set (Troll/Cyclop/Yeti style)."""
    return {
        "idle":   (f"{base_dir}/{prefix}Idle.png",   idle_frames,   FRAME_SLOW_MS),
        "walk":   (f"{base_dir}/{prefix}Walk.png",   walk_frames,   FRAME_SLOW_MS),
        "attack": (f"{base_dir}/{prefix}Attack.png", attack_frames, FRAME_FAST_MS),
        "dmg":    (f"{base_dir}/{prefix}Dmg.png",    dmg_frames,    FRAME_FAST_MS),
        "die":    (f"{base_dir}/{prefix}Die.png",    die_frames,    FRAME_FAST_MS),
        "jump":   (f"{base_dir}/{prefix}Jump.png",   jump_frames,   FRAME_FAST_MS),
    }


def _slime_sheets(base_dir: str, prefix: str,
                  idle_frames=8, jump_frames=4, dmg_frames=4, die_frames=9) -> dict:
    return {
        "idle":   (f"{base_dir}/{prefix}Idle.png",        idle_frames, FRAME_SLOW_MS),
        "walk":   (f"{base_dir}/{prefix}Idle.png",        idle_frames, FRAME_SLOW_MS),  # no dedicated Walk
        "attack": (f"{base_dir}/{prefix}JumpAttack.png",  jump_frames, FRAME_FAST_MS),
        "jump":   (f"{base_dir}/{prefix}JumpAttack.png",  jump_frames, FRAME_FAST_MS),
        "dmg":    (f"{base_dir}/{prefix}Dmg.png",         dmg_frames,  FRAME_FAST_MS),
        "die":    (f"{base_dir}/{prefix}Die.png",         die_frames,  FRAME_FAST_MS),
    }


# ── Asset base paths ─────────────────────────────────────────────────────────
_BH = "assets/Base_Humanoids"
_MO = "assets/Monsters"
_UN = "assets/Undead"
_SL = "assets/Slimes"

MOB_SPRITE_DB: dict[str, dict[str, tuple]] = {

    # ── Player (Base Human) ───────────────────────────────────────────────────
    "player": _humanoid_sheets(f"{_BH}/Human/Base_Human", "Human",
                               die_key="SpinDie", die_frames=12),

    # ── Goblin ────────────────────────────────────────────────────────────────
    "goblin": _humanoid_sheets(f"{_BH}/Goblin", "Goblin",
                               attack_key="Attack", die_key="SpinDie", die_frames=12),

    # ── Orc (Base) ────────────────────────────────────────────────────────────
    "orc": _humanoid_sheets(f"{_BH}/Orc/Base_Orc", "Orc",
                            attack_key="BaseAttack", die_key="Die", die_frames=12),

    # ── Wild Orc ──────────────────────────────────────────────────────────────
    "wild orc": _humanoid_sheets(f"{_BH}/Orc/Wild Orc", "WildOrc",
                                 attack_key="Attack", die_key="Die", die_frames=12),

    # ── Vampire (Base Elf sheets, as specified) ──────────────────────────────
    "vampire": _humanoid_sheets(f"{_BH}/Elf", "Elf",
                                attack_key="Attack", die_key="SpinDie", die_frames=12),

    # ── Dwarf ─────────────────────────────────────────────────────────────────
    "dwarf": _humanoid_sheets(f"{_BH}/Dwarf/Base_Dwarf", "Dwarf",
                              die_key="SpinDie", die_frames=11),

    # ── Halfling ──────────────────────────────────────────────────────────────
    "halfling": _humanoid_sheets(f"{_BH}/Halfling", "Halfling",
                                 die_key="SpinDie", die_frames=12),

    # ── Skeleton ─────────────────────────────────────────────────────────────
    "skeleton": {
        "idle":   (f"{_UN}/Skeleton/SkeletonIdle.png",   5,  FRAME_SLOW_MS),
        "walk":   (f"{_UN}/Skeleton/SkeletonWalk.png",   2,  FRAME_SLOW_MS),
        "attack": (f"{_UN}/Skeleton/SkeletonAttack.png", 5,  FRAME_FAST_MS),
        "dmg":    (f"{_UN}/Skeleton/SkeletonDmg.png",    4,  FRAME_FAST_MS),
        "die":    (f"{_UN}/Skeleton/SkeletonDie.png",    9,  FRAME_FAST_MS),
    },

    # ── Zombie ───────────────────────────────────────────────────────────────
    "zombie": {
        "idle":   (f"{_UN}/Zombie/ZombieIdle.png",   19, FRAME_SLOW_MS),
        "walk":   (f"{_UN}/Zombie/ZombieWalk.png",    4, FRAME_SLOW_MS),
        "attack": (f"{_UN}/Zombie/ZombieAttack.png",  5, FRAME_FAST_MS),
        "dmg":    (f"{_UN}/Zombie/ZombieDmg.png",     4, FRAME_FAST_MS),
        "die":    (f"{_UN}/Zombie/ZombieDie.png",    11, FRAME_FAST_MS),
    },

    # ── Wraith (Wildfire ghost spirit) ──────────────────────────────────────
    "wraith": {
        "idle":   (f"{_UN}/Wildfire/WildfireIdle.png", 4, FRAME_SLOW_MS),
        "walk":   (f"{_UN}/Wildfire/WildfireFly.png",  4, FRAME_SLOW_MS),
        "attack": (f"{_UN}/Wildfire/WildfireFly.png",  4, FRAME_FAST_MS),
        "dmg":    (f"{_UN}/Wildfire/WildfireDmg.png",  4, FRAME_FAST_MS),
        "die":    (f"{_UN}/Wildfire/WildfireDie.png", 12, FRAME_FAST_MS),
    },

    # ── Troll ────────────────────────────────────────────────────────────────
    "troll": _monster_sheets(f"{_MO}/Troll", "Troll",
                             idle_frames=16, walk_frames=6,
                             attack_frames=4, dmg_frames=4,
                             die_frames=14, jump_frames=6),

    # ── Cyclops ──────────────────────────────────────────────────────────────
    "cyclops": _monster_sheets(f"{_MO}/Cyclop", "Cyclop",
                               idle_frames=16, walk_frames=6,
                               attack_frames=4, dmg_frames=4,
                               die_frames=14, jump_frames=6),

    # ── Minotaur ─────────────────────────────────────────────────────────────
    "minotaur": _monster_sheets(f"{_MO}/Minotaur", "Minotaur",
                                idle_frames=16, walk_frames=6,
                                attack_frames=8, dmg_frames=4,
                                die_frames=16, jump_frames=6),

    # ── Centaur ──────────────────────────────────────────────────────────────
    "centaur": _monster_sheets(f"{_MO}/Centaur", "Centaur",
                               idle_frames=16, walk_frames=4,
                               attack_frames=4, dmg_frames=4,
                               die_frames=12, jump_frames=4),

    # ── Yeti ─────────────────────────────────────────────────────────────────
    "yeti": _monster_sheets(f"{_MO}/Yeti", "Yeti",
                            idle_frames=16, walk_frames=6,
                            attack_frames=4, dmg_frames=4,
                            die_frames=14, jump_frames=6),

    # ── Pumpkin Horror ───────────────────────────────────────────────────────
    "pumpkin horror": {
        "idle":   (f"{_MO}/Pumpkin_Horror/PumpkinHorrorBaseIdleActivation.png", 5,  FRAME_SLOW_MS),
        "walk":   (f"{_MO}/Pumpkin_Horror/PumpkinHorrorBaseWalk.png",           2,  FRAME_SLOW_MS),
        "attack": (f"{_MO}/Pumpkin_Horror/PumpkinHorrorBaseAttack.png",         5,  FRAME_FAST_MS),
        "dmg":    (f"{_MO}/Pumpkin_Horror/PumpkinHorrorBaseDmg.png",            4,  FRAME_FAST_MS),
        "die":    (f"{_MO}/Pumpkin_Horror/PumpkinHorrorBaseDie.png",           12,  FRAME_FAST_MS),
    },

    # ── Trasgo (Dark Mage / Imp-like caster) ─────────────────────────────────
    "dark mage": _humanoid_sheets(f"{_MO}/Trasgo", "Trasgo",
                                  attack_key="Attack", die_key="SpinDie", die_frames=11),

    # ── Slimes ───────────────────────────────────────────────────────────────
    "green slime": _slime_sheets(f"{_SL}/Green_Slime", "SlimeGreen",
                                 idle_frames=8, jump_frames=4, dmg_frames=4, die_frames=9),

    "blue slime":  _slime_sheets(f"{_SL}/Blue_Slime", "BlueSlime",
                                 idle_frames=8, jump_frames=4, dmg_frames=4, die_frames=9),

    "mother slime green": _slime_sheets(f"{_SL}/Green_Mother_Slime", "MotherSlimeGreen",
                                        idle_frames=8, jump_frames=4, dmg_frames=4, die_frames=11),

    "mother slime blue":  _slime_sheets(f"{_SL}/Blue_Mother_Slime", "BlueMotherSlime",
                                        idle_frames=8, jump_frames=4, dmg_frames=4, die_frames=11),
}

# ---------------------------------------------------------------------------
# Facing → row index mapping
#
# Sheets may have 1, 2, 3, or 4 rows.
# Per asset convention:
#   row 0 = right-facing
#   row 1 = left-facing
#   row 2 = right-facing (variant)
#   row 3 = left-facing  (variant)
# If a sheet has only one row, that row is right-facing and we horizontally
# flip for left-facing.
# ---------------------------------------------------------------------------

def _row_for_facing(facing: str, n_rows: int) -> tuple[int, bool]:
    """
    Given a facing direction and the number of rows in a sheet, return:
      (row_index, flip_horizontally)
    """
    face_left = (facing == "left")

    if n_rows <= 1:
        return 0, face_left
    # Two or more rows: row 0 = right, row 1 = left.
    return (1 if face_left else 0), False


# ---------------------------------------------------------------------------
# AnimSprite
# ---------------------------------------------------------------------------

class AnimSprite:
    """
    Animated sprite for a single entity.

    Usage:
        sprite = AnimSprite("goblin")
        sprite.set_facing("right")
        sprite.set_state("walk")
        frame_surf = sprite.get_frame()   # call once per render tick
    """

    # Cache keyed by (path, row, flip) -> list[pygame.Surface]
    _sheet_cache: dict[tuple, list[pygame.Surface]] = {}
    _row_count_cache: dict[str, int] = {}

    def __init__(self, mob_key: str, cell_size: int = CELL_SIZE):
        key = mob_key.lower()
        # Fallback: if exact key not found, try substring match
        if key not in MOB_SPRITE_DB:
            for k in MOB_SPRITE_DB:
                if k in key or key in k:
                    key = k
                    break
            else:
                key = "goblin"

        self._db        = MOB_SPRITE_DB[key]
        self._cell_size = cell_size
        self._state     = "idle"
        self._facing    = "right"
        self._frame_idx = 0
        self._last_tick = time.time()
        self._one_shot  = False
        self._done      = False

    # ── State management ─────────────────────────────────────────────────────

    def set_state(self, state: str, one_shot: bool = False):
        """
        Switch animation state.

        one_shot=True: play once, then freeze on last frame (e.g. die/attack).
        """
        if state not in self._db:
            return
        if self._state == state and not self._done:
            return
        self._state     = state
        self._frame_idx = 0
        self._last_tick = time.time()
        self._one_shot  = one_shot
        self._done      = False

    def set_facing(self, facing: str):
        """Update the sprite's facing. Accepts 'up'|'down'|'left'|'right'."""
        if facing and facing != self._facing:
            self._facing = facing

    def is_done(self) -> bool:
        return self._done

    # ── Frame retrieval ──────────────────────────────────────────────────────

    def get_frame(self) -> Optional[pygame.Surface]:
        """Return current frame surface, advancing the animation timer."""
        frames = self._get_frames(self._state, self._facing)
        if not frames:
            return None

        entry = self._db[self._state]
        n_frames = entry[1]
        ms       = entry[2]
        now = time.time()
        elapsed_ms = (now - self._last_tick) * 1000

        if elapsed_ms >= ms:
            advance = int(elapsed_ms // ms)
            self._last_tick = now

            if self._one_shot:
                next_idx = self._frame_idx + advance
                if next_idx >= n_frames:
                    self._frame_idx = n_frames - 1
                    self._done = True
                else:
                    self._frame_idx = next_idx
            else:
                self._frame_idx = (self._frame_idx + advance) % n_frames

        idx = min(self._frame_idx, len(frames) - 1)
        return frames[idx]

    # ── Internal helpers ─────────────────────────────────────────────────────

    def _get_frames(self, state: str, facing: str) -> list[pygame.Surface]:
        """
        Extract 32×32 frames from the current sheet, one row for the chosen facing.

        Row selection per asset convention:
          row 0 = right-facing
          row 1 = left-facing
          rows 2+ = unused (pose variants)
        Single-row sheets use horizontal flipping for left-facing.
        """
        if state not in self._db:
            state = "idle"
        entry = self._db[state]
        path_rel = entry[0]
        n_frames = entry[1]

        path = Path(path_rel)
        if not path.exists():
            return []

        n_rows = self._get_row_count(path_rel)
        row_idx, flip = _row_for_facing(facing, n_rows)

        cache_key = (path_rel, row_idx, flip, self._cell_size)
        if cache_key in AnimSprite._sheet_cache:
            return AnimSprite._sheet_cache[cache_key]

        sheet = pygame.image.load(str(path)).convert_alpha()
        w, h = sheet.get_size()
        actual_frames = min(n_frames, w // FRAME_SIZE)
        y = row_idx * FRAME_SIZE
        if y + FRAME_SIZE > h:
            y = 0

        frames: list[pygame.Surface] = []
        for i in range(actual_frames):
            rect = pygame.Rect(i * FRAME_SIZE, y, FRAME_SIZE, FRAME_SIZE)
            sub  = sheet.subsurface(rect).copy()
            if flip:
                sub = pygame.transform.flip(sub, True, False)
            sub = pygame.transform.scale(sub, (self._cell_size*2, self._cell_size*2))
            frames.append(sub)

        AnimSprite._sheet_cache[cache_key] = frames
        return frames

    @classmethod
    def _get_row_count(cls, path_rel: str) -> int:
        """How many 32-pixel rows fit in the sheet at path_rel."""
        if path_rel in cls._row_count_cache:
            return cls._row_count_cache[path_rel]
        path = Path(path_rel)
        if not path.exists():
            cls._row_count_cache[path_rel] = 1
            return 1
        sheet = pygame.image.load(str(path)).convert_alpha()
        _, h = sheet.get_size()
        rows = max(1, h // FRAME_SIZE)
        cls._row_count_cache[path_rel] = rows
        return rows


# ---------------------------------------------------------------------------
# Convenience factory
# ---------------------------------------------------------------------------

def make_sprite(mob_key: str) -> AnimSprite:
    """Return a fresh AnimSprite for the given mob key (case-insensitive)."""
    return AnimSprite(mob_key.lower())

async def preload_sprites():
    """Load all sprite sheets up-front AND pre-slice frame lists into
    AnimSprite._sheet_cache so the first render of each mob doesn't stall.

    Yields between sheets so the browser frame pump can run during loading.
    """
    import asyncio
    seen_paths = set()
    # Preload at the same render size that _get_frames uses (CELL_SIZE*2).
    render_size = CELL_SIZE * 2

    for mob_key, states in MOB_SPRITE_DB.items():
        for state, (path_rel, n_frames, _ms) in states.items():
            if path_rel in seen_paths:
                continue
            seen_paths.add(path_rel)
            p = Path(path_rel)
            if not p.exists():
                continue

            sheet = pygame.image.load(str(p)).convert_alpha()
            w, h = sheet.get_size()
            n_rows = max(1, h // FRAME_SIZE)
            AnimSprite._row_count_cache[path_rel] = n_rows
            actual_frames = min(n_frames, w // FRAME_SIZE)

            # Build the two facings we actually render with.
            for facing in ("right", "left"):
                row_idx, flip = _row_for_facing(facing, n_rows)
                cache_key = (path_rel, row_idx, flip, CELL_SIZE)
                if cache_key in AnimSprite._sheet_cache:
                    continue
                y = row_idx * FRAME_SIZE
                if y + FRAME_SIZE > h:
                    y = 0
                frames: list[pygame.Surface] = []
                for i in range(actual_frames):
                    rect = pygame.Rect(i * FRAME_SIZE, y, FRAME_SIZE, FRAME_SIZE)
                    sub = sheet.subsurface(rect).copy()
                    if flip:
                        sub = pygame.transform.flip(sub, True, False)
                    sub = pygame.transform.scale(sub, (render_size, render_size))
                    frames.append(sub)
                AnimSprite._sheet_cache[cache_key] = frames

            # Yield after each sheet so we don't starve the frame pump.
            await asyncio.sleep(0)