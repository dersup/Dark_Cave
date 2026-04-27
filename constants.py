from classes import *
INSPECT_WHITELIST = {
	"Entity": ["name", "health", "max_health", "armor", "weapon", "damage_resistance"],
	"item": ["name", "damage"],
	"weapon": ["name", "damage", "attack"],
	"armor": ["name", "AC"],
	"Cell": ["enemy_entity", "inventory"],
}
COLOURS = {
    "dark_gray":  (10,    8,  12),
    "gray":       (110, 105,  98),
    "black":      (  0,   0,   0),
    "blue":       ( 60, 120, 255),
    "red":        (220,  50,  50),
    "green":      ( 50, 180,  50),
    "dark_green": (  0, 100,   0),
    "gold":       (255, 210,  50),
    "orange":     (255, 165,   0),
    "purple":     (160,  32, 240),
    "brown":      (139,  90,  43),
    "white":      (255, 255, 255),
}
USED_KEYS =["<Shift-KeyPress-Up>",
            "<Shift-KeyPress-Down>",
            "<Shift-KeyPress-Right>",
            "<Shift-KeyPress-Left>",
            "<Shift-KeyPress-w>",
            "<Shift-KeyPress-s>",
            "<Shift-KeyPress-d>",
            "<Shift-KeyPress-a>",
            "<Enter>",
            "<Up>",
            "<Down>",
            "<Left>",
            "<Right>",
            "w",
            "s",
            "a",
            "d",
            "e",
            "j",
            "i",
]
ELEMENTS = [
    "fire",
    "ice",
    "lightning",
    "water",
    "earth",
    "wind",
    "light",
    "dark",
    "poison",
    "physical",
]
ENEMIES = {
    "goblin": {"stats":{
        "health": 20, "mana":40, "attack": 3, "defence": 5, "luck": 10,
        "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 10, "gold": 1
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.10, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": -0.25, "physical": 0.00,
        }
    },
    "orc": {"stats":{
        "health": 50, "mana":40, "attack": 8, "defence": 8, "luck": 5,
        "magic_defence": 2, "magic_attack": 0, "agility": 3, "exp": 25, "gold": 3
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.20, "wind": 0.00, "light": 0.00, "dark": 0.10,
            "poison": -0.10, "physical": 0.15,
        }
    },
    "skeleton": {"stats":{
        "health": 60, "mana":70, "attack": 8, "defence": 10, "luck": 5,
        "magic_defence": 15, "magic_attack": 0, "agility": 0, "exp": 30, "gold": 10
        },
        "resistances": {
            "fire": -0.50, "ice": 0.50, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.00, "light": -0.50, "dark": 0.75,
            "poison": 1.00, "physical": 0.25,
        }
    },
    "troll": {"stats":{
        "health": 90, "mana":40, "attack": 10, "defence": 10, "luck": 3,
        "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 50, "gold": 5
        },
        "resistances": {
            "fire": -0.50, "ice": 0.10, "lightning": 0.00, "water": 0.20,
            "earth": 0.30, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": 0.25, "physical": 0.20,
        }
    },
    "wraith": {"stats":{
        "health": 35, "mana":200, "attack": 10, "defence": 5, "luck": 10,
        "magic_defence": 10, "magic_attack": 8, "agility": 25, "exp": 55, "gold": 15
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.50, "light": -0.75, "dark": 1.00,
            "poison": 1.00, "physical": 1.00,
        }
    },
    "dark mage": {"stats":{
        "health": 30, "mana":400, "attack": 3, "defence": 5, "luck": 15,
        "magic_defence": 10, "magic_attack": 15, "agility": 5, "exp": 60, "gold": 20
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.00, "light": -0.50, "dark": 0.75,
            "poison": 0.25, "physical": 0.00,
        }
    },
    "vampire": {"stats":{
        "health": 70, "mana":400, "attack": 20, "defence": 15, "luck": 20,
        "magic_defence": 25, "magic_attack": 15, "agility": 20, "exp": 80, "gold": 25
        },
        "resistances": {
            "fire": -0.25, "ice": 0.25, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.00, "light": -1.00, "dark": 1.00,
            "poison": 1.00, "physical": 0.25,
        }
    },
    "zombie": {"stats":{
        "health": 40, "mana":0, "attack": 5, "defence": 4, "luck": 2,
        "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 18, "gold": 2
        },
        "resistances": {
            "fire": -0.25, "ice": 0.20, "lightning": 0.00, "water": 0.00,
            "earth": 0.10, "wind": 0.00, "light": -0.50, "dark": 0.75,
            "poison": 1.00, "physical": 0.10,
        }
    },
    "wild orc": {"stats":{
        "health": 60, "mana":20, "attack": 10, "defence": 6, "luck": 4,
        "magic_defence": 0, "magic_attack": 0, "agility": 5, "exp": 30, "gold": 4
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.20, "wind": 0.00, "light": 0.00, "dark": 0.10,
            "poison": -0.15, "physical": 0.20,
        }
    },
    "cyclops": {"stats":{
        "health": 100, "mana":30, "attack": 15, "defence": 12, "luck": 3,
        "magic_defence": 5, "magic_attack": 0, "agility": 0, "exp": 60, "gold": 8
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": -0.25, "water": 0.10,
            "earth": 0.30, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": 0.10, "physical": 0.25,
        }
    },
    "minotaur": {"stats":{
        "health": 120, "mana":30, "attack": 18, "defence": 14, "luck": 3,
        "magic_defence": 5, "magic_attack": 0, "agility": 5, "exp": 70, "gold": 10
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.20, "wind": -0.10, "light": 0.00, "dark": 0.10,
            "poison": 0.10, "physical": 0.30,
        }
    },
    "centaur": {"stats":{
        "health": 85, "mana":60, "attack": 14, "defence": 10, "luck": 8,
        "magic_defence": 5, "magic_attack": 3, "agility": 15, "exp": 55, "gold": 7
        },
        "resistances": {
            "fire": 0.00, "ice": -0.10, "lightning": 0.00, "water": 0.10,
            "earth": 0.15, "wind": 0.10, "light": 0.10, "dark": 0.00,
            "poison": 0.00, "physical": 0.15,
        }
    },
    "yeti": {"stats":{
        "health": 110, "mana":20, "attack": 16, "defence": 12, "luck": 4,
        "magic_defence": 3, "magic_attack": 0, "agility": 3, "exp": 65, "gold": 9
        },
        "resistances": {
            "fire": -0.50, "ice": 1.00, "lightning": 0.00, "water": 0.20,
            "earth": 0.10, "wind": 0.20, "light": 0.00, "dark": 0.00,
            "poison": 0.10, "physical": 0.20,
        }
    },
    "pumpkin horror": {"stats":{
        "health": 55, "mana":80, "attack": 7, "defence": 6, "luck": 12,
        "magic_defence": 8, "magic_attack": 5, "agility": 5, "exp": 40, "gold": 6
        },
        "resistances": {
            "fire": -0.75, "ice": 0.20, "lightning": 0.00, "water": 0.10,
            "earth": 0.10, "wind": 0.00, "light": -0.25, "dark": 0.50,
            "poison": 0.20, "physical": 0.00,
        }
    },
    "green slime": {"stats":{
        "health": 15, "mana":0, "attack": 2, "defence": 2, "luck": 5,
        "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 8, "gold": 1
        },
        "resistances": {
            "fire": -0.50, "ice": 0.20, "lightning": -0.25, "water": 0.50,
            "earth": 0.00, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": 0.50, "physical": -0.25,
        }
    },
    "blue slime": {"stats":{
        "health": 18, "mana":10, "attack": 3, "defence": 2, "luck": 5,
        "magic_defence": 5, "magic_attack": 0, "agility": 0, "exp": 10, "gold": 1
        },
        "resistances": {
            "fire": 0.00, "ice": 0.50, "lightning": -0.25, "water": 1.00,
            "earth": 0.00, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": 0.25, "physical": -0.25,
        }
    },
    "mother slime green": {"stats":{
        "health": 60, "mana":0, "attack": 6, "defence": 5, "luck": 5,
        "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 35, "gold": 5
        },
        "resistances": {
            "fire": -0.50, "ice": 0.20, "lightning": -0.25, "water": 0.50,
            "earth": 0.10, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": 1.00, "physical": -0.20,
        }
    },
    "mother slime blue": {"stats":{
        "health": 65, "mana":30, "attack": 7, "defence": 5, "luck": 5,
        "magic_defence": 10, "magic_attack": 0, "agility": 0, "exp": 38, "gold": 5
        },
        "resistances": {
            "fire": 0.00, "ice": 0.50, "lightning": -0.20, "water": 1.00,
            "earth": 0.00, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": 0.50, "physical": -0.20,
        }
    },
}


