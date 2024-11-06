#!/bin/bash

sudo apt-get install -y python3-pip tmux

# Create and activate a new python venv
python3 -m venv ../venv
source ../venv/bin/activate

# Install the required python packages
pip install -r ../requirements.txt
