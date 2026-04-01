import random
import re
from classes import *
from constants import *


def inspect(target):
	attrs = vars(target)
	class_name = type(target).__name__
	allowed = INSPECT_WHITELIST.get(class_name, [])
	print(f"\n=== {class_name} ===")
	for key, value in attrs.items():
		if key in allowed:
			print(f"  {key}: {value}")


def next_cell(row, col, direction):
	if direction == "up":
		row -= 1
	elif direction == "down":
		row += 1
	elif direction == "left":
		col -= 1
	elif direction == "right":
		col += 1
	return row, col


class Entity:
	def __init__(self, name, max_health, armor_=Armour(), weapon_=Weapon()):
		self.name = name
		self.max_health = max_health
		self.health = max_health
		self.stats = {
			"attack": 0,
			"defence": 0,
			"luck": 0,
			"magic_defence": 0,
			"magic_attack": 0,
			"agility": 0,
			"exp":0
		}
		self.resistances = {
			"fire": 0.00,
			"ice": 0.00,
			"lightning": 0.00,
			"water": 0.00,
			"earth": 0.00,
			"wind": 0.00,
			"light": 0.00,
			"dark": 0.00,
			"poison": 0.00,
			"physical": 0.00,
		}
		self.level = 1
		self.armor = None
		self.weapon = None
		self.inventory = Inventory()
		self.gold = 0
		self.kills = 0
		self.location = None
		self.facing = None
		self.is_player = False
		self.id_ = None
		self.add_items_to_inventory([armor_, weapon_])
		self.use_item(self.inventory.items["Armors"][0].name)
		self.use_item(self.inventory.items["Weapons"][0].name)

	# ------------------------
	# Combat
	# ------------------------

	def take_damage(self, elements:list,extra_dam=0,mod=1.0)-> dict:
		total = {}
		damage = random.randint(1,6)
		for element in elements:
			if element == elements[0]:
				damage += extra_dam
			damage = max((damage + element.damage) - (damage + element.damage * self.resistances[element.type]),0)
			damage = int(mod * damage)
			total[element.type] = damage
			self.health -= damage
			if self.health <= 0:
				break
		return total

	def attack_target(self, enemy, weapon_,maze):
		def killed(attacker,dead):
			attacker.kills += 1
			attacker.stats["exp"] += dead.stats["exp"]
			enemy.give_inventory(maze.cells[enemy.location.location[0]][enemy.location.location[1]])
			def level_check():
				if attacker.stats["exp"] >= 75 * attacker.level:
					attacker.stats["exp"] = 0
					attacker.level += 1
					maze.level_up(attacker)
			level_check()

		if not weapon_:
			print("You have no weapon.")
			return
		dam_taken = {}

		roll = random.randint(1, 20)
		roll += int(self.stats["luck"]*0.2)
		roll += int(self.stats["attack"] // 4)
		if isinstance(weapon_, Throwing):
			if "bomb" in weapon_.name:
				if roll > 10:
					dam_taken = enemy.take_damage(weapon_.elements)
				else:
					dam_taken = enemy.take_damage(weapon_.elements,0.5)
		else:
			attack_total = roll + weapon_.attack

			enemy_ac = 10 + enemy.stats["defence"]

			if attack_total >= enemy_ac:
				dam_taken = enemy.take_damage(weapon_.elements,extra_dam=self.stats["attack"])
			else:
				print(f"{self.name} misses {enemy.name}.")
				return
		if dam_taken:
			print(f"{self.name} hits {enemy.name} with {weapon_.name} for ",end='')
			for ele,dam in dam_taken.items():
				if len(list(dam_taken.keys())) >= 3:
					if ele == list(dam_taken.keys())[-1]:
						print(f"and {dam} {ele}")
						break
					else:
						print(f"{dam} {ele} damage",end=",")
						continue
				elif len(list(dam_taken.keys())) == 2:
					if ele == list(dam_taken.keys())[0]:
						print(f"{dam} {ele}",end=" and ")
				print(f"{dam} {ele} damage")
			if enemy.health <= 0:
				killed(self,enemy)
		else:
			print(f"{enemy.name} took no damage")

	# ------------------------
	# Inventory
	# ------------------------

	def remove_inventory(self):
		self.inventory = Inventory()

	def remove_item(self, item_):
		if isinstance(item_, Weapon):
			self.inventory.items["Weapons"].remove(item_)
		elif isinstance(item_, Armour):
			self.inventory.items["Armors"].remove(item_)
		elif isinstance(item_, Item):
			self.inventory.items["Consumables"].remove(item_)
		else:
			print("item not in inventory")

	def add_to_inventory(self, item_):
		key = "Weapons" if isinstance(item_, Weapon) else "Armors" if isinstance(item_, Armour) else "Consumables"
		if not key:
			print(f"not able to put {item_} in inventory")
			return
		else:
			self.inventory.items[key].append(item_)

	def add_items_to_inventory(self, items):
		if len(items) == 1:
			self.add_to_inventory(items[0])
			return
		else:
			for item in items:
				self.add_to_inventory(item)

	def get_cell_inventory(self,target):
		for category in list(target.inventory.items.keys()):
			if target.inventory.items[category] and category != "Equipped":
				self.add_items_to_inventory(target.inventory.items[category])
				print(f"adding{target.inventory.items[category]} to inventory")
		self.gold += target.gold
		print(f"adding gold: {target.gold}")
		target.remove_inventory()
		target.gold = 0


	def give_inventory(self, target):
		for category in self.inventory.items.keys():
			if self.inventory.items[category]:
				target.add_items_to_inventory(self.inventory.items[category])
		target.gold += self.gold
		self.remove_inventory()

	def give_items(self, target, items):
		target.add_items_to_inventory(items)
		for item in items:
			self.remove_item(item)

	def show_inventory(self, win):
		win.inventory_show = not win.inventory_show
		if win.inventory_show:
			win.set_inventory(self)

	# ------------------------
	# Item Usage
	# ------------------------

	def use_item(self, item_name, maze=None):
		pattern = re.compile(rf"{item_name}", flags=re.IGNORECASE)
		for category, items in self.inventory.items.items():
			for item_ in items:
				match = pattern.search(item_.name)
				if match:
					if isinstance(item_, Healing):
						if "healing potion" in item_.name.lower():
							self.health = min(self.max_health, self.health + item_.healing[0])
							print(f"{self.name} heals to {self.health}/{self.max_health}")
						self.remove_item(item_)
						return
					elif isinstance(item_, Throwing):
						if "bomb" in item_.name.lower():
							if not maze:
								print("you need to see where your throwing")
								return
							self.throw(item_, maze)
						self.remove_item(item_)
						return
					elif isinstance(item_, Weapon):
						self.equip_weapon(item_)
						return
					elif isinstance(item_, Armour):
						self.equip_armor(item_)
						return

		print("Item not found.")

	def equip_weapon(self, weapon_):
		if self.weapon == weapon_:
			self.unequip_weapon()
			return
		else:
			self.inventory.items["Equipped"].append(weapon_)
			for stat,val_1 in weapon_.stat_bonuses.items():
				self.stats[stat] += val_1
			self.weapon = weapon_
			self.remove_item(weapon_)

	def unequip_weapon(self):
		equipped = self.inventory.items["Equipped"]
		for items in equipped:
			if not isinstance(items, list):
				if isinstance(items, Weapon):
					self.add_to_inventory(items)
					self.inventory.items["Equipped"].remove(items)
					for stat, val_1 in items.stat_bonuses.items():
						self.stats[stat] -= val_1
					self.equip_weapon(Weapon())
				return
			for item in items:
				if isinstance(item, Weapon):
					self.add_to_inventory(item)
					self.inventory.items["Equipped"].remove(item)
					for stat, val_1 in item.stat_bonuses.items():
						self.stats[stat] -= val_1
					self.equip_weapon(Weapon())
					return

	def unequip_armor(self):
		equipped = self.inventory.items["Equipped"]
		for items in equipped:
			if not isinstance(items, list):
				items = [items]
			for item in items:
				if isinstance(item, Armour):
					self.add_to_inventory(item)
					self.inventory.items["Equipped"].remove(item)
					for (stat, val_1), (resist, val_2) in zip(item.stat_bonuses.items(),item.resistances.items()):
						self.stats[stat] -= val_1
						self.resistances[resist] -= val_2
					self.equip_armor(Armour())
					return

	def equip_armor(self, armor_):
		if self.armor == armor_:
			self.unequip_armor()
			return
		else:
			self.inventory.items["Equipped"].append(armor_)
			for (stat, val_1), (resist, val_2) in zip(armor_.stat_bonuses.items(),armor_.resistances.items()):
				self.stats[stat] += val_1
				self.resistances[resist] += val_2
			self.armor = armor_
			self.remove_item(armor_)

	def throw(self, item, maze):
		row_old, col_old = self.location.location
		distance = item.distance
		for i in range(0,distance-1):
			curr_cell = maze.cells[row_old][col_old]
			if curr_cell.can_move(self.facing, maze) == "move":
				row, col = next_cell(row_old, col_old, self.facing)
				if not((0 < row < maze.num_rows - 1) and (0 < col < maze.num_cols - 1)):
					print(f"you tossed {item} outside")
					return
				if curr_cell.enemy_entity:
					self.attack_target(curr_cell.enemy_entity, item, maze)
					return
			if "bomb" in item.name.lower():
				row, col = next_cell(row_old, col_old, self.facing)
				if curr_cell.can_move(self.facing, maze) == "bump":
					if self.facing == "up":
						maze.cells[row_old][col_old].top = False
						maze.cells[row][col].bottom = False
					if self.facing == "down":
						maze.cells[row_old][col_old].bottom = False
						maze.cells[row][col].top = False
					if self.facing == "left":
						maze.cells[row_old][col_old].left = False
						maze.cells[row][col].right = False
					if self.facing == "right":
						maze.cells[row_old][col_old].right = False
						maze.cells[row][col].left = False
					if curr_cell == self.location:
						for element in item.elements:
							element.damage *= 0.5
						self.take_damage(item.elements)
					other_side = maze.cells[row][col]
					if other_side.enemy_entity:
						for element in item.elements:
							element.damage *= 0.5
						other_side.enemy_entity.take_damage(item.elements)
					print("the wall collapses!")
					return
			row_old, col_old = next_cell(row_old, col_old, self.facing)

		print(f"{item.name} hits the ground")

		pass

	# ------------------------
	# Actions
	# ------------------------

	def move(self, direction, maze, on_complete=None):
		if not direction:
			if on_complete:
				on_complete()
			return
		row_old, col_old = self.location.location
		row, col = next_cell(row_old, col_old, direction)
		movement = maze.cells[row_old][col_old].can_move(direction, maze)

		if movement == "bump":
			print("You bump into a wall.")
			if on_complete:
				on_complete()
			return
		elif movement != "move":
			print(movement)
			if "continue" in movement:
				maze.next_level(self)
			if on_complete:
				on_complete()
			return

		if 0 <= row < maze.num_rows and 0 <= col < maze.num_cols:
			if maze.cells[row][col].enemy:
				self.attack_target(maze.cells[row][col].enemy_entity, self.weapon, maze)
				if on_complete:
					on_complete()
				return
			maze.cells[row_old][col_old].ani_move(maze.cells[row][col], duration=200, on_complete=on_complete)
			maze.cells[row_old][col_old].remove_player()
			maze.cells[row][col].set_player(self)
			self.location = maze.cells[row][col]
			self.facing = direction






	def enemy_turn(self, player, maze, on_complete=None):
		if not self.location:
			if on_complete:
				on_complete()
			return
		row_old, col_old = self.location.location
		my_row, my_col = row_old, col_old
		p_row, p_col = player.location.location
		if self.health <= 0:
			self.give_inventory(maze.cells[my_row][my_col])
			maze.cells[my_row][my_col].remove_enemy()
			return

		# If adjacent → attack
		if abs(my_col - p_col) + abs(my_row - p_row) == 1:
			x_axe = my_col - p_col
			y_axe = my_row - p_row
			if x_axe == -1 and not self.location.right:
				self.attack_target(player, self.weapon, maze)
				if on_complete:
					on_complete()
				return
			elif x_axe == 1 and not self.location.left:
				self.attack_target(player, self.weapon, maze)
				if on_complete:
					on_complete()
				return
			elif y_axe == 1 and not self.location.top:
				self.attack_target(player, self.weapon, maze)
				if on_complete:
					on_complete()
				return
			elif y_axe == -1 and not self.location.bottom:
				self.attack_target(player, self.weapon, maze)
				if on_complete:
					on_complete()
				return

		# Otherwise move randomly (simple AI)
		directions = [d for d in ["up", "down", "left", "right"] if self.location.can_move(d, maze, is_enemy=True) != "bump"]
		if not directions:
			if on_complete:
				on_complete()
			return
		direction = random.choice(directions)
		row, col = next_cell(my_row, my_col, direction)
		if 0 <= row < maze.num_rows and 0 <= col < maze.num_cols:
			maze.cells[row_old][col_old].ani_move(maze.cells[row][col], duration=200, on_complete=on_complete)
			maze.cells[row_old][col_old].remove_enemy()
			maze.cells[row][col].set_enemy(self)
			self.location = maze.cells[row][col]
		if on_complete:
			on_complete()
		return