ENEMIES_WEIGHT = {
    # Level  goblin  orc  wild_orc  zombie  green_slime  blue_slime  skeleton  troll  pumpkin  centaur  cyclops  minotaur  yeti  wraith  dark_mage  vampire  mother_slime_green  mother_slime_blue
    "1":  {"goblin": 60, "orc": 10, "wild orc": 0,  "zombie": 15, "green slime": 10, "blue slime": 5,
           "skeleton": 0,  "troll": 0,  "pumpkin horror": 0, "centaur": 0, "cyclops": 0, "minotaur": 0, "yeti": 0,
           "wraith": 0,  "dark mage": 0, "vampire": 0, "mother slime green": 0, "mother slime blue": 0},
    "2":  {"goblin": 50, "orc": 15, "wild orc": 5,  "zombie": 15, "green slime": 10, "blue slime": 5,
           "skeleton": 0,  "troll": 0,  "pumpkin horror": 0, "centaur": 0, "cyclops": 0, "minotaur": 0, "yeti": 0,
           "wraith": 0,  "dark mage": 0, "vampire": 0, "mother slime green": 0, "mother slime blue": 0},
    "3":  {"goblin": 35, "orc": 20, "wild orc": 10, "zombie": 10, "green slime": 8,  "blue slime": 5,
           "skeleton": 0,  "troll": 5,  "pumpkin horror": 5, "centaur": 2, "cyclops": 0, "minotaur": 0, "yeti": 0,
           "wraith": 0,  "dark mage": 0, "vampire": 0, "mother slime green": 0, "mother slime blue": 0},
    "4":  {"goblin": 20, "orc": 20, "wild orc": 10, "zombie": 10, "green slime": 5,  "blue slime": 5,
           "skeleton": 5,  "troll": 8,  "pumpkin horror": 5, "centaur": 5, "cyclops": 3, "minotaur": 0, "yeti": 0,
           "wraith": 0,  "dark mage": 0, "vampire": 0, "mother slime green": 2, "mother slime blue": 2},
    "5":  {"goblin": 15, "orc": 15, "wild orc": 10, "zombie": 8,  "green slime": 0,  "blue slime": 0,
           "skeleton": 10, "troll": 10, "pumpkin horror": 5, "centaur": 8, "cyclops": 5, "minotaur": 3, "yeti": 3,
           "wraith": 0,  "dark mage": 0, "vampire": 0, "mother slime green": 4, "mother slime blue": 4},
    "6":  {"goblin": 10, "orc": 10, "wild orc": 8,  "zombie": 5,  "green slime": 0,  "blue slime": 0,
           "skeleton": 12, "troll": 12, "pumpkin horror": 8, "centaur": 8, "cyclops": 8, "minotaur": 5, "yeti": 5,
           "wraith": 5,  "dark mage": 4, "vampire": 0, "mother slime green": 0, "mother slime blue": 0},
    "7":  {"goblin": 5,  "orc": 5,  "wild orc": 5,  "zombie": 0,  "green slime": 0,  "blue slime": 0,
           "skeleton": 15, "troll": 15, "pumpkin horror": 5, "centaur": 8, "cyclops": 8, "minotaur": 8, "yeti": 8,
           "wraith": 8,  "dark mage": 5, "vampire": 0, "mother slime green": 0, "mother slime blue": 0},
    "8":  {"goblin": 0,  "orc": 0,  "wild orc": 0,  "zombie": 0,  "green slime": 0,  "blue slime": 0,
           "skeleton": 15, "troll": 15, "pumpkin horror": 5, "centaur": 5, "cyclops": 10, "minotaur": 10, "yeti": 10,
           "wraith": 12, "dark mage": 8, "vampire": 5, "mother slime green": 5, "mother slime blue": 0},
    "9":  {"goblin": 0,  "orc": 0,  "wild orc": 0,  "zombie": 0,  "green slime": 0,  "blue slime": 0,
           "skeleton": 10, "troll": 10, "pumpkin horror": 0, "centaur": 5, "cyclops": 10, "minotaur": 15, "yeti": 10,
           "wraith": 15, "dark mage": 10, "vampire": 10, "mother slime green": 5, "mother slime blue": 0},
    "10": {"goblin": 0,  "orc": 0,  "wild orc": 0,  "zombie": 0,  "green slime": 0,  "blue slime": 0,
           "skeleton": 5,  "troll": 5,  "pumpkin horror": 0, "centaur": 5, "cyclops": 10, "minotaur": 15, "yeti": 10,
           "wraith": 15, "dark mage": 10, "vampire": 20, "mother slime green": 0, "mother slime blue": 5},
}

