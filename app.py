import tkinter as tk
from collections import defaultdict, deque
import math
import random
import json
import matplotlib.colors as mc
import colorsys
from tkinter import simpledialog
import copy
import os

class DirectedGraph:
    def __init__(self):
        self.nodes = defaultdict(list)
        self.node_types = defaultdict(list)
        self.deck_name = None
        self.nodeId_to_fixedId = defaultdict(list)
        self.fixedId_to_nodeId = defaultdict(list)
        

    def add_edge(self, node1, node2, edge_type):
        if node1 != node2 and (node2 not in self.nodes[node1]):
            self.nodes[node1].append((node2, edge_type))

    def has_edge(self, node1, node2, edge_type):
        if self.nodes.get(node1) is None:
            return False
        return any(n == node2 and et == edge_type for n, et in self.nodes[node1])

    def degree(self, node, edge_type):
        out_degree = sum(1 for n, et in self.nodes[node] if et == edge_type)
        in_degree = sum(1 for n in self.nodes if any(node == n2 and et == edge_type for n2, et in self.nodes[n]))
        return out_degree, in_degree

    def connected_nodes(self, node, edge_type):
        connected = [n for n, et in self.nodes[node] if et == edge_type]
        connected += [n for n in self.nodes if any(node == n2 and et == edge_type for n2, et in self.nodes[n])]
        return connected

    def bfs(self, start_nodes):
        visited = set()
        queue = deque(list(start_nodes))

        monster_exist = False
        ns_monsters = set()
        eq_magics = set()
        neighbours = []

        # 無条件で使えるサーチで探索
        while queue:
            node = queue.popleft()
            if node not in visited:
                visited.add(node)
                if self.node_types[node] in ["magic", "monster_ss"]:
                    if self.node_types[node] == "monster_ss":
                        monster_exist = True
                    neighbours = [n for n, et in self.nodes[node] if et == "search"]
                
                queue.extend(neighbours)
        ns_monsters.update([node for node in visited if self.node_types[node] == "monster_ns"])
        eq_magics.update([node for node in visited if self.node_types[node] == "magic_eq"])

        # 一番召喚したいモンスター１体だけのサーチで探索
        if ns_monsters:
            visited.remove(sorted(list(ns_monsters))[0])
            queue = deque(sorted(list(ns_monsters))[0:1])
            summoned = False
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    if self.node_types[node] == "monster_ns":
                        if not summoned:
                            summoned = True
                            monster_exist = True
                            neighbours = [n for n, et in self.nodes[node] if et == "search"]
                    if self.node_types[node] in ["magic", "monster_ss"]:
                        if self.node_types[node] == "monster_ss":
                            monster_exist = True
                        neighbours = [n for n, et in self.nodes[node] if et == "search"]

                    queue.extend(neighbours)

        ns_monsters.update([node for node in visited if self.node_types[node] == "monster_ns"])
        eq_magics.update([node for node in visited if self.node_types[node] == "magic_eq"])

        # ポプルス系サーチ
        if ns_monsters:
            for node in sorted(list(ns_monsters))[1:]:
                visited.remove(node)
            queue = deque(sorted(list(ns_monsters))[1:])
            summoned = False
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    if self.node_types[node] == "monster_ns":
                        monster_exist = True
                        neighbours = [n for n, et in self.nodes[node] if et == "chain search" and node not in start_nodes]
                    if self.node_types[node] in ["magic", "monster_ss"]:
                        if self.node_types[node] == "monster_ss":
                            monster_exist = True
                        neighbours = [n for n, et in self.nodes[node] if et == "search"]

                    queue.extend(neighbours)

            eq_magics.update([node for node in visited if self.node_types[node] == "magic_eq"])


        
        # 装備魔法条件のサーチで探索
        if eq_magics:
            for node in eq_magics:
                visited.remove(node)
            queue = deque(list(eq_magics))
            while queue:
                node = queue.popleft()
                if node not in visited:
                    visited.add(node)
                    if self.node_types[node] == "magic_eq":
                        if monster_exist:
                            neighbours = [n for n, et in self.nodes[node] if et == "search"]
                    if self.node_types[node] in ["magic", "monster_ss"]:
                        neighbours = [n for n, et in self.nodes[node] if et == "search"]
                    if self.node_types[node] in ["monster_ns"]:
                        neighbours = [n for n, et in self.nodes[node] if et == "chain search" and node not in start_nodes]
                    
                    
                    queue.extend(neighbours)



        return visited

    def save_edges(self):
        if self.deck_name is None:
            return
        with open(f'./edges/{self.deck_name}_edge_info.txt', 'w') as f:
            #json.dump({str(k): v for k, v in self.nodes.items()}, f)
            json.dump({str(self.nodeId_to_fixedId[node1]): [[self.nodeId_to_fixedId[data[0]],data[1]] for data in self.nodes[node1]] for node1 in self.nodes.keys()},f)

    def load_edges(self):
        file_path = f'./edges/{self.deck_name}_edge_info.txt'
        if not os.path.exists(file_path):
            return
        with open(file_path, 'r') as f:
            self.nodes.update({self.fixedId_to_nodeId[int(k)]: [[self.fixedId_to_nodeId[vv[0]], vv[1]] for vv in v] for k, v in json.load(f).items()})

    def remove_edge(self, node1, node2, edge_type):
        self.nodes[node1] = [(n, et) for n, et in self.nodes[node1] if not (n == node2 and et == edge_type)]

