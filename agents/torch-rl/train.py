#!/usr/bin/env python3

import argparse

import gym
import time
import datetime
import torch
import torch_rl
import sys
import random, string
import copy, os, shutil
from configurations import config_grabber as cg
from configurations import args_grabber as ag
import logging

try:
    from envelopes.mtsa.envelopes import SafetyEnvelope as MTSASafetyEnvelope
    import gym_minigrid
except ImportError:
    pass

import utils
from model import ACModel

logging.getLogger("transitions.core").setLevel(logging.WARNING)

script_args = ag.get_args()

if script_args.n_timesteps != -1:
    print("...setting up the n_timesteps to " + str(script_args.n_timesteps) + "...")
    cg.Configuration.set("n_timesteps", script_args.n_timesteps)

if script_args.env_name:
    cg.Configuration.set("env_name", script_args.env_name)

config = cg.Configuration.grab()
log_dir = "./storage/"

# Parse arguments

parser = argparse.ArgumentParser()
parser.add_argument("--n_timesteps", required=False,
                    help="n_timesteps")
parser.add_argument("--folder_name", action="store_true", default=False,
                    help="folder_name")
parser.add_argument("--config_file_name", required=False,
                    help="config_file_name")
parser.add_argument("--algo", required=False,
                    help="algorithm to use: a2c | ppo (REQUIRED)")
parser.add_argument("--env", required=False,
                    help="name of the environment to train on (REQUIRED)")
parser.add_argument("--model", default=None,
                    help="name of the model (default: {ENV}_{ALGO}_{TIME})")
parser.add_argument("--seed", type=int, default=1,
                    help="random seed (default: 1)")
parser.add_argument("--procs", type=int, default=16,
                    help="number of processes (default: 16)")
parser.add_argument("--frames", type=int, default=10**7,
                    help="number of frames of training (default: 10e7)")
parser.add_argument("--log-interval", type=int, default=1,
                    help="number of updates between two logs (default: 1)")
parser.add_argument("--save-interval", type=int, default=0,
                    help="number of updates between two saves (default: 0, 0 means no saving)")
parser.add_argument("--tb", action="store_true", default=False,
                    help="log into Tensorboard")
parser.add_argument("--frames-per-proc", type=int, default=None,
                    help="number of frames per process before update (default: 5 for A2C and 128 for PPO)")
parser.add_argument("--discount", type=float, default=0.99,
                    help="discount factor (default: 0.99)")
parser.add_argument("--lr", type=float, default=7e-4,
                    help="learning rate for optimizers (default: 7e-4)")
parser.add_argument("--gae-lambda", type=float, default=0.95,
                    help="lambda coefficient in GAE formula (default: 0.95, 1 means no gae)")
parser.add_argument("--entropy-coef", type=float, default=0.01,
                    help="entropy term coefficient (default: 0.01)")
parser.add_argument("--value-loss-coef", type=float, default=0.5,
                    help="value loss term coefficient (default: 0.5)")
parser.add_argument("--max-grad-norm", type=float, default=0.5,
                    help="maximum norm of gradient (default: 0.5)")
parser.add_argument("--recurrence", type=int, default=1,
                    help="number of steps the gradient is propagated back in time (default: 1)")
parser.add_argument("--optim-eps", type=float, default=1e-5,
                    help="Adam and RMSprop optimizer epsilon (default: 1e-5)")
parser.add_argument("--optim-alpha", type=float, default=0.99,
                    help="RMSprop optimizer apha (default: 0.99)")
parser.add_argument("--clip-eps", type=float, default=0.2,
                    help="clipping epsilon for PPO (default: 0.2)")
parser.add_argument("--epochs", type=int, default=4,
                    help="number of epochs for PPO (default: 4)")
parser.add_argument("--batch-size", type=int, default=256,
                    help="batch size for PPO (default: 256)")
parser.add_argument("--no-instr", action="store_true", default=True,
                    help="don't use instructions in the model")
parser.add_argument("--no-mem", action="store_true", default=False,
                    help="don't use memory in the model")
args = parser.parse_args()


# Overriding args with config
args.algo = config.rl_parameters.algo
args.env = config.env_name
args.frames = config.rl_parameters.frames
args.recurrence = config.rl_parameters.recurrence
args.save_interval = config.rl_parameters.save_interval
args.tb = config.rl_parameters.tb
if hasattr(config.rl_parameters, "learning_rate"):
    args.lr = config.rl_parameters.learning_rate

random_id = ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(4))

n_timesteps = args.frames
if args.config_file_name is not None:
    config_name = args.config_file_name + "__" + str(random_id)
else:
    config_name = "main__" + str(random_id)
cg.Configuration.set("config_name", config_name)
cg.Configuration.set("debug_mode", False)

if script_args.folder_name:
    args.model = config_name
    log_dir_config = log_dir + config_name + "/"
else:
    args.model = config.rl_parameters.model
    log_dir_config = log_dir + config.rl_parameters.model + "/"

print("using " + log_dir_config + " folder to store the results")

os.makedirs(log_dir_config, exist_ok=True)
shutil.copy("../../configurations/main.json", log_dir_config)
shutil.move(log_dir_config + "main.json", log_dir_config + "configuration.txt")


# Define run dir