MOB_WEAPON_PREFERENCES = {
    "player":{
        "axe": 100/6,
        "club": 100/6,
        "spear": 100/6,
        "short sword": 100/6,
        "dagger": 100/6,
        "long sword": 100/6,
    },
    "goblin": {
        "dagger": 40,
        "short sword": 30,
        "spear": 20,
        "axe": 5,
        "club": 5,
    },
    "orc": {
        "axe": 40,
        "club": 30,
        "spear": 15,
        "short sword": 10,
        "dagger": 5,
    },
    "skeleton": {
        "short sword": 35,
        "spear": 35,
        "axe": 15,
        "long sword": 10,
        "club": 5,
    },
    "troll": {
        "club": 50,
        "axe": 50,
    },
    "wraith": {
        "dagger": 60,
        "short sword": 40,
    },
    "dark mage": {
        "dagger": 50,
        "short sword": 30,
        "spear": 20,
    },
    "vampire": {
        "short sword": 40,
        "long sword": 35,
        "axe": 25,
    },
    # -- New mobs --------------------------------------------------------------
    "zombie": {
        "club": 50,
        "axe": 30,
        "dagger": 20,
    },
    "wild orc": {
        "axe": 45,
        "club": 35,
        "spear": 20,
    },
    "cyclops": {
        "club": 60,
        "axe": 40,
    },
    "minotaur": {
        "axe": 55,
        "club": 30,
        "spear": 15,
    },
    "centaur": {
        "spear": 50,
        "long sword": 30,
        "axe": 20,
    },
    "yeti": {
        "club": 70,
        "axe": 30,
    },
    "pumpkin horror": {
        "dagger": 40,
        "short sword": 35,
        "club": 25,
    },
    "green slime": {
        "dagger": 60,
        "club": 40,
    },
    "blue slime": {
        "dagger": 60,
        "club": 40,
    },
    "mother slime green": {
        "club": 50,
        "axe": 30,
        "dagger": 20,
    },
    "mother slime blue": {
        "club": 50,
        "axe": 30,
        "dagger": 20,
    },
}

MOB_ARMOR_PREFERENCES = {
    "player": {
        "leather jerkin": 100
    },
    "goblin": {
        "cloth": 40,
        "leather jerkin": 35,
        "hide armor": 20,
        "chain shirt": 5,
    },
    "orc": {
        "hide armor": 30,
        "chain shirt": 35,
        "scale mail": 25,
        "half plate": 10,
    },
    "skeleton": {
        "chain shirt": 40,
        "scale mail": 30,
        "half plate": 20,
        "leather jerkin": 10,
    },
    "troll": {
        "hide armor": 60,
        "cloth": 30,
        "leather jerkin": 10,
    },
    "wraith": {
        "cloth": 70,
        "leather jerkin": 30,
    },
    "dark mage": {
        "cloth": 80,
        "leather jerkin": 20,
    },
    "vampire": {
        "leather jerkin": 40,
        "chain shirt": 35,
        "scale mail": 25,
    },
    # -- New mobs --------------------------------------------------------------
    "zombie": {
        "cloth": 60,
        "leather jerkin": 30,
        "hide armor": 10,
    },
    "wild orc": {
        "hide armor": 40,
        "chain shirt": 30,
        "leather jerkin": 20,
        "cloth": 10,
    },
    "cyclops": {
        "hide armor": 50,
        "chain shirt": 30,
        "scale mail": 20,
    },
    "minotaur": {
        "hide armor": 40,
        "chain shirt": 30,
        "scale mail": 20,
        "half plate": 10,
    },
    "centaur": {
        "leather jerkin": 30,
        "chain shirt": 30,
        "scale mail": 25,
        "hide armor": 15,
    },
    "yeti": {
        "hide armor": 60,
        "cloth": 25,
        "leather jerkin": 15,
    },
    "pumpkin horror": {
        "cloth": 50,
        "leather jerkin": 30,
        "hide armor": 20,
    },
    "green slime": {
        "cloth": 100,
    },
    "blue slime": {
        "cloth": 100,
    },
    "mother slime green": {
        "cloth": 60,
        "leather jerkin": 40,
    },
    "mother slime blue": {
        "cloth": 60,
        "leather jerkin": 40,
    },
}

