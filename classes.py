class Elements:
    def __init__(self, type_='physical', damage=-1):
        self.type   = type_
        self.damage = damage

    def __repr__(self):  return f"{self.type} (DMG: {self.damage})"
    def __eq__(self, other):
        return isinstance(other, Elements) and self.type == other.type
    def __hash__(self):  return hash((self.type, self.damage))

    def _check(self, other):
        if not isinstance(other, Elements): raise TypeError
        if self.type != other.type:         raise TypeError

    def __add__(self, other):
        if not isinstance(other, Elements): raise TypeError
        if self.type != other.type:
            return [Elements(self.type, self.damage), Elements(other.type, other.damage)]
        return Elements(self.type, self.damage + other.damage)

    def __sub__(self, other):
        self._check(other)
        return Elements(self.type, max(0, self.damage - other.damage))

    def __mul__(self, other):
        self._check(other)
        return Elements(self.type, self.damage * other.damage)

    def __truediv__(self, other):
        self._check(other)
        if other.damage == 0: raise ZeroDivisionError
        return Elements(self.type, self.damage // other.damage)

    __floordiv__ = __truediv__


# ---------------------------------------------------------------------------
# Shared default dicts (avoids repeating them in every class)
# ---------------------------------------------------------------------------
def _default_stats():
    return {"attack": 0, "defence": 0, "luck": 0,
            "magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 0}

def _default_resistances():
    return {k: 0.00 for k in (
        "fire", "ice", "lightning", "water", "earth",
        "wind", "light", "dark", "poison", "physical"
    )}


class Item:
    def __init__(self, in_name: str, gold=0, description=""):
        self.name        = in_name
        self.value       = int(gold)
        self.description = description

    def _repr_stats(self):  return f"(G: {self.value})"
    def __repr__(self):     return f"({self.name}) ({self._repr_stats()}) ({self.description})"

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.name == other.name and self.value == other.value

    def __hash__(self):     return hash((self.name, self.value))


class Healing(Item):
    def __init__(self, in_name, healing: list, gold=0):
        super().__init__(in_name=in_name, gold=gold)
        self.healing = healing

    def _repr_stats(self):  return f"Healing: ({self.healing})"

    def __add__(self, other):
        if not isinstance(other, int): raise TypeError
        return other + sum(e.damage for e in self.healing)

    def __eq__(self, other):
        return isinstance(other, self.__class__) \
               and self.name == other.name and self.healing == other.healing

    def __hash__(self):
        return hash((self.name,
                     tuple(self.healing) if isinstance(self.healing, list) else self.healing))


class Weapon(Item):
    def __init__(self, in_name="fists", gold=0, attack=-1,
                 elements=None, description=""):
        super().__init__(in_name=in_name, gold=gold, description=description)
        self.attack       = attack
        self.elements     = elements if elements is not None else [Elements()]
        self.stat_bonuses = _default_stats()
        self.description  = f"({self.elements})({self.stat_bonuses}) ({self.description})"

    def __repr__(self):
        return (f"{self.name} (DMG: ({self.elements}), ATK: ({self.attack}), "
                f"(G: ({self.value})) ({self.description})")

    def __eq__(self, other):
        return (isinstance(other, Weapon)
                and self.name == other.name
                and self.elements == other.elements
                and self.attack == other.attack
                and self.value == other.value)

    def __hash__(self):  return hash((self.name, self.attack))


class Staff(Weapon):
    def __init__(self, in_name, gold=0, attack=-1, elements=None,
                 spells=None, description=""):
        super().__init__(in_name=in_name, gold=gold, attack=attack,
                         elements=elements, description=description)
        self.spells = spells or {}

    def __repr__(self):
        spell_names = ", ".join(s for s in list(self.spells.keys()))
        return (f"{self.name} (DMG: ({self.elements}) ATK: ({self.attack}) "
                f"(G: ({self.value})) Spells: ({spell_names}) ({self.description})")

    def __eq__(self, other):
        return isinstance(other, Staff) and self.name == other.name and self.spells == other.spells

    def __hash__(self):  return hash((self.name, self.attack, tuple(self.spells.keys())))


class Throwing(Weapon):
    def __init__(self, in_name, distance: int, gold: int,
                 elements: list, attack=0, description=""):
        super().__init__(in_name=in_name, gold=gold, attack=attack,
                         elements=elements, description=description)
        self.distance = distance

    def __repr__(self):
        return (f"{self.name} (Range: ({self.distance}), ({self.elements}), "
                f"ATK: ({self.attack}), (G: ({self.value})) {self.description}")

    def __eq__(self, other):
        return (isinstance(other, Throwing)
                and self.name == other.name
                and self.elements == other.elements
                and self.distance == other.distance)

    def __hash__(self):  return hash((self.name, self.attack, self.distance))


class Armour(Item):
    def __init__(self, in_name="undergarments", gold=0, description=""):
        super().__init__(in_name=in_name, gold=gold, description=description)
        self.resistances  = _default_resistances()
        self.stat_bonuses = _default_stats()
        self.description  = f"({self.resistances}) ({self.stat_bonuses}) ({self.description})"

    def __repr__(self):
        return f"{self.name} (G: ({self.value})) ({self.description})"

    def __eq__(self, other):
        return (isinstance(other, Armour)
                and self.name == other.name
                and self.description == other.description
                and self.value == other.value)

    def __hash__(self):  return hash((self.name, self.value))


class Magic:
    def __init__(self, name: str, elements: list, spell_description: str,
                 cost=10, distance=1):
        self.name        = name
        self.elements          = elements
        self.spell_description = spell_description
        self.cost              = cost
        self.distance          = distance

    def __repr__(self):
        return (f"{self.name} ({self.elements}) "
                f"MP:({self.cost}) Range:({self.distance}) — ({self.spell_description})")

    def __eq__(self, other):
        if isinstance(other, Magic) and self.name == other.name:
            return True
        elif isinstance(other, str) and self.name.lower() == other.lower():
            return True
        return False
    def __hash__(self):       return hash(self.name)


class Inventory:
    def __init__(self):
        self.items = {"Equipped": [], "Armors": [], "Weapons": [], "Consumables": []}

    def length(self):
        return sum(len(v) for v in self.items.values())

    def __repr__(self):
        lines = []
        for category, items in self.items.items():
            if not items:
                continue
            header = f"{category}\n" if category == "Equipped" else f"-------------\n{category}\n"
            lines.append(header)
            counts = {}
            for item_ in items:
                counts[item_] = counts.get(item_, 0) + 1
            for item_, count in counts.items():
                lines.append(f"  {count}x {item_}" if count > 1 else f"{item_}")
        return "\n".join(lines)