from entity import *

ENEMYS = {
    "goblin":    {"health": 20,  "attack": 5,  "defence": 10, "luck": 20, "magic_defence": 0,  "magic_attack": 0,  "agility": 0,  "exp": 10,  "gold": 1},
    "orc":       {"health": 50,  "attack": 12, "defence": 18, "luck": 5,  "magic_defence": 2,  "magic_attack": 0,  "agility": 3,  "exp": 25,  "gold": 3},
    "skeleton":  {"health": 60,  "attack": 8,  "defence": 25, "luck": 5,  "magic_defence": 15, "magic_attack": 0,  "agility": 0,  "exp": 30,  "gold": 10},
    "troll":     {"health": 90,  "attack": 18, "defence": 20, "luck": 3,  "magic_defence": 0,  "magic_attack": 0,  "agility": 0,  "exp": 50,  "gold": 5},
    "wraith":    {"health": 35,  "attack": 10, "defence": 5,  "luck": 10, "magic_defence": 30, "magic_attack": 20, "agility": 25, "exp": 55,  "gold": 15},
    "dark mage": {"health": 30,  "attack": 3,  "defence": 5,  "luck": 15, "magic_defence": 20, "magic_attack": 30, "agility": 5,  "exp": 60,  "gold": 20},
    "vampire":   {"health": 70,  "attack": 20, "defence": 15, "luck": 20, "magic_defence": 25, "magic_attack": 15, "agility": 20, "exp": 80,  "gold": 25},
}

ENEMYS_WEIGHT = {
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
    "dagger": {"damage": 2, "attack": 4, "value": 40},
    "short sword": {"damage": 3, "attack": 3, "value": 60},
    "long sword": {"damage": 4, "attack": 2, "value": 80},
    "spear": {"damage": 4, "attack": 2, "value": 100},
    "club": {"damage": 5, "attack": 1, "value": 50},
    "axe": {"damage": 6, "attack": 0, "value": 70},
}

BASE_ARMOR = {
    "cloth": {"AC":1,"value":30},
    "leather jerkin": {"AC":2,"value":60},
    "hide armor": {"AC":3,"value":120},
    "chain shirt": {"AC":4,"value":240},
    "scale mail": {"AC":5,"value":480},
    "half plate": {"AC":6,"value":960},
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
    damage = base["damage"]
    attack = base["attack"]
    gold = base["value"]
    if rarity:
        name = f"{rarity} {name}"
        damage += RARITY_BONUS[rarity]
        attack += RARITY_BONUS[rarity]
        gold *= RARITY_BONUS[rarity] or 1
    if quality_name:
        name = f"{quality_name} {name}"
        quality = WEAPON_QUALITIES[quality_name]
        damage += quality["damage_mod"]
        attack += quality["attack_mod"]
        gold *= quality["gold_mod"]
    return Weapon(name, gold, damage, attack)


def generate_armor_loot(mob_type,):
    base_name = weighted_choice(MOB_ARMOR_PREFERENCES[mob_type])
    quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["armor"])
    rarity = weighted_choice(RARITY)

    base = BASE_ARMOR[base_name]
    ac = base["AC"]
    name = base_name
    gold = base["value"]
    if rarity:
        name = f"{rarity} {name}"
        ac += RARITY_BONUS[rarity]
        gold *= RARITY_BONUS[rarity] or 1
    if quality_name:
        name = f"{quality_name} {name}"
        ac *= ARMOR_QUALITIES[quality_name]["mod"]
        gold *= ARMOR_QUALITIES[quality_name]["gold_mod"]

    return Armour(name, gold, ac)


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
    base_name = weighted_choice(ENEMYS_WEIGHT[str(level)])
    rarity = weighted_choice(RARITY)
    i = 1
    enemy = None
    if rarity and level >= 3:
        if base_name == "goblin":
            enemy = Entity(f"{rarity} {base_name}", ENEMYS[base_name]["health"] * RARITY_BONUS[rarity], generate_armor_loot(base_name), generate_weapon_loot(base_name))
        if level >= 5:
            if base_name == "orc":
                enemy = Entity(f"{rarity} {base_name}", ENEMYS[base_name]["health"] * RARITY_BONUS[rarity], generate_armor_loot(base_name), generate_weapon_loot(base_name))
        if level >= 7:
            if base_name == "skeleton":
                enemy = Entity(f"{rarity} {base_name}", ENEMYS[base_name]["health"] * RARITY_BONUS[rarity], generate_armor_loot(base_name), generate_weapon_loot(base_name), random.randint(3, 8) * RARITY_BONUS[rarity])
        while RARITY_BONUS[rarity] >= i:
            if random.uniform(0, 1) <= level*0.1:
                enemy.add_to_inventory(generate_items_loot(base_name))
            enemy.gold += random.randint(1, 9) + ENEMYS[base_name]["gold"]
            i += 1
        return enemy

    else:
        if base_name == "skeleton":
            enemy = Entity(base_name, ENEMYS[base_name]["health"], generate_armor_loot(base_name), generate_weapon_loot(base_name), random.randint(3, 8))
        else:
            enemy = Entity(base_name, ENEMYS[base_name]["health"], generate_armor_loot(base_name), generate_weapon_loot(base_name))

    if random.uniform(0, 1) <= level * 0.1:
        enemy.add_to_inventory(generate_items_loot(base_name))
    enemy.gold = ENEMYS[base_name]["gold"]
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