MOB_ITEM_PREFERENCES = {
    "player":{
        "Bomb": 50,
        "Healing Potion": 50
    },
    "goblin": {
        "Bomb": 60,
        "Healing Potion": 40
    },
    "orc": {
        "Bomb": 50,
        "Healing Potion": 50
    },
    "skeleton": {
        "Bomb": 25,
        "Healing Potion": 75
    },
    "troll": {
        "Bomb": 10,
        "Healing Potion": 90
    },
    "wraith": {
        "Bomb": 40,
        "Healing Potion": 60
    },
    "dark mage": {
        "Bomb": 60,
        "Healing Potion": 40
    },
    "vampire": {
        "Bomb": 20,
        "Healing Potion": 80
    },
    # -- New mobs --------------------------------------------------------------
    "zombie": {
        "Bomb": 15,
        "Healing Potion": 85,
    },
    "wild orc": {
        "Bomb": 55,
        "Healing Potion": 45,
    },
    "cyclops": {
        "Bomb": 20,
        "Healing Potion": 80,
    },
    "minotaur": {
        "Bomb": 25,
        "Healing Potion": 75,
    },
    "centaur": {
        "Bomb": 30,
        "Healing Potion": 70,
    },
    "yeti": {
        "Bomb": 10,
        "Healing Potion": 90,
    },
    "pumpkin horror": {
        "Bomb": 50,
        "Healing Potion": 50,
    },
    "green slime": {
        "Bomb": 20,
        "Healing Potion": 80,
    },
    "blue slime": {
        "Bomb": 20,
        "Healing Potion": 80,
    },
    "mother slime green": {
        "Bomb": 30,
        "Healing Potion": 70,
    },
    "mother slime blue": {
        "Bomb": 30,
        "Healing Potion": 70,
    },
}

