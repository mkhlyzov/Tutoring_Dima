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

    pos_exit: tuple
    t_max: int
    t: int
    p_pit: float

    def __init__(
        self, size=(4,4),
        p_pit=0.2, t_max=50
    ):
        self.size = size
        self.new_episode()
        self.p_pit = p_pit
        self.t_max = t_max
        self.actions = [
            self._act_forward,
            self._act_left, 
            self._act_right ,
            self._act_grab,
            self._act_shoot,
            self._act_climb
        ]
        obs_example = self._get_observation()
        self.net = NeuralNetwork(
            input_dim=obs_example.shape[0],
            output_dim=len(self.actions),
            layers=[]
        )
        if len(AGENT_WEIGHTS) > 0:
            self.net = NeuralNetwork.from_string(AGENT_WEIGHTS)

    def new_episode(self):
        self.map = -np.ones((*self.size, NUM_PERCEPTIONS), dtype=int)
        self.pos_agent = (0, 0)
        self.orientation_agent = Orientation.NORTH
        self.has_arrow = True
        self.has_gold = False
        self.wumpus_alive = True

        self.pos_exit = self.pos_agent
        self.t = 0

    def get_action(self, percept, reward) -> Actions:
        self._update_game_state(percept)
        obs = self._get_observation()
        action_probas = self.net.forward(obs) # np.array(6)
        a = np.argmax(action_probas)
        # a = np.random.choice(len(self.actions), p=action_probas)
        action = self.actions[a]()

        return action

    def _get_observation(self):
        orientation = np.zeros(4)
        orientation[self.orientation_agent] = 1
        s1 = np.array([
            # *self.pos_agent,
            *orientation,
            self.has_arrow,
            self.has_gold,
            self.wumpus_alive,
            self.map[self.pos_agent][Percepts.GLITTER] == 1,
            np.log10(self.t_max - self.t),
            self.p_pit,
        ], dtype=np.float32)

        # def to_decimal(x):
        #     if x[0] >= 0:
        #         return int(''.join(map(str, x)), 2) / (2**PERCEPT_DIM - 1)
        #     else:
        #         return -1
        # decimal_matrix = np.apply_along_axis(to_decimal, axis=2, arr=self.map)
        # s2 = decimal_matrix.flatten()
        s2 = self.map[:, :, :2].flatten()

        s3 = np.zeros(self.size)
        s3[self.pos_agent] = 1
        s3[self.pos_exit] = -1
        s3 = s3.flatten()

        s = np.concatenate([s1, s2, s3])
        return s
    
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

        self.t += 1

        return Actions.FORWARD
    
    def _act_left(self) -> Actions:
        self.orientation_agent = (self.orientation_agent - 1) % 4
        self.t += 1
        return Actions.LEFT
    
    def _act_right(self) -> Actions:
        self.orientation_agent = (self.orientation_agent + 1) % 4
        self.t += 1
        return Actions.RIGHT
    
    def _act_grab(self) -> Actions:
        if self.map[self.pos_agent][Percepts.GLITTER] == 1:
            self.has_gold = True
        self.t += 1
        return Actions.GRAB
    
    def _act_shoot(self) -> Actions:
        self.has_arrow = False
        self.t += 1
        return Actions.SHOOT

    def _act_climb(self) -> Actions:
        self.t += 1
        return Actions.CLIMB


import gymnasium
import wumpus_mike


class WumpusEnv(wumpus_mike.Wumpus, gymnasium.Env):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.agent = Agent(
            size=self.size, t_max=self.Tmax, p_pit=self.p_pit
        )
        obs_example = self.agent._get_observation()
        self.observation_space = gymnasium.spaces.Box(
            low=-np.inf, high=np.inf,
            shape=obs_example.shape,
            dtype=obs_example.dtype
        )
        self.action_space = gymnasium.spaces.Discrete(
            len(self.agent.actions)
        )
    
    def step(self, action: Actions):
        self.agent.actions[action]()
        perc, reward, term, _ = super().step(action)
        self.agent._update_game_state(perc)
        obs = self.agent._get_observation()
        return obs, reward, term, False, {}
    
    def reset(self, *args, **kwargs):
        perc = super().reset()
        self.agent.new_episode()

        # randomizations for curriculum
        self.agent.t_max = self.Tmax
        self.agent.p_pit = self.p_pit
        self.agent.wumpus_alive = self.wumpus_alive
        self.agent.has_arrow = self.has_arrow
        self.agent.pos_agent = self.pos_agent
        self.agent.pos_exit = self.pos_exit
        self.agent.orientation_agent = self.orientation_agent

        self.agent._update_game_state(perc)
        obs = self.agent._get_observation()
        return obs, {}

