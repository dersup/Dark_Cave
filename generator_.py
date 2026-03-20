from classes import Elements
from entity import *

ENEMIES = {
    "goblin": {"stats":{
        "health": 20, "attack": 5, "defence": 10, "luck": 20,
        "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 10, "gold": 1
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.10, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": -0.25, "physical": 0.00,
        }
    },
    "orc": {"stats":{
        "health": 50, "attack": 12, "defence": 18, "luck": 5,
        "magic_defence": 2, "magic_attack": 0, "agility": 3, "exp": 25, "gold": 3
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.20, "wind": 0.00, "light": 0.00, "dark": 0.10,
            "poison": -0.10, "physical": 0.15,
        }
    },
    "skeleton": {"stats":{
        "health": 60, "attack": 8, "defence": 25, "luck": 5,
        "magic_defence": 15, "magic_attack": 0, "agility": 0, "exp": 30, "gold": 10
        },
        "resistances": {
            "fire": -0.50, "ice": 0.50, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.00, "light": -0.50, "dark": 0.75,
            "poison": 1.00, "physical": 0.25,
        }
    },
    "troll": {"stats":{
        "health": 90, "attack": 18, "defence": 20, "luck": 3,
        "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 50, "gold": 5
        },
        "resistances": {
            "fire": -0.50, "ice": 0.10, "lightning": 0.00, "water": 0.20,
            "earth": 0.30, "wind": 0.00, "light": 0.00, "dark": 0.00,
            "poison": 0.25, "physical": 0.20,
        }
    },
    "wraith": {"stats":{
        "health": 35, "attack": 10, "defence": 5, "luck": 10,
        "magic_defence": 30, "magic_attack": 20, "agility": 25, "exp": 55, "gold": 15
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.50, "light": -0.75, "dark": 1.00,
            "poison": 1.00, "physical": 0.50,
        }
    },
    "dark mage": {"stats":{
        "health": 30, "attack": 3, "defence": 5, "luck": 15,
        "magic_defence": 20, "magic_attack": 30, "agility": 5, "exp": 60, "gold": 20
        },
        "resistances": {
            "fire": 0.00, "ice": 0.00, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.00, "light": -0.50, "dark": 0.75,
            "poison": 0.25, "physical": 0.00,
        }
    },
    "vampire": {"stats":{
        "health": 70, "attack": 20, "defence": 15, "luck": 20,
        "magic_defence": 25, "magic_attack": 15, "agility": 20, "exp": 80, "gold": 25
        },
        "resistances": {
            "fire": -0.25, "ice": 0.25, "lightning": 0.00, "water": 0.00,
            "earth": 0.00, "wind": 0.00, "light": -1.00, "dark": 1.00,
            "poison": 1.00, "physical": 0.25,
        }
    },
}


ENEMIES_WEIGHT = {
    "1":  {"goblin": 90, "orc": 10, "skeleton": 0,  "troll": 0,  "wraith": 0,  "dark mage": 0,  "vampire": 0},
    "2":  {"goblin": 80, "orc": 20, "skeleton": 0,  "troll": 0,  "wraith": 0,  "dark mage": 0,  "vampire": 0},
    "3":  {"goblin": 65, "orc": 30, "skeleton": 0,  "troll": 5,  "wraith": 0,  "dark mage": 0,  "vampire": 0},
    "4":  {"goblin": 50, "orc": 35, "skeleton": 5,  "troll": 10, "wraith": 0,  "dark mage": 0,  "vampire": 0},
    "5":  {"goblin": 40, "orc": 35, "skeleton": 10, "troll": 15, "wraith": 0,  "dark mage": 0,  "vampire": 0},
    "6":  {"goblin": 25, "orc": 30, "skeleton": 15, "troll": 20, "wraith": 5,  "dark mage": 5,  "vampire": 0},
    "7":  {"goblin": 10, "orc": 25, "skeleton": 20, "troll": 20, "wraith": 15, "dark mage": 10, "vampire": 0},
    "8":  {"goblin": 0,  "orc": 20, "skeleton": 25, "troll": 20, "wraith": 20, "dark mage": 10, "vampire": 5},
    "9":  {"goblin": 0,  "orc": 10, "skeleton": 25, "troll": 15, "wraith": 20, "dark mage": 15, "vampire": 15},
    "10": {"goblin": 0,  "orc": 0,  "skeleton": 20, "troll": 15, "wraith": 20, "dark mage": 20, "vampire": 25},
}