QUALITY_WEIGHT = {
    "player":{
        "items": {
            "":100
        },
        "weapon": {
            "":100
        },
        "armor": {
            "":100
        },
        "staff": {
            "": 100
        }
    },
    "goblin": {
        "items": {
            "diluted": 40,
            "low": 38,
            "": 20,
            "concentrated": 2},
        "weapon": {
            "broken": 20,
            "crude": 40,
            "rusted": 30,
            "": 10
        },
        "armor": {
            "destroyed": 60,
            "worn": 30,
            "": 10
        },
        "staff": {
            "broken": 30,
            "crude": 50,
            "": 20
        }
    },
    "orc": {
        "items": {
            "diluted": 20,
            "low": 40,
            "": 35,
            "concentrated": 5},
        "weapon": {
            "broken": 5,
            "crude": 30,
            "rusted": 30,
            "": 20,
            "reinforced": 10,
            "masterwork": 5,
        },
        "armor": {
            "destroyed": 5,
            "worn": 30,
            "": 30,
            "sturdy": 20,
            "reinforced": 10,
            "masterwork": 5
        },
        "staff": {
            "crude": 30,
            "rusted": 30,
            "": 30,
            "reinforced": 10
        }
    },
    "skeleton": {
        "items": {
            "low": 10,
            "": 70,
            "concentrated": 20},
        "weapon": {
            "rusted": 10,
            "": 40,
            "reinforced": 40,
            "masterwork": 10,
        },
        "armor": {
            "worn": 10,
            "": 30,
            "sturdy": 30,
            "reinforced": 20,
            "masterwork": 10
        },
        "staff": {
            "rusted": 20,
            "": 40,
            "reinforced": 30,
            "masterwork": 10
        }
    },
    "troll": {
        "items": {
            "diluted": 10,
            "low": 50,
            "": 35,
            "concentrated": 5},
        "weapon": {
            "crude": 30,
            "rusted": 20,
            "": 30,
            "reinforced": 15,
            "masterwork": 5,
        },
        "armor": {
            "destroyed": 20,
            "worn": 40,
            "": 30,
            "sturdy": 10,
        },
        "staff": {
            "broken": 50,
            "crude": 30,
            "": 20
        }
    },
    "wraith": {
        "items": {
            "low": 10,
            "": 50,
            "concentrated": 40},
        "weapon": {
            "": 30,
            "reinforced": 40,
            "masterwork": 30,
        },
        "armor": {
            "worn": 20,
            "": 50,
            "sturdy": 30,
        },
        "staff": {
            "": 30,
            "reinforced": 40,
            "masterwork": 30
        }
    },
    "dark mage": {
        "items": {
            "low": 5,
            "": 45,
            "concentrated": 50},
        "weapon": {
            "": 30,
            "reinforced": 40,
            "masterwork": 30,
        },
        "armor": {
            "worn": 30,
            "": 50,
            "sturdy": 20,
        },
        "staff": {
            "": 20,
            "reinforced": 40,
            "masterwork": 40
        }
    },
    "vampire": {
        "items": {
            "": 40,
            "concentrated": 60},
        "weapon": {
            "": 20,
            "reinforced": 40,
            "masterwork": 40,
        },
        "armor": {
            "": 20,
            "sturdy": 30,
            "reinforced": 30,
            "masterwork": 20
        },
        "staff": {
            "": 20,
            "reinforced": 30,
            "masterwork": 50
        }
    },
    # -- New mobs --------------------------------------------------------------
    "zombie": {
        "items": {"diluted": 50, "low": 40, "": 10},
        "weapon": {"broken": 30, "crude": 40, "rusted": 20, "": 10},
        "armor":  {"destroyed": 50, "worn": 40, "": 10},
        "staff":  {"broken": 50, "crude": 30, "": 20},
    },
    "wild orc": {
        "items": {"diluted": 20, "low": 40, "": 35, "concentrated": 5},
        "weapon": {"crude": 20, "rusted": 30, "": 30, "reinforced": 15, "masterwork": 5},
        "armor":  {"destroyed": 10, "worn": 30, "": 35, "sturdy": 20, "reinforced": 5},
        "staff":  {"crude": 30, "rusted": 30, "": 30, "reinforced": 10},
    },
    "cyclops": {
        "items": {"low": 30, "": 55, "concentrated": 15},
        "weapon": {"crude": 10, "rusted": 20, "": 40, "reinforced": 20, "masterwork": 10},
        "armor":  {"worn": 20, "": 40, "sturdy": 25, "reinforced": 15},
        "staff":  {"crude": 30, "rusted": 30, "": 40},
    },
    "minotaur": {
        "items": {"low": 20, "": 55, "concentrated": 25},
        "weapon": {"rusted": 10, "": 35, "reinforced": 35, "masterwork": 20},
        "armor":  {"worn": 10, "": 30, "sturdy": 30, "reinforced": 20, "masterwork": 10},
        "staff":  {"crude": 20, "rusted": 20, "": 40, "reinforced": 20},
    },
    "centaur": {
        "items": {"low": 20, "": 55, "concentrated": 25},
        "weapon": {"rusted": 10, "": 35, "reinforced": 35, "masterwork": 20},
        "armor":  {"worn": 10, "": 35, "sturdy": 30, "reinforced": 25},
        "staff":  {"crude": 20, "": 40, "reinforced": 30, "masterwork": 10},
    },
    "yeti": {
        "items": {"diluted": 10, "low": 45, "": 40, "concentrated": 5},
        "weapon": {"crude": 20, "rusted": 30, "": 35, "reinforced": 15},
        "armor":  {"destroyed": 10, "worn": 30, "": 40, "sturdy": 20},
        "staff":  {"broken": 40, "crude": 40, "": 20},
    },
    "pumpkin horror": {
        "items": {"": 40, "concentrated": 60},
        "weapon": {"": 40, "reinforced": 35, "masterwork": 25},
        "armor":  {"worn": 10, "": 40, "sturdy": 30, "reinforced": 20},
        "staff":  {"": 30, "reinforced": 40, "masterwork": 30},
    },
    "green slime": {
        "items": {"diluted": 60, "low": 35, "": 5},
        "weapon": {"broken": 60, "crude": 30, "": 10},
        "armor":  {"destroyed": 70, "worn": 25, "": 5},
        "staff":  {"broken": 60, "crude": 30, "": 10},
    },
    "blue slime": {
        "items": {"diluted": 60, "low": 35, "": 5},
        "weapon": {"broken": 60, "crude": 30, "": 10},
        "armor":  {"destroyed": 70, "worn": 25, "": 5},
        "staff":  {"broken": 60, "crude": 30, "": 10},
    },
    "mother slime green": {
        "items": {"low": 20, "": 60, "concentrated": 20},
        "weapon": {"crude": 20, "rusted": 30, "": 35, "reinforced": 15},
        "armor":  {"worn": 20, "": 50, "sturdy": 30},
        "staff":  {"crude": 30, "": 40, "reinforced": 30},
    },
    "mother slime blue": {
        "items": {"low": 20, "": 60, "concentrated": 20},
        "weapon": {"crude": 20, "rusted": 30, "": 35, "reinforced": 15},
        "armor":  {"worn": 20, "": 50, "sturdy": 30},
        "staff":  {"crude": 30, "": 40, "reinforced": 30},
    },
}
RARE_LEVEL_THRESHOLD = {
        "goblin":              3,
        "orc":                 5,
        "skeleton":            7,
        "troll":               6,
        "wraith":              8,
        "dark mage":           8,
        "vampire":             9,
        # New mobs
        "zombie":              3,
        "wild orc":            5,
        "cyclops":             6,
        "minotaur":            7,
        "centaur":             6,
        "yeti":                7,
        "pumpkin horror":      5,
        "green slime":         2,
        "blue slime":          2,
        "mother slime green":  5,
        "mother slime blue":   5,
    }
RARITY = {
    "": 98.498,
    "rare": 1,
    "epic": 0.5,
    "legendary": 0.002,
}

RARITY_BONUS = {
    "": 0,
    "rare": 2,
    "epic": 4,
    "legendary": 7,
}

BASE_WEAPONS = {
    "dagger": {"damage": Elements("physical",5), "attack": 4, "value": 40, "description": "A small, easily concealed blade. Quick to draw and deadly in close quarters."},
    "short sword": {"damage":  Elements("physical",10), "attack": 3, "value": 60, "description": "A versatile one-handed blade, well-balanced for both offense and defense."},
    "long sword": {"damage":  Elements("physical",12), "attack": 2, "value": 80, "description": "A classic knightly weapon. Longer reach and heavier strikes, but slower to swing."},
    "spear": {"damage":  Elements("physical",11), "attack": 2, "value": 100, "description": "A long-shafted weapon tipped with an iron point. Excellent for keeping enemies at distance."},
    "club": {"damage":  Elements("physical",17), "attack": 1, "value": 50, "description": "A crude but effective bludgeon. Slow and graceless, but capable of bone-crushing blows."},
    "axe": {"damage":  Elements("physical",20), "attack": 0, "value": 70, "description": "A heavy cleaving weapon. Devastating on impact, but leaves you wide open between swings."},
}

