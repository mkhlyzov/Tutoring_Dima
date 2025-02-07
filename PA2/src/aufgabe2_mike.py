import numpy as np
from wumpus import Actions, Orientation, Percepts, Wumpus

NUM_PERCEPTIONS = 5

AGENT_WEIGHTS: str = "" # example: "0.1111, -1.4, 0.53, ..."

class NeuralNetwork:
    """Simple Neural Network that supports exporting/importing weights
    """
    def __init__(self,
        input_dim: int,
        output_dim: int,
        layers: list[int] | None=None,
        dtype=np.float32
    ):
        if layers is None:
            layers = []

        self.weights: list[np.ndarray] = []
        self.biases: list[np.ndarray] = []
        for input_size, output_size in zip([input_dim] + layers, layers + [output_dim]):
            w = np.random.randn(input_size, output_size).astype(dtype=dtype)
            b = np.zeros(output_size).astype(dtype=dtype)
            self.weights.append(w)
            self.biases.append(b)

    def forward(self, x: np.ndarray):
        def stablemax(x):
            s = (x + 1) * (x >= 0) + (1 / (1 - x)) * (x < 0)
            s /= np.sum(s, axis=-1, keepdims=True)
            return s

        def softmax(x: np.ndarray):
            e_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
            return e_x / e_x.sum(axis=-1, keepdims=True)

        for i, (w, b) in enumerate(zip(self.weights, self.biases)):
            x = np.dot(x, w) + b
            if i < len(self.weights) - 1:
                x = np.tanh(x)
        x = softmax(x)
        return x
    
    def get_weights_flat(self):
        arr = np.concatenate([
            np.concatenate([w.flatten(), b.flatten()])
            for w, b in zip(self.weights, self.biases)
        ])
        return arr
    
    def set_weights_flat(self, flat: np.ndarray):
        new_weights = []
        new_biases = []
        idx = 0
        for w, b in zip(self.weights, self.biases):
            size = w.size + b.size
            new_weights.append(flat[idx:idx+w.size].reshape(w.shape))
            new_biases.append(flat[idx+w.size:idx+w.size+b.size].reshape(b.shape))
            idx += size
        self.weights = new_weights
        self.biases = new_biases

    def to_string(self):
        import base64
        arch = [self.weights[i].shape for i in range(len(self.weights))]
        weights = self.get_weights_flat()
        dtype = weights.dtype

        string_repr = "{};{};{}".format(
            arch,
            dtype,
            base64.b64encode(weights.tobytes() ).decode('ascii'),
        )
        return string_repr
    
    @staticmethod
    def from_string(weights: str):
        import ast  # For safely parsing the architecture string
        import base64

        arch_str, dtype_str, weights_str = weights.split(';', 2)

        arch = ast.literal_eval(arch_str)
        dtype = np.dtype(dtype_str)
        
        input_dim = arch[0][0]
        layers = [shape[1] for shape in arch[:-1]]
        output_dim = arch[-1][1]

        decoded_bytes = base64.b64decode(weights_str.encode('ascii'))
        flat_weights = np.frombuffer(decoded_bytes, dtype=dtype)
        
        net = NeuralNetwork(input_dim, output_dim, layers)
        net.set_weights_flat(flat_weights)
        
        return net

    @classmethod
    def test_myself(cls):
        for _ in range(50):
            input_dim = np.random.randint(10, 100)
            output_dim = np.random.randint(10, 100)
            hidden = [
                np.random.randint(10, 100),
                np.random.randint(10, 100),
                np.random.randint(10, 100),
            ]
            dtype = np.random.choice([np.float16, np.float32, np.float64])

            net = cls(input_dim, output_dim, hidden, dtype=dtype)
            x = np.random.randn(32, input_dim)
            y1 = net.forward(x)
            s = net.to_string()
            net = cls.from_string(s)
            y2 = net.forward(x)

            assert np.allclose(y1, y2)

        print("OK")


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
        obs_example = self._get_observation()
        self.actions = [
            self._act_forward,
            self._act_left, 
            self._act_right ,
            self._act_grab,
            self._act_shoot,
            self._act_climb
        ]
        self.brains = NeuralNetwork(
            input_dim=obs_example.shape[0],
            output_dim=len(self.actions),
            layers=[]
        )
        if len(AGENT_WEIGHTS) > 0:
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
        action_probas = self.brains.farward(obs) # np.array(6)
        action = np.argmax(action_probas)

        return action

    def _get_observation(self):
        s1 = [
            *self.pos_agent, # change encoding
            self.orientation_agent, # change encoding
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


import gymnasium


class WumpusEnv(Wumpus, gymnasium.Env):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = Agent(
            # size=kwargs['size']
        )
        obs_example = self.agent._get_observation()
        self.observation_space = gymnasium.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=obs_example.shape,
            dtype=obs_example.dtype
        )
        self.action_space = gymnasium.spaces.Discrete(
            len(self.agent.actions)
        )
    
    def step(self, action: Actions):
        self.agent.actions[action]()
        obs, reward, term, info = super().step(action)
        obs = self.agent._get_observation()
        return obs, reward, term, False, {}
    
    def reset(self, *args, **kwargs):
        perc = super().reset()
        self.agent.new_episode()
        self.agent._update_game_state(perc)
        obs = self.agent._get_observation()
        return obs, {}

