import copy
from entity import *


def weighted_choice(weighted_dict):
    total = sum(weighted_dict.values())
    roll = random.uniform(0, total)

    upto = 0
    for item, weight in weighted_dict.items():
        if upto + weight >= roll:
            return item
        upto += weight
    return None


def generate_weapon_loot(mob_type,weapon_name=""):
    if mob_type == "player":
        rarity = ""
    else:
        rarity = weighted_choice(RARITY)
    base_name = weighted_choice(MOB_WEAPON_PREFERENCES[mob_type])
    if weapon_name:
        base_name = weapon_name
    quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["weapon"])

    base = copy.deepcopy(BASE_WEAPONS[base_name])
    name = base_name
    damages =[base["damage"]]
    attack = base["attack"]
    gold = base["value"]
    description = base["description"]
    stat_bonus = 0
    if rarity:
        choice = {}
        choice_name = ""
        for i in range(RARITY_BONUS[rarity]):
            if rarity in ["rare","epic","legendary"] and not choice in list(ITEM_MODIFIERS["weapons"]["double"]):
                if random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["single"]))
                    choice = ITEM_MODIFIERS["weapons"]["single"][choice]
            elif rarity == "epic":
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]
                elif random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]
            elif rarity in ["legendary"]:
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]
                elif random.uniform(0, 1) > 0.5:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]
            if not choice:
                damages[0].damage += 1
                attack += 1
                stat_bonus += random.randint(0, 1)
                gold += random.randint(20, 50)
            if choice and isinstance(choice, dict):
                choice_name = str(list(choice.keys())[0])
                for ele,percent in choice["damage_bonus"].items():
                    percent += random.uniform(0, 0.01)
                    choice["damage_bonus"][ele] = percent
                attack += 1
                gold += random.randint(100, 200)

        if choice:
            name = f"{name} {choice_name}"
            description = f"{description}\n{choice['description']}"
            for i in range(0,len(damages)):
                for e_type, damage_percent in choice["damage_bonus"].items():
                    new_element = Elements(e_type, damages[0].damage*damage_percent)
                    if damages[i] == new_element:
                        damages[i] += new_element
                        continue
                    elif i == len(damages)-1:
                        damages.append(new_element)
        name = f"{rarity} {name}"

    if quality_name:
        name = f"{quality_name} {name}"
        quality = WEAPON_QUALITIES[quality_name]
        for i in range(0,len(damages)):
            damages[i].damage = max(int(damages[i].damage * quality["damage_mod"]),1)
        attack += quality["attack_mod"]
        gold *= quality["gold_mod"]
    weapon = Weapon(name, gold, attack, damages, description=description)
    if stat_bonus:
        while stat_bonus:
            stat = random.choice(list(weapon.stat_bonuses.keys()))
            weapon.stat_bonuses[stat] += 1
            stat_bonus -= 1
    return weapon

