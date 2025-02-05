'''
from wumpus import Orientation, Actions, Percepts

class Agent:
    
    def __init__(self, size=(4, 4)):
        self.size = size
        self.knowledge_base = {}
        self.possible_pit_locations = set()
        self.possible_wumpus_locations = set()
        self.arrow_used = False

    def new_episode(self):
        self.pos = (0, 0)
        self.orientation = Orientation.NORTH
        self.has_gold = False
        self.run = False
        self.arrow_used = False
        self.visited = set()
        self.knowledge_base = {
            (0, 0): "safe",
        }
        self.visited.add(self.pos)

    def turn_left(self):
        self.orientation = (self.orientation - 1) % 4

    def turn_right(self):
        self.orientation = (self.orientation + 1) % 4

    def move_forward(self):
        dx = 1 * (self.orientation == Orientation.EAST) + (-1) * (self.orientation == Orientation.WEST)
        dy = 1 * (self.orientation == Orientation.NORTH) + (-1) * (self.orientation == Orientation.SOUTH)
        new_pos = (self.pos[0] + dx, self.pos[1] + dy)

        if 0 <= new_pos[0] < self.size[0] and 0 <= new_pos[1] < self.size[1]:
            self.pos = new_pos
            self.visited.add(self.pos)
        return Actions.FORWARD

    def update_knowledge_base(self, percept):
        if percept[Percepts.BREEZE]:
            self.knowledge_base[self.pos] = "breezy"
            self.add_possible_pit_locations()
        elif percept[Percepts.STENCH]:
            self.knowledge_base[self.pos] = "stenchy"
            self.add_possible_wumpus_locations()
        elif percept[Percepts.GLITTER]:
            self.knowledge_base[self.pos] = "glitter"
        else:
            self.knowledge_base[self.pos] = "safe"

    def add_possible_pit_locations(self):
        neighbors = self.get_neighbors(self.pos)
        for neighbor in neighbors:
            if neighbor not in self.visited and neighbor not in self.knowledge_base:
                self.possible_pit_locations.add(neighbor)

    def add_possible_wumpus_locations(self):
        neighbors = self.get_neighbors(self.pos)
        for neighbor in neighbors:
            if neighbor not in self.visited and neighbor not in self.knowledge_base:
                self.possible_wumpus_locations.add(neighbor)

    def infer_safe_squares(self):
        keys = list(self.knowledge_base.keys())
        for (x, y) in keys:
            status = self.knowledge_base[(x, y)]
            if status == "breezy":
                neighbors = self.get_neighbors((x, y))
                for nx, ny in neighbors:
                    if (nx, ny) not in self.knowledge_base:
                        self.knowledge_base[(nx, ny)] = "unknown"
            elif status == "safe":
                neighbors = self.get_neighbors((x, y))
                for nx, ny in neighbors:
                    if (nx, ny) not in self.knowledge_base:
                        self.knowledge_base[(nx, ny)] = "safe"

    def get_neighbors(self, pos):
        x, y = pos
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def use_arrow(self):
        if not self.arrow_used:
            self.arrow_used = True
            return Actions.SHOOT
        return None

    def get_action(self, percept, reward):
        self.update_knowledge_base(percept)
        self.infer_safe_squares()

        if percept[Percepts.GLITTER]:
            self.has_gold = True
            return Actions.GRAB

        if (not self.run) and (percept[Percepts.BREEZE] or percept[Percepts.STENCH] or percept[Percepts.BUMP]):
            self.run = True
            self.turn_left()
            return Actions.LEFT

        if self.run:
            if self.orientation != Orientation.SOUTH:
                self.turn_left()
                return Actions.LEFT
            if self.pos == (0, 0):
                return Actions.CLIMB
        else:
            if self.has_gold:
                if self.pos == (0, 0):
                    return Actions.CLIMB
                if self.orientation != Orientation.SOUTH:
                    self.turn_left()
                    return Actions.LEFT

            for (x, y), status in self.knowledge_base.items():
                if status == "safe" and (x, y) not in self.visited:
                    return self.move_forward()

            if self.possible_wumpus_locations and not self.arrow_used:
                return self.use_arrow()

        return self.move_forward()
'''


import heapq

from wumpus import Actions, Orientation, Percepts


