import random
import re
import asyncio

from classes import *
from constants import *


def inspect(target):
	class_name = type(target).__name__
	allowed    = INSPECT_WHITELIST.get(class_name, [])
	lines = [
		f"\n  {k}: {v}" for k, v in vars(target).items()
		if k in allowed and v
		and not (isinstance(v, Inventory) and v.length() == 0)
	]
	return f"\n=== {class_name} ===" + "\n".join(lines) if lines else "Nothing found"


def next_cell(row, col, direction):
	offsets = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
	dr, dc  = offsets.get(direction, (0, 0))
	return row + dr, col + dc

def get_neighbors(maze, row, col):
	neighbors = []
	cell = maze.cells[row][col]

	directions = {
		"up":    (-1, 0, "top"),
		"down":  (1, 0, "bottom"),
		"left":  (0, -1, "left"),
		"right": (0, 1, "right"),
	}

	for d, (dr, dc, wall) in directions.items():
		if not getattr(cell, wall):  # no wall -> can move
			nr, nc = row + dr, col + dc
			if 0 <= nr < maze.num_rows and 0 <= nc < maze.num_cols:
				neighbors.append((nr, nc))

	return neighbors


class Entity:
	def __init__(self, name, max_health, max_mana, armor_=Armour(), weapon_=Weapon()):
		self.name       = name
		self.max_health = max_health
		self.health     = max_health
		self.max_mana   = max_mana
		self.mana       = max_mana
		self.stats = {
			"attack": 0, "defence": 0, "luck": 0,
			"magic_defence": 0, "magic_attack": 0, "agility": 0, "exp": 0,
		}
		self.resistances = {k: 0.00 for k in (
			"fire", "ice", "lightning", "water", "earth",
			"wind", "light", "dark", "poison", "physical",
		)}
		self.level    = 1
		self.armor    = None
		self.weapon   = None
		self.inventory = Inventory()
		self.gold     = 0
		self.kills    = 0
		self.location = None
		self.facing   = None
		self.is_player = False
		self.id_      = None
		self.visible_cells = set()

		self.add_items_to_inventory([armor_, weapon_])
		self.use_item(self.inventory.items["Armors"][0].name)
		self.use_item(self.inventory.items["Weapons"][0].name)

	# -- Combat ----------------------------------------------------------------

	def cast_spell(self, spell, maze):
		if not isinstance(self.weapon, Staff):
			return "You don't have a Staff."
		spells = self.get_spells()
		spell = spells.get(spell.lower().strip("\'"), None)
		if not spell:
			return "You don't have that spell equipped."
		if self.mana < spell.cost:
			return f"Not enough mana to cast {spell.name}!"
		self.mana -= spell.cost
		return f"You cast {spell.name}" + self.throw(spell, maze)

	def take_damage(self, elements: list, extra_dam=0, mod=1.0) -> dict:
		total  = {}
		damage = random.randint(1, 6)
		for element in elements:
			if element is elements[0]:
				damage += extra_dam
			damage = max(
				int(mod * ((damage + element.damage) -
						   (damage + element.damage) * self.resistances[element.type])),
				0,
			)
			total[element.type] = damage
			self.health -= damage
			if self.health <= 0:
				break
		return total

	def attack_target(self, enemy, weapon_, maze):
		if not weapon_:
			return "You have no weapon."

		def _killed(attacker, dead):
			attacker.kills      += 1
			attacker.stats["exp"] += dead.stats["exp"]
			dead.give_inventory(maze.cells[dead.location.location[0]][dead.location.location[1]])
			dead_name = dead.name
			dy,dx = dead.location.location
			if attacker.stats["exp"] >= 75 * attacker.level and not getattr(attacker, '_leveling_up', False):
				attacker.stats["exp"] = 0
				attacker.level       += 1
				attacker._leveling_up = True
				asyncio.ensure_future(maze.level_up(attacker))
			# Trigger death animation on dead entity's sprite (one-shot)
			if hasattr(dead, '_sprite') and dead._sprite is not None:
				dead._sprite.set_state("die", one_shot=True)
			maze.cells[dy][dx].remove_enemy()
			return f"{dead_name} has been slain"

		# Trigger attack animation on the attacker
		if hasattr(self, '_sprite') and self._sprite is not None:
			self._sprite.set_state("attack", one_shot=True)

		roll  = random.randint(1, 20)
		roll += int(self.stats["luck"] * 0.2)
		if isinstance(weapon_, Magic):
			roll += int(self.stats["magic_attack"])
			attack_total = roll + self.get_equipped_staff().attack
			e_defence = int(enemy.stats["magic_defence"])

		else:
			roll += int(self.stats["attack"])
			attack_total = roll + self.weapon.attack
			e_defence = int(enemy.stats["defence"])
		dam_taken = enemy.take_damage(weapon_.elements)
		if isinstance(weapon_, Throwing) and "bomb" in weapon_.name:
			dam_taken = enemy.take_damage(weapon_.elements) if roll > 10 \
				else enemy.take_damage(weapon_.elements, 0.5)
		elif attack_total < 10 + e_defence:
			return f"{self.name} misses {enemy.name}."

		if not dam_taken:
			return f"{enemy.name} took no damage"

		# Trigger damage animation on the target (if still alive and has a sprite)
		if enemy.health > 0 and hasattr(enemy, '_sprite') and enemy._sprite is not None:
			enemy._sprite.set_state("dmg", one_shot=True)

		parts   = list(dam_taken.items())
		message = f"{self.name} hits {enemy.name} with {weapon_.name} for "
		for i, (ele, dam) in enumerate(parts):
			if i > 0:
				message += " and " if i == len(parts) - 1 else ", "
			message += f"{dam} {ele}"
		message += " damage"

		return _killed(self, enemy) if enemy.health <= 0 else message

	def get_equipped_staff(self):
		return next((i for i in self.inventory.items["Equipped"] if isinstance(i, Staff)), None)

	def get_spells(self):
		staff = self.get_equipped_staff()
		return staff.spells if staff else {}

	# -- Inventory -------------------------------------------------------------

	def _category(self, item_):
		if isinstance(item_, Weapon): return "Weapons"
		if isinstance(item_, Armour): return "Armors"
		return "Consumables"

	def add_to_inventory(self, item_):
		key = self._category(item_)
		self.inventory.items[key].append(item_)
		return f"{item_} added to inventory"

	def add_items_to_inventory(self, items):
		return "\n".join(self.add_to_inventory(i) for i in items)

	def remove_item(self, item_):
		key = self._category(item_)
		try:
			self.inventory.items[key].remove(item_)
		except ValueError:
			return "item not in inventory"
		return f"{item_} removed"

	def remove_inventory(self):
		self.inventory = Inventory()

	def give_inventory(self, target):
		for items in self.inventory.items.values():
			if items:
				target.add_items_to_inventory(items)
		target.gold += self.gold
		self.remove_inventory()

	def give_items(self, target, items):
		target.add_items_to_inventory(items)
		for item in items:
			self.remove_item(item)

	def get_cell_inventory(self, target):
		messages = []
		for category, items in target.inventory.items.items():
			if items and category != "Equipped":
				self.add_items_to_inventory(items)
				for item in items:
					messages.append(f"adding {item.name} to inventory")
		gold_msg = ""
		if target.gold > 0:
			self.gold  += target.gold
			gold_msg    = f"adding gold: {target.gold}"
		target.remove_inventory()
		target.gold = 0
		return (messages or ["no items to be found"]), gold_msg

	# -- Panels (inventory / spell_list) ---------------------------------------

	def show_panel(self, win, panel: str):
		"""Toggle a named panel and populate it. panel: 'inventory' | 'spell_list'"""
		setters = {"inventory": win.set_inventory, "spell_list": win.set_spell_list}
		if panel not in setters:
			return
		flag = f"{panel}_show"
		new_state = not getattr(win, flag)
		setattr(win, flag, new_state)
		if new_state:
			setters[panel](self)

	# Convenience shorthands
	def show_inventory(self, win):  self.show_panel(win, "inventory")
	def show_spell_list(self, win): self.show_panel(win, "spell_list")

	# -- Item usage ------------------------------------------------------------

	def use_item(self, item_name, maze=None):
		item_name = re.sub(r'^\d+x\s*', '', item_name).strip()
		for category, items in self.inventory.items.items():
			for item_ in items:
				if item_.name.lower() != item_name.lower():
					continue
				if isinstance(item_, Healing):
					self.health = min(self.max_health, self.health + item_.healing[0].damage)
					self.remove_item(item_)
					return f"{self.name} heals to {self.health}/{self.max_health}"
				if isinstance(item_, Throwing):
					msg = ""
					if "bomb" in item_.name.lower():
						if not maze:
							return "you need to see where you're throwing"
						msg = self.throw(item_, maze)
					self.remove_item(item_)
					return msg
				if isinstance(item_, Weapon):
					return self.equip_weapon(item_)
				if isinstance(item_, Armour):
					return self.equip_armor(item_)
		return "Item not found."

	def equip_weapon(self, weapon_):
		if isinstance(self.weapon,Weapon):
			self.unequip_weapon()
		self.inventory.items["Equipped"].append(weapon_)
		for stat, val in weapon_.stat_bonuses.items():
			self.stats[stat] += val
		self.weapon = weapon_
		self.remove_item(weapon_)
		return f"{weapon_} was equipped."

	def unequip_weapon(self):
		for item in list(self.inventory.items["Equipped"]):
			if isinstance(item, Weapon):
				self.add_to_inventory(item)
				for stat, val in item.stat_bonuses.items():
					self.stats[stat] -= val
				self.inventory.items["Equipped"].remove(item)
				self.weapon = None
				return

	def equip_armor(self, armor_):
		if isinstance(self.armor, Armour) :
			self.unequip_armor()
		self.inventory.items["Equipped"].append(armor_)
		for stat, val in armor_.stat_bonuses.items():
			self.stats[stat] += val
		for resist, val in armor_.resistances.items():
			self.resistances[resist] += val
		self.armor = armor_
		self.remove_item(armor_)
		return f"{armor_} was equipped."

	def unequip_armor(self):
		for item in list(self.inventory.items["Equipped"]):
			if isinstance(item, Armour):
				self.add_to_inventory(item)
				for stat, val in item.stat_bonuses.items():
					self.stats[stat] -= val
				for resist, val in item.resistances.items():
					self.resistances[resist] -= val
				self.inventory.items["Equipped"].remove(item)
				self.armor = None
				return

	# -- Throw / projectile ----------------------------------------------------

	def throw(self, item, maze):
		row, col = self.location.location
		for _ in range(item.distance):
			curr = maze.cells[row][col]
			if curr.enemy_entity:
				return self.attack_target(curr.enemy_entity, item, maze)
			if curr.can_move(self.facing, maze) == "move":
				row, col = next_cell(row, col, self.facing)
				if not (0 <= row <= maze.num_rows - 1 and 0 <= col <= maze.num_cols - 1):
					return (f"{item.name} disappears!" if isinstance(item, Magic)
							else f"you tossed {item.name} outside")
			elif "bomb" in item.name.lower():
				nr, nc = next_cell(row, col, self.facing)
				# Knock the wall down
				wall_pairs = {
					"up":    ("top",    "bottom"),
					"down":  ("bottom", "top"),
					"left":  ("left",   "right"),
					"right": ("right",  "left"),
				}
				w_self, w_other = wall_pairs[self.facing]
				setattr(maze.cells[row][col], w_self,  False)
				setattr(maze.cells[nr][nc],   w_other, False)
				if curr is self.location:
					for el in item.elements:
						el.damage = int(el.damage * 0.5)
					return str(self.take_damage(item.elements))
				other = maze.cells[nr][nc]
				msg   = ""
				if other.enemy_entity:
					for el in item.elements:
						el.damage = int(el.damage * 0.5)
					msg = str(other.enemy_entity.take_damage(item.elements))
				return msg + "\nthe wall collapses!"
			else:
				row, col = next_cell(row, col, self.facing)
		return f"{item.name} dissipates" if isinstance(item, Magic) else f"{item.name} hits the ground"

	# -- Movement --------------------------------------------------------------

	def move(self, direction, maze, on_complete=None):
		self.mana = min(self.mana+2 ,self.max_mana)
		def _done():
			if on_complete: on_complete()

		if not direction:
			_done(); return ""

		row_old, col_old = self.location.location
		movement = maze.cells[row_old][col_old].can_move(direction, maze)

		if movement == "bump":
			_done(); return "You bump into a wall."
		if movement != "move":
			if "continue" in movement and not getattr(maze, '_transitioning', False):
				maze._transitioning = True
				asyncio.ensure_future(maze.next_level(self))
			_done(); return movement

		row, col = next_cell(row_old, col_old, direction)
		if 0 <= row < maze.num_rows and 0 <= col < maze.num_cols:
			target = maze.cells[row][col]
			if target.enemy:
				self.facing = direction
				result = self.attack_target(target.enemy_entity, self.weapon, maze)
				_done(); return result
			maze.cells[row_old][col_old].ani_move(target, duration=200, on_complete=on_complete)
			maze.cells[row_old][col_old].remove_player()
			target.set_player(self)
			self.location = target
			self.facing   = direction

	# -- Enemy AI --------------------------------------------------------------
	def bfs_path(self, maze, start, goal):
		from collections import deque
		queue = deque([start])
		came_from = {start: None}
		while queue:
			current = queue.popleft()
			if current == goal:
				break
			for neighbor in get_neighbors(maze, *current):
				if neighbor not in came_from:
					queue.append(neighbor)
					came_from[neighbor] = current
		if goal not in came_from:
			return None
		path = []
		curr = goal
		while curr:
			path.append(curr)
			curr = came_from[curr]
		path.reverse()
		return path


	def enemy_turn(self, player, maze, on_complete=None):
		message = ""
		def _done():
			if on_complete: on_complete()

		def direction_from_to(a, b):
			ay, ax = a
			by, bx = b

			if by == ay - 1: return "up"
			if by == ay + 1: return "down"
			if bx == ax - 1: return "left"
			if bx == ax + 1: return "right"
			return None
		if "troll" in self.name.lower():
			self.health = min(10 + self.health,self.max_health)

		if not self.location:
			_done(); return None,None
		my_row, my_col = self.location.location

		if self.health <= 0:
			self.give_inventory(maze.cells[my_row][my_col])
			maze.cells[my_row][my_col].remove_enemy()
			return None,None

		p_row, p_col = player.location.location
		dist_r = my_row - p_row
		dist_c = my_col - p_col

		# Adjacent -> try to attack through an open wall
		if abs(dist_c) + abs(dist_r) == 1:
			attack_conds = [
				(dist_c == -1, "right"),  # player is to the right
				(dist_c == 1, "left"),  # player is to the left
				(dist_r == 1, "top"),  # player is above
				(dist_r == -1, "bottom"),  # player is below
			]
			for cond, wall in attack_conds:
				if cond and not getattr(self.location, wall):
					# also verify the player's side wall is open
					opposite = {"right": "left", "left": "right", "top": "bottom", "bottom": "top"}
					if not getattr(player.location, opposite[wall]):
						message = self.attack_target(player, self.weapon, maze)
						_done();
						return self.location,message
		path = None
		for (y,x) in self.visible_cells:
			if maze.cells[y][x].player_entity:
				path = self.bfs_path(maze, (my_row, my_col), (p_row, p_col))
				break

		if path:
			next_step = path[1]
			direction = direction_from_to((my_row,my_col), next_step)
			self.facing = direction
			row, col = next_cell(my_row, my_col, direction)
		else:
			dirs = [d for d in ("up", "down", "left", "right")
			        if self.location.can_move(d, maze, is_enemy=True) != "bump"]
			if not dirs:
				_done();
				return self.location,None
			direction = random.choice(dirs)
			row, col = next_cell(my_row, my_col, direction)
		if 0 <= row < maze.num_rows and 0 <= col < maze.num_cols:
			maze.cells[my_row][my_col].ani_move(maze.cells[row][col], duration=200,
												 on_complete=on_complete)
			maze.cells[my_row][my_col].remove_enemy()
			maze.cells[row][col].set_enemy(self)
			self.location = maze.cells[row][col]
			_done(); return self.location,None