def generate_staff(mob_type, staff_name=""):
    if mob_type == "player":
        rarity = ""
    else:
        rarity = weighted_choice(RARITY)

    # Pick base staff
    if staff_name:
        base_name = staff_name
    elif mob_type in MOB_STAFF_PREFERENCES:
        base_name = weighted_choice(MOB_STAFF_PREFERENCES[mob_type])
    else:
        base_name = weighted_choice(MOB_STAFF_PREFERENCES["player"])

    quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["staff"]) if mob_type in QUALITY_WEIGHT else ""

    base = copy.deepcopy(BASE_STAFFS[base_name])
    name = base_name
    damages = list(base.elements)
    attack = base.attack
    gold = base.value
    description = base.description
    stat_bonus = 0

    if rarity:
        choice = {}
        choice_name = ""
        for i in range(RARITY_BONUS[rarity]):
            if rarity in ["rare", "epic", "legendary"] and not choice in list(ITEM_MODIFIERS["weapons"]["double"]):
                if random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["single"]))
                    choice = ITEM_MODIFIERS["weapons"]["single"][choice]
            elif rarity == "epic":
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]
                elif random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]
            elif rarity == "legendary":
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]
                elif random.uniform(0, 1) > 0.5:
                    choice = random.choice(list(ITEM_MODIFIERS["weapons"]["double"]))
                    choice = ITEM_MODIFIERS["weapons"]["double"][choice]

            if not choice:
                damages[0].damage += 1
                attack += 1
                stat_bonus += random.randint(0, 1)
                gold += random.randint(20, 50)
            if choice and isinstance(choice, dict):
                choice_name = str(list(choice.keys())[0])
                for ele, percent in choice["damage_bonus"].items():
                    percent += random.uniform(0, 0.01)
                    choice["damage_bonus"][ele] = percent
                attack += 1
                gold += random.randint(100, 200)

        if choice:
            name = f"{name} {choice_name}"
            description = f"{description}\n{choice['description']}"
            for i in range(len(damages)):
                for e_type, damage_percent in choice["damage_bonus"].items():
                    new_element = Elements(e_type, damages[0].damage * damage_percent)
                    if damages[i] == new_element:
                        damages[i] += new_element
                        continue
                    elif i == len(damages) - 1:
                        damages.append(new_element)
        name = f"{rarity} {name}"

    # ── Quality modifier ──────────────────────────────────────────────────────
    if quality_name:
        name = f"{quality_name} {name}"
        quality = WEAPON_QUALITIES[quality_name]
        for i in range(len(damages)):
            damages[i].damage = max(int(damages[i].damage * quality["damage_mod"]), 1)
        attack += quality["attack_mod"]
        gold *= quality["gold_mod"]

    # ── Spell assignment ──────────────────────────────────────────────────────
    # Determine core element(s) of the staff for affinity weighting
    core_elements = {ele.type for ele in damages}

    # Build a weighted spell pool:
    #   - spells matching a core element  -> weight 10
    #   - all other spells                -> weight 1
    spell_pool = {}
    for spell_key, spell_obj in BASE_SPELLS.items():
        spell_elements = {ele.type for ele in spell_obj.elements}
        if spell_elements & core_elements:          # overlapping element
            spell_pool[spell_key] = 10
        else:
            spell_pool[spell_key] = 1

    # Number of spells scales with rarity
    num_spells = {
        "":          random.randint(1, 2),
        "rare":      random.randint(2, 3),
        "epic":      random.randint(3, 4),
        "legendary": random.randint(4, 6),
    }[rarity]

    chosen_spells = {}
    remaining_pool = dict(spell_pool)
    for _ in range(num_spells):
        if not remaining_pool:
            break
        picked_key = weighted_choice(remaining_pool)
        chosen_spells.update({picked_key:copy.deepcopy(BASE_SPELLS[picked_key])})
        del remaining_pool[picked_key]          # no duplicates

    # ── Assemble final Staff object ───────────────────────────────────────────
    staff = Staff(name, gold, attack, damages, spells=chosen_spells, description=description)

    if stat_bonus:
        while stat_bonus:
            stat = random.choice(list(staff.stat_bonuses.keys()))
            staff.stat_bonuses[stat] += 1
            stat_bonus -= 1

    return staff




def generate_armor_loot(mob_type,):
    if mob_type == "player":
        rarity = ""
    else:
        rarity = weighted_choice(RARITY)
    base_name = weighted_choice(MOB_ARMOR_PREFERENCES[mob_type])
    quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["armor"])

    base = copy.copy(BASE_ARMOR[base_name])
    ac = base["AC"]
    name = base_name
    gold = base["value"]
    description = base["description"]
    stat_bonus = 0
    choice = {}
    choice_name = ""
    if rarity:
        for i in range(RARITY_BONUS[rarity]):
            if rarity in ["rare", "epic", "legendary"] and not choice in list(ITEM_MODIFIERS["armour"]["double"]):
                if random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["armour"]["single"]))
                    choice = ITEM_MODIFIERS["armour"]["single"][choice]
            elif rarity == "epic":
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["armour"]["double"]))
                    choice = ITEM_MODIFIERS["armour"]["double"][choice]
                elif random.uniform(0, 1) > 0.2:
                    choice = random.choice(list(ITEM_MODIFIERS["armour"]["double"]))
                    choice = ITEM_MODIFIERS["armour"]["double"][choice]
            elif rarity in ["legendary"]:
                if choice:
                    choice = random.choice(list(ITEM_MODIFIERS["armour"]["double"]))
                    choice = ITEM_MODIFIERS["armour"]["double"][choice]
                elif random.uniform(0, 1) > 0.5:
                    choice = random.choice(list(ITEM_MODIFIERS["armour"]["double"]))
                    choice = ITEM_MODIFIERS["armour"]["double"][choice]
            if not choice:
                ac += 1
                stat_bonus += random.randint(1, 2)
                gold += random.randint(20, 50)
            if choice:
                choice_name = str(list(choice.keys())[0])
                for resistance, amount in choice["resistance_bonus"].items():
                    amount += random.uniform(0, 0.01)
                    choice["resistance_bonus"][resistance] = amount

                gold += random.randint(100, 200)
        if choice:
            name = f"{name} {choice_name}"

        name = f"{rarity} {name}"
    if quality_name:
        name = f"{quality_name} {name}"
        ac = round(ac * ARMOR_QUALITIES[quality_name]["mod"])
        gold *= ARMOR_QUALITIES[quality_name]["gold_mod"]
    armour = Armour(name, gold)
    if choice:
        for e_type, resist in choice["resistance_bonus"].items():
            armour.resistances[e_type] += resist
        description = f"{description}\n{choice['description']}"
    if stat_bonus:
        while stat_bonus:
            stat = random.choice(list(armour.stat_bonuses.keys()))
            armour.stat_bonuses[stat] += 1
            stat_bonus -= 1
    armour.stat_bonuses["defence"] = ac
    armour.description = description
    return armour


