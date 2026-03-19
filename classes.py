


class Item:
    def __init__(self,in_name: str, gold=0, description=""):
        self.name = in_name
        self.value = gold
        self.description = description

    def __repr__(self):
        return f"{self.name} (G: {self.value})\n{self.description}"

    def __eq__(self, other):
        if not isinstance(other, Item):
            return False
        return self.name == other.name and self.value == other.value

    def __hash__(self):
        return hash((self.name, self.value))

class Healing(Item):
    def __init__(self,in_name ,healing:int ,gold=0):
        super().__init__(in_name=in_name,gold=gold, description="")
        self.healing = healing

    def __repr__(self):
        return f"{self.name} (Healing: {self.healing})\n{self.description}"

    def __eq__(self, other):
        if not isinstance(other, Healing):
            return False
        return self.name == other.name and self.healing == other.healing

    def __hash__(self):
        return hash((self.name, self.healing))


class Weapon(Item):
    def __init__(self,in_name ="fists", gold= 0, attack=-1, damage=-1):
        super().__init__(in_name= in_name, gold= gold, description="")
        self.attack = attack
        self.damage = damage

    def __repr__(self):
        return f"{self.name} (DMG: {self.damage}, ATK: {self.attack}, G: {self.value})\n{self.description}"

    def __eq__(self, other):
        if not isinstance(other, Weapon):
            return False
        return self.name == other.name and self.damage == other.damage and self.attack == other.attack and self.value == other.value


    def __hash__(self):
        return hash((self.name, self.damage, self.attack))


class Throwing(Weapon):
    def __init__(self,in_name, distance: int,gold: int, attack=0, damage=0):
        super().__init__(in_name=in_name, gold = gold,attack=attack, damage=damage)
        self.distance = distance

    def __repr__(self):
        return f"{self.name} (Range: {self.distance}, DMG: {self.damage}, ATK: {self.attack}, G: {self.value})\n{self.description}"

    def __eq__(self, other):
        if not isinstance(other, Throwing):
            return False
        return self.name == other.name and self.damage == other.damage and self.distance == other.distance

    def __hash__(self):
        return hash((self.name, self.damage, self.attack ,self.distance))


class Armour(Item):
    def __init__(self, in_name="undergarments", gold=0, ac=-1):
        super().__init__(in_name=in_name, gold=gold, description="")
        self.AC = ac

    def __repr__(self):
        return f"{self.name} (AC: {self.AC}, G: {self.value})\n{self.description}"

    def __eq__(self, other):
        if not isinstance(other, Armour):
            return False
        return self.name == other.name and self.AC == other.AC and self.value == other.value

    def __hash__(self):
        return hash((self.name, self.AC, self.value))


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