class Agent:

    def __init__(self, size=(4, 4)):
        self.size = size
        self.knowledge_base = {}
        self.possible_pit_locations = set()
        self.possible_wumpus_locations = set()
        self.arrow_used = False
        self.visited = set()
        self.run = False
        self.has_gold = False
        self.orientation = Orientation.NORTH
        self.pos = (0, 0)

    def new_episode(self):
        self.pos = (0, 0)
        self.orientation = Orientation.NORTH
        self.has_gold = False
        self.run = False
        self.arrow_used = False
        self.visited = set()
        self.knowledge_base = {
            (0, 0): "safe",
        }
        self.visited.add(self.pos)

    def turn_left(self):
        self.orientation = (self.orientation - 1) % 4

    def turn_right(self):
        self.orientation = (self.orientation + 1) % 4

    def move_forward(self):
        dx = 1 * (self.orientation == Orientation.EAST) + (-1) * (self.orientation == Orientation.WEST)
        dy = 1 * (self.orientation == Orientation.NORTH) + (-1) * (self.orientation == Orientation.SOUTH)
        new_pos = (self.pos[0] + dx, self.pos[1] + dy)

        if 0 <= new_pos[0] < self.size[0] and 0 <= new_pos[1] < self.size[1]:
            self.pos = new_pos
            self.visited.add(self.pos)
        return Actions.FORWARD

    def update_knowledge_base(self, percept):
        if percept[Percepts.BREEZE]:
            self.knowledge_base[self.pos] = "breezy"
            self.add_possible_pit_locations()
        elif percept[Percepts.STENCH]:
            self.knowledge_base[self.pos] = "stenchy"
            self.add_possible_wumpus_locations()
        elif percept[Percepts.GLITTER]:
            self.knowledge_base[self.pos] = "glitter"
        else:
            self.knowledge_base[self.pos] = "safe"

    def add_possible_pit_locations(self):
        neighbors = self.get_neighbors(self.pos)
        for neighbor in neighbors:
            if neighbor not in self.visited and neighbor not in self.knowledge_base:
                self.possible_pit_locations.add(neighbor)

    def add_possible_wumpus_locations(self):
        neighbors = self.get_neighbors(self.pos)
        for neighbor in neighbors:
            if neighbor not in self.visited and neighbor not in self.knowledge_base:
                self.possible_wumpus_locations.add(neighbor)

    def infer_safe_squares(self):
        keys = list(self.knowledge_base.keys())
        for (x, y) in keys:
            status = self.knowledge_base[(x, y)]
            if status == "breezy":
                neighbors = self.get_neighbors((x, y))
                for nx, ny in neighbors:
                    if (nx, ny) not in self.knowledge_base:
                        self.knowledge_base[(nx, ny)] = "unknown"
            elif status == "safe":
                neighbors = self.get_neighbors((x, y))
                for nx, ny in neighbors:
                    if (nx, ny) not in self.knowledge_base:
                        self.knowledge_base[(nx, ny)] = "safe"

    def get_neighbors(self, pos):
        x, y = pos
        return [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]

    def use_arrow_logically(self):
        if not self.arrow_used and self.possible_wumpus_locations:
            self.arrow_used = True
            # Shoot in the direction of a suspected Wumpus location
            return Actions.SHOOT
        return None

    def find_safe_path(self, target):
        # Implement a pathfinding algorithm like A*
        pass

    def get_action(self, percept, reward):
        self.update_knowledge_base(percept)
        self.infer_safe_squares()

        if percept[Percepts.GLITTER]:
            self.has_gold = True
            return Actions.GRAB

        if (not self.run) and (percept[Percepts.BREEZE] or percept[Percepts.STENCH] or percept[Percepts.BUMP]):
            self.run = True
            self.turn_left()
            return Actions.LEFT

        if self.run:
            if self.orientation != Orientation.SOUTH:
                self.turn_left()
                return Actions.LEFT
            if self.pos == (0, 0):
                return Actions.CLIMB
        else:
            if self.has_gold:
                if self.pos == (0, 0):
                    return Actions.CLIMB
                if self.orientation != Orientation.SOUTH:
                    self.turn_left()
                    return Actions.LEFT

            for (x, y), status in self.knowledge_base.items():
                if status == "safe" and (x, y) not in self.visited:
                    return self.move_forward()

            if self.possible_wumpus_locations and not self.arrow_used:
                return self.use_arrow_logically()

        return self.move_forward()








    



















           
























           





