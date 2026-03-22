import time
from tkinter import Tk, Canvas, IntVar, Label, Text, font
from main import USED_KEYS


class Windows:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.__root = Tk()
        self.__root.title("The Dark Cave")
        self.canvas = Canvas(self.__root, bg="black", height=y, width=x)
        self.canvas.pack()
        self.counter = IntVar(value=1)
        self.level_label = Label(self.__root, text="level: 1", font=("Arial", 16), bg="black", fg="white")
        self.level_label.place(relx=0.5, rely=0.05, anchor="n")
        self.health_label = Label(self.__root, text="HP: 0/0", font=("Arial", 16), bg="black", fg="red")
        self.health_label.place(relx=0.1, rely=0.05, anchor="nw")
        self.inventory_text = Text(self.__root, font=("Arial", 11), bg="black", fg="white", bd=0, highlightthickness=0, state="disabled", width=30)
        bold_font = font.Font(family="Arial", size=11, weight="bold")
        self.inventory_text.tag_configure("bold", font=bold_font)
        self.gold_label = Label(self.__root, text="Gold: 0", font=("Arial", 16), bg="black", fg="gold")
        self.gold_label.place(relx=0.1, rely=0.9, anchor="sw")
        self.game_over_label = Label(self.__root, text="GAME OVER",font=("Arial", 25), bg="black", fg="darkred")
        self.info_label = Label(self.__root, font=("Arial", 12), bg="black", fg="white")
        self.P_level = Text(self.__root, font=("Arial", 11), bg="black", fg="gold", bd=0, highlightthickness=0, state="disabled", width=30)

        self.offset_x = 0
        self.offset_y = 0
        self.inventory_show = False

    def center_on(self, player):
        self.offset_x = self.x / 2 - player.location.cent.x
        self.offset_y = self.y / 2 - player.location.cent.y

    def redraw(self):
        self.__root.update_idletasks()
        self.__root.update()

    def wait_for_close(self):
        self.__root.mainloop()

    def draw_line(self, line, colour):
        line.draw(self.canvas, colour, self.offset_x, self.offset_y)

    def draw_circle(self, point, radius, fill:str, outline="", tag="world"):
        x, y = point.x + self.offset_x, point.y + self.offset_y
        id_ = self.canvas.create_oval(
            x - radius, y - radius,
            x + radius, y + radius,
            fill=fill, outline=outline, tags=tag)
        return id_

    def bind_key(self,key,callback):
        self.__root.bind(key,callback)

    def unbind_key(self,key):
        self.__root.unbind(key)

    def clear(self, tags=("world",)):
        self.canvas.delete(tags)

    def set_level(self, lvl):
        self.level_label.config(text=f"level: {lvl}")

    def player_labels(self, player=None,game_over=False):
        if game_over:
            self.gold_label.place_forget()
            self.health_label.place_forget()
            self.inventory_text.place_forget()
            return
        else:
            if self.inventory_show:
                if not self.inventory_text.winfo_ismapped():
                    self.inventory_text.place(relx=0.5, rely=0.25,anchor="n")
                if not self.info_label.winfo_ismapped():
                    self.info_label.place(relx=0.7, rely=0.25,anchor="n")
                self.inventory_formatted(str(player.inventory))
            else:
                self.inventory_text.place_forget()
                self.info_label.place_forget()
            self.health_label.config(text=f"HP: {player.health}/{player.max_health}")
            self.gold_label.config(text=f"Gold: {str(player.gold) or "0"}")

    def inventory_formatted(self, content):
        self.inventory_text.config(state="normal")
        self.inventory_text.delete("1.0", "end")
        for line in content.split("\n"):
            if line in ["Equipped", "Armors", "Weapons", "Consumables"]:
                self.inventory_text.insert("end", line + "\n", "bold")
            elif not line:
                continue
            else:
                self.inventory_text.insert("end", line.split("(")[0].strip() + "\n")
        self.inventory_text.config(state="disabled")

    def display_info(self,content):
        self.info_label.config(text=content)
        self.info_label.update()

    def highlight_line(self,line_number, player,bg="darkgray", fg="blue"):
        # Remove previous highlight
        self.inventory_text.tag_remove("highlight", "1.0", "end")

        def display_item(place):
            text = self.inventory_text.get("1.0", f"{place}.end").split("\n")
            text = text[::-1]
            item_name = self.inventory_text.get(f"{place}.0", f"{place}.end")
            for category in text:
                if category in list(player.inventory.items.keys()):
                    items = player.inventory.items[category]
                    for item in items:
                        if item.name == item_name:
                            self.display_info(str(item))

        # Tag format is "line.col" — col 0 to end of line
        start = f"{line_number}.0"
        end = f"{line_number}.end"
        display_item(line_number)
        self.inventory_text.tag_add("highlight", start, end)
        self.inventory_text.tag_config("highlight", background=bg, foreground=fg)
        return self.inventory_text.get(start, end)

    def GAME_OVER(self,player,maze):
        for key in USED_KEYS:
            self.unbind_key(key)

        self.bind_key("y",lambda e: maze.new_maze(player,0))
        self.bind_key("n",self.__root.destroy())
        self.game_over_label.place(relx=0.5, rely=0.5)
        self.game_over_label.config(text=f"""
              SCORE: {player.gold * maze.level}
                GAME OVER
                TRY AGAIN?
                  Y) (N
        """)

    def show_level_up(self,player):
        self.P_level.place(relx=0.5, rely=0.5)
        self.P_level.config(state="normal")
        self.P_level.delete("1.0", "end")
        self.P_level.insert("end",f"LEVEL UP!, LEVEL {player.level}","bold",)
        self.P_level.config(state="disabled")
        time.sleep(1)
        total_points = 3
        incr = {"num":2}
        def increment(change):
            new_val = incr["num"] + change
            if 2 < new_val < len(player.stats.keys()-1):
                incr["num"] = new_val
                self.highlight_line(incr["num"], player)
        def get_item():
            item_name = self.highlight_line(incr["num"], player).split(":")[0].strip()
            print(f"{item_name} increased you have {total_points} points remaining")
            player.stats[item_name] += 1
        self.bind_key("<Up>", lambda e: increment(-1))
        self.bind_key("<Down>", lambda e: increment(1))
        self.bind_key("<Enter>", lambda e: get_item())
        self.bind_key("<w>", lambda e: increment(-1))
        self.bind_key("<s>", lambda e: increment(1))
        self.bind_key("<e>", lambda e: get_item())
        while total_points:
            self.inventory_text.config(state="normal")
            self.inventory_text.delete("1.0", "end")
            self.P_level.insert("end",
                                f" you have {total_points} stat points choose an ability score to increase:\nattack: {player.stats["attack"]}\ndefence: {player.stats["defence"]}\nluck: {player.stats["luck"]}\nmagic_defence: {player.stats["magic_defence"]}\nmagic_attack: {player.stats["magic_attack"]}\nagility: {player.stats["agility"]}",
                                "bold")
            self.P_level.config(state="disabled")
            time.sleep(1/60)
        self.P_level.place_forget()