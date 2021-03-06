#!/usr/bin/env bash

# Sets the main.json as default, if the -c is specifed
# it will use that as config file.
configuration_file="main.json"
configuration_name="main"

n_timesteps=-1
start_training=false
start_tensorboard=false
verbose=false

while getopts c:s:vtb opt; do
    case ${opt} in
        c)
            configuration_name=${OPTARG}
            configuration_file="$configuration_name.json"
            start_training=true
            ;;
        s)
            n_timesteps=${OPTARG}
            start_training=true
            ;;
        v)
            verbose=true
            start_training=true
            ;;
        t)
            start_training=true
            ;;
        b)
            start_tensorboard=true
            ;;
    esac
done


if $start_tensorboard ; then
    echo "...launching tensorboard..."
    tensorboard --logdir=evaluation/tensorboard &
fi


if $start_training ; then
        echo "...environment name is..."
        echo $configuration_file

        if [ $configuration_file -eq "main.json" ]; then
            echo "using default configuration file: $configuration_file"
            cd ./configurations
        else
            echo "...wupdating selected configuration file..."
            cd ./configurations
            echo "using configuration file: $configuration_file"
            yes | cp -rf $configuration_file "main.json"
        fi
        cd ..

        echo "...setting up python environment..."
        PYTHONPATH=../gym-minigrid/:../gym-minigrid/gym_minigrid/:../baselines/:../pytorch-a2c-ppo/:../pytorch-a2c-ppo/torch_rl/:./configurations:./envelopes:./:$PYTHONPATH
        export PYTHONPATH

        echo "...launching the training..."
        cd agents/torch-rl/
        if $verbose ; then
            python3 train.py --n_timesteps=$n_timesteps --config_file_name=$configuration_name --folder_name --verbose
        else
            python3 train.py --n_timesteps=$n_timesteps --config_file_name=$configuration_name --folder_name
        fi
else
        echo "...accessing the container without launching anything..."
        bash
fi