MOB_WEAPON_PREFERENCES = {
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
        "dagger": 10,
        "club": 5,
    },
    "troll": {
        "club": 50,
        "axe": 35,
        "spear": 15,
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
        "dagger": 35,
        "axe": 25,
    },
}

MOB_ARMOR_PREFERENCES = {
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
}

MOB_ITEM_PREFERENCES = {
    "goblin": {
        "Bomb": 90,
        "Healing Potion": 10
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
}

QUALITY_WEIGHT = {
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
        }
    },
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
    "dagger": {"damage": Elements("physical",2), "attack": 4, "value": 40, "description": "A small, easily concealed blade. Quick to draw and deadly in close quarters."},
    "short sword": {"damage":  Elements("physical",3), "attack": 3, "value": 60, "description": "A versatile one-handed blade, well-balanced for both offense and defense."},
    "long sword": {"damage":  Elements("physical",4), "attack": 2, "value": 80, "description": "A classic knightly weapon. Longer reach and heavier strikes, but slower to swing."},
    "spear": {"damage":  Elements("physical",3), "attack": 2, "value": 100, "description": "A long-shafted weapon tipped with an iron point. Excellent for keeping enemies at distance."},
    "club": {"damage":  Elements("physical",5), "attack": 1, "value": 50, "description": "A crude but effective bludgeon. Slow and graceless, but capable of bone-crushing blows."},
    "axe": {"damage":  Elements("physical",6), "attack": 0, "value": 70, "description": "A heavy cleaving weapon. Devastating on impact, but leaves you wide open between swings."},
}

BASE_ARMOR = {
    "cloth": {"AC":1,"value":30, "description": "Simple layered fabric. Offers little protection but allows free movement."},
    "leather jerkin": {"AC":2,"value":60, "description": "Toughened leather stitched into a fitted vest. Light and flexible with modest protection."},
    "hide armor": {"AC":3,"value":120, "description": "Thick pelts and cured hides lashed together. Crude but surprisingly resilient."},
    "chain shirt": {"AC":4,"value":240, "description": "Interlocking iron rings woven into a shirt. Deflects slashing blows without restricting movement."},
    "scale mail": {"AC":5,"value":480, "description": "Overlapping metal scales riveted to a leather backing. Solid protection at the cost of some agility."},
    "half plate": {"AC":6,"value":960, "description": "Fitted metal plates covering the vital areas. Near-impenetrable defense, but heavy and cumbersome."},
}

WEAPON_QUALITIES = {
    "broken": {"damage_mod": -3, "attack_mod": -2, "gold_mod": 0.1},
    "crude": {"damage_mod": -2, "attack_mod": -1, "gold_mod": 0.3},
    "rusted": {"damage_mod": -1, "attack_mod": 0, "gold_mod": 0.6},
    "reinforced": {"damage_mod": 2, "attack_mod": 1, "gold_mod": 1.5},
    "masterwork": {"damage_mod": 3, "attack_mod": 2, "gold_mod": 2},
}

ARMOR_QUALITIES = {
    "destroyed": {"mod":-2,"gold_mod":0.1},
    "worn": {"mod":-1,"gold_mod":0.5},
    "sturdy": {"mod":1,"gold_mod":1.2},
    "reinforced": {"mod":2,"gold_mod":1.5},
    "masterwork": {"mod":3,"gold_mod":2}
}

