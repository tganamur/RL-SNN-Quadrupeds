import argparse
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple, Type, Union

from gymnasium import spaces

import gymnasium as gym
from stable_baselines3 import PPO, TD3, SAC
from stable_baselines3.common.callbacks import EvalCallback
from stable_baselines3.common.vec_env import SubprocVecEnv
from stable_baselines3.common.env_util import make_vec_env
from go1_mujoco_env import Go1MujocoEnv
from tqdm import tqdm
import torch as th
from torch import nn
import snntorch as snn

from stable_baselines3 import PPO, DDPG
from stable_baselines3.common.policies import ActorCriticPolicy
import spikingjelly
from spikingjelly.activation_based import neuron, encoding, functional, surrogate, layer

MODEL_DIR = "models"
LOG_DIR = "logs"

class extract_tensor(nn.Module):
    def forward(self,x):
        # Output shape (batch, features, hidden)
        tensor, _ = x
        # Reshape shape (batch, hidden)
        return tensor

class CustomNetwork(nn.Module):
    """
    Custom network for policy and value function.
    It receives as input the features extracted by the features extractor.

    :param feature_dim: dimension of the features extracted with the features_extractor (e.g. features from a CNN)
    :param last_layer_dim_pi: (int) number of units for the last layer of the policy network
    :param last_layer_dim_vf: (int) number of units for the last layer of the value network
    """

    def __init__(
        self,
        feature_dim: int,
        last_layer_dim_pi: int = 12,
        last_layer_dim_vf: int = 12,
    ):
        super().__init__()

        # IMPORTANT:
        # Save output dimensions, used to create the distributions
        self.latent_dim_pi = last_layer_dim_pi
        self.latent_dim_vf = last_layer_dim_vf
        
        # print("HELLO")
        # print(feature_dim)

        # Policy network
        self.policy_net = nn.Sequential(
            # nn.Flatten(),
            # nn.Linear(feature_dim, feature_dim*2),
            # neuron.IFNode(step_mode='m'),
            # nn.Dropout(), 
            # nn.Linear(feature_dim*2, last_layer_dim_pi), 
            # nn.ReLU() 

            
            
            nn.Flatten(),
            neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan()),
            nn.Linear(feature_dim, feature_dim*2),
            nn.ReLU(),
            nn.Dropout(), 
            nn.Linear(feature_dim*2, last_layer_dim_pi), 
            nn.ReLU()
            
            # nn.Flatten(),
            # neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan()),
            # nn.LSTM(feature_dim, feature_dim*2),
            # extract_tensor(),
            # nn.Linear(feature_dim*2, last_layer_dim_pi),
            # nn.ReLU()
            
            
            # nn.Flatten(), 
            # nn.Linear(feature_dim, last_layer_dim_pi),
            # neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan())
        )
        # Value network
        self.value_net = nn.Sequential(
            # Fails to move past 24,567 steps
            # nn.Flatten(),
            # nn.Linear(feature_dim, feature_dim*2),
            # neuron.IFNode(step_mode='m'),
            # nn.Dropout(), 
            # nn.Linear(feature_dim*2, last_layer_dim_vf), 
            # nn.ReLU() 
            # neuron.IFNode(step_mode='m')

            
            # Stand capable, basic linear model
            nn.Flatten(),
            neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan()),
            nn.Linear(feature_dim, feature_dim*2),
            nn.ReLU(),
            nn.Dropout(), 
            nn.Linear(feature_dim*2, last_layer_dim_vf), 
            nn.ReLU()
            
            # LSTMs kinda just fall off
            # nn.Flatten(),
            # neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan()),
            # nn.LSTM(feature_dim, feature_dim*2),
            # extract_tensor(),
            # nn.Linear(feature_dim*2, last_layer_dim_vf),
            # nn.ReLU()
            
            
            # nn.Flatten(), 
            # nn.Linear(feature_dim, last_layer_dim_vf),
            # neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan())
        )
        
        functional.set_step_mode(self.value_net, step_mode='m')
        functional.set_step_mode(self.policy_net, step_mode='m')


    def forward(self, features: th.Tensor) -> Tuple[th.Tensor, th.Tensor]:
        """
        :return: (th.Tensor, th.Tensor) latent_policy, latent_value of the specified network.
            If all layers are shared, then ``latent_policy == latent_value``
        """
        return self.forward_actor(features), self.forward_critic(features)

    def forward_actor(self, features: th.Tensor) -> th.Tensor:
        return self.policy_net(features)

    def forward_critic(self, features: th.Tensor) -> th.Tensor:
        return self.value_net(features)
    