BASE_ARMOR = {
    "cloth": {"AC":1,"value":30, "description": "Simple layered fabric. Offers little protection but allows free movement."},
    "leather jerkin": {"AC":2,"value":60, "description": "Toughened leather stitched into a fitted vest. Light and flexible with modest protection."},
    "hide armor": {"AC":3,"value":120, "description": "Thick pelts and cured hides lashed together. Crude but surprisingly resilient."},
    "chain shirt": {"AC":4,"value":240, "description": "Interlocking iron rings woven into a shirt. Deflects slashing blows without restricting movement."},
    "scale mail": {"AC":5,"value":480, "description": "Overlapping metal scales riveted to a leather backing. Solid protection at the cost of some agility."},
    "half plate": {"AC":6,"value":960, "description": "Fitted metal plates covering the vital areas. Near-impenetrable defense, but heavy and cumbersome."},
}

BASE_SPELLS = {
    # -- Fire -----------------------------------------------------------------
    "fireball": Magic("Fireball", [Elements("fire", 30)], "A burst of flame that scorches on impact.", cost=15,
                      distance=5),
    "flame lance": Magic("Flame Lance", [Elements("fire", 50)], "A piercing spear of concentrated fire.", cost=25,
                         distance=7),
    # -- Ice ------------------------------------------------------------------
    "ice shard": Magic("Ice Shard", [Elements("ice", 25)], "A razor-sharp shard of conjured ice.", cost=12, distance=5),
    "ice spear": Magic("Ice Spear", [Elements("ice", 45)], "A razor-sharp length of conjured ice.", cost=28,
                       distance=3),
    # -- Lightning ------------------------------------------------------------
    "lightning bolt": Magic("Lightning Bolt", [Elements("lightning", 40)], "A crackling bolt of raw electricity.",
                            cost=20, distance=6),
    # -- Water ----------------------------------------------------------------
    "tidal wave": Magic("Tidal Wave", [Elements("water", 35)], "A rushing wall of water that bowls enemies over.",
                        cost=18, distance=4),
    # -- Earth ----------------------------------------------------------------
    "stone spike": Magic("Stone Spike", [Elements("earth", 32)], "Jagged spires of rock erupt beneath the target.",
                         cost=16, distance=4),
    # -- Wind -----------------------------------------------------------------
    "gust blade": Magic("Gust Blade", [Elements("wind", 22)], "A razor-edged current of compressed air.", cost=11,
                        distance=5),
    # -- Light ----------------------------------------------------------------
    "holy light": Magic("Holy Light", [Elements("light", 45)], "A blinding beam of radiant divine energy.", cost=22,
                        distance=8),
    "smite": Magic("Smite", [Elements("light", 30)], "A concentrated strike of sacred power.", cost=15, distance=5),
    # -- Dark -----------------------------------------------------------------
    "dark pulse": Magic("Dark Pulse", [Elements("dark", 35)], "A wave of shadowy energy that drains the soul.", cost=18,
                        distance=4),
    "void rift": Magic("Void Rift", [Elements("dark", 55)], "Tears a wound in reality, unleashing consuming darkness.",
                       cost=32, distance=6),
    # -- Poison ---------------------------------------------------------------
    "poison cloud": Magic("Poison Cloud", [Elements("poison", 20)], "A lingering toxic cloud that chokes and corrodes.",
                          cost=10, distance=3),
    "venom strike": Magic("Venom Strike", [Elements("poison", 30)], "A concentrated burst of lethal venom.", cost=16,
                          distance=5),
    # -- Physical -------------------------------------------------------------
    "force wave": Magic("Force Wave", [Elements("physical", 28)], "A concussive shockwave of pure kinetic force.",
                        cost=14, distance=3),
    "arcane barrage": Magic("Arcane Barrage", [Elements("physical", 18)], "Rapid-fire bolts of raw magical force.",
                            cost=9, distance=5),
    # -- Multi-element --------------------------------------------------------
    "hellfire": Magic("Hellfire", [Elements("fire", 25), Elements("dark", 20)],
                      "Infernal flames mingled with corrupting shadow.", cost=28, distance=5),
    "steam burst": Magic("Steam Burst", [Elements("fire", 18), Elements("water", 18)],
                         "Superheated water erupts in a scalding explosion.", cost=20, distance=3),
    "frostbolt": Magic("Frostbolt", [Elements("ice", 20), Elements("water", 15)],
                       "A bolt of freezing water that chills to the bone.", cost=18, distance=6),
    "thunder clap": Magic("Thunder Clap", [Elements("lightning", 22), Elements("wind", 18)],
                          "A booming shockwave crackling with electric charge.", cost=22, distance=3),
    "plague bolt": Magic("Plague Bolt", [Elements("poison", 18), Elements("dark", 18)],
                         "A bolt of festering dark corruption.", cost=20, distance=5),
    "divine wrath": Magic("Divine Wrath", [Elements("light", 30), Elements("fire", 20)],
                          "Sacred flames of righteous fury smite the wicked.", cost=30, distance=6),
    "frozen earth": Magic("Frozen Earth", [Elements("ice", 20), Elements("earth", 20)],
                          "Permafrost erupts from the ground, trapping foes.", cost=22, distance=3),
    # -- Healing --------------------------------------------------------------
    "mend": Magic("Mend", [Elements("healing", 25)], "A gentle pulse of restorative energy.", cost=12, distance=1),
    "greater heal": Magic("Greater Heal", [Elements("healing", 50)], "A powerful wave of healing light.", cost=28,
                          distance=1),
}

