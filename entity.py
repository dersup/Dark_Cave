import random
import re
from classes import *


INSPECT_WHITELIST = {
	"Entity": ["name", "health", "max_health", "armor", "weapon", "damage_resistance"],
	"item": ["name", "damage"],
	"weapon": ["name", "damage", "attack"],
	"armor": ["name", "AC"],
	"Cell": ["enemy_entity", "player_entity", "inventory"],
	"Player": ["name", "health", "max_health", "armor", "weapon", "damage_resistance"],
}


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
	def __init__(self, name, max_health, armor_=Armour(), weapon_=Weapon(), damage_resistance=0):
		self.name = name
		self.max_health = max_health
		self.health = max_health
		self.damage_resistance = damage_resistance
		self.attack = 0
		self.defence = 0
		self.luck = 0
		self.magic_defence = 0
		self.magic_attack = 0
		self.agility = 0
		self.experience = 0

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

	def take_damage(self, amount, bypass_dr=False):
		total = amount
		if not bypass_dr:
			total -= self.damage_resistance
		if total <= 0:
			return 0
		else:
			self.health -= total
			return total

	def attack_target(self, enemy, weapon_,maze):
		if not weapon_:
			print("You have no weapon.")
			return
		dam_taken = 0

		roll = random.randint(1, 20)
		if isinstance(weapon_, Throwing):
			if "bomb" in weapon_.name:
				if roll > 10:
					dam_taken = enemy.take_damage(weapon_.damage, bypass_dr=True)
				else:
					dam_taken = enemy.take_damage(weapon_.damage // 2, bypass_dr=True)
		else:
			attack_total = roll + weapon_.attack

			enemy_ac = 10
			if enemy.armor:
				enemy_ac += enemy.armor.AC

			if attack_total >= enemy_ac:
				damage = weapon_.damage + random.randint(1, 6)
				dam_taken = enemy.take_damage(damage)
			else:
				print(f"{self.name} misses {enemy.name}.")
				return
		if dam_taken:
			print(f"{self.name} hits {enemy.name} with {weapon_.name} for {dam_taken} damage!")
			if enemy.health <= 0:
				self.kills += 1
				self.give_inventory(maze.cells[self.location.location[0]][self.location.location[1]])
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
		if isinstance(item_, Weapon):
			self.inventory.items["Weapons"].append(item_)
		elif isinstance(item_, Armour):
			self.inventory.items["Armors"].append(item_)
		elif isinstance(item_, Item):
			self.inventory.items["Consumables"].append(item_)
		else:
			print(f"not able to put {item_} in inventory")

	def add_items_to_inventory(self, items):
		if len(items) == 1:
			self.add_to_inventory(items[0])
			return
		else:
			for item in items:
				self.add_to_inventory(item)

	def get_cell_inventory(self,target):
		for category in target.inventory.items.keys():
			if target.inventory.items[category] and category != "Equipped":
				self.add_items_to_inventory(target.inventory.items[category])
				print(f"adding{target.inventory.items[category]} to inventory")
		self.gold += target.gold
		print(f"adding gold: {target.gold}")
		target.remove_inventory()
		target.gold = 0


	def give_inventory(self, target):
		for category in self.inventory.items.keys():
			if self.inventory.items[category] and category != "Equipped":
				target.add_items_to_inventory(self.inventory.items[category])
		target.gold += self.gold
		self.remove_inventory()

	def give_items(self, target, items):
		target.add_items_to_inventory(items)
		for item in items:
			self.remove_item(item)

	def show_inventory(self, win):
		if win.inventory_show:
			win.inventory_show = False
		else:
			win.inventory_show = True
		win.player_labels(self)

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
							self.health = min(self.max_health, self.health + item_.healing)
							print(f"{self.name} heals to {self.health}/{self.max_health}")
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
		if weapon_ != Weapon():
			if self.weapon == weapon_:
				self.unequip_weapon()
				return
			else:
				self.inventory.items["Equipped"].append(weapon_)
				self.weapon = weapon_
				self.remove_item(weapon_)
		else:
			self.weapon = weapon_

	def unequip_weapon(self):
		equipped = self.inventory.items["Equipped"]
		for items in equipped:
			if not isinstance(items, list):
				if isinstance(items, Weapon):
					self.add_to_inventory(items)
					self.inventory.items["Equipped"].remove(items)
					self.equip_weapon(Weapon())
				return
			for item in items:
				if isinstance(item, Weapon):
					self.add_to_inventory(item)
					self.inventory.items["Equipped"].remove(item)
					self.equip_weapon(Weapon())
					return

	def unequip_armor(self):
		equipped = self.inventory.items["Equipped"]
		for items in equipped:
			if not isinstance(items, list):
				if isinstance(items, Armour):
					self.add_to_inventory(items)
					self.inventory.items["Equipped"].remove(items)
					self.equip_armor(Armour())
				return
			for item in items:
				if isinstance(item, Armour):
					self.add_to_inventory(item)
					self.inventory.items["Equipped"].remove(item)
					self.equip_armor(Armour())
					return

	def equip_armor(self, armor_):
		if armor_ != Armour():
			if self.armor == armor_:
				self.unequip_armor()
				return
			else:
				self.inventory.items["Equipped"].append(armor_)
				self.armor = armor_
				self.remove_item(armor_)
		else:
			self.armor = armor_

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
			if "Bomb" in item.name:
				row, col = next_cell(row_old, col_old, self.facing)
				if curr_cell.can_move(self.facing, maze) == "bump":
					if self.facing == "up":
						maze.cells[row_old][col_old].top = False
						maze.cells[row][col].bottom = False
					if self.facing == "down":
						maze.cells[row_old][col_old].bottem = False
						maze.cells[row][col].top = False
					if self.facing == "left":
						maze.cells[row_old][col_old].left = False
						maze.cells[row][col].right = False
					if self.facing == "right":
						maze.cells[row_old][col_old].right = False
						maze.cells[row][col].left = False
					if curr_cell == self.location:
						self.take_damage(item.damage * 0.5, bypass_dr=True)
					other_side = maze.cells[row][col]
					if other_side.enemy_entity:
						other_side.enemy_entity.take_damage(item.damage * 0.5, bypass_dr=True)
					print("the wall collapses!")
					return
			row_old += 1
			col_old += 1

		print(f"{item.name} hits the ground")

		pass

	# ------------------------
	# Actions
	# ------------------------

	def move(self, direction, maze, on_complete=None):

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
				maze.new_maze()
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