class CNN(nn.Module):
    def __init__(self, input_channels, output_size):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(input_channels, 96, kernel_size=3, stride=1, padding=1)
        self.pool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv2 = nn.Conv2d(96, 256, kernel_size=3, stride=1, padding=1)
        self.pool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.conv3 = nn.Conv2d(256, 384, kernel_size=3, stride=1, padding=1)
        self.conv4 = nn.Conv2d(384, 384, kernel_size=3, stride=1, padding=1)
        self.conv5 = nn.Conv2d(384, 256, kernel_size=3, stride=1, padding=1)
        self.pool5 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.pool6 = nn.AdaptiveAvgPool2d((8, 8))
        self.fc1 = nn.Linear(48, 4096)
        self.fc2 = nn.Linear(4096, 4096)
        self.fc3 = nn.Linear(4096, 12)
        self.relu = nn.ReLU()
        self.dropout = nn.Dropout()
        self.flatten = nn.Flatten()
        self.latent_dim_pi = 12
        self.latent_dim_vf = 12
        
    def forward(self, x):
        return self.forward_actor(x), self.forward_critic(x)
        
    def forward_actor(self, x):
        # x = self.conv1(x)
        # x = self.relu(x)
        # x = self.pool1(x)
        # x = self.conv2(x)
        # x = self.relu(x)
        # x = self.pool2(x)
        # x = self.conv3(x)
        # x = self.relu(x)
        # x = self.conv4(x)
        # x = self.relu(x)
        # x = self.conv5(x)
        # x = self.relu(x)
        # x = self.pool5(x)
        # x = self.pool6(x)
        # x = x.view(-1, 256 * 8 * 8)
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc3(x)
        return x
    
    def forward_critic(self, x):
        # x = self.conv1(x)
        # x = self.relu(x)
        # x = self.pool1(x)
        # x = self.conv2(x)
        # x = self.relu(x)
        # x = self.pool2(x)
        # x = self.conv3(x)
        # x = self.relu(x)
        # x = self.conv4(x)
        # x = self.relu(x)
        # x = self.conv5(x)
        # x = self.relu(x)
        # x = self.pool5(x)
        # x = self.pool6(x)
        # x = x.view(-1, 256 * 8 * 8)
        x = self.flatten(x)
        x = self.fc1(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.relu(x)
        x = self.dropout(x)
        x = self.fc3(x)
        return x
    
# class NonSpikingLIFNode(neuron.LIFNode):
#     def forward(self, dv: th.Tensor):
#         self.neuronal_charge(dv)
#         # self.neuronal_fire()
#         # self.neuronal_reset()
#         return self.v

# class ActorCritic(nn.Module):
#     def __init__(self, num_inputs, num_outputs, hidden_size, T=16, std=0.0):
#         super(ActorCritic, self).__init__()
        
#         self.latent_dim_pi = num_outputs
#         self.latent_dim_vf = num_outputs

#         self.critic = nn.Sequential(
#             nn.Linear(num_inputs, hidden_size),
#             # neuron.IFNode(),
#             nn.Linear(hidden_size, num_outputs),
#             # nn.ReLU()
#             # neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan())
#             # NonSpikingLIFNode(tau=2.0)
#         )

#         self.actor = nn.Sequential(
#             nn.Linear(num_inputs, hidden_size),
#             # neuron.IFNode(),
#             nn.Linear(hidden_size, num_outputs),
#             # nn.ReLU()
#             # neuron.LIFNode(tau=4.0, surrogate_function=surrogate.ATan())
#             # NonSpikingLIFNode(tau=2.0)
#         )

#         self.log_std = nn.Parameter(th.ones(1, num_outputs) * std)

#         self.T = T

#     def forward(self, x):
#         for t in range(self.T):
#             self.critic(x)
#             self.actor(x)
#         value = self.critic[-1].v
#         mu    = self.actor[-1].v
#         std   = self.log_std.exp().expand_as(mu)
#         dist  = th.normal(mu, std)
#         return dist, value


class CustomActorCriticPolicy(ActorCriticPolicy):
    def __init__(
        self,
        observation_space: spaces.Space,
        action_space: spaces.Space,
        lr_schedule: Callable[[float], float],
        *args,
        **kwargs,
    ):
        # Disable orthogonal initialization
        kwargs["ortho_init"] = False
        super().__init__(
            observation_space,
            action_space,
            lr_schedule,
            # Pass remaining arguments to base class
            *args,
            **kwargs,
        )


    def _build_mlp_extractor(self) -> None:
        self.mlp_extractor = CNN(self.features_dim, self.features_dim)

# Define the SNN layer using SpikingJelly
class SpikingNeuron(neuron.BaseNode):
    def __init__(self, input_size, output_size, tau_m=20, tau_s=10):
        super().__init__(input_size, output_size)
        self.fc = nn.Linear(input_size, output_size)
        self.tau_m = tau_m
        self.tau_s = tau_s
        self.reset_parameters()

    def reset_parameters(self):
        nn.init.xavier_uniform_(self.fc.weight)
        nn.init.zeros_(self.fc.bias)

    def forward(self, x, mem_potential, syn_current):
        cur_spike = functional.multi_spike(mem_potential, syn_current, self.tau_m, self.tau_s)
        mem_potential = functional.mem_update(mem_potential, cur_spike, self.tau_m)
        syn_current = self.fc(x)
        return cur_spike, mem_potential, syn_current

# Create a custom SNN policy
class CustomSNNPolicy(ActorCriticPolicy):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _build_mlp_extractor(self):
        self.mlp_extractor = nn.Sequential(
            SpikingNeuron(self.features_dim, 64),
            nn.ReLU(),
            SpikingNeuron(64, 64),
            nn.ReLU(),
            nn.Linear(64, self.action_dim)
        )
        
alpha = 0.9
beta = 0.85

batch_size = 128

num_inputs = 784
num_hidden = 1000
num_outputs = 10

num_steps = 100


# Define Network
class Net(nn.Module):
   def __init__(self):
      super().__init__()
      
      self.latent_dim_pi = 12
      self.latent_dim_vf = 12

      # initialize layers
      self.fc1 = nn.Linear(num_inputs, num_hidden)
      self.lif1 = snn.Synaptic(alpha=alpha, beta=beta)
      self.fc2 = nn.Linear(num_hidden, num_outputs)
      self.lif2 = snn.Synaptic(alpha=alpha, beta=beta)

   def forward(self, x):
      spk1, syn1, mem1 = self.lif1.init_synaptic()
      spk2, syn2, mem2 = self.lif2.init_synaptic()

      spk2_rec = []  # Record the output trace of spikes
      mem2_rec = []  # Record the output trace of membrane potential

      for step in range(num_steps):
            cur1 = self.fc1(x)
            spk1, syn1, mem1 = self.lif1(cur1, syn1, mem1)
            cur2 = self.fc2(spk1)
            spk2, syn2, mem2 = self.lif2(cur2, syn2, mem2)

            spk2_rec.append(spk2)
            mem2_rec.append(mem2)

      return th.stack(spk2_rec, dim=0), th.stack(mem2_rec, dim=0)


def train(args):
    vec_env = make_vec_env(
        Go1MujocoEnv,
        env_kwargs={"ctrl_type": args.ctrl_type},
        n_envs=args.num_parallel_envs,
        seed=args.seed,
        vec_env_cls=SubprocVecEnv,
    )

    train_time = time.strftime("%Y-%m-%d_%H-%M-%S")
    if args.run_name is None:
        run_name = f"{train_time}"
    else:
        run_name = f"{train_time}-{args.run_name}"

    model_path = f"{MODEL_DIR}/{run_name}"
    print(
        f"Training on {args.num_parallel_envs} parallel training environments and saving models to '{model_path}'"
    )

    # Evaluate the model every eval_frequency for 5 episodes and save
    # it if it's improved over the previous best model.
    eval_callback = EvalCallback(
        vec_env,
        best_model_save_path=model_path,
        log_path=LOG_DIR,
        eval_freq=args.eval_frequency,
        n_eval_episodes=5,
        deterministic=True,
        render=False,
    )


    if args.model_path is not None:
        model = PPO.load(
            path=args.model_path, env=vec_env, verbose=1, tensorboard_log=LOG_DIR
        )
    else:
        # Default PPO model hyper-parameters give good results
        # TODO: Use dynamic learning rate
        policy_kwargs = dict(activation_fn=SNNActivation)
        model = PPO("MlpPolicy", vec_env, verbose=1, policy_kwargs=policy_kwargs, tensorboard_log=LOG_DIR, learning_rate=0.0001)
        # functional.set_step_mode(model, step_mode='m')
        # model = PPO(CustomActorCriticPolicy, vec_env, verbose=1, tensorboard_log=LOG_DIR)

    model.learn(
        total_timesteps=args.total_timesteps,
        reset_num_timesteps=False,
        progress_bar=True,
        tb_log_name=run_name,
        callback=eval_callback,
    )
    # Save final model
    model.save(f"{model_path}/final_model")


def test(args):
    model_path = Path(args.model_path)

    if not args.record_test_episodes:
        # Render the episodes live
        env = Go1MujocoEnv(
            ctrl_type=args.ctrl_type,
            render_mode="human",
        )
        inter_frame_sleep = 0.016
    else:
        # Record the episodes
        env = Go1MujocoEnv(
            ctrl_type=args.ctrl_type,
            render_mode="rgb_array",
            camera_name="tracking",
            width=1920,
            height=1080,
        )
        env = gym.wrappers.RecordVideo(
            env, video_folder="recordings/", name_prefix=model_path.parent.name
        )
        inter_frame_sleep = 0.0

    model = PPO.load(path=model_path, env=env, verbose=1)

    num_episodes = args.num_test_episodes
    total_reward = 0
    total_length = 0
    
    thigh_range = (-0.686, 4.5)
    knee_range = (-2.82, -0.888)
    output_range = (1.5, -1.3)
    puppy_actions = []
    
    for _ in tqdm(range(num_episodes)):
        obs, _ = env.reset()
        env.render()

        ep_len = 0
        ep_reward = 0
        while True:
            action, _ = model.predict(obs, deterministic=True)
            obs, reward, terminated, truncated, info = env.step(action)
            
            # print(action)
            
            # puppy_action = [[0., 0., 0., 0.],
            #                 [scale(action[1], thigh_range, output_range), scale(action[4], thigh_range, output_range), scale(action[7], thigh_range, output_range), scale(action[10], thigh_range, output_range)],
            #                 [scale(action[2], thigh_range, output_range), scale(action[5], thigh_range, output_range), scale(action[8], thigh_range, output_range), scale(action[11], thigh_range, output_range)]]
            
            puppy_action = [[0., 0., 0., 0.],
                            [action[1], action[4], action[7], action[10]],
                            [action[2], action[5], action[8], action[11]]]
            
            puppy_actions.append(puppy_action)
            
            ep_reward += reward
            ep_len += 1

            # Slow down the rendering
            time.sleep(inter_frame_sleep)

            if terminated or truncated:
                print(f"{ep_len=}  {ep_reward=}")
                break

        total_length += ep_len
        total_reward += ep_reward

    print(
        f"Avg episode reward: {total_reward / num_episodes}, avg episode length: {total_length / num_episodes}"
    )
    
    print(puppy_actions)
    
    
class SNNActivation(nn.Module):
    def __init__(self, threshold=0.5, decay=0.9):
        super(SNNActivation, self).__init__()
        self.threshold = threshold
        self.decay = decay
        self.membrane_potential = None

    def forward(self, x):
        if self.membrane_potential is None or self.membrane_potential.size() != x.size():
            self.membrane_potential = th.zeros_like(x)

        self.membrane_potential = self.decay * self.membrane_potential + x
        # print(self.membrane_potential)
        spikes = self.membrane_potential >= self.threshold

        self.membrane_potential = th.where(spikes, th.zeros_like(x), self.membrane_potential)
        return spikes.float()
    

def scale(input_value, input_range, output_range):
    """
    Scale input value from input range to output range.
    
    Parameters:
        input_value (float): The value to scale.
        input_range (tuple): The input range (min, max).
        output_range (tuple): The output range (min, max).
        
    Returns:
        float: The scaled value.
    """
    # Unpack input range
    input_min, input_max = input_range
    
    # Unpack output range
    output_min, output_max = output_range
    
    # Scale the input value
    scaled_value = ((input_value - input_min) / (input_max - input_min)) * (output_max - output_min) + output_min
    
    return scaled_value


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=str, required=True, choices=["train", "test"])
    parser.add_argument(
        "--run_name",
        type=str,
        default=None,
        help="Custom name of the run. Note that all runs are saved in the 'models' directory and have the training time prefixed.",
    )
    parser.add_argument(
        "--num_parallel_envs",
        type=int,
        default=12,
        help="Number of parallel environments while training",
    )
    parser.add_argument(
        "--num_test_episodes",
        type=int,
        default=5,
        help="Number of episodes to test the model",
    )
    parser.add_argument(
        "--record_test_episodes",
        action="store_true",
        help="Whether to record the test episodes or not. If false, the episodes are rendered in the window.",
    )
    parser.add_argument(
        "--total_timesteps",
        type=int,
        default=5_000_000,
        help="Number of timesteps to train the model for",
    )
    parser.add_argument(
        "--eval_frequency",
        type=int,
        default=10_000,
        help="The frequency of evaluating the models while training",
    )
    parser.add_argument(
        "--model_path",
        type=str,
        default=None,
        help="Path to the model (.zip). If passed for training, the model is used as the starting point for training. If passed for testing, the model is used for inference.",
    )
    parser.add_argument(
        "--ctrl_type",
        type=str,
        choices=["torque", "position"],
        default="position",
        help="Whether the model should control the robot using torque or position control.",
    )
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args()

    if args.run == "train":
        os.makedirs(MODEL_DIR, exist_ok=True)
        os.makedirs(LOG_DIR, exist_ok=True)
        train(args)
    elif args.run == "test":
        if args.model_path is None:
            raise ValueError("--model_path is required for testing")
        test(args)
