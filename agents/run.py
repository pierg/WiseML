import gym_minigrid
import gym
import time

from envelopes.patterns.envelopes_light import *
from stable_baselines.bench import Monitor

from stable_baselines.common.policies import MlpPolicy, MlpLstmPolicy, MlpLnLstmPolicy
from stable_baselines.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines import PPO2

from agents.utils_functions import *
from configurations import config_grabber as cg

config = cg.Configuration.grab()
env_id = config.env_name
n_timesteps = config.n_timesteps

args = get_args()

n_cpu = 4
env = SubprocVecEnv([lambda: gym.make(env_id) for i in range(n_cpu)])

model_id = "PPO2_" + env_id + "_" + n_timesteps + "ts"
model = PPO2.load("./trained_models/" + model_id)
print("Model Loaded!")

# Enjoy trained agent
obs = env.reset()
while True:
    action, _states = model.predict(obs)
    obs, rewards, dones, info = env.step(action)
    env.render()


