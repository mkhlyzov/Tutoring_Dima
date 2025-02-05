from wumpus import Wumpus
from wumpus import Actions, Percepts, Orientation
from tqdm import tqdm
import numpy as np
from aufgabe2 import Agent

size = (4,4)
n_repeat = 1000

if __name__ == "__main__":   
    env = Wumpus(seed=2025, size=size)

    cum_rewards = np.zeros(n_repeat)
    agent = Agent(size=size)
    for run in tqdm(range(n_repeat)):
        agent.new_episode()

        terminated = False
        percept = env.reset()
        reward = 0
        while not terminated:
            action = agent.get_action(percept, reward)
            # tqdm.write(f"{action}")
            percept, reward, terminated, info = env.step(action)
            # tqdm.write("   percept: " + str(percept))
            cum_rewards[run] += reward

        tqdm.write(f"[{run+1:02d}] Total reward={cum_rewards[run]}")

    # compute stats
    average_total_reward = np.mean(cum_rewards)
    print(f"Average total reward: {average_total_reward}")

    # TODO plot histogram