BASE_ITEMS = {
    "Healing Potion":{"damage":20,"value":120},
    "Bomb": {"damage":30,"attack":-1,"value":200,"distance":3},
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

ITEM_MODIFIERS = { "weapons": {
    "single": {
    # ── WEAPONS ──────────────────────────────────────────────────────────────
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
    "dual":{
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

    # ── ARMOR ─────────────────────────────────────────────────────────────────
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
        "dual":{
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


def weighted_choice(weighted_dict):
    total = sum(weighted_dict.values())
    roll = random.uniform(0, total)

    upto = 0
    for item, weight in weighted_dict.items():
        if upto + weight >= roll:
            return item
        upto += weight
    return None


def generate_weapon_loot(mob_type):
    base_name = weighted_choice(MOB_WEAPON_PREFERENCES[mob_type])
    quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["weapon"])
    rarity = weighted_choice(RARITY)

    base = BASE_WEAPONS[base_name]
    name = base_name
    damages = [base["damage"]]
    attack = base["attack"]
    gold = base["value"]
    description = base["description"]
    stat_bonus = 0
    if rarity:
        choice = None
        for i in range(RARITY_BONUS[rarity]):
            if rarity in ["rare","epic","legendary"] and not choice in list(ITEM_MODIFIERS["weapons"]["double"]):
                if random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["single"]))
            elif rarity == "epic":
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                elif random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
            elif rarity in ["legendary"]:
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                elif random.uniform(0, 1) > 0.5:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
            if not choice:
                damages[0].damage += 1
                attack += 1
                stat_bonus += random.randint(0, 1)
                gold += random.randint(20, 50)
            if choice:
                for element_percent in choice["damage_bonus"].values():
                    element_percent += random.uniform(0, 0.01)
                attack += 1
                gold += random.randint(100, 200)

        if choice:
            name = f"{rarity} {str(choice.keys())} {name}"
            description = f"{description}\n{choice['description']}"
            for i in range(0,len(damages)):
                for e_type, damage_percent in choice["damage_bonus"].items():
                    new_element = Elements(e_type, damages[0]*damage_percent)
                    if damages[i] == new_element:
                        damages[i] += new_element
                        continue
                    elif i == len(damages)-1:
                        damages.append(new_element)
        else:
            name = f"{rarity} {name}"

    if quality_name:
        name = f"{quality_name} {name}"
        quality = WEAPON_QUALITIES[quality_name]
        damages[0].damage += quality["damage_mod"]
        attack += quality["attack_mod"]
        gold *= quality["gold_mod"]
    weapon = Weapon(name, gold, attack, damages, description=description)
    if stat_bonus:
        while stat_bonus:
            stat = random.choice(list(weapon.stat_bonuses.keys()))
            weapon.stat_bonuses[stat] += 1
            stat_bonus -= 1
    return weapon


def generate_armor_loot(mob_type,):
    base_name = weighted_choice(MOB_ARMOR_PREFERENCES[mob_type])
    quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["armor"])
    rarity = weighted_choice(RARITY)

    base = BASE_ARMOR[base_name]
    ac = base["AC"]
    name = base_name
    gold = base["value"]
    description = base["description"]
    stat_bonus = 0
    choice = None
    if rarity:
        for i in range(RARITY_BONUS[rarity]):
            if rarity in ["rare", "epic", "legendary"] and not choice in list(ITEM_MODIFIERS["armor"]["double"]):
                if random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["armor"]["single"]))
            elif rarity == "epic":
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["armor"]["double"]))
                elif random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["armor"]["double"]))
            elif rarity in ["legendary"]:
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["armor"]["double"]))
                elif random.uniform(0, 1) > 0.5:
                    choice = random.choice(list(ITEM_MODIFIERS["armor"]["double"]))
            if not choice:
                ac += 1
                stat_bonus += random.randint(1, 2)
                gold += random.randint(20, 50)
            if choice:
                resistances = choice["resistance_bonus"]
                for amount in resistances.values():
                    amount += random.uniform(0, 0.01)
                gold += random.randint(100, 200)


        else:
            name = f"{rarity} {name}"
    if quality_name:
        name = f"{quality_name} {name}"
        ac *= ARMOR_QUALITIES[quality_name]["mod"]
        gold *= ARMOR_QUALITIES[quality_name]["gold_mod"]
    armour = Armour(name,gold,ac)
    if choice:
        for e_type, resist in choice["resistance_bonus"].items():
            armour.resistances[e_type] += resist
    if stat_bonus:
        while stat_bonus:
            stat = random.choice(list(armour.stat_bonuses.keys()))
            armour.stat_bonuses[stat] += 1
            stat_bonus -= 1

    return armour