BASE_STAFFS = {
    # -- Starter ---------------------------------------------------------------
    "apprentice staff":  Staff("Apprentice Staff",   gold= 80,  attack= 5,  elements=[Elements("physical",   5)],  description="A plain wooden staff. Enchantments are weak but serviceable."),
    # -- Elemental -------------------------------------------------------------
    "fire staff":        Staff("Fire Staff",          gold=180,  attack= 8,  elements=[Elements("fire",      14)],  description="Tipped with a smouldering ruby. Warm to the touch even without a spell."),
    "frost staff":       Staff("Frost Staff",         gold=190,  attack= 8,  elements=[Elements("ice",       14)],  description="A pale-blue staff that frosts the air around it."),
    "storm staff":       Staff("Storm Staff",         gold=200,  attack=10,  elements=[Elements("lightning", 15)],  description="Crackles with electricity. Static clings to the wielder's hair."),
    "earth staff":       Staff("Earth Staff",         gold=175,  attack= 7,  elements=[Elements("earth",     16)],  description="Carved from ancient oak fused with iron-rich stone."),
    "wind staff":        Staff("Wind Staff",          gold=170,  attack= 9,  elements=[Elements("wind",      13)],  description="Hollow-cored and light; it whistles faintly when swung."),
    "tide staff":        Staff("Tide Staff",          gold=180,  attack= 8,  elements=[Elements("water",     14)],  description="A staff of sea-glass and driftwood. Smells faintly of the ocean."),
    "venom staff":       Staff("Venom Staff",         gold=160,  attack= 7,  elements=[Elements("poison",    12)],  description="Stained green along the grain; the wood itself has been toxified."),
    # -- Prestige --------------------------------------------------------------
    "shadow staff":      Staff("Shadow Staff",        gold=250,  attack= 8,  elements=[Elements("dark",      20)],  description="Wreathed in shifting shadow. Light faintly dims near it."),
    "holy staff":        Staff("Holy Staff",          gold=300,  attack=12,  elements=[Elements("light",     25)],  description="Glows with divine light. The warmth is comforting to the righteous."),
    "plague staff":      Staff("Plague Staff",        gold=270,  attack= 9,  elements=[Elements("poison",    18), Elements("dark",  10)],
                                                                                       description="A gnarled staff oozing with corruption. Insects flee its presence."),
    "inferno staff":     Staff("Inferno Staff",       gold=320,  attack=11,  elements=[Elements("fire",      22), Elements("dark",  12)],
                                                                                       description="Forged in hellfire. The crystal at its tip burns with an otherworldly flame."),
    "blizzard staff":    Staff("Blizzard Staff",      gold=310,  attack=10,  elements=[Elements("ice",       20), Elements("wind",  12)],
                                                                                       description="An arctic staff that trails snowflakes with every step."),
    "tempest staff":     Staff("Tempest Staff",       gold=330,  attack=12,  elements=[Elements("lightning", 20), Elements("wind",  14)],
                                                                                       description="Resonates with the frequency of storm-clouds. Thunder follows its swing."),
    "arcane staff":      Staff("Arcane Staff",        gold=400,  attack=14,  elements=[Elements("physical",  30)],  description="Brimming with raw unaligned magic. Every element bends to its wielder."),
}

# Element -> list of spell keys that match it (including multi-element spells)
STAFF_ELEMENT_SPELL_AFFINITIES = {
    "fire":      ["fireball", "flame lance", "hellfire", "steam burst", "divine wrath"],
    "ice":       ["ice shard", "ice spear", "frostbolt", "frozen earth"],
    "lightning": ["lightning bolt", "thunder clap"],
    "water":     ["tidal wave", "frostbolt", "steam burst"],
    "earth":     ["stone spike", "frozen earth"],
    "wind":      ["gust blade", "thunder clap"],
    "light":     ["holy light", "smite", "radiant burst", "divine wrath", "mend", "greater heal"],
    "dark":      ["dark pulse", "void rift", "shadow bolt", "hellfire", "plague bolt"],
    "poison":    ["poison cloud", "venom strike", "plague bolt"],
    "physical":  ["force wave", "arcane barrage"],
    "healing":   ["mend", "greater heal"],
}

MOB_STAFF_PREFERENCES = {
    "player":     {"apprentice staff": 100},
    "dark mage":  {"shadow staff": 50, "plague staff": 25, "apprentice staff": 15, "venom staff": 10},
    "wraith":     {"shadow staff": 55, "frost staff": 25, "apprentice staff": 20},
    "vampire":    {"shadow staff": 40, "inferno staff": 30, "plague staff": 20, "apprentice staff": 10},
    "skeleton":   {"apprentice staff": 40, "frost staff": 30, "shadow staff": 20, "earth staff": 10},
}

WEAPON_QUALITIES = {
    "broken": {"damage_mod": 0.3, "attack_mod": -2, "gold_mod": 0.1},
    "crude": {"damage_mod": 0.5, "attack_mod": -1, "gold_mod": 0.3},
    "rusted": {"damage_mod": 0.7, "attack_mod": 0, "gold_mod": 0.6},
    "reinforced": {"damage_mod": 1.5, "attack_mod": 1, "gold_mod": 1.5},
    "masterwork": {"damage_mod": 2, "attack_mod": 2, "gold_mod": 2},
}

ARMOR_QUALITIES = {
    "destroyed": {"mod":0.2,"gold_mod":0.1},
    "worn": {"mod":0.7,"gold_mod":0.5},
    "sturdy": {"mod":1.4,"gold_mod":1.2},
    "reinforced": {"mod":1.7,"gold_mod":1.5},
    "masterwork": {"mod":2,"gold_mod":2}
}

BASE_ITEMS = {
    "Healing Potion":{"damage":{"healing":20},"value":120},
    "Bomb": {"damage":{"fire":30},"attack":-1,"value":200,"distance":3},
}



ITEM_QUALITY = {
    "diluted":{"mod":0.5,"gold_mod":0.5},
    "low": {"mod":0.75,"gold_mod":0.75},
    "concentrated": {"mod":1.5,"gold_mod":1.5}
}

PLAYER_STARTING_GEAR = {
    "armor": {
        "leather jerkin": BASE_ARMOR["leather jerkin"]
    },
    "weapon":
        BASE_WEAPONS

}

