# Spiking Neural Networks for Quadruped Gait Learning
A project researching the efficacy of Spiking Neural Networks based neural networks for reinforcement learning of walking for quadrupeds. I worked on this project with @LakshBhambhani, @FahimChoudhury007, and @EdwardShiBerkeley, intially as a part of our EECS206B final project at UC Berkeley.

## Overview
This project explores the application of Spiking Neural Networks (SNNs) for reinforcement learning-based gait optimization in quadruped robots. SNNs, inspired by biological neural networks, model the communication between neurons through discrete events called spikes, offering potential advantages in speed and energy efficiency compared to traditional artificial neural networks (ANNs).
The project aims to implement SNNs for unsupervised control of a real-world quadruped robot, the PuppyPi, and evaluate their performance in learning to walk compared to a benchmark multilayer perceptron (MLP) reinforcement learning approach.

## Key Contributions

-Pioneering effort in implementing SNN-based reinforcement learning for unsupervised control of a physical quadruped robot.
-Successful implementation of an SNN-based reinforcement learning agent, capable of learning a steady standing position on the PuppyPi robot.
-Comparative evaluation of the SNN approach against a traditional MLP-based reinforcement learning benchmark for quadruped gait learning.
-Identification of challenges and limitations in the current implementation, providing insights for future research directions.

## Novelty: Applying SNNs on Actual Hardware
A key novelty and pioneering aspect of this project was the implementation of SNN-based reinforcement learning for unsupervised control of a real-world quadruped robot. Prior to this work, SNN approaches for quadruped control had only been explored in simulation environments. Our group was the first to semi-successfully implement an SNN-based reinforcement learning algorithm on physical quadruped hardware, which can be used to further study the efficacy of SNNs in robotic applications.
Methodology

Benchmark: Established a traditional ANN-based reinforcement learning gait benchmark using the stable_baselines3 library and a Proximal Policy Optimization (PPO) algorithm with a pre-built MLP policy.
SNN Implementation: Developed an SNN-based reinforcement learning agent by modifying the activation function of the MLP policy to incorporate spiking neuron dynamics, effectively transforming the network into an SNN.
Evaluation: Trained and evaluated both the MLP and SNN-based agents in a simulated environment, and subsequently tested their performance on the physical PuppyPi robot.

## Results

The MLP-based approach successfully learned an "ape-like" gait cycle, allowing the robot to move forward by rotating its leg motors and hopping.
The SNN-based approach learned a steady standing position but could not achieve successful gait walking behavior.
Challenges included modeling complexities due to the lack of an accurate XML file for the PuppyPi robot, resulting in a sim2real gap, and potential mismatch between the SNN model and conventional computing hardware.


[Simulation RL-MLP](https://youtu.be/wbziPAfzTOY)
[Simulation RL-SNN](https://youtu.be/OcE09OZipx0?t=106)
[Real World RL-MLP Demo](https://youtu.be/tYcQa-Ws68Q)
[Real World RL-SNN Demo](https://youtu.be/57tLUr4B-6M)

## Future Work

Explore the integration of neuromorphic hardware architectures, which are better suited for SNN computation, potentially unlocking the full potential of SNN-based reinforcement learning for quadruped control.
Address the sim2real gap by incorporating more accurate physical models and environmental conditions in the simulation.
Investigate the potential energy efficiency benefits of SNNs by leveraging neuromorphic hardware.

This project represents a significant step forward in applying SNNs to real-world robotic systems and paves the way for further exploration in this promising field.




## How to Run
### Training Quadruped Locomotion using Reinforcement Learning in Mujoco

A custom gymnasium environment for training quadruped locomotion using reinforcement learning in the Mujoco simulator. The environment has been set up for the Unitree Go1 robot, however, it can be easily extended to train other robots as well. 

There are two MJCF models provided for the Go1 robot. One tuned for position control with a proportional controller, and one model which directly takes in torque values for end-to-end training.

### Setup
```bash
python -m pip install -r requirements.txt
```

### Train
```bash
python train.py --run train
```

### Displaying Trained Models 

```bash
python train.py --run test --model_path <path to model zip file>
```

<details>
  <summary>Additional arguments for customizing training and testing</summary>

    usage: train.py [-h] --run {train,test} [--run_name RUN_NAME] [--num_parallel_envs NUM_PARALLEL_ENVS]
                    [--num_test_episodes NUM_TEST_EPISODES] [--record_test_episodes] [--total_timesteps TOTAL_TIMESTEPS]      
                    [--eval_frequency EVAL_FREQUENCY] [--model_path MODEL_PATH] [--seed SEED]

    optional arguments:
    -h, --help            show this help message and exit
    --run {train,test}
    --run_name RUN_NAME   Custom name of the run. Note that all runs are saved in the 'models' directory and have the       
                            training time prefixed.
    --num_parallel_envs NUM_PARALLEL_ENVS
                            Number of parallel environments while training
    --model_path MODEL_PATH
                            Path to the model (.zip)
    --seed SEED

</details>

## Acknowledgements 
The base framework for the envirnoment and reward setup was given by: https://github.com/nimazareian/quadruped-rl-locomotion, special thanks to the authors of "quadruped-rl-locomotion" for inspriation on how to implement gait learning for quadrupeds. 