suffix = datetime.datetime.now().strftime("%y-%m-%d-%H-%M-%S")
default_model_name = "{}_{}_seed{}_{}".format(args.env, args.algo, args.seed, suffix)
model_name = args.model or default_model_name
model_dir = utils.get_model_dir(model_name)

# Define logger, CSV writer and Tensorboard writer

logger = utils.get_logger(model_dir)
csv_file, csv_writer = utils.get_csv_writer(model_dir)
if args.tb:
    from tensorboardX import SummaryWriter
    tb_writer = SummaryWriter(model_dir)

# Log command and all script arguments

logger.info("{}\n".format(" ".join(sys.argv)))
logger.info("{}\n".format(args))

# Set seed for all randomness sources

utils.seed(args.seed)

# Generate environments

envs = []
for i in range(args.procs):
    env = gym.make(args.env)
    if config.envelope:
        if config.envelope_type == "mtsa":
            env = MTSASafetyEnvelope(env)
    env.seed(args.seed + 10000*i)
    envs.append(env)

# Define obss preprocessor

preprocess_obss = utils.ObssPreprocessor(model_dir, envs[0].observation_space)

# Load training status

try:
    status = utils.load_status(model_dir)
except OSError:
    status = {"num_frames": 0, "update": 0}

# Define actor-critic model

try:
    acmodel = utils.load_model(model_dir)
    logger.info("Model successfully loaded\n")
except OSError:
    acmodel = ACModel(preprocess_obss.obs_space, envs[0].action_space, not args.no_instr, not args.no_mem)
    logger.info("Model successfully created\n")
logger.info("{}\n".format(acmodel))

if torch.cuda.is_available():
    acmodel.cuda()
logger.info("CUDA available: {}\n".format(torch.cuda.is_available()))

# Define actor-critic algo

if args.algo == "a2c":
    algo = torch_rl.A2CAlgo(envs, acmodel, args.frames_per_proc, args.discount, args.lr, args.gae_lambda,
                            args.entropy_coef, args.value_loss_coef, args.max_grad_norm, args.recurrence,
                            args.optim_alpha, args.optim_eps, preprocess_obss)
elif args.algo == "ppo":
    algo = torch_rl.PPOAlgo(envs, acmodel, args.frames_per_proc, args.discount, args.lr, args.gae_lambda,
                            args.entropy_coef, args.value_loss_coef, args.max_grad_norm, args.recurrence,
                            args.optim_eps, args.clip_eps, args.epochs, args.batch_size, preprocess_obss)
else:
    raise ValueError("Incorrect algorithm name: {}".format(args.algo))

# Train model

num_frames = status["num_frames"]
total_start_time = time.time()
update = status["update"]


latest_steps_to_goal = -1

while num_frames < args.frames:
    # Update model parameters

    update_start_time = time.time()
    logs = algo.update_parameters()
    update_end_time = time.time()

    if logs["steps_to_goal"] != -1:
        latest_steps_to_goal = logs["steps_to_goal"]


    num_frames += logs["num_frames"]
    update += 1

    # Print logs

    if update % args.log_interval == 0:
        fps = logs["num_frames"]/(update_end_time - update_start_time)
        duration = int(time.time() - total_start_time)
        return_per_episode = utils.synthesize(logs["return_per_episode"])
        rreturn_per_episode = utils.synthesize(logs["reshaped_return_per_episode"])
        num_frames_per_episode = utils.synthesize(logs["num_frames_per_episode"])

        header = ["update", "frames", "FPS", "duration"]
        data = [update, num_frames, fps, duration]
        header += ["rreturn_" + key for key in rreturn_per_episode.keys()]
        data += rreturn_per_episode.values()
        header += ["num_frames_" + key for key in num_frames_per_episode.keys()]
        data += num_frames_per_episode.values()
        header += ["entropy", "value", "policy_loss", "value_loss", "grad_norm", "late_mean_n_steps_to_goal", "steps_to_goal", "n_deaths", "n_violations"]
        data += [logs["entropy"], logs["value"], logs["policy_loss"], logs["value_loss"], logs["grad_norm"], latest_steps_to_goal, logs["steps_to_goal"], logs["n_deaths"], logs["n_violations"]]


        logger.info(
            "U {} | F {:06} | FPS {:04.0f} | D {} | rR:x̄σmM {:.2f} {:.2f} {:.2f} {:.2f} | F:x̄σmM {:.1f} {:.1f} {} {} | H {:.3f} | V {:.3f} | pL {:.3f} | vL {:.3f} | ∇ {:.3f} | lsG {} | sG {} | nD {} | nV {}"
            .format(*data))

        header += ["return_" + key for key in return_per_episode.keys()]
        data += return_per_episode.values()

        if status["num_frames"] == 0:
            csv_writer.writerow(header)
        csv_writer.writerow(data)
        csv_file.flush()

        if args.tb:
            for field, value in zip(header, data):
                tb_writer.add_scalar(field, value, num_frames)

        status = {"num_frames": num_frames, "update": update}
        utils.save_status(status, model_dir)

    # Save vocabulary and model

    if args.save_interval > 0 and update % args.save_interval == 0:
        preprocess_obss.vocab.save()

        if torch.cuda.is_available():
            acmodel.cpu()
        utils.save_model(acmodel, model_dir)
        logger.info("Model successfully saved")
        if torch.cuda.is_available():
            acmodel.cuda()