def generate_items_loot(mob_type):
    if mob_type != "player":
        base_name = weighted_choice(MOB_ITEM_PREFERENCES[mob_type])
        quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["items"])
    else:
        base_name = random.choice(list(BASE_ITEMS.keys()))
        quality_name = ""

    base = BASE_ITEMS[base_name]
    damage = base["damage"]
    name = base_name
    gold = base["value"]
    attack = 0
    if not "Healing" in base_name:
        attack = base["attack"]
    if quality_name:
        name = f"{quality_name} {name}"
        damage *= ITEM_QUALITY[quality_name]["mod"]
        gold *= ITEM_QUALITY[quality_name]["gold_mod"]
        if not "Healing" in base_name:
            attack += ITEM_QUALITY[quality_name]["mod"]
    if "Healing" in base_name:
        return Healing(name,damage,gold)
    distance = base["distance"]

    return Throwing(name, distance, gold, attack, damage)


def generate_enemy(level=1):
    base_name = weighted_choice(ENEMIES_WEIGHT[str(level)])
    rarity = weighted_choice(RARITY)
    i = 1
    enemy = None

    # Enemies that have a damage reduction stat (undead)
    UNDEAD = {"skeleton", "wraith", "vampire"}

    # Minimum level required for a rare variant of each enemy to spawn
    RARE_LEVEL_THRESHOLD = {
        "goblin":    3,
        "orc":       5,
        "skeleton":  7,
        "troll":     6,
        "wraith":    8,
        "dark mage": 8,
        "vampire":   9,
    }

    def make_entity(name, health, base_name):
        if base_name in UNDEAD:
            enemy = Entity(name, health, generate_armor_loot(base_name), generate_weapon_loot(base_name))
        else:
            enemy = Entity(name, health, generate_armor_loot(base_name), generate_weapon_loot(base_name))
        for stats in list(ENEMIES[base_name].keys())[1:]:
            enemy.stats[stats] = ENEMIES[base_name][stats]

        return enemy

    if rarity and level >= RARE_LEVEL_THRESHOLD[base_name]:
        enemy = make_entity(
            f"{rarity} {base_name}",
            ENEMIES[base_name]["health"] * RARITY_BONUS[rarity],
            base_name
        )
        while i <= RARITY_BONUS[rarity]:
            if random.uniform(0, 1) <= level * 0.1:
                enemy.add_to_inventory(generate_items_loot(base_name))
            for stat in list(ENEMIES[base_name].keys())[1:]:
                enemy.stats[stat] += random.randint(0,RARITY_BONUS[rarity])
            enemy.gold += random.randint(1, 9) + ENEMIES[base_name]["gold"]
            i += 1
        return enemy

    else:
        enemy = make_entity(base_name, ENEMIES[base_name]["health"], base_name)

    if random.uniform(0, 1) <= level * 0.1:
        enemy.add_to_inventory(generate_items_loot(base_name))
    enemy.gold = ENEMIES[base_name]["gold"]
    return enemy


def name_gen(gender=""):
    names = {
        "female": [
            "Aria", "Luna", "Aurora", "Celeste", "Seraphina",
            "Hazel", "Stella", "Rose", "Lyra", "Violet",
            "Ember", "Scarlett", "Ophelia", "Delilah", "Penelope",
            "Juniper", "Clementine", "Magnolia", "Everly", "Genevieve",
            "Ivy", "Willow", "Atla", "Iri", "Nova"
        ],
        "male": [
            "Orion", "Jasper", "Felix", "Leo", "Axel",
            "Dante", "Caspian", "Ezra", "Mile", "Asher",
            "Theo", "Finn", "Arlo", "Knox", "Ryder",
            "Atticus", "Jude", "Sila", "Phoenix", "Zephyr"
        ],
        "unisex": [
            "Sage", "River", "Kai", "Blake", "Zara",
            "Avery", "Quinn", "Reese", "Rowan", "Skylar",
            "Morgan", "Jordan", "Hayden", "Elliot", "Marlowe",
            "Finley", "Charlie", "Indigo", "Cypress", "Wren"
        ]
    }

    if gender is "non-binary" or gender is "":
        all_names = [name for group in names.values() for name in group]
        return random.choice(all_names)

    names_list = names[gender]
    names_list.extend(names["unisex"])
    return random.choice(names_list)
