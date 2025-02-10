import importlib
import time

import aufgabe2_mike
import numpy as np

importlib.reload(aufgabe2_mike)

import stable_baselines3
import torch
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import DummyVecEnv

size = (4, 4)
p_pit = 0.
with_wumpus = True
time_max = 100

env_fn_easy_v1 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0., seed=None, Tmax=time_max, with_wumpus=False,
))
env_fn_easy_v2 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0., seed=None, with_wumpus=False, Tmax=(15, 100), start_orientation=None,
))
env_fn_easy_v3 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0., seed=None, Tmax=(90, 100), with_wumpus=False, start_pos=None, start_orientation=None
))
env_fn_easy_v4 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0., seed=None, Tmax=(15, 100), with_wumpus=False, start_pos=None, start_orientation=None
))

env_fn_medium_v1 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0., seed=None, Tmax=time_max, with_wumpus=True, #start_pos=None, start_orientation=None
))
env_fn_medium_v2 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0., seed=None, Tmax=(40, 81), with_wumpus=True, start_orientation=None,
))

env_fn_hard_v1 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0.05, seed=None, Tmax=time_max, with_wumpus=False,
))
env_fn_hard_v2 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=(0.05, 0.20), seed=None, Tmax=(40, 100), with_wumpus=False,
))

env_fn_expert_v1 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0.05, seed=None, Tmax=time_max, with_wumpus=True, #start_pos=None, start_orientation=None
))
env_fn_expert_v2 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=(0.05, 0.20), seed=None, Tmax=(40, 100), with_wumpus=True, start_orientation=None,
))
env_fn_expert_v3 = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=(0.0, 0.25), seed=None, Tmax=(40, 100), with_wumpus=True, start_orientation=None,
))

env_fn_validation = lambda: Monitor(aufgabe2_mike.WumpusEnv(
    size=size, p_pit=0.20, seed=None, Tmax=50,
))



# vec_env = DummyVecEnv([env_fn_easy_v2] * 16 + [env_fn_medium_v2] * 64 + [env_fn_expert_v2] * 48)
vec_env = DummyVecEnv([env_fn_easy_v2] * 16 + [env_fn_medium_v2] * 8 + [env_fn_expert_v3] * 104)
torch.set_num_threads(2)

policy_kwargs = dict(
    net_arch=[256,256],
    activation_fn=torch.nn.Tanh,                     
    optimizer_class=torch.optim.SGD,
    optimizer_kwargs=dict(
        weight_decay=0e-4,
        momentum=0.9,
        nesterov=True
    ),
)
agent = stable_baselines3.PPO(
    "MlpPolicy",
    vec_env,
    learning_rate=1e-3,
    batch_size = 512,
    ent_coef=0.03,
    verbose=1,
    stats_window_size=1000,
    policy_kwargs=policy_kwargs,
)
proxy_model = stable_baselines3.PPO.load("ppo_sgd_256", env=vec_env)
agent.policy.load_state_dict(proxy_model.policy.state_dict())
# agent.set_parameters("ppo_sgd")

for i in range(5):
    if i != 0:
        time.sleep(60)
    agent.learn(total_timesteps=5_000_000, log_interval=1)
    agent.save(f"ppo_sgd_{i+1}")
