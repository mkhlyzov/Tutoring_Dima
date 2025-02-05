import numpy as np
from wumpus import Actions, Orientation, Percepts, Wumpus

NUM_PERCEPTIONS = 5

AGENT_WEIGHTS: str = "" # example: "0.1111, -1.4, 0.53, ..."

class NeuralNetwork:
    def __init__(self, *args, **kwargs):
        pass

    def proba(
        self,
        obs: np.ndarray
    ) -> np.ndarray:
        ...

    def from_string(self, weights: str) -> None:
        ...
    
    def dumps(self) -> str:
        return ""


class Agent:
    map: np.ndarray
    pos_agent: tuple
    orientation_agent: Orientation
    has_arrow: bool
    has_gold: bool
    wumpus_alive: bool

    def __init__(self, size=(4,4)):
        self.size = size
        self.new_episode()
        self.brains = NeuralNetwork()
        self.brains.from_string(AGENT_WEIGHTS)

    def new_episode(self):
        self.map = -np.ones((*self.size, NUM_PERCEPTIONS), dtype=int)
        self.pos_agent = (0, 0)
        self.orientation_agent = Orientation.NORTH
        self.has_arrow = True
        self.has_gold = False
        self.wumpus_alive = True

    def get_action(self, percept, reward) -> Actions:
        self._update_game_state(percept)
        obs = self._get_observation()
        action_probas = self.brains.proba(obs) # np.array(6)
        action = np.argmax(action_probas)

        return action

    def _get_observation(self):
        s1 = [
            *self.pos_agent,
            self.orientation_agent,
            self.has_arrow,
            self.has_gold,
            self.wumpus_alive
        ]
        s2 = self.map.flatten()
        obs = np.hstack([s1, s2])
        return obs
    
    def _update_game_state(self, percept):
        self.map[self.pos_agent] = percept
        if percept[Percepts.SCREAM] == 1:
            self.wumpus_alive = False
    
    
    def _act_forward(self) -> Actions:
        if self.orientation_agent == Orientation.NORTH:
            self.pos_agent = (self.pos_agent[0], self.pos_agent[1] + 1)
        elif self.orientation_agent == Orientation.SOUTH:
            self.pos_agent = (self.pos_agent[0], self.pos_agent[1] - 1)
        elif self.orientation_agent == Orientation.EAST:
            self.pos_agent = (self.pos_agent[0] + 1, self.pos_agent[1])
        elif self.orientation_agent == Orientation.WEST:
            self.pos_agent = (self.pos_agent[0] - 1, self.pos_agent[1])

        x = np.clip(self.pos_agent[0], 0, self.size[0] - 1)
        y = np.clip(self.pos_agent[1], 0, self.size[1] - 1)
        self.pos_agent = (x, y)

        return Actions.FORWARD
    
    def _act_left(self) -> Actions:
        self.orientation_agent = (self.orientation_agent - 1) % 4
        return Actions.LEFT
    
    def _act_right(self) -> Actions:
        self.orientation_agent = (self.orientation_agent + 1) % 4
        return Actions.RIGHT
    
    def _act_grab(self) -> Actions:
        if self.map[self.pos_agent][Percepts.GLITTER] == 1:
            self.has_gold = True
        return Actions.GRAB
    
    def _act_shoot(self) -> Actions:
        self.has_arrow = False
        return Actions.SHOOT

    def _act_climb(self) -> Actions:
        return Actions.CLIMB



class WumpusEnv(Wumpus):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def step(self, action):
        return super().step(action)
    
    def reset(self):
        return super().reset()