ELEMENT_RESIST = {
    "fire":      0.00,  # % damage blocked
    "ice":       0.00,
    "lightning": 0.00,
    "water":     0.00,
    "earth":     0.00,
    "wind":      0.00,
    "light":     0.00,
    "dark":      0.00,
    "poison":    0.00,
    "physical":  0.00,
}

ITEM_MODIFIERS = {
    "weapons": {
        "single": {
    # -- WEAPONS --------------------------------------------------------------
            "of_fire": {
                "type": "weapon",
                "damage_bonus": {"fire": 0.25},
                "description": "Wreathed in flames, deals bonus fire damage.",
            },
            "of_frost": {
                "type": "weapon",
                "damage_bonus": {"ice": 0.25},
                "description": "Chills the air, deals bonus ice damage.",
            },
            "of_storms": {
                "type": "weapon",
                "damage_bonus": {"lightning": 0.35},
                "description": "Crackles with electricity, deals bonus lightning damage.",
            },
            "of_venom": {
                "type": "weapon",
                "damage_bonus": {"poison": 0.20},
                "description": "Drips with toxin, deals bonus poison damage.",
            },
            "of_darkness": {
                "type": "weapon",
                "damage_bonus": {"dark": 0.30},
                "description": "Radiates shadow energy, deals bonus dark damage.",
            },
            "of_radiance": {
                "type": "weapon",
                "damage_bonus": {"light": 0.30},
                "description": "Gleams with holy light, deals bonus light damage.",
            },
            "of_the_gale": {
                "type": "weapon",
                "damage_bonus": {"wind": 0.20},
                "description": "Hums with wind force, deals bonus wind damage.",
            },
            "of_the_earth": {
                "type": "weapon",
                "damage_bonus": {"earth": 0.20},
                "description": "Resonates with stone, deals bonus earth damage.",
            },
            "of_the_tide": {
                "type": "weapon",
                "damage_bonus": {"water": 0.20},
                "description": "Flows with aquatic force, deals bonus water damage.",
            },
        },
        # Dual-element weapons
        "double":{
            "of_hellfire": {
                "type": "weapon",
                "damage_bonus": {"fire": 0.20, "dark": 0.20},
                "description": "Burns with infernal energy, deals fire and dark damage.",
            },
            "of_the_blizzard": {
                "type": "weapon",
                "damage_bonus": {"ice": 0.20, "wind": 0.15},
                "description": "Howls with arctic winds, deals ice and wind damage.",
            },
            "of_the_tempest": {
                "type": "weapon",
                "damage_bonus": {"lightning": 0.20, "wind": 0.20},
                "description": "Roars with storm power, deals lightning and wind damage.",
            },
            "of_the_plague": {
                "type": "weapon",
                "damage_bonus": {"poison": 0.15, "dark": 0.15},
                "description": "Festers with corruption, deals poison and dark damage.",
            },
            "of_the_crusader": {
                "type": "weapon",
                "damage_bonus": {"light": 0.20, "fire": 0.15},
                "description": "Blazes with divine wrath, deals light and fire damage.",
            },
        },

        # -- ARMOR -----------------------------------------------------------------
    },
    "armour":{
        "single":{
            "of_flame_warding": {
                "type": "armor",
                "resistance_bonus": {"fire": 0.20},
                "description": "Treated with fireproof resin, resists fire damage.",
            },
            "of_frost_warding": {
                "type": "armor",
                "resistance_bonus": {"ice": 0.20},
                "description": "Lined with insulating fur, resists ice damage.",
            },
            "of_grounding": {
                "type": "armor",
                "resistance_bonus": {"lightning": 0.20},
                "description": "Woven with copper mesh, resists lightning damage.",
            },
            "of_the_antidote": {
                "type": "armor",
                "resistance_bonus": {"poison": 0.25},
                "description": "Laced with alchemical herbs, resists poison damage.",
            },
            "of_the_shadow": {
                "type": "armor",
                "resistance_bonus": {"dark": 0.25},
                "description": "Warded with runes, resists dark damage.",
            },
            "of_the_faithful": {
                "type": "armor",
                "resistance_bonus": {"light": 0.25},
                "description": "Blessed by a priest, resists light damage.",
            },
            "of_the_zephyr": {
                "type": "armor",
                "resistance_bonus": {"wind": 0.20},
                "description": "Aerodynamic weave, resists wind damage.",
            },
            "of_the_bedrock": {
                "type": "armor",
                "resistance_bonus": {"earth": 0.20},
                "description": "Reinforced with stone dust, resists earth damage.",
            },
            "of_the_depths": {
                "type": "armor",
                "resistance_bonus": {"water": 0.20},
                "description": "Sealed with pitch, resists water damage.",
            },
        },
    # Dual-element armor
        "double":{
            "of_the_guardian": {
                "type": "armor",
                "resistance_bonus": {"fire": 0.15, "ice": 0.15},
                "description": "Balanced against extremes, resists fire and ice damage.",
            },
            "of_the_exorcist": {
                "type": "armor",
                "resistance_bonus": {"dark": 0.20, "poison": 0.15},
                "description": "Purified against corruption, resists dark and poison damage.",
            },
            "of_the_ancients": {
                "type": "armor",
                "resistance_bonus": {"earth": 0.15, "water": 0.15},
                "description": "Attuned to nature, resists earth and water damage.",
            },
            "of_the_storm_wall": {
                "type": "armor",
                "resistance_bonus": {"lightning": 0.15, "wind": 0.15},
                "description": "Braced against the tempest, resists lightning and wind damage.",
            },
            "of_the_sanctified": {
                "type": "armor",
                "resistance_bonus": {"light": 0.15, "dark": 0.15},
                "description": "Attuned to both planes, resists light and dark damage.",
                },
            }
        }
    }