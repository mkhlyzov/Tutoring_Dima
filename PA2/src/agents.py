from wumpus import Orientation, Actions, Percepts

class AgentV1:
    """
    Example agent V1
    """
    def __init__(self, size=(4,4)):
        self.size = size

    def new_epsiode(self):
        self.pos = (0,0)
        self.orientation = Orientation.NORTH
        self.has_gold = False

    def get_action(self, percept):
        if percept[Percepts.GLITTER]:
            self.has_gold = True
            return Actions.GRAB
        if self.has_gold and (self.orientation != Orientation.SOUTH):
            self.orientation = (self.orientation - 1) % 4
            return Actions.LEFT
        if self.has_gold and (self.pos == (0,0)):
            return Actions.CLIMB
        
        action = Actions.FORWARD
        dx = 1 * (self.orientation == Orientation.EAST) + (-1) * (self.orientation == Orientation.WEST)
        dy = 1 * (self.orientation == Orientation.NORTH) + (-1) * (self.orientation == Orientation.SOUTH)
        self.pos = (self.pos[0] + dx, self.pos[1] + dy)

        return Actions.FORWARD
    
class AgentV2:
    """
    Example agent V2
    """
    def __init__(self, size=(4,4)):
        self.size = size

    def new_episode(self):
        self.pos = (0,0)
        self.orientation = Orientation.NORTH
        self.has_gold = False
        self.run = False

    def get_action(self, percept, reward):
        if percept[Percepts.GLITTER]:
            self.has_gold = True
            return Actions.GRAB
        if (not self.run) and (percept[Percepts.BREEZE] or percept[Percepts.STENCH] or percept[Percepts.BUMP]):
            self.run = True
            self.orientation = (self.orientation - 1) % 4
            return Actions.LEFT
        if self.run:
            if (self.orientation != Orientation.SOUTH):
                self.orientation = (self.orientation - 1) % 4
                return Actions.LEFT
            if (self.pos == (0,0)):
                return Actions.CLIMB
        else:
            if self.has_gold and (self.orientation != Orientation.SOUTH):
                self.orientation = (self.orientation - 1) % 4
                return Actions.LEFT
            if self.has_gold and (self.pos == (0,0)):
                return Actions.CLIMB
        
        action = Actions.FORWARD
        dx = 1 * (self.orientation == Orientation.EAST) + (-1) * (self.orientation == Orientation.WEST)
        dy = 1 * (self.orientation == Orientation.NORTH) + (-1) * (self.orientation == Orientation.SOUTH)
        self.pos = (self.pos[0] + dx, self.pos[1] + dy)

        return Actions.FORWARD