class Application(tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        self.title("Deck Graph Drawer")
        self.whole_width = 960
        self.whole_height = 540
        self.width = self.whole_width*4//5
        self.height = self.whole_height
        self.main_frame = tk.Frame(self)
        self.main_frame.pack()
        self.canvas = tk.Canvas(self.main_frame, width=self.width, height=self.height, bg="#dddddd")
        self.canvas.pack(side=tk.LEFT)

        self.graph = DirectedGraph()
        self.nodes = {}
        self.node_names = {}
        self.node_types = {}
        self.temp_line = None
        self.temp_node = None
        self.texts = []
        self.edge_type = tk.StringVar(self)
        self.edge_type.set("search")  # default value
        self.edge_types = {"search": "#ff0000", "chain search": "#0000ff"}#, "c": "#008000", "d": "#000000"}
        self.node_colors = {"monster_ns": "yellow", "monster_ss": "orange", "magic": self.lighten_color("green"),
                            "magic_eq": self.lighten_color("green"), "trap": self.lighten_color("purple")}
        self.nodeId_to_fixedId = {}
        self.fixedId_to_nodeId = {}
        self.hand_number = tk.IntVar(self)
        

        self.edge_drawings = {}
        self.start_x = None
        self.start_y = None
        self.node_now = None
        self.lines_for_nodes = {}
        self.resizable(False,False)
        

        self.canvas.bind("<Button-1>", self.create_node)
        self.canvas.bind("<B1-Motion>", self.create_edge)
        self.canvas.bind("<ButtonRelease-1>", self.finalize_edge)
        self.canvas.bind("<Button-3>", self.restore_point)
        self.canvas.bind("<ButtonRelease-3>", self.change_node_type)

        

        self.button_frame = tk.Frame(self.main_frame, width=self.whole_width//5, height=self.height, bg=self.lighten_color("cyan", amount=0.3))
        self.button_frame.pack(side=tk.RIGHT)
        self.button_frame.pack_propagate(0)
        
        # 区切り線
        separator = tk.Label(self.button_frame, text="", bg=self.lighten_color("cyan", amount=0.3))
        separator.pack(pady=5)  # padyで上下にスペースを追加


        self.button = tk.Button(self.button_frame, text="Load Deck", command=self.on_button_click, width=15, bg=self.lighten_color("yellow"))
        self.button.pack(padx=3,pady=3, side=tk.TOP)
        self.button = tk.Button(self.button_frame, text="Save Deck", command=self.save_deck, width=15, bg=self.lighten_color("yellow"))
        self.button.pack(padx=3,pady=3, side=tk.TOP)
        

        separator = tk.Label(self.button_frame, text="", bg=self.lighten_color("cyan", amount=0.3))
        separator.pack(pady=5)
        
        self.load_button = tk.Button(self.button_frame, text="Load Edges", command=self.load_edges, width=15, bg=self.lighten_color("yellow"))
        self.load_button.pack(padx=5,pady=5, side=tk.TOP)
        self.save_button = tk.Button(self.button_frame, text="Save Edges", command=self.graph.save_edges, width=15, bg=self.lighten_color("yellow"))
        self.save_button.pack(padx=5,pady=5, side=tk.TOP)
        self.node_size = self.width // 50


        separator = tk.Label(self.button_frame, text="", bg=self.lighten_color("cyan", amount=0.3))
        separator.pack(pady=5)
        

        for edge_type, color in self.edge_types.items():
            light_color = self.lighten_color(color, amount=0.6)
            rb = tk.Radiobutton(self.button_frame, text=edge_type, variable=self.edge_type, value=edge_type, bg=light_color, width=15)
            rb.pack(pady=3, side=tk.TOP, anchor=tk.CENTER)



        
        separator = tk.Label(self.button_frame, text="", bg=self.lighten_color("cyan", amount=0.3))
        separator.pack(pady=5)


        spin = tk.Spinbox(self.button_frame, from_=1, to=10, width=15, textvariable=self.hand_number, justify=tk.CENTER)
        spin.pack(padx=3, pady=3)
        self.hand_number.set(5)


        self.button = tk.Button(self.button_frame, text="Draw", command=self.one_draw, width=15, bg=self.lighten_color("yellow"))
        self.button.pack(padx=3,pady=3)

        self.button = tk.Button(self.button_frame, text="Draw 100000", command=self.calculate_probability, width=15, bg=self.lighten_color("yellow"))
        self.button.pack(padx=3,pady=3)


        self.card_kinds = tk.Label(self.button_frame, text="", bg=self.lighten_color("cyan", amount=0.3), width=15)
        self.card_kinds.pack(padx=3,pady=3, side=tk.TOP)
        

    def restart(self):
        self.canvas.delete("all")
        self.graph.__init__()
        self.nodes = {}
        self.node_names = {}
        self.node_types = {}
        self.temp_line = None
        self.temp_node = None
        self.texts = []
        self.edge_type.set("search")  # default value
        self.edge_drawings = {}
        self.start_x = None
        self.start_y = None
        self.node_now = None
        self.card_kinds.config(text=f"", bg=self.lighten_color("cyan", amount=0.3), width=15)
        self.lines_for_nodes = {}
        self.nodeId_to_fixedId = {}
        self.fixedId_to_nodeId = {}


    def reindex_keys(dictionary):
        keys = list(dictionary.keys())
        keys.sort()
        new_dict = {}
        for i, key in enumerate(keys, start=1):
            new_dict[i] = dictionary[key]
        return new_dict


    def save_deck(self):
        if self.graph.deck_name is None:
            return
        lines = ""
        for node in self.nodes.keys():
            line = self.node_names[node] + " " + self.node_types[node] + "\n"
            lines = lines + line

        with open(f'./decks/{self.graph.deck_name}.txt', 'w', encoding='utf-8') as f:
            f.write(lines)


    def on_button_click(self):
        self.restart()

        node_names, node_types = [], []
        answer = simpledialog.askstring("Input", "Input deck name:",
                            parent=self.button_frame)
        if answer is None:
            return
            
        try:
            with open(f'./decks/{answer}.txt', 'r', encoding='utf-8') as f:
                node_names = f.read().splitlines()
            self.graph.deck_name = answer
        except FileNotFoundError:
            return


        num_nodes = len(node_names)
        cols = 10
        rows = math.ceil(num_nodes / cols)
        
        for i, node_name in enumerate(node_names):
            try:
                node_name, node_type = node_name.split()
            except ValueError:
                node_name, node_type = node_name, "monster_ns"

            if node_type not in ["monster_ns","monster_ss", "magic", "magic_eq", "trap"]:
                node_type = "monster_ns"
            
            row = i // cols
            col = i % cols
            x = ((col+1)*self.width//(cols+1))
            y = ((row+1)*self.height//(rows+1))

            node = self.canvas.create_oval(x-self.node_size, y-self.node_size, x+self.node_size, y+self.node_size, fill=self.node_colors[node_type], width=3, outline="gray")

            
            line1 = self.canvas.create_line(x-self.node_size, y, x + self.node_size, y, width=3, fill="green", state="hidden")
            line2 = self.canvas.create_line(x, y-self.node_size, x, y + self.node_size, width=3, fill="green", state="hidden")

            if node_type == "magic_eq":
                self.canvas.itemconfig(line1, state="normal")
                self.canvas.itemconfig(line2, state="normal")
            
            
            self.nodeId_to_fixedId[node] = i
            self.fixedId_to_nodeId[i] = node

            self.nodes[node] = (x, y)
            self.lines_for_nodes[node] = (line1, line2)

            self.node_names[node] = node_name
            self.node_types[node] = node_type
            self.canvas.create_text(x, y-round(self.node_size*1.6), text=node_name, fill="black", font=("Meiryo", 7))
            #self.canvas.create_text(x, y, text=node, fill="black", font=("Meiryo", 7))
        
        self.graph.node_types = self.node_types
        self.graph.nodeId_to_fixedId = self.nodeId_to_fixedId
        self.graph.fixedId_to_nodeId = self.fixedId_to_nodeId

    def create_node(self, event):
        overlapping = self.canvas.find_overlapping(event.x-self.node_size, event.y-self.node_size, event.x+self.node_size, event.y+self.node_size)
        for node in overlapping:
            if node in self.nodes.keys():
                self.temp_node = node
                return

    def create_edge(self, event):
        if self.temp_line:
            self.canvas.delete(self.temp_line)
        try:
            self.temp_line = self.canvas.create_line(self.nodes[self.temp_node][0], self.nodes[self.temp_node][1], event.x, event.y, arrow=tk.LAST, fill=self.edge_types[self.edge_type.get()], arrowshape=(16, 20, 6))
        except KeyError:
            pass



    """def finalize_edge(self, event):
        overlapping = self.canvas.find_overlapping(event.x-self.node_size, event.y-self.node_size, event.x+self.node_size, event.y+self.node_size)
        for node in overlapping:
            if node in self.nodes.keys() and node != self.temp_node:
                # ユーザがクリックしたノード間にエッジを作成
                if not self.graph.has_edge(self.temp_node, node, self.edge_type.get()):
                    self.graph.add_edge(self.temp_node, node, self.edge_type.get())
                    self.canvas.create_line(self.nodes[self.temp_node][0], self.nodes[self.temp_node][1], self.nodes[node][0], self.nodes[node][1], arrow=tk.LAST, fill=self.edge_types[self.edge_type.get()], arrowshape=(16, 20, 6))
                
                # 同じ名前のノード間にエッジを作成
                for node1 in self.nodes:
                    for node2 in self.nodes:
                        if self.node_names[node1] == self.node_names[self.temp_node] and self.node_names[node2] == self.node_names[node]:
                            if not self.graph.has_edge(node1, node2, self.edge_type.get()):
                                self.graph.add_edge(node1, node2, self.edge_type.get())
                                self.canvas.create_line(self.nodes[node1][0], self.nodes[node1][1], self.nodes[node2][0], self.nodes[node2][1], arrow=tk.LAST, fill=self.edge_types[self.edge_type.get()], arrowshape=(16, 20, 6))
                break
        self.canvas.delete(self.temp_line)
        self.temp_line = None
        self.temp_node = None
    """
    

    def finalize_edge(self, event):
        overlapping = self.canvas.find_overlapping(event.x-self.node_size, event.y-self.node_size, event.x+self.node_size, event.y+self.node_size)
        for node in overlapping:
            if node is None or self.temp_node is None:
                continue
            if node in self.nodes.keys() and node != self.temp_node:
                # ユーザがクリックしたノード間にエッジを作成
                if self.graph.has_edge(self.temp_node, node, self.edge_type.get()):
                    self.graph.remove_edge(self.temp_node, node, self.edge_type.get())
                    if (self.temp_node, node, self.edge_type.get()) in self.edge_drawings:  # 描画が存在する場合
                        line_id = self.edge_drawings[(self.temp_node, node, self.edge_type.get())]
                        self.canvas.delete(line_id)
                        del self.edge_drawings[(self.temp_node, node, self.edge_type.get())]
                        
                    # 同じ名前のノード間にエッジを削除
                    for node1 in self.nodes:
                        for node2 in self.nodes:
                            if self.node_names[node1] == self.node_names[self.temp_node] and self.node_names[node2] == self.node_names[node]:
                                if self.graph.has_edge(node1, node2, self.edge_type.get()):
                                    self.graph.remove_edge(node1, node2, self.edge_type.get())
                                    if (node1, node2, self.edge_type.get()) in self.edge_drawings:  # 描画が存在する場合
                                        line_id = self.edge_drawings[(node1, node2, self.edge_type.get())]
                                        self.canvas.delete(line_id)
                                        del self.edge_drawings[(node1, node2, self.edge_type.get())]
                else:
                    self.graph.add_edge(self.temp_node, node, self.edge_type.get())
                    line_id = self.canvas.create_line(self.nodes[self.temp_node][0], self.nodes[self.temp_node][1], self.nodes[node][0], self.nodes[node][1], arrow=tk.LAST, fill=self.edge_types[self.edge_type.get()], arrowshape=(16, 20, 6))
                    self.edge_drawings[(self.temp_node, node, self.edge_type.get())] = line_id
                    # 同じ名前のノード間にエッジを作成
                    for node1 in self.nodes:
                        for node2 in self.nodes:
                            if self.node_names[node1] == self.node_names[self.temp_node] and self.node_names[node2] == self.node_names[node]:
                                if not self.graph.has_edge(node1, node2, self.edge_type.get()):
                                    self.graph.add_edge(node1, node2, self.edge_type.get())
                                    line_id = self.canvas.create_line(self.nodes[node1][0], self.nodes[node1][1], self.nodes[node2][0], self.nodes[node2][1], arrow=tk.LAST, fill=self.edge_types[self.edge_type.get()], arrowshape=(16, 20, 6))
                                    self.edge_drawings[(node1, node2, self.edge_type.get())] = line_id
                break
        self.canvas.delete(self.temp_line)
        self.temp_line = None
        self.temp_node = None



    def restore_point(self, event):
        for node, (x, y) in self.nodes.items():
            r2 = (event.x-x)**2+(event.y-y)**2
            if r2<=(self.node_size)**2:
                self.start_x = x
                self.start_y = y
                self.node_now = node
                break

    def change_node_type(self, event):
        if self.start_x is None or self.start_y is None or self.node_now is None:
            return
        if (self.start_x-event.x)**2 + (self.start_y-event.y)**2 <= (self.node_size)**2:
            if self.node_types[self.node_now]=="monster_ns":
                self.canvas.itemconfig(self.node_now, fill="orange")
                self.node_types[self.node_now] = "monster_ss"
            elif self.node_types[self.node_now]=="monster_ss":
                self.canvas.itemconfig(self.node_now, fill=self.lighten_color("green"))
                self.node_types[self.node_now] = "magic"
            elif self.node_types[self.node_now]=="magic":
                self.canvas.itemconfig(self.node_now, fill=self.lighten_color("green"))
                self.canvas.itemconfig(self.lines_for_nodes[self.node_now][0], state="normal")
                self.canvas.itemconfig(self.lines_for_nodes[self.node_now][1], state="normal")
                self.node_types[self.node_now] = "magic_eq"
            elif self.node_types[self.node_now]=="magic_eq":
                self.canvas.itemconfig(self.node_now, fill=self.lighten_color("purple"))
                self.canvas.itemconfig(self.lines_for_nodes[self.node_now][0], state="hidden")
                self.canvas.itemconfig(self.lines_for_nodes[self.node_now][1], state="hidden")
                self.node_types[self.node_now] = "trap"
            elif self.node_types[self.node_now]=="trap":
                self.canvas.itemconfig(self.node_now, fill="yellow")
                self.node_types[self.node_now] = "monster_ns"

    def one_draw(self):
        if self.graph.deck_name is None or \
              not (int(self.hand_number.get())<=len(self.nodes.keys()) and len(self.nodes.keys())<=60):
            return

        for node in self.nodes.keys():
            self.canvas.itemconfig(node, width=3, outline="gray")


        for text in self.texts:
            self.canvas.delete(text)
        self.texts = []
        """for node, coords in self.nodes.items():
            out_degree, in_degree = self.graph.degree(node, self.edge_type.get())
            text = self.canvas.create_text(coords[0], coords[1]+round(self.node_size*1.4), text=f"degree: {out_degree}, {in_degree}", fill="black")
            self.texts.append(text)"""


        hands = random.sample(list(self.nodes.keys()), int(self.hand_number.get()))
        if self.graph.deck_name.find("example") != -1:
            hands = sorted(list(self.nodes.keys()))[:int(self.hand_number.get())]
        

        reachable_nodes = copy.deepcopy(set(hands))
        reachable_nodes.update(self.graph.bfs(reachable_nodes))

        for node in self.nodes.keys():
            if node in reachable_nodes:
                self.canvas.itemconfig(node, width=5, outline="red")
                if node in hands:
                    self.canvas.itemconfig(node, width=5, outline="black")
            else:
                self.canvas.itemconfig(node, width=3, outline="gray")

        accessible_cards = set()
        for node in reachable_nodes:
            accessible_cards.add(self.node_names[node])
        kind = (len(accessible_cards))
        self.card_kinds.config(text=f"accessible types\n{kind}", bg="white", font=("Meiryo", 10), width=15)

    def calculate_probability(self):
        if self.graph.deck_name is None or \
              not (int(self.hand_number.get())<=len(self.nodes.keys()) and len(self.nodes.keys())<=60):
            return

        for text in self.texts:
            self.canvas.delete(text)
        self.texts = []

        counts = {node: 0 for node in self.nodes.keys()}
        trial_number = 100000
        kinds = []

        for _ in range(trial_number):
            hands = random.sample(list(self.nodes.keys()), int(self.hand_number.get()))
            reachable_nodes = copy.deepcopy(set(hands))
            reachable_nodes.update(self.graph.bfs(reachable_nodes))

            accessible_cards = set()
            for node in reachable_nodes:
                counts[node] += 1
                accessible_cards.add(self.node_names[node])
            kinds.append(len(accessible_cards))
        
        for node in self.nodes.keys():
            x, y = self.nodes[node]
            text = self.canvas.create_text(x, y+round(self.node_size*1.6), text=f"{100*counts[node]/trial_number:.2f}%", fill="black", font=("Meiryo", 7))
            self.texts.append(text)
        
        self.card_kinds.config(text=f"accessible types\n{sum(kinds)/trial_number:.2f}", bg="white", font=("Meiryo", 10), width=15)
        
        
        


    def lighten_color(self, color, amount=0.5):
        
        try:
            c = mc.cnames[color]
        except:
            c = color
        c = colorsys.rgb_to_hls(*mc.to_rgb(c))
        light_color = colorsys.hls_to_rgb(c[0], 1 - amount * (1 - c[1]), c[2])
        light_color = '#%02x%02x%02x' % (int(light_color[0]*255), int(light_color[1]*255), int(light_color[2]*255))
        return light_color

    def load_edges(self):
        before = copy.deepcopy(self.graph.nodes)
        before.update({node1: [[data[0],data[1]] for data in before[node1]] for node1 in before.keys()})
        self.graph.load_edges()

        loaded = defaultdict(list)
        loaded.update({node1: [[data[0],data[1]] for data in self.graph.nodes[node1]] for node1 in self.graph.nodes.keys()})

        after = defaultdict(list)
        after.update({node1: [data for data in loaded[node1] if before.get(node1) is None or data not in before.get(node1)] for node1 in loaded.keys()})
        

        for node1, edges in after.items():
            for node2, edge_type in edges:
                #try:
                self.nodes[node1][0], self.nodes[node1][1], self.nodes[node2][0], self.nodes[node2][1]
                #except KeyError:
                #    self.graph.nodes = before
                #    return
        
        for node1, edges in after.items():
            for node2, edge_type in edges:
                line_id = self.canvas.create_line(self.nodes[node1][0], self.nodes[node1][1], self.nodes[node2][0], self.nodes[node2][1], arrow=tk.LAST, fill=self.edge_types[edge_type], arrowshape=(16, 20, 6))
                self.edge_drawings[(node1,node2,edge_type)] = line_id


if __name__ == "__main__":
    app = Application()
    app.mainloop()