def generate_items_loot(mob_type):
    if mob_type != "player":
        base_name = weighted_choice(MOB_ITEM_PREFERENCES[mob_type])
        quality_name = weighted_choice(QUALITY_WEIGHT[mob_type]["items"])
    else:
        base_name = random.choice(list(BASE_ITEMS.keys()))
        quality_name = ""

    base = copy.deepcopy(BASE_ITEMS[base_name])
    damage = base["damage"]
    name = base_name
    gold = base["value"]
    attack = 0
    elements = []
    if not "Healing" in base_name:
        attack = base["attack"]
    if quality_name:
        name = f"{quality_name} {name}"
        for e_type,value in damage.items():
            value *= ITEM_QUALITY[quality_name]["mod"]
            damage[e_type] = value
        gold *= ITEM_QUALITY[quality_name]["gold_mod"]
        if not "Healing" in base_name:
            attack += ITEM_QUALITY[quality_name]["mod"]
    if "Healing" in base_name:
        for key, value in damage.items():
            elements.append(Elements(key, value))
        return Healing(name,elements,gold)
    distance = base["distance"]
    for key,value in damage.items():
        elements.append(Elements(key,value))

    return Throwing(name, distance, gold, elements,attack)


def generate_enemy(level=1):
    base_name = weighted_choice(ENEMIES_WEIGHT[str(level)])
    rarity = weighted_choice(RARITY)
    i = 1

    def make_entity(name, health, mana, base_name_):
        enemy_ = Entity(name, health, mana, generate_armor_loot(base_name_), generate_weapon_loot(base_name_))
        for stat_, val in list(ENEMIES[base_name_]["stats"].items())[1:-1]:
            enemy_.stats[stat_] = val
        for resist,val in ENEMIES[base_name_]["resistances"].items():
            enemy_.resistances[resist] = val
        return enemy_

    if rarity and level >= RARE_LEVEL_THRESHOLD[base_name]:
        enemy = make_entity(f"{rarity} {base_name}",
                            ENEMIES[base_name]["stats"]["health"] * RARITY_BONUS[rarity],
                            ENEMIES[base_name]["stats"]["mana"]* RARITY_BONUS[rarity],
                            base_name)
        while i <= RARITY_BONUS[rarity]:
            if random.uniform(0, 1) <= level * 0.1:
                enemy.add_to_inventory(generate_items_loot(base_name))
            for stat in list(ENEMIES[base_name]["stats"].keys())[2:]:
                enemy.stats[stat] += random.randint(0,3)
            enemy.gold += random.randint(1, 9) + ENEMIES[base_name]["stats"]["gold"]
            i += 1
        return enemy

    else:
        enemy = make_entity(base_name, ENEMIES[base_name]["stats"]["health"], ENEMIES[base_name]["stats"]["mana"], base_name)

    if random.uniform(0, 1) <= level * 0.1:
        enemy.add_to_inventory(generate_items_loot(base_name))
    enemy.gold = ENEMIES[base_name]["stats"]["gold"]
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

    if gender == "non-binary" or gender not in list(names.keys()):
        all_names = [name for group in names.values() for name in group]
        return random.choice(all_names)
    names_list = names[gender]
    names_list.extend(names["unisex"])
    return random.choice(names_list)