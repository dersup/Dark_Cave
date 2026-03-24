class Elements:
    def __init__(self,type_ ='physical',damage=-1):
        self.type = type_
        self.damage = damage

    def __repr__(self):
        return f"{self.type} (DMG: {self.damage})"

    def __eq__(self, other):
        if not isinstance(other, Elements):
            return False
        return self.type == other.type

    def __hash__(self):
        return hash((self.type, self.damage))

    def __add__(self, other):
        if not isinstance(other, Elements):
            raise TypeError
        if self.type != other.type:
            return [Elements(self.type, self.damage), Elements(other.type, other.damage)]
        return Elements(self.type, self.damage + other.damage)
    def __sub__(self, other):
        if not isinstance(other, Elements):
            raise TypeError
        if self.type != other.type:
            raise TypeError
        if self.damage < other.damage:
            return Elements(self.type, 0)
        return Elements(self.type, self.damage - other.damage)
    def __mul__(self, other):
        if not isinstance(other, Elements):
            raise TypeError
        if self.type != other.type:
            raise TypeError
        return Elements(self.type, self.damage * other.damage)
    def __truediv__(self, other):
        if not isinstance(other, Elements):
            raise TypeError
        if self.type != other.type:
            raise TypeError
        if other.damage == 0:
            raise ZeroDivisionError
        return Elements(self.type, self.damage // other.damage)
    def __floordiv__(self, other):
        if not isinstance(other, Elements):
            raise TypeError
        if self.type != other.type:
            raise TypeError
        if other.damage == 0:
            raise ZeroDivisionError
        return Elements(self.type, self.damage // other.damage)

class Item:
    def __init__(self, in_name: str, gold=0, description=""):
        self.name = in_name
        self.value = int(gold)
        self.description = description

    def _repr_stats(self):
        return f"G: {self.value}"

    def __repr__(self):
        return f"{self.name} ({self._repr_stats()}) {self.description}"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name and self.value == other.value

    def __hash__(self):
        return hash((self.name, self.value))


class Healing(Item):
    def __init__(self, in_name, healing:list, gold=0):
        super().__init__(in_name=in_name, gold=gold)
        self.healing = healing

    def _repr_stats(self):
        return f"Healing: {self.healing}"

    def __add__(self, other):
        if isinstance(other, int):
            total =0
            for element in self.healing:
                total += element.damage
            return other + total

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.name == other.name and self.healing == other.healing
    def __hash__(self):
        super().__hash__()
        return hash((self.name, tuple(self.healing) if isinstance(self.healing, list) else self.healing))

class Weapon(Item):
    def __init__(self,in_name ="fists", gold= 0, attack=-1, elements=[Elements(),],description=""):
        super().__init__(in_name= in_name, gold= gold, description=description)
        self.attack = attack
        self.elements = elements
        self.stat_bonuses =  {
			"attack": 0,
			"defence": 0,
			"luck": 0,
			"magic_defence": 0,
			"magic_attack": 0,
			"agility": 0,
			"exp":0
		}
        self.description = f"{self.elements}{str(self.stat_bonuses)} {self.description}"

    def __repr__(self):
        return f"{self.name} (DMG: {self.elements}, ATK: {self.attack}, G: {self.value}) {self.description}"

    def __eq__(self, other):
        if not isinstance(other, Weapon):
            return False
        return self.name == other.name and self.elements == other.elements and self.attack == other.attack and self.value == other.value


    def __hash__(self):
        return hash((self.name, self.attack))


class Throwing(Weapon):
    def __init__(self,in_name, distance: int, gold: int, elements: list, attack=0, description=""):
        super().__init__(in_name=in_name, gold = gold, attack=attack, elements=elements, description=description)
        self.distance = distance

    def __repr__(self):
        return f"{self.name} (Range: {self.distance}, {self.elements}, ATK: {self.attack}, G: {self.value}) {self.description}"

    def __eq__(self, other):
        if not isinstance(other, Throwing):
            return False
        return self.name == other.name and self.elements == other.elements and self.distance == other.distance

    def __hash__(self):
        return hash((self.name, self.attack ,self.distance))


class Armour(Item):
    def __init__(self, in_name="undergarments", gold=0,description=""):
        super().__init__(in_name=in_name, gold=gold, description=description)
        self.resistances = {
        "fire":      0.00,
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
        self.stat_bonuses = {
            "attack": 0,
            "defence": 0,
            "luck": 0,
            "magic_defence": 0,
            "magic_attack": 0,
            "agility": 0,
            "exp": 0
        }
        self.description = f"{str(self.resistances)} {str(self.stat_bonuses)} {self.description}"

    def __repr__(self):
        return f"{self.name} (G: {self.value} {self.description})"

    def __eq__(self, other):
        if not isinstance(other, Armour):
            return False
        return self.name == other.name and self.description == other.description and self.value == other.value

    def __hash__(self):
        return hash((self.name, self.value))


class Magic:
    def __init__(self,spell_name:str,elements:list, spell_description:str):
        self.spell_name = spell_name
        self.elements = elements
        self.spell_description = spell_description
    def __repr__(self):
        return f"{self.spell_name} ({self.elements}) {self.spell_description}"


class Inventory:
    def __init__(self):
        self.items = {
            "Equipped": [],
            "Armors": [],
            "Weapons": [],
            "Consumables": []
        }
    def length(self):
        total = []
        for items in self.items.values():
            total.extend(items)
        return len(total)

    def __repr__(self):
        lines = []
        for category, items in self.items.items():
            if not items:
                continue
            if category == "Equipped":
                lines.append(f"{category}\n")
            else:
                lines.append(f"-------------\n{category}\n")
            counts = {}
            for item_ in items:
                counts[item_] = counts.get(item_, 0) + 1
            for item_, count in counts.items():
                if count > 1:
                    lines.append(f"  {count}x {item_}")
                else:
                    lines.append(f"{item_}")
        return "\n".